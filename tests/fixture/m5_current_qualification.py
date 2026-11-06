"""Attested native/fake qualification through the current canonical campaign runner.

No provider credentials, external clients or production volumes. The fake is a
declared scripted choice policy; gameplay, clock and stop decisions are real.
"""

import argparse
import asyncio
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
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()


def validate_result(reader, run, seconds, state, saved, require_progress):
    data = summary(reader, run["id"])
    events = list(reader.all_events(run["id"]))
    samples = [e for e in events if e["kind"] == "sample"]
    assert len(samples) >= 2
    stops = [
        e["data"]
        for e in events
        if e["kind"] == "lifecycle" and e["data"].get("phase") == "run_supervisor_stop"
    ]
    with sqlite3.connect(f"file:{state}?mode=ro", uri=True) as db:
        requests = db.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    checks = {
        "completed": run["status"] == "completed" and not run["incomplete"],
        "supervisor_completed": bool(stops) and stops[-1]["reason"] == "completed",
        "exact_horizon_recorded": samples[-1]["t_ms"] - samples[0]["t_ms"]
        >= seconds * 1000,
        "bounded_recorded_duration": samples[-1]["t_ms"] - samples[0]["t_ms"]
        <= (seconds + 5) * 1000,
        "observed_horizon": bool(stops)
        and stops[-1].get("observed_seconds", 0) >= seconds,
        "no_gaps": data["metrics"]["gaps"] == 0,
        "zero_inference": requests == 0,
        "saved_xp_matches": saved["experience"] == samples[-1]["data"]["bot"]["xp"],
    }
    if require_progress:
        checks["positive_xp"] = data["metrics"]["xp_delta"] > 0
        checks["zero_observed_deaths"] = data["metrics"]["deaths"] == 0
        hunts = {
            a["id"]
            for event in samples
            for a in event["data"].get("actions", [])
            if a["action"] == "hunt"
        }
        checks["multiple_hunts_offered"] = len(hunts) >= 2
    status_path = state.parent / "phase-status.jsonl"
    statuses = (
        [json.loads(line) for line in status_path.read_text().splitlines()]
        if status_path.exists()
        else []
    )
    phases = [row.get("status", "") for row in statuses]
    native_cycle = any("phase=LEAVING" in row for row in phases) and any(
        "state=RESUPPLYING" in row for row in phases
    )
    return {
        "checks": checks,
        "accepted": all(checks.values()),
        "summary": data,
        "supervisor": stops,
        "first_sample": samples[0],
        "last_sample": samples[-1],
        "requests": requests,
        "native_hunt_leave_and_supply_phases_observed": native_cycle,
        "status_observation_count": len(statuses),
        "supply_limit": "RESUPPLYING is a native phase; purchase requires stock, bank and confirmed outcome evidence separately.",
    }


async def execute(args):
    os.umask(0o077)
    work = args.output.resolve()
    work.mkdir(mode=0o700, exist_ok=False)
    fixture_root = args.fixture_root.resolve()
    frozen = json.loads((fixture_root / "manifest.json").read_text())
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
    )
    assert {
        Path(path).name: value
        for value, path in (line.split() for line in actual.splitlines())
    } == frozen["binary_sha256"]
    revision = current_revision()
    (work / "driver.py").write_bytes(Path(__file__).read_bytes())
    attestation = {
        "source_revision": revision,
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
                ).strip()
                assert actual == frozen["database_image_id"]

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
        observer = asyncio.create_task(observe_status(configuration, stopped))
        try:
            await original_run(configuration, stopped)
        finally:
            observer.cancel()
            await asyncio.gather(observer, return_exceptions=True)

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
    result = validate_result(
        reader,
        run,
        args.seconds,
        directory / "worker.sqlite3",
        saved,
        args.require_progress,
    )
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
    parser.add_argument("--require-progress", action="store_true")
    asyncio.run(execute(parser.parse_args()))


if __name__ == "__main__":
    main()
