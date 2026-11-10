"""Attested native/fake qualification through the current canonical campaign runner.

No provider credentials, external clients or production volumes. The fake is a
declared scripted choice policy; gameplay, clock and stop decisions are real.
"""

import argparse
import asyncio
import datetime
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from m5_current_lowstock import cleanup_evidence, native_build_contract
from m5_qualification_gates import qualify_run
from m5_status_capture import ExternalEpoch
from m5_status_runner_adapter import (BOT_NAME, CaptureDriver, ExactProcessedTransport,
                                      StatusEvidence, cleanup_observer)

from canary_brain import benchmark, runtime
from canary_brain.recording import ReplayReader
from canary_brain.replay import summary
from canary_brain.store import Store

ROOT = Path(__file__).resolve().parents[2]
WORLD = Path("/tmp/canary-lifecycle-qa-world.otbm")


def short_status_options(args):
    """Reject trial-only switches before touching a fixture or output path."""
    short_native = (args.status_capture_opt_in and args.mode == "native"
                    and args.seconds == 10)
    requested = (args.status_script_id != 77
                 or args.status_first_periodic is not None
                 or args.status_period is not None
                 or args.world_map is not None
                 or args.status_hold_first_fetch
                 or args.status_terminate_log_after_observed)
    if requested and not short_native:
        raise ValueError("short status options require opt-in native 10s mode")
    if not short_native:
        return WORLD, 540.0, 10.0
    if args.world_map is None:
        raise ValueError("short status capture requires a private --world-map")
    if args.world_map.is_symlink():
        raise ValueError("short status world map cannot be a symlink")
    world = args.world_map.resolve(strict=True)
    private_root = args.fixture_root.resolve().parent
    if (not world.is_file() or private_root.stat().st_mode & 0o077
            or world.stat().st_mode & 0o077
            or not world.is_relative_to(args.fixture_root.resolve().parent)):
        raise ValueError("short status world map must be a private fixture file")
    if ((args.status_first_periodic is None) != (args.status_period is None)):
        raise ValueError("short status cadence requires both switches")
    if args.status_first_periodic is None:
        return world, 540.0, 10.0
    if (args.status_first_periodic, args.status_period) != (1.0, 3.0):
        raise ValueError("short status cadence must be 1/3 seconds")
    if args.status_hold_first_fetch and args.status_terminate_log_after_observed:
        raise ValueError("fault injections are separate trials")
    return world, 1.0, 3.0


class HeldFetchAfterFence:
    """Hold one real processed reply until shutdown has durably fenced capture."""

    def __init__(self, transport, emit):
        self.transport = transport
        self.emit = emit
        self.used = False
        self.fenced = asyncio.Event()
        self.held = asyncio.Event()

    async def submit(self, bot_name):
        return await self.transport.submit(bot_name)

    async def fetch(self, command_id):
        status = await self.transport.fetch(command_id)
        if not self.used:
            self.used = True
            self.emit({"event": "test_fetch_held", "command_id": command_id,
                       "at_mono": time.monotonic()})
            self.held.set()
            await self.fenced.wait()
            self.emit({"event": "test_fetch_released_after_fence",
                       "command_id": command_id, "at_mono": time.monotonic()})
        return status

    def release_after_shutdown(self):
        self.fenced.set()


def apply_short_trace_guid(compose, args, guid):
    """Add the native trace switch only to this private ten-second fixture."""
    if args.status_capture_opt_in and args.mode == "native" and args.seconds == 10:
        compose["services"]["game"]["environment"][
            "CANARY_QA_HUNT_PHASE_TRACE_GUID"] = str(guid)
    return compose


async def terminate_owned_log_after_observed(ready, stopped, process, sink, game_id):
    await ready.wait()
    if not stopped.is_set() and process.returncode is None:
        sink({"event": "test_trace_log_termination", "at_mono": time.monotonic(),
              "log_pid": process.pid, "game_container_id": game_id})
        process.terminate()
    # Let read_trace report the resulting EOF. This injector is not itself a
    # reason to finish the observer before the worker's stop event.
    await stopped.wait()


def forbidden(*args, **kwargs):
    raise AssertionError(
        "free qualification cannot read credentials or call a provider"
    )


