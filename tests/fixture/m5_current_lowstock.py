"""Separate normal NPC purchase and solo return proof, never a timed pilot run."""

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

from canary_brain import benchmark, runtime
from canary_brain.protocol import Outcome
from canary_brain.recording import RecordingStore, ReplayReader
from canary_brain.replay import summary

WORLD = Path("/tmp/canary-lifecycle-qa-world.otbm")


def forbidden(*args, **kwargs):
    raise AssertionError("low-stock proof cannot read credentials or call providers")


def goal_checks(initial, saved, character, home, purchase, returned, metrics, requests):
    delta = purchase.get("metrics", {}).get("supply_delta", 0)
    return {
        "authoritative_purchase": purchase.get("status") == "completed" and delta >= 38,
        "authoritative_return": returned.get("status") == "completed"
        and returned.get("reason")
        in {"party_rejoined", "supplies_bought_and_party_rejoined"},
        "stock_persisted": initial["potions"] == 2
        and saved["potions"] == 40
        and saved["potions"] - initial["potions"] == delta,
        "bank_debit_persisted": initial["bank"] == 10000 and saved["bank"] == 7986,
        "saved_near_temple": character["posz"] == home["posz"]
        and max(abs(character[k] - home[k]) for k in ("posx", "posy")) <= 3,
        "no_recorded_gaps": metrics["gaps"] == 0,
        "no_observed_deaths": metrics["deaths"] == 0,
        "zero_inference": requests == 0,
    }


