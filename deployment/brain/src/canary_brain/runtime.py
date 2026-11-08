"""Private local IPC, optional local operator console and process lifecycle."""

import asyncio
import fcntl
import json
import os
import re
import signal
import socket
import sqlite3
import stat
import time
from pathlib import Path
from typing import Any, Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field, model_validator

from . import tracing
from .benchmark_stops import Stops, TelemetryTail
from .controller import Controller
from .gateway import GatewayConfiguration, GatewayProvider
from .operator_http import OperatorServer
from .provider import Provider
from .recording import (
    Manifest,
    Recorder,
    RecordingConfiguration,
    RecordingStore,
    ReplayReader,
    digest,
)
from .store import USD, Store
from .testing import FakeProvider


class Configuration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["shadow", "active"] = "shadow"
    provider: Literal["openai", "fake", "litellm", "native"] = "openai"
    socket_directory: Path
    state_file: Path
    budget_file: Path | None = None
    credential_file: Path | None = None
    bots: list[int] = Field(min_length=1, max_length=3)
    monthly_usd: int = Field(default=50, ge=1, le=50)
    decision_timeout: float = Field(default=1.2, ge=0.1, le=30)
    learning: bool = False
    exploration: float = Field(default=0.15, ge=0.05, le=0.5)
    operator_port: int | None = Field(default=None, ge=1024, le=65535)
    operator_host: Literal["127.0.0.1", "0.0.0.0"] = "127.0.0.1"
    recording: RecordingConfiguration | None = None
    gateway: GatewayConfiguration | None = None
    memory_mode: Literal["existing", "frozen", "independent"] = "existing"
    policy_seed: int = 0
    run_cap_nanousd: int | None = Field(default=None, gt=0)
    run_seconds: int | None = Field(default=None, ge=10, le=86400)
    benchmark_supervision: bool = False
    native_source_revision: str | None = Field(default=None, pattern=r"^[a-f0-9]{40}$")

    @model_validator(mode="after")
    def isolated_recording(self) -> "Configuration":
        if self.benchmark_supervision and (
            self.run_seconds is None or self.recording is None or len(self.bots) != 1
        ):
            raise ValueError(
                "benchmark supervision requires a timed, recorded single-bot run"
            )
        if self.benchmark_supervision:
            if (
                self.native_source_revision is None
                and self.recording
                and self.recording.manifests
            ):
                source = self.recording.manifests[0].source_revision
                if re.fullmatch(r"[a-f0-9]{40}", source):
                    self.native_source_revision = source
            if self.native_source_revision is None:
                raise ValueError(
                    "supervised admission requires a pinned native source commit"
                )
            if self.recording and any(
                m.source_revision != self.native_source_revision
                for m in self.recording.manifests
            ):
                raise ValueError("manifest and native source pins must agree")
        if self.provider != "litellm" and self.decision_timeout > 3:
            raise ValueError("legacy decision timeout must not exceed three seconds")
        if self.provider == "litellm" and self.gateway is None:
            raise ValueError(
                "LiteLLM participant requires an explicit gateway configuration"
            )
        if self.run_cap_nanousd is not None and self.recording is None:
            raise ValueError("a run budget requires recording identities")
        if self.recording:
            if self.recording.path.resolve() in {
                self.state_file.resolve(),
                (self.budget_file or self.state_file).resolve(),
            }:
                raise ValueError(
                    "recording must not share the state or budget database"
                )
            manifests = self.recording.manifests
            if manifests and (
                {m.bot_id for m in manifests} != set(self.bots)
                or len(manifests) != len(self.bots)
            ):
                raise ValueError(
                    "recording manifests must match the pilot roster exactly"
                )
        return self


def read_credential(path: Path, variable: str = "OPENAI_API_KEY") -> str:
    if (
        path.is_symlink()
        or not path.is_file()
        or stat.S_IMODE(path.stat().st_mode) & 0o077
    ):
        raise ValueError("credential file must be private and must not be a symlink")
    for line in path.read_text().splitlines():
        name, separator, value = line.partition("=")
        if (
            separator
            and name == variable
            and value.strip()
            and (variable != "OPENAI_API_KEY" or value.startswith("sk-"))
        ):
            return value.strip()
    raise ValueError("credential file has no configured key")


class DatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, controller: Controller, server: str) -> None:
        self.controller, self.server = controller, server
        self.tasks: set[asyncio.Task[None]] = set()

    def datagram_received(self, data: bytes, address: Any) -> None:
        if address != self.server:
            return
        native = self.controller.native_run
        if native and not native.check_peer(self.server):
            return
        if len(data) > 32768 or len(self.tasks) >= 32:
            if native:
                native.abort("worker_ingress_overflow")
            return

        async def consume() -> None:
            try:
                packet = json.loads(data)
                if isinstance(packet, dict):
                    await self.controller.handle(packet)
                elif native:
                    native.abort("native_packet_invalid")
            except (ValueError, KeyError, TypeError):
                if native:
                    native.abort("native_packet_invalid")

        task = asyncio.create_task(consume())
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    def error_received(self, exc: Exception) -> None:
        if self.controller.native_run:
            self.controller.native_run.abort("native_peer_lost")


def recording_failure(recorder: Recorder) -> str | None:
    if recorder.errors or recorder.dropped:
        return "recorder_error"
    try:
        if any(
            ReplayReader(recorder.config.path).run(m.run_id)["incomplete"]
            for m in recorder.manifests.values()
        ):
            return "recording_gap"
    except (sqlite3.Error, OSError, ValueError):
        return "recorder_error"
    return None