class ScriptedFake(runtime.FakeProvider):
    async def decide(self, observation, memory=None):
        candidates = {a.id: a.action for a in observation.actions}
        if observation.bot.objective_running:
            return next(
                (k for k, v in candidates.items() if v == "continue"),
                next(iter(candidates)),
            )
        if observation.bot.potions < 10 and "resupply" in candidates:
            return "resupply"
        for preferred in ("hunt:399", "hunt:77", "resupply", "continue"):
            if preferred in candidates:
                return preferred
        return next(iter(candidates))


def current_revision():
    package = ROOT.resolve() / "deployment/brain/src/canary_brain"
    for name, module in (("runtime", runtime), ("benchmark", benchmark)):
        imported = getattr(module, "__file__", None)
        assert imported is not None and Path(imported).resolve() == package / (
            name + ".py"
        ), "qualification imports must resolve from the driver application checkout"
    assert not subprocess.check_output(
        ["git", "-C", str(ROOT), "status", "--porcelain"],
        text=True,
        timeout=30,
        cwd="/",
    ).strip(), "qualification must freeze a clean committed application checkout"
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True, timeout=30, cwd="/"
    ).strip()


class QualificationObserverError(RuntimeError):
    """A failed status observer makes this qualification unavailable."""


async def read_native_status(query):
    identity = int(
        await asyncio.to_thread(
            query,
            "INSERT INTO bot_commands(bot_name,command) VALUES('Grizzle Alyronia','status');SELECT LAST_INSERT_ID();",
        )
    )
    if identity <= 0:
        raise ValueError("native status command has no valid identity")
    for _ in range(20):
        status = await asyncio.to_thread(
            query,
            f"SELECT result FROM bot_commands WHERE id={identity} AND processed=1;",
        )
        if status:
            if not isinstance(status, str) or not re.fullmatch(
                r"Bot 'Grizzle Alyronia': state=[A-Z_]+ pos=\(\d+,\d+,\d+\) active=(?:yes|no)(?: [^\r\n]*)?\s*",
                status,
            ):
                raise ValueError("native status command returned an invalid result")
            return identity, status
        await asyncio.sleep(0.2)
    raise TimeoutError("native status command did not produce a processed result")


async def run_with_status_observer(configuration, stopped, run, observe,
                                   *, strict_cleanup=False):
    worker = asyncio.create_task(run(configuration, stopped))
    observer = asyncio.create_task(observe(configuration, stopped))
    try:
        completed, _ = await asyncio.wait(
            (worker, observer), return_when=asyncio.FIRST_COMPLETED
        )
        if observer in completed:
            error = (
                RuntimeError("status observer cancelled unexpectedly")
                if observer.cancelled()
                else observer.exception()
            )
            if error is not None or not stopped.is_set():
                error = error or RuntimeError(
                    "status observer returned before the worker stopped"
                )
                (configuration.state_file.parent / "observer-error.json").write_text(
                    json.dumps(
                        {
                            "error_type": type(error).__name__,
                            "at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
                            "scope": "Qualification observer failure; worker stopped and result must be rejected",
                        },
                        indent=2,
                    )
                )
                stopped.set()
                await asyncio.gather(worker, return_exceptions=True)
                raise QualificationObserverError(
                    "Qualification status observer failed"
                ) from error
        await worker
    finally:
        stopped.set()
        if strict_cleanup and not observer.done():
            # Give the observer its normal stop path so it can close and seal
            # completed evidence. An outstanding SQL call remains unsealed.
            await asyncio.wait((observer,), timeout=5)
        for task in (observer, worker):
            if not task.done():
                task.cancel()
        observer_result, _ = await asyncio.gather(
            observer, worker, return_exceptions=True
        )
        if (strict_cleanup and isinstance(observer_result, BaseException)
                and not isinstance(observer_result, asyncio.CancelledError)):
            marker = configuration.state_file.parent / "observer-error.json"
            if not marker.exists():
                marker.write_text(json.dumps({
                    "error_type": type(observer_result).__name__,
                    "at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
                    "scope": "Status observer cleanup failed; result must be rejected",
                }, indent=2))
            if sys.exc_info()[0] is None:
                raise QualificationObserverError(
                    "Qualification status observer failed during cleanup"
                ) from observer_result