async def execute(args):
    os.umask(0o077)
    work = args.output.resolve()
    work.mkdir(mode=0o700, exist_ok=False)
    frozen = json.loads((args.fixture_root / "manifest.json").read_text())
    assert (
        benchmark.fixture_hash(args.fixture_root / "fixture", WORLD)
        == frozen["fixture_sha256"]
    )
    assert args.game_image.startswith("sha256:") and len(args.game_image) == 71
    assert args.game_image == frozen["image_id"], (
        "freeze the patched game identity before proof"
    )
    source_root = Path(runtime.__file__).resolve().parents[4]
    app_revision = (
        await asyncio.to_thread(
            subprocess.check_output,
            ["git", "-C", str(source_root), "rev-parse", "HEAD"],
            text=True,
        )
    ).strip()
    shutil.copytree(args.fixture_root / "fixture", work / "fixture")
    with (work / "fixture/database.sql").open("a") as stream:
        stream.write(
            "\nUPDATE player_items SET count=1 WHERE player_id=65001 AND itemtype IN (266,268);\n"
        )
    fixture_sha = benchmark.fixture_hash(work / "fixture", WORLD)
    experiment = benchmark.Experiment(
        name="m5-supply-" + hashlib.sha256(str(work).encode()).hexdigest()[:10],
        output=work / "runs",
        fixture=work / "fixture",
        world_map=WORLD,
        budget_file=work / "offline-ledger.sqlite3",
        game_image=args.game_image,
        database_image=frozen["database_image_id"],
        bot_id=65001,
        participants=[benchmark.Participant(name="supply", kind="native")],
        repetitions=1,
        seconds=args.maximum_seconds,
        source_revision=app_revision,
        expected_initial_sha256=fixture_sha,
    )
    directory = work / "supply"
    harness = benchmark.DockerFixture(
        experiment, directory, hashlib.sha256(str(work).encode()).hexdigest()
    )
    harness.prepare(experiment.participants[0])
    server_file = directory / "config/server.json"
    server = json.loads(server_file.read_text())
    server["mode"] = "active"
    server_file.write_text(json.dumps(server))
    compose = json.loads(harness.compose.read_text())
    compose["networks"] = {"default": {"internal": True}}
    compose["services"]["game"]["volumes"].append(f"{directory}:/m5")
    harness.compose.write_text(json.dumps(compose))
    (work / "proof-plan.json").write_text(
        json.dumps(
            {
                "purpose": "goal proof, not 30-minute qualification or paid tournament",
                "parent_fixture_sha256": frozen["fixture_sha256"],
                "fixture_sha256": fixture_sha,
                "game_image": args.game_image,
                "database_image": frozen["database_image_id"],
                "application_source_revision": app_revision,
                "native_source_revision": args.source_revision,
                "policy": "fake: resupply below10 potions, then retreat after confirmed purchase",
                "expected_bank_debit": 2014,
                "expected_stock": 40,
                "project": harness.project,
            },
            indent=2,
        )
    )
    stop = asyncio.Event()
    purchase = {}
    returned = {}
    original_controller = runtime.Controller

    class ProofController(original_controller):
        async def handle(self, packet):
            nonlocal purchase, returned
            await super().handle(packet)
            if packet.get("type") != "outcome":
                return
            outcome = Outcome.model_validate(packet)
            if (
                outcome.status == "completed"
                and outcome.reason
                in {"supplies_bought", "supplies_bought_and_party_rejoined"}
                and outcome.metrics.get("supply_delta", 0) >= 38
            ):
                purchase = outcome.model_dump()
                (work / "purchase.json").write_text(json.dumps(purchase, indent=2))
            if (
                purchase
                and outcome.status == "completed"
                and outcome.reason
                in {"party_rejoined", "supplies_bought_and_party_rejoined"}
            ):
                returned = outcome.model_dump()
                (work / "return.json").write_text(json.dumps(returned, indent=2))
                self.record(
                    65001,
                    "lifecycle",
                    {
                        "phase": "supply_goal_confirmed",
                        "termination": "external goal proof stop, not horizon completion",
                    },
                )
                stop.set()

    class ProofFake(runtime.FakeProvider):
        async def decide(self, observation, memory=None):
            options = {a.id for a in observation.actions}
            if observation.bot.objective_running:
                return "continue" if "continue" in options else next(iter(options))
            if purchase:
                return "retreat" if "retreat" in options else "continue"
            return "resupply" if "resupply" in options else "continue"

    runtime.Controller = ProofController
    runtime.FakeProvider = ProofFake
    runtime.read_credential = forbidden
    runtime.AsyncOpenAI = forbidden
    config = runtime.Configuration(
        provider="fake",
        mode="active",
        socket_directory=directory / "socket",
        state_file=directory / "worker.sqlite3",
        bots=[65001],
        memory_mode="frozen",
        policy_seed=42,
        run_seconds=args.maximum_seconds,
        benchmark_supervision=True,
        recording={
            "path": work / "recording.sqlite3",
            "namespace": experiment.name,
            "manifests": [
                {
                    "run_id": experiment.name + ":supply",
                    "bot_id": 65001,
                    "lineage": experiment.name,
                    "experiment": experiment.name,
                    "scenario": "separate-lowstock-purchase-return-proof",
                    "participant": "fake-supply-proof",
                    "provider": "fake",
                    "model": "none",
                    "initial_sha256": fixture_sha,
                    "source_revision": app_revision,
                    "memory_mode": "frozen",
                }
            ],
        },
    )
    worker = None
    result = {}

    def supplies():
        text = harness.command(
            "exec",
            "-T",
            "database",
            "sh",
            "-c",
            'MYSQL_PWD="$MARIADB_PASSWORD" mariadb -u canary canary -N -e "$1"',
            "sh",
            "SELECT balance,(SELECT COALESCE(SUM(count),0) FROM player_items WHERE player_id=65001 AND itemtype IN (266,268)) FROM players WHERE id=65001;",
        )
        return dict(zip(("bank", "potions"), map(int, text.split()), strict=True))

    try:
        await asyncio.to_thread(harness.start_database)
        result["initial_character"] = await asyncio.to_thread(harness.character)
        result["initial_supplies"] = await asyncio.to_thread(supplies)
        worker = asyncio.create_task(runtime.run(config, stop))
        for _ in range(100):
            if (directory / "socket/worker.sock").exists():
                break
            if worker.done():
                await worker
            await asyncio.sleep(0.1)
        await asyncio.to_thread(harness.start_game)
        runtime_rows = json.loads(
            await asyncio.to_thread(
                subprocess.check_output,
                [
                    "docker",
                    "inspect",
                    harness.project + "-game-1",
                    harness.project + "-database-1",
                ],
                text=True,
            )
        )
        actual_images = {
            row["Config"]["Labels"]["com.docker.compose.service"]: row["Image"]
            for row in runtime_rows
        }
        assert actual_images == {
            "game": args.game_image,
            "database": frozen["database_image_id"],
        }
        (work / "runtime-images.json").write_text(json.dumps(actual_images, indent=2))
        await asyncio.wait_for(worker, timeout=args.maximum_seconds + 300)
        await asyncio.to_thread(harness.stop_game)
        result["saved_character"] = await asyncio.to_thread(harness.character)
        result["saved_supplies"] = await asyncio.to_thread(supplies)
    finally:
        stop.set()
        if worker:
            await asyncio.gather(worker, return_exceptions=True)
        await asyncio.to_thread(harness.close)
    reader = ReplayReader(config.recording.path)
    run = reader.runs()[0]
    metrics = summary(reader, run["id"])["metrics"]
    with sqlite3.connect(config.state_file) as db:
        requests = db.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    result["checks"] = goal_checks(
        result["initial_supplies"],
        result["saved_supplies"],
        result["saved_character"],
        result["initial_character"],
        purchase,
        returned,
        metrics,
        requests,
    )
    result.update(
        purchase=purchase,
        returned=returned,
        goal_accepted=all(result["checks"].values()),
        metrics=metrics,
        scope="Separate normal-action goal proof; no operator commands, teleports, rescue, or paid inference",
    )
    RecordingStore(config.recording.path).finish(
        run["id"], "completed" if result["goal_accepted"] else "failed"
    )
    (work / "goal-proof.json").write_text(json.dumps(result, indent=2))
    print(
        json.dumps(
            {
                "output": str(work),
                "checks": result["checks"],
                "goal_accepted": result["goal_accepted"],
            }
        )
    )
    if not result["goal_accepted"]:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--game-image", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--maximum-seconds", type=int, default=300)
    asyncio.run(execute(parser.parse_args()))


if __name__ == "__main__":
    main()