async def run(configuration: Configuration, stop: asyncio.Event | None = None) -> None:
    os.umask(0o077)
    directory = configuration.socket_directory
    if directory.is_symlink() or not directory.is_absolute():
        raise ValueError("private socket directory must be an absolute nonsymlink path")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    endpoint, server = directory / "worker.sock", str(directory / "server.sock")
    descriptor = os.open(
        directory / "worker.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
    )
    transport: asyncio.DatagramTransport | None = None
    controller: Controller | None = None
    client: AsyncOpenAI | None = None
    operator: OperatorServer | None = None
    recorder: Recorder | None = None
    benchmark_stops: Stops | None = None
    tail: TelemetryTail | None = None
    tail_observed: float | None = None
    previous_signals: dict[signal.Signals, Any] = {}
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        tracing.configure()
        if endpoint.is_symlink() or (
            endpoint.exists() and not stat.S_ISSOCK(endpoint.stat().st_mode)
        ):
            raise ValueError("worker endpoint must be a socket")
        endpoint.unlink(missing_ok=True)
        store = Store(configuration.state_file, cap=configuration.monthly_usd * USD)
        ledger = Store(
            configuration.budget_file or configuration.state_file,
            cap=configuration.monthly_usd * USD,
        )
        if configuration.recording:
            recording = configuration.recording
            gateway = configuration.gateway
            manifests = recording.manifests or [
                Manifest(
                    run_id=f"{recording.namespace}:{bot}:life",
                    bot_id=bot,
                    lineage=f"{recording.namespace}:{bot}",
                    sample_ms=recording.sample_ms,
                    provider=gateway.provider if gateway else configuration.provider,
                    model=gateway.effective_model
                    if gateway
                    else (
                        "none"
                        if configuration.provider in {"fake", "native"}
                        else "gpt-6-luna"
                    ),
                    memory_mode=configuration.memory_mode,
                    source_revision=configuration.native_source_revision or "unknown",
                )
                for bot in configuration.bots
            ]
            recorder = Recorder(recording, manifests)
            for bot in configuration.bots:
                recorder.emit(
                    bot,
                    "configuration",
                    {
                        "provider": configuration.provider,
                        "memory_mode": configuration.memory_mode,
                        "gateway": gateway.model_dump(exclude={"base_url"})
                        if gateway
                        else None,
                        "configuration_sha256": digest(
                            configuration.model_dump(
                                mode="json", exclude={"credential_file"}
                            )
                        ),
                    },
                )
        if configuration.provider == "openai":
            if configuration.credential_file is None:
                raise ValueError("OpenAI provider requires a private credential file")
            client = AsyncOpenAI(
                api_key=read_credential(configuration.credential_file),
                max_retries=0,
                base_url="https://api.openai.com/v1",
                timeout=45,
            )
            provider: Provider | FakeProvider = Provider(
                ledger,
                client,
                configuration.decision_timeout,
                recorder=recorder,
                run_cap=configuration.run_cap_nanousd,
            )
        elif configuration.provider == "litellm":
            if configuration.credential_file is None or configuration.gateway is None:
                raise ValueError(
                    "LiteLLM requires a private gateway credential and model mapping"
                )
            client = AsyncOpenAI(
                api_key=read_credential(
                    configuration.credential_file, "LITELLM_API_KEY"
                ),
                base_url=configuration.gateway.base_url,
                max_retries=0,
                timeout=45,
            )
            provider = GatewayProvider(
                ledger,
                client,
                configuration.decision_timeout,
                gateway=configuration.gateway,
                recorder=recorder,
                run_cap=configuration.run_cap_nanousd,
            )
        else:
            provider = FakeProvider()

        def send(packet: dict[str, Any]) -> None:
            encoded = json.dumps(
                packet, separators=(",", ":"), ensure_ascii=False
            ).encode()
            if transport is not None and len(encoded) <= 32768:
                transport.sendto(encoded, server)

        benchmark_stops = (
            Stops(
                horizon=configuration.run_seconds or 1800,
                model=configuration.provider != "native",
            )
            if configuration.benchmark_supervision
            else None
        )
        active_controller = Controller(
            store,
            provider,
            send,
            configuration.mode,
            set(configuration.bots),
            configuration.learning,
            configuration.exploration,
            recorder=recorder,
            memory_mode=configuration.memory_mode,
            observe_only=configuration.provider == "native",
            require_benchmark_bridge=bool(
                configuration.recording
                and any(m.experiment for m in configuration.recording.manifests)
            ),
            benchmark_stops=benchmark_stops,
            require_telemetry_delivery=configuration.benchmark_supervision,
            native_source_revision=configuration.native_source_revision
            if configuration.benchmark_supervision
            else None,
        )
        if configuration.memory_mode != "existing":
            import random

            active_controller.policy.rng = random.Random(configuration.policy_seed)
        controller = active_controller
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: DatagramProtocol(active_controller, server),
            family=socket.AF_UNIX,
            local_addr=str(endpoint),
        )
        if configuration.operator_port:
            operator = OperatorServer(
                controller.supervisor,
                configuration.operator_port,
                ReplayReader(configuration.recording.path)
                if configuration.recording
                else None,
            )
            await operator.start(configuration.operator_host)
        stopped = stop or asyncio.Event()
        last_maintenance = time.monotonic()
        launched = last_maintenance
        if stop is None:
            for sig in (signal.SIGINT, signal.SIGTERM):
                previous_signals[sig] = signal.getsignal(sig)
                loop.add_signal_handler(sig, stopped.set)
        while not stopped.is_set():
            remaining = 1.0
            if benchmark_stops:
                now = time.monotonic()
                reason = benchmark_stops.check(now)
                if tail and controller.world != tail.observation.world:
                    reason = "world_changed"
                if benchmark_stops.start is None and now - launched > 240:
                    reason = "startup_timeout"
                if reason in {
                    None,
                    "completed",
                    "deaths_limit",
                    "stalled",
                    "proposal_timeout",
                } and store.get("budget_stop", str(configuration.bots[0])):
                    reason = "budget_stop"
                if recorder:
                    failure = recording_failure(recorder)
                    if failure and not (
                        failure == "recording_gap" and reason == "world_changed"
                    ):
                        reason = failure
                if reason == "completed" and recorder:
                    if tail is None:
                        snapshot = (
                            active_controller.native_run.horizon
                            if active_controller.native_run
                            else None
                        )
                        if snapshot is None:
                            reason = "native_transport_unconfirmed"
                        else:
                            # Freeze the actual observed horizon and deadline before
                            # cancellation can await SQL or an in-flight provider.
                            native = active_controller.native_run
                            assert (
                                native is not None
                                and native.admission is not None
                                and native.deadline is not None
                            )
                            tail = TelemetryTail(snapshot, deadline=native.deadline)
                            tail_observed = (
                                snapshot.captured_ms - native.admission.captured_ms
                            ) / 1000
                            if not recorder.freeze_horizon(snapshot):
                                reason = "recorder_error"
                            else:
                                recorder.emit(
                                    snapshot.bot.id,
                                    "lifecycle",
                                    {
                                        "phase": "native_telemetry_tail_wait",
                                        "world": snapshot.world,
                                        "target_captured_ms": snapshot.captured_ms,
                                        "observed_seconds": tail_observed,
                                    },
                                )
                                active_controller.observe_only = True
                                await active_controller.close()
                                # Re-evaluate all stop priorities and elapsed time;
                                # an operator stop during cancellation must win.
                                continue
                    elif now >= tail.deadline:
                        reason = "native_transport_unconfirmed"
                    elif (
                        active_controller.native_run
                        and active_controller.native_run.confirmed
                        and tail.confirm(
                            active_controller.native_run.terminal,
                            recorder.native.get(tail.observation.bot.id),
                            invalid=tail.observation.bot.id
                            in recorder.delivery_invalid,
                        )
                    ):
                        recorder.emit(
                            tail.observation.bot.id,
                            "lifecycle",
                            {
                                "phase": "native_telemetry_tail_confirmed",
                                "world": tail.observation.world,
                                "target_captured_ms": tail.observation.captured_ms,
                                "required_sequence": tail.required_sequence,
                                "status": tail.cutoff.model_dump()
                                if tail.cutoff
                                else None,
                            },
                        )
                    else:
                        reason = None
                        remaining = min(0.05, tail.deadline - now)
                if reason:
                    details = {
                        "reason": reason,
                        "elapsed_seconds": now - benchmark_stops.start
                        if benchmark_stops.start is not None
                        else None,
                        "observed_seconds": tail_observed
                        if tail
                        else (
                            benchmark_stops.last - benchmark_stops.start
                            if benchmark_stops.last is not None
                            and benchmark_stops.start is not None
                            else None
                        ),
                    }
                    store.put(
                        "run_stop",
                        "end",
                        {
                            **details,
                            "reason": "native_finalizing"
                            if reason == "completed"
                            else reason,
                        },
                    )
                    if recorder:
                        recorder.emit(
                            configuration.bots[0],
                            "lifecycle",
                            {
                                "phase": "run_supervisor_stop",
                                **details,
                                "reason": "native_finalizing"
                                if reason == "completed"
                                else reason,
                            },
                        )
                    if reason != "completed":
                        stopped.set()
                    break
            if configuration.run_seconds is not None and benchmark_stops is None:
                clock = store.get("run_clock", "start")
                if clock is not None:
                    remaining = configuration.run_seconds - (
                        time.monotonic() - clock["monotonic"]
                    )
                    if remaining <= 0:
                        stopped.set()
                        break
            if tail is None and time.monotonic() - last_maintenance >= 60:
                store.prune()
                if ledger.path != store.path:
                    ledger.prune()
                last_maintenance = time.monotonic()
            if controller.native_run:
                controller.native_run.request()
            if controller.world:
                send({"version": 1, "type": "heartbeat", "world": controller.world})
                if tail is None:
                    controller.reconcile()
            try:
                await asyncio.wait_for(stopped.wait(), timeout=min(1, remaining))
            except TimeoutError:
                pass
        if benchmark_stops and store.get("run_stop", "end") is None:
            reason = (
                "budget_stop"
                if store.get("budget_stop", str(configuration.bots[0]))
                else "operator_stop"
            )
            store.put("run_stop", "end", {"reason": reason})
        if protocol.tasks:
            _, waiting = await asyncio.wait(protocol.tasks, timeout=1.0)
            if waiting and controller.native_run:
                controller.native_run.abort("native_ingress_shutdown_timeout")
            for task in waiting:
                task.cancel()
    finally:
        for sig, previous in previous_signals.items():
            asyncio.get_running_loop().remove_signal_handler(sig)
            signal.signal(sig, previous)
        if operator is not None:
            await operator.close()
        if controller is not None:
            await controller.close()
        if transport is not None:
            transport.close()
            endpoint.unlink(missing_ok=True)
        if client is not None:
            await client.close()
        await asyncio.to_thread(tracing.shutdown_bounded)
        if recorder is not None:
            close_failed = await asyncio.to_thread(recorder.close) is False
            if benchmark_stops:
                ending = store.get("run_stop", "end") or {}
                failure = recording_failure(recorder)
                if close_failed and failure is None:
                    failure = "recorder_error"
                if ending.get("reason") in {"completed", "native_finalizing"}:
                    if (
                        benchmark_stops.reason == "world_changed"
                        or (
                            tail
                            and controller
                            and controller.world != tail.observation.world
                        )
                    ) and failure in {None, "recording_gap"}:
                        failure = "world_changed"
                    if failure is None and store.get(
                        "budget_stop", str(configuration.bots[0])
                    ):
                        failure = "budget_stop"
                    if failure is None and stopped.is_set():
                        failure = "operator_stop"
                    if failure is None and (
                        tail is None
                        or not tail.confirm(
                            controller.native_run.terminal
                            if controller and controller.native_run
                            else None,
                            recorder.native.get(configuration.bots[0]),
                            invalid=configuration.bots[0] in recorder.delivery_invalid,
                        )
                    ):
                        failure = "native_transport_unconfirmed"
                if (
                    ending.get("reason") in {"completed", "native_finalizing"}
                    and failure is None
                ):
                    native = controller.native_run if controller else None
                    try:
                        valid = (
                            native is not None
                            and not native.failure
                            and native.check_peer(server)
                            and await asyncio.wait_for(
                                asyncio.to_thread(native.durable_complete), timeout=1.0
                            )
                        )
                    except (TimeoutError, sqlite3.Error, OSError, ValueError):
                        valid = False
                    if valid and native:
                        # Awaited durable proof is not the final decision point:
                        # stops or peer faults can arrive while its thread reads.
                        failure = native.failure
                        if failure is None and not native.check_peer(server):
                            failure = native.failure
                        if failure is None and store.get(
                            "budget_stop", str(configuration.bots[0])
                        ):
                            failure = "budget_stop"
                        if failure is None and stopped.is_set():
                            failure = "operator_stop"
                        valid = failure is None
                    if not valid:
                        failure = failure or (
                            native.failure
                            if native and native.failure
                            else "native_transport_unconfirmed"
                        )
                    else:
                        manifest = next(iter(recorder.manifests.values()))
                        end = ReplayReader(recorder.config.path).run(manifest.run_id)[
                            "duration_ms"
                        ]
                        RecordingStore(recorder.config.path).append(
                            {
                                "run": manifest.run_id,
                                "key": "supervisor-native-qualified",
                                "segment": "supervisor",
                                "t_ms": end + 1,
                                "wall": time.time(),
                                "kind": "lifecycle",
                                "data": {
                                    "phase": "run_supervisor_stop",
                                    **ending,
                                    "reason": "completed",
                                    "after_flush": True,
                                },
                            }
                        )
                        store.put("run_stop", "end", {**ending, "reason": "completed"})
                if failure:
                    if (
                        failure == "recording_gap"
                        and ending.get("reason") == "world_changed"
                    ):
                        failure = "world_changed"
                    store.put("run_stop", "end", {**ending, "reason": failure})
                    for manifest in recorder.manifests.values():
                        end = ReplayReader(recorder.config.path).run(manifest.run_id)[
                            "duration_ms"
                        ]
                        RecordingStore(recorder.config.path).append(
                            {
                                "run": manifest.run_id,
                                "key": "supervisor-final-validation",
                                "segment": "supervisor",
                                "t_ms": end + 1,
                                "wall": time.time(),
                                "kind": "gap"
                                if close_failed or recorder.shutdown_timed_out
                                else "lifecycle",
                                "data": {
                                    "phase": "run_supervisor_stop",
                                    "reason": failure,
                                    "after_flush": True,
                                },
                            }
                        )
        os.close(descriptor)