def validate_result(
    reader, run, seconds, state, initial, saved, require_progress, mode
):
    data = summary(reader, run["id"])
    events = list(reader.all_events(run["id"]))
    with sqlite3.connect(f"file:{state}?mode=ro", uri=True) as db:
        requests = db.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    status_path = state.parent / "phase-status.jsonl"
    statuses = (
        [json.loads(line) for line in status_path.read_text().splitlines()]
        if status_path.exists()
        else []
    )
    qualification = qualify_run(
        mode=mode,
        run=run,
        events=events,
        metrics=data["metrics"],
        initial=initial,
        saved=saved,
        requests=requests,
        statuses=statuses,
        seconds=seconds,
        require_progress=require_progress,
    )
    qualification["checks"]["status_observer_healthy"] = not (
        state.parent / "observer-error.json"
    ).exists()
    qualification["accepted"] = all(qualification["checks"].values())
    return {
        **qualification,
        "summary": data,
        "requests": requests,
        "status_observation_count": len(statuses),
        "supply_limit": "RESUPPLYING is a native phase; purchase requires stock, bank and confirmed outcome evidence separately.",
    }


async def execute(args):
    os.umask(0o077)
    world, first_periodic, period = short_status_options(args)
    work = args.output.resolve()
    work.mkdir(mode=0o700, exist_ok=False)
    fixture_root = args.fixture_root.resolve()
    frozen = json.loads((fixture_root / "manifest.json").read_text())
    native_revision = frozen["native_build"]["source_revision"]
    assert (
        native_build_contract(frozen, native_revision, frozen["image_id"])
        == frozen["binary_sha256"]
    )
    assert frozen["database_image_id"].startswith("sha256:")
    assert (
        benchmark.fixture_hash(fixture_root / "fixture", world)
        == frozen["fixture_sha256"]
    )
    assert benchmark.file_hash(world) == frozen["world_sha256"]
    if args.status_capture_opt_in and (
        args.status_script_id not in frozen["hunts"]
        or frozen["guid"] != 65001
    ):
        raise ValueError("status capture bindings differ from the frozen fixture")
    actual = await asyncio.to_thread(
        subprocess.check_output,
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--entrypoint",
            "sha256sum",
            frozen["image_id"],
            "/canary/canary",
            "/canary/libbot_engine.so",
        ],
        text=True,
        timeout=30,
        cwd="/",
    )
    assert {
        Path(path).name: value
        for value, path in (line.split() for line in actual.splitlines())
    } == frozen["binary_sha256"]
    revision = current_revision()
    (work / "driver.py").write_bytes(Path(__file__).read_bytes())
    attestation = {
        "source_revision": revision,
        "application_source_revision": revision,
        "native_source_revision": native_revision,
        "native_build": frozen["native_build"],
        "fixture_parent": str(fixture_root),
        "fixture_sha256": frozen["fixture_sha256"],
        "world_sha256": frozen["world_sha256"],
        "game_image": frozen["image_id"],
        "database_image": frozen["database_image_id"],
        "binary_sha256": frozen["binary_sha256"],
        "mode": args.mode,
        "seconds": args.seconds,
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Controlled fixture G; real game with native or explicitly scripted fake choices. No provider inference.",
    }
    if args.status_capture_opt_in:
        attestation["status_capture_opt_in"] = {
            "script_id": args.status_script_id,
            "first_periodic_seconds": first_periodic,
            "period_seconds": period,
            "trace_guid": frozen["guid"] if args.mode == "native" and args.seconds == 10 else None,
            "hold_first_fetch_after_processed": args.status_hold_first_fetch,
            "terminate_own_log_after_observed": args.status_terminate_log_after_observed,
            "source_sha256": {
                name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                for name in ("m5_status_capture.py", "m5_status_runner_adapter.py")
            },
            "qualification_input": True,
        }
    (work / "attestation.json").write_text(json.dumps(attestation, indent=2))
    runtime.read_credential = forbidden
    runtime.AsyncOpenAI = forbidden
    runtime.FakeProvider = ScriptedFake
    base = benchmark.DockerFixture
    active_fixture = None
    game_started = asyncio.Event()
    loop = asyncio.get_running_loop()

    class AttestedFixture(base):
        def prepare(self, participant):
            nonlocal active_fixture
            active_fixture = self
            super().prepare(participant)
            compose = json.loads(self.compose.read_text())
            compose["networks"] = {"default": {"internal": True}}
            compose["services"]["game"]["volumes"].append(f"{self.directory}:/m5")
            apply_short_trace_guid(compose, args, frozen["guid"])
            self.compose.write_text(json.dumps(compose))

        def start_database(self):
            super().start_database()
            for service in ("database",):
                actual = subprocess.check_output(
                    [
                        "docker",
                        "inspect",
                        self.project + "-" + service + "-1",
                        "--format",
                        "{{.Image}}",
                    ],
                    text=True,
                    timeout=30,
                    cwd="/",
                ).strip()
                assert actual == frozen["database_image_id"]

        def start_game(self):
            super().start_game()
            identities = {}
            for service in ("game", "database"):
                identity = subprocess.check_output(
                    [
                        "docker",
                        "inspect",
                        self.project + "-" + service + "-1",
                        "--format",
                        "{{.Image}}",
                    ],
                    text=True,
                    timeout=30,
                    cwd="/",
                ).strip()
                assert (
                    identity
                    == frozen["image_id" if service == "game" else "database_image_id"]
                )
                identities[service] = identity
            self.diagnostics(
                "runtime-image-attestation.json",
                json.dumps(
                    {
                        "at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
                        "project": self.project,
                        "images": identities,
                        "native_build": frozen["native_build"],
                        "application_source_revision": revision,
                    },
                    indent=2,
                ),
            )
            if args.status_capture_opt_in:
                loop.call_soon_threadsafe(game_started.set)

        def close(self):
            try:
                super().close()
            finally:
                self.diagnostics(
                    "resources-cleaned.json",
                    json.dumps(cleanup_evidence(self.project), indent=2),
                )

    async def observe_status(configuration, stopped):
        last = -100.0
        while not stopped.is_set():
            clock = Store(configuration.state_file).get("run_clock", "start")
            elapsed = time.monotonic() - clock["monotonic"] if clock else None
            if (
                elapsed is not None
                and elapsed >= 540
                and elapsed - last >= 10
                and active_fixture
            ):
                last = elapsed

                def query(sql):
                    return active_fixture.command(
                        "exec",
                        "-T",
                        "database",
                        "sh",
                        "-c",
                        'MYSQL_PWD="$MARIADB_PASSWORD" mariadb -u canary canary -N -e "$1"',
                        "sh",
                        sql,
                    )

                identity, status = await read_native_status(query)
                with (configuration.state_file.parent / "phase-status.jsonl").open(
                    "a"
                ) as stream:
                    stream.write(
                        json.dumps(
                            {
                                "elapsed": elapsed,
                                "command_id": identity,
                                "status": status,
                            }
                        )
                        + "\n"
                    )
            await asyncio.sleep(1)

    async def observe_status_opt_in(configuration, stopped):
        await game_started.wait()
        fixture = active_fixture
        if fixture is None:
            raise RuntimeError("opt-in capture has no active fixture")
        container_name = fixture.project + "-game-1"

        def inspect_epoch():
            raw = subprocess.check_output(
                ["docker", "inspect", container_name, "--format",
                 '{"id":{{json .Id}},"image":{{json .Image}},'
                 '"started":{{json .State.StartedAt}},"running":{{json .State.Running}},'
                 '"project":{{json (index .Config.Labels "com.docker.compose.project")}},'
                 '"service":{{json (index .Config.Labels "com.docker.compose.service")}}}'],
                text=True, timeout=10, cwd="/",
            )
            value = json.loads(raw)
            if (value["image"] != frozen["image_id"] or value["running"] is not True
                    or value["project"] != fixture.project or value["service"] != "game"):
                raise ValueError("game identity or state differs from frozen trial")
            return value

        initial = await asyncio.to_thread(inspect_epoch)
        clock = Store(configuration.state_file).get("run_clock", "start")
        if not clock or type(clock.get("monotonic")) not in (int, float):
            raise ValueError("opt-in capture lacks the observed worker clock")
        epoch = ExternalEpoch(
            run_id=f"{experiment.name}:{args.mode}:0",
            world_sha256=frozen["world_sha256"],
            game_container_id=initial["id"],
            game_started_at=initial["started"],
            bot_guid=frozen["guid"], bot_name=BOT_NAME,
            script_id=args.status_script_id,
        )

        def verify_epoch():
            actual = inspect_epoch()
            if (actual["id"] != epoch.game_container_id
                    or actual["started"] != epoch.game_started_at
                    or benchmark.file_hash(world) != epoch.world_sha256):
                raise ValueError("external world or game epoch changed")

        def query(sql):
            return fixture.command(
                "exec", "-T", "database", "sh", "-c",
                'MYSQL_PWD="$MARIADB_PASSWORD" mariadb -u canary canary -N -e "$1"',
                "sh", sql, timeout=10,
            )

        sink = StatusEvidence(
            configuration.state_file.parent / "status-capture-events.jsonl",
            configuration.state_file.parent / "phase-status.jsonl",
            clock["monotonic"],
        )
        transport = ExactProcessedTransport(query, verify_epoch)
        held = HeldFetchAfterFence(transport, sink) if args.status_hold_first_fetch else None
        trace_loss_ready = asyncio.Event()

        def record(row):
            sink(row)
            if row.get("event") == "status_observed":
                trace_loss_ready.set()

        driver = CaptureDriver(epoch, held or transport, record,
                               start_mono=clock["monotonic"],
                               first_periodic=first_periodic, period=period)
        if held is not None:
            original_shutdown = driver.shutdown

            def shutdown_and_release():
                original_shutdown()
                held.release_after_shutdown()

            driver.shutdown = shutdown_and_release
        sink({"event": "trace_source_start", "external_epoch": epoch.__dict__,
              "at_mono": time.monotonic(), "source": "docker_logs_follow"})
        stderr_path = configuration.state_file.parent / "status-trace-source.stderr"
        with stderr_path.open("xb") as stderr:
            try:
                process = await asyncio.create_subprocess_exec(
                    "docker", "logs", "--follow", "--timestamps", "--since",
                    epoch.game_started_at, epoch.game_container_id,
                    stdout=asyncio.subprocess.PIPE, stderr=stderr,
                    limit=65536,
                )
            except BaseException as original:
                try:
                    driver.shutdown()
                except BaseException as cleanup_error:
                    original.add_note(f"status shutdown also failed: {type(cleanup_error).__name__}")
                finally:
                    sink.close()
                raise
            wake = asyncio.Event()
            trace_lines = 0
            matched_hints = 0

            async def read_trace():
                nonlocal trace_lines, matched_hints
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        if not stopped.is_set():
                            driver.source_lost(lines=trace_lines,
                                               matched_hints=matched_hints,
                                               process_exit=process.returncode)
                        return
                    trace_lines += 1
                    if driver.hint(line.decode("utf-8", errors="replace")) is not None:
                        matched_hints += 1
                        wake.set()

            async def schedule_periodic():
                while not stopped.is_set():
                    delay = max(0, driver.next_periodic - time.monotonic())
                    try:
                        await asyncio.wait_for(stopped.wait(), timeout=delay)
                    except asyncio.TimeoutError:
                        driver.periodic_due()
                        wake.set()

            async def drain_capture():
                while not stopped.is_set():
                    await wake.wait()
                    wake.clear()
                    await driver.drain()

            tasks = [asyncio.create_task(coro()) for coro in
                     (read_trace, schedule_periodic, drain_capture)]
            if args.status_terminate_log_after_observed:
                tasks.append(asyncio.create_task(terminate_owned_log_after_observed(
                    trace_loss_ready, stopped, process, sink, epoch.game_container_id)))
            stop_task = asyncio.create_task(stopped.wait())
            completed_normally = False
            try:
                done, _ = await asyncio.wait((*tasks, stop_task),
                                             return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    if task is not stop_task:
                        await task
                if stop_task not in done:
                    raise RuntimeError("opt-in status capture ended before worker")
                completed_normally = True
            finally:
                original = sys.exc_info()[1]
                try:
                    await cleanup_observer(
                        driver, tasks, stop_task, process, sink, stderr,
                        configuration.state_file.parent / "status-capture-seal.json",
                        completed_normally,
                        lines=trace_lines, matched_hints=matched_hints,
                    )
                except BaseException as cleanup_error:
                    if original is None:
                        raise
                    original.add_note(
                        f"status cleanup also failed: {type(cleanup_error).__name__}"
                    )

    original_run = benchmark.run

    async def observed_worker(configuration, stopped):
        await run_with_status_observer(
            configuration, stopped, original_run,
            observe_status_opt_in if args.status_capture_opt_in else observe_status,
            strict_cleanup=args.status_capture_opt_in,
        )

    benchmark.DockerFixture = AttestedFixture
    benchmark.run = observed_worker
    experiment = benchmark.Experiment(
        name="m5-current-"
        + args.mode
        + "-"
        + hashlib.sha256(str(work).encode()).hexdigest()[:10],
        output=work / "runs",
        fixture=fixture_root / "fixture",
        world_map=world,
        budget_file=work / "offline-ledger.sqlite3",
        game_image=frozen["image_id"],
        database_image=frozen["database_image_id"],
        bot_id=65001,
        participants=[benchmark.Participant(name=args.mode, kind=args.mode)],
        repetitions=1,
        seconds=args.seconds,
        source_revision=revision,
        expected_initial_sha256=frozen["fixture_sha256"],
    )
    (work / "experiment.json").write_text(experiment.model_dump_json(indent=2))
    # Root coordinates this single isolated stack; no concurrent game access here.
    await benchmark.run_campaign(experiment, live=True)
    reader = ReplayReader(experiment.output / "recording.sqlite3")
    run = reader.runs()[0]
    directory = experiment.output / (args.mode + "-0")
    saved = json.loads((directory / "saved-character.json").read_text())
    initial = json.loads((experiment.output / "experiment.json").read_text())[
        "preflight"
    ]["character"]
    result = validate_result(
        reader,
        run,
        args.seconds,
        directory / "worker.sqlite3",
        initial,
        saved,
        args.require_progress,
        args.mode,
    )
    cleanup = json.loads((directory / "resources-cleaned.json").read_text())
    images = json.loads((directory / "runtime-image-attestation.json").read_text())
    result["checks"]["resources_cleaned"] = cleanup["resources_cleaned"]
    result["checks"]["runtime_images_verified"] = images["images"] == {
        "game": frozen["image_id"],
        "database": frozen["database_image_id"],
    }
    result["accepted"] = all(result["checks"].values())
    if args.status_capture_opt_in:
        capture_path = directory / "status-capture-events.jsonl"
        canonical_path = directory / "phase-status.jsonl"
        seal_path = directory / "status-capture-seal.json"
        sealed = seal_path.exists() and capture_path.exists() and canonical_path.exists()
        hashes = json.loads(seal_path.read_text()) if sealed else {}
        digest = hashes.get("events_sha256")
        canonical_digest = hashes.get("canonical_sha256")
        sealed = (sealed and digest == hashlib.sha256(capture_path.read_bytes()).hexdigest()
                  and canonical_digest == hashlib.sha256(canonical_path.read_bytes()).hexdigest())
        result["checks"]["status_capture_sealed"] = sealed
        result["accepted"] = all(result["checks"].values())
        result["status_capture_diagnostic"] = {
            "path": str(capture_path),
            "sha256": digest if sealed else None,
            "canonical_sha256": canonical_digest if sealed else None,
            "seal_path": str(seal_path) if sealed else None,
            "sealed": sealed,
            "qualification_input": False,
            "internal_epoch": "not_demonstrated",
        }
    result["attestation"] = attestation
    (work / "qualification.json").write_text(json.dumps(result, indent=2))
    print(
        json.dumps(
            {
                "output": str(work),
                "run_id": run["id"],
                "checks": result["checks"],
                "accepted": result["accepted"],
            }
        ),
        flush=True,
    )
    if not result["accepted"]:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["native", "fake"], required=True)
    parser.add_argument("--seconds", type=int, choices=[10, 1800], default=10)
    parser.add_argument("--status-capture-opt-in", action="store_true",
                        help="write separate command-correlated diagnostic evidence; not a qualification input")
    parser.add_argument("--status-script-id", type=int, default=77,
                        help="frozen fixture hunt identity for opt-in diagnostics")
    parser.add_argument("--world-map", type=Path,
                        help="private world copy for opt-in native 10s capture")
    parser.add_argument("--status-first-periodic", type=float)
    parser.add_argument("--status-period", type=float)
    parser.add_argument("--status-hold-first-fetch", action="store_true",
                        help="test-only: release first processed reply after capture shutdown")
    parser.add_argument("--status-terminate-log-after-observed", action="store_true",
                        help="test-only: terminate only owned docker-logs process")
    parser.add_argument(
        "--require-progress",
        action="store_true",
        help="also require progress for short smokes; mandatory for 1800-second runs",
    )
    asyncio.run(execute(parser.parse_args()))


if __name__ == "__main__":
    main()
