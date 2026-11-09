"""Serialized, durable single-attempt admission before any supervised model work."""

from __future__ import annotations

import asyncio
import os
import sqlite3
import stat
import time
import uuid
from typing import TYPE_CHECKING, Any

from .native_admission import Admission, Qualification
from .protocol import Observation, TelemetryStatus
from .recording import ReplayReader, public_data

if TYPE_CHECKING:
    from .controller import Controller


class SupervisedNative:
    def __init__(self, controller: Controller, source: str) -> None:
        self.controller = controller
        self.source = source
        self.nonce = uuid.uuid4().hex
        self.fence_nonce = uuid.uuid4().hex
        self.world = ""
        self.failure: str | None = None
        self.admission: Admission | None = None
        self.qualification: Qualification | None = None
        self.horizon: Observation | None = None
        self.terminal: TelemetryStatus | None = None
        self.deadline: float | None = None
        self.ready = False
        self.confirmed = False
        self.buffer: list[dict[str, Any]] = []
        self.lock = asyncio.Lock()
        self.peer: tuple[int, int, int] | None = None
        self.original_observe_only = controller.observe_only
        controller.model_admission_closed = True

    def abort(self, reason: str) -> None:
        if self.failure is None:
            self.failure = reason
            self.controller.close_admission()
            if self.controller.benchmark_stops:
                self.controller.benchmark_stops.reason = reason
            if self.controller.recorder:
                for bot in self.controller.recorder.manifests:
                    self.controller.recorder.emit(bot, "gap", {"reason": reason})

    def check_peer(self, path: str) -> bool:
        try:
            info = os.stat(path, follow_symlinks=False)
            if not stat.S_ISSOCK(info.st_mode):
                raise ValueError("not a socket")
            identity = (info.st_dev, info.st_ino, info.st_uid)
            if self.peer is not None and identity != self.peer:
                raise ValueError("peer replaced")
            self.peer = identity
            return True
        except (OSError, ValueError):
            self.abort("native_peer_changed")
            return False

    def request(self) -> None:
        if not self.world or self.failure or self.confirmed:
            return
        c = self.controller
        assert c.roster is not None
        if self.admission is None:
            c.send(
                {
                    "version": 1,
                    "type": "telemetry_admit",
                    "world": self.world,
                    "bot_id": next(iter(c.roster)),
                    "nonce": self.nonce,
                }
            )
        elif self.horizon is not None:
            c.send(
                {
                    "version": 1,
                    "type": "telemetry_fence",
                    "world": self.world,
                    "bot_id": self.admission.bot_id,
                    "nonce": self.fence_nonce,
                    "admission_nonce": self.nonce,
                }
            )

    async def handle(self, packet: dict[str, Any]) -> None:
        async with self.lock:
            if self.failure:
                return
            try:
                await self._handle(packet)
            except (
                ValueError,
                KeyError,
                TypeError,
                OSError,
                TimeoutError,
                sqlite3.Error,
            ):
                self.abort("native_admission_invalid")

    async def _handle(self, packet: dict[str, Any]) -> None:
        c = self.controller
        kind = packet.get("type")
        world = packet.get("world")
        if self.world and world != self.world:
            self.abort("world_changed")
            return
        if kind == "hello":
            caps = packet.get("capabilities", {})
            if (
                packet.get("version") != 1
                or not isinstance(world, str)
                or not 0 < len(world) <= 80
                or not isinstance(caps, dict)
                or any(
                    caps.get(key) != 1
                    for key in (
                        "lifecycle_telemetry",
                        "telemetry_delivery",
                        "telemetry_admission",
                        "telemetry_fence",
                    )
                )
                or caps.get("keep_awake") is not True
            ):
                self.abort("native_capability_missing")
                return
            self.world = world
            await c._handle(packet)
            self.request()
            return
        if not self.world:
            # No inference, intents, or clock can start before a trusted hello.
            if len(self.buffer) >= 256:
                self.abort("native_admission_backlog")
            else:
                self.buffer.append(packet)
            return
        bot_data = packet.get("bot")
        bot = packet.get(
            "bot_id", bot_data.get("id") if isinstance(bot_data, dict) else None
        )
        if type(bot) is not int or c.roster is None or bot not in c.roster:
            self.abort("native_bot_changed")
            return
        if kind == "telemetry_admitted":
            admitted = Admission.model_validate(packet)
            if self.qualification is not None:
                self.qualification.retry(admitted)
                self._check_failure()
                return
            assert c.benchmark_stops is not None
            self.qualification = Qualification(
                admitted,
                nonce=self.nonce,
                world=self.world,
                bot_id=bot,
                source=self.source,
                horizon_ms=max(1800000, int(c.benchmark_stops.horizon * 1000)),
            )
            assert c.recorder is not None and c.benchmark_stops is not None
            run = c.recorder.manifests[bot].run_id
            if c.store.get("native_admission", run) is not None:
                self.abort("worker_restart")
                return
            # No controller work is admitted while either durable write is pending.
            await asyncio.wait_for(
                asyncio.to_thread(c.recorder.admit_native, admitted), timeout=1.5
            )
            c.store.put("native_admission", run, admitted.model_dump())
            self.admission = admitted
            stops = c.benchmark_stops
            stops.world, stops.deaths_base = self.world, admitted.deaths
            stops.native_start_ms = admitted.captured_ms
            # Receipt of the reply alone cannot open a clock or disable startup timeout.
            # Controller starts watchdogs only after B has arrived and O0 is released.
            backlog, self.buffer = self.buffer, []
            for queued in backlog:
                await self._handle(queued)
                if self.failure:
                    return
            return
        if self.admission is None:
            if len(self.buffer) >= 256:
                self.abort("native_admission_backlog")
            else:
                self.buffer.append(packet)
            return
        q = self.qualification
        assert q is not None
        if not self.ready and kind not in {"telemetry", "telemetry_status"}:
            if len(self.buffer) >= 256:
                self.abort("native_admission_backlog")
            else:
                self.buffer.append(packet)
            return
        if kind == "telemetry":
            if packet["sequence"] < self.admission.begin_sequence:
                return
            q.telemetry(packet)
            self._check_failure()
            if self.failure:
                return
            await c._handle(packet)
            if not self.ready:
                self.ready = True
                if not c.admission_ended:
                    c.model_admission_closed = False
                    c.observe_only = self.original_observe_only
                await c._handle(self.admission.observation.model_dump())
                waiting, self.buffer = self.buffer, []
                for queued in waiting:
                    await self._handle(queued)
                    if self.failure:
                        return
            return
        if kind == "telemetry_status":
            q.complete(
                packet
            )  # Validate faults even before horizon/terminal readiness.
            self._check_failure()
            if self.failure:
                return
            status = TelemetryStatus.model_validate(packet)
            await c._handle(packet)
            if c.recorder and bot in c.recorder.delivery_invalid:
                self.abort("native_status_invalid")
                return
            if status.fence_nonce and (
                status.fence_nonce != self.fence_nonce or self.horizon is None
            ):
                self.abort("native_fence_changed")
                return
            if (
                self.horizon is not None
                and self.deadline is not None
                and time.monotonic() >= self.deadline
                and not self.confirmed
            ):
                self.abort("native_transport_unconfirmed")
                return
            if (
                not self.confirmed
                and self.horizon is not None
                and status.fence_nonce == self.fence_nonce
                and q.complete(packet)
            ):
                self.terminal = status
                self.confirmed = True
                c.record(
                    bot,
                    "lifecycle",
                    {"phase": "native_terminal_fence", **status.model_dump()},
                    "native-terminal-fence",
                )
            return
        if kind == "observation":
            if packet["sequence"] < self.admission.observation.sequence:
                return
            q.observe(packet)
            self._check_failure()
            if self.failure:
                return
            if self.horizon is None and q.horizon is not None:
                self.horizon = q.horizon
                self.deadline = time.monotonic() + 3
                c.close_admission()  # Synchronous cutoff, before any await/model spawn.
                assert c.recorder is not None
                if not c.recorder.freeze_horizon(self.horizon):
                    self.abort("recorder_error")
                    return
                self.request()
            # O0 is dispatched only after B; later observations cannot bypass it.
            if self.ready:
                await c._handle(packet)
                if (
                    self.horizon is not None
                    and packet["sequence"] == self.horizon.sequence
                ):
                    assert (
                        c.benchmark_stops is not None
                        and c.benchmark_stops.last is not None
                    )
                    c.benchmark_stops.freeze_window(
                        self.horizon.captured_ms, c.benchmark_stops.last
                    )
            return
        if self.ready:
            await c._handle(packet)

    def _check_failure(self) -> None:
        if self.qualification and self.qualification.failure:
            self.abort(self.qualification.failure)

    def durable_complete(self) -> bool:
        """Check committed keys and exact boundaries after bounded close/flush."""
        c, a, terminal = self.controller, self.admission, self.terminal
        if (
            self.failure
            or not self.confirmed
            or a is None
            or terminal is None
            or self.horizon is None
        ):
            return False
        assert c.recorder is not None
        reader = ReplayReader(c.recorder.config.path)
        run = c.recorder.manifests[a.bot_id].run_id
        if reader.run(run)["incomplete"]:
            return False
        expected = a.begin_sequence
        admitted = initial = horizon = fence = False
        prefix = f"native:{a.world}:{a.bot_id}:"
        for event in reader.all_events(run):
            data = event["data"]
            if event["key"] == "native-admission":
                admitted = data == {
                    "phase": "native_admitted",
                    **public_data(a.model_dump()),
                }
            if event["kind"] == "sample":
                initial |= data == public_data(
                    a.observation.model_dump(exclude={"lease", "messages"})
                )
            if event["key"] == "horizon-final-sample":
                horizon = data == public_data(
                    self.horizon.model_dump(exclude={"lease", "messages"})
                )
            if event["key"] == "native-terminal-fence":
                fence = data == {
                    "phase": "native_terminal_fence",
                    **terminal.model_dump(),
                }
            if event["key"].startswith(prefix):
                sequence = int(event["key"][len(prefix) :])
                if sequence <= terminal.issued_sequence:
                    if sequence != expected:
                        return False
                    frame = (
                        self.qualification.frame(sequence)
                        if self.qualification
                        else None
                    )
                    if frame is None:
                        return False
                    payload = {
                        "world": a.world,
                        **public_data(
                            frame.model_dump(
                                exclude={
                                    "version",
                                    "type",
                                    "world",
                                    "sequence",
                                    "bot_id",
                                }
                            )
                        ),
                    }
                    if frame.captured_ms > self.horizon.captured_ms:
                        payload = {"phase": "post_horizon_telemetry", "data": payload}
                    if data != payload:
                        return False
                    expected += 1
        return (
            admitted
            and initial
            and horizon
            and fence
            and expected == terminal.issued_sequence + 1
        )
