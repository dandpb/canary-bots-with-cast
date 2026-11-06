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
import sqlite3
import subprocess
import time
from pathlib import Path

from canary_brain import benchmark, runtime
from canary_brain.recording import ReplayReader
from canary_brain.replay import summary
from canary_brain.store import Store
from m5_current_lowstock import cleanup_evidence, native_build_contract
from m5_qualification_gates import qualify_run

ROOT = Path(__file__).resolve().parents[2]
WORLD = Path("/tmp/canary-lifecycle-qa-world.otbm")


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


async def run_with_status_observer(configuration, stopped, run, observe):
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
        for task in (observer, worker):
            if not task.done():
                task.cancel()
        await asyncio.gather(observer, worker, return_exceptions=True)


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
        benchmark.fixture_hash(fixture_root / "fixture", WORLD)
        == frozen["fixture_sha256"]
    )
    assert benchmark.file_hash(WORLD) == frozen["world_sha256"]
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
    (work / "attestation.json").write_text(json.dumps(attestation, indent=2))
    runtime.read_credential = forbidden
    runtime.AsyncOpenAI = forbidden
    runtime.FakeProvider = ScriptedFake
    base = benchmark.DockerFixture
    active_fixture = None

    class AttestedFixture(base):
        def prepare(self, participant):
            nonlocal active_fixture
            active_fixture = self
            super().prepare(participant)
            compose = json.loads(self.compose.read_text())
            compose["networks"] = {"default": {"internal": True}}
            compose["services"]["game"]["volumes"].append(f"{self.directory}:/m5")
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

                identity = int(
                    await asyncio.to_thread(
                        query,
                        "INSERT INTO bot_commands(bot_name,command) VALUES('Grizzle Alyronia','status');SELECT LAST_INSERT_ID();",
                    )
                )
                status = ""
                for _ in range(20):
                    status = await asyncio.to_thread(
                        query,
                        f"SELECT result FROM bot_commands WHERE id={identity} AND processed=1;",
                    )
                    if status:
                        break
                    await asyncio.sleep(0.2)
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

    original_run = benchmark.run

    async def observed_worker(configuration, stopped):
        await run_with_status_observer(
            configuration, stopped, original_run, observe_status
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
        world_map=WORLD,
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
    parser.add_argument(
        "--require-progress",
        action="store_true",
        help="also require progress for short smokes; mandatory for 1800-second runs",
    )
    asyncio.run(execute(parser.parse_args()))


if __name__ == "__main__":
    main()
