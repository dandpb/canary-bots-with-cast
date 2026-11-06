"""Separate normal NPC purchase and solo return proof, never a timed pilot run."""

import argparse
import asyncio
import csv
import hashlib
import json
import os
import re
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


def derive_lowstock(parent, destination):
    """A declared supply-only variation; never mutate the scored fixture."""
    shutil.copytree(parent, destination)
    with (destination / "database.sql").open("a") as stream:
        stream.write(
            "\nUPDATE player_items SET count=1 WHERE player_id=65001 AND itemtype IN (266,268);\n"
        )
    scripts = destination / "authored/hunt_scripts.csv"
    with scripts.open(newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames
        rows = list(reader)
    previously_enabled = [row["id"] for row in rows if row["enabled"] == "1"]
    for row in rows:
        row["enabled"] = "0"
    with scripts.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return {
        "variation": "supply-only proof, not a scored equivalent-start trial",
        "changes": {
            "health_potion_stack": 1,
            "mana_potion_stack": 1,
            "hunt_mask_before": previously_enabled,
            "hunt_mask_after": [],
        },
        "unchanged": "map, native code, HP, offers/filter implementation, bank, equipment, town, spawn",
        "purpose": "At 40 potions no resupply is offered; no hunts remain, so normal retreat survives the healthy-idle filter.",
    }


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
        "no_operator_interventions": metrics["interventions"] == 0,
        "no_automatic_recoveries": metrics["automatic_recoveries_requested"] == 0,
        "zero_inference": requests == 0,
    }


def native_build_contract(frozen, revision, image):
    """Bind the declared native revision to the frozen image and both binaries."""
    build = frozen["native_build"]
    assert image == frozen["image_id"]
    assert re.fullmatch(r"[0-9a-f]{40}", revision)
    assert build["source_revision"] == revision
    assert re.fullmatch(r"[0-9a-f]{64}", build["archive_sha256"])
    hashes = build["binary_sha256"]
    assert set(hashes) == {"canary", "libbot_engine.so"}
    assert all(re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes.values())
    return hashes


def cleanup_evidence(project):
    """Inspect only resources carrying this newly generated Compose identity."""
    evidence = {"project": project, "resources_cleaned": False}
    try:
        for resource, command in (
            ("containers", ["docker", "ps", "-a", "--format", "{{.ID}} {{.Names}}"]),
            ("networks", ["docker", "network", "ls", "--format", "{{.ID}} {{.Name}}"]),
        ):
            output = subprocess.check_output(
                command + ["--filter", "label=com.docker.compose.project=" + project],
                text=True,
            )
            evidence[resource] = output.splitlines()
        evidence["resources_cleaned"] = (
            not evidence["containers"] and not evidence["networks"]
        )
    except (OSError, subprocess.CalledProcessError) as error:
        evidence["inspection_error"] = type(error).__name__
    return evidence


def disable_recovery(controller):
    controller.supervisor.state(65001)["automatic"] = False
    controller.supervisor.save(65001)


def check_interrupted(stop):
    if stop.is_set():
        raise InterruptedError("proof interrupted before goal")


async def execute(args, stop):
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
    expected_binaries = native_build_contract(
        frozen, args.source_revision, args.game_image
    )
    source_root = Path(runtime.__file__).resolve().parents[4]
    status = await asyncio.to_thread(
        subprocess.check_output,
        ["git", "-C", str(source_root), "status", "--porcelain"],
        text=True,
    )
    assert not status.strip(), (
        "proof must freeze a clean committed application checkout"
    )
    app_revision = (
        await asyncio.to_thread(
            subprocess.check_output,
            ["git", "-C", str(source_root), "rev-parse", "HEAD"],
            text=True,
        )
    ).strip()
    variation = derive_lowstock(args.fixture_root / "fixture", work / "fixture")
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
                "native_build": frozen["native_build"],
                "fixture_variation": variation,
                "policy": "fake: resupply below10 potions, then retreat after confirmed purchase",
                "expected_bank_debit": 2014,
                "expected_stock": 40,
                "project": harness.project,
            },
            indent=2,
        )
    )
    purchase = {}
    returned = {}
    original_controller = runtime.Controller

    class ProofController(original_controller):
        def __init__(self, *controller_args, **controller_kwargs):
            super().__init__(*controller_args, **controller_kwargs)
            disable_recovery(self)

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
        check_interrupted(stop)
        await asyncio.to_thread(harness.start_database)
        check_interrupted(stop)
        result["initial_character"] = await asyncio.to_thread(harness.character)
        result["initial_supplies"] = await asyncio.to_thread(supplies)
        check_interrupted(stop)
        worker = asyncio.create_task(runtime.run(config, stop))
        for _ in range(100):
            if (directory / "socket/worker.sock").exists():
                break
            if worker.done():
                await worker
            check_interrupted(stop)
            await asyncio.sleep(0.1)
        check_interrupted(stop)
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
        binary_output = await asyncio.to_thread(
            harness.command,
            "exec",
            "-T",
            "game",
            "sha256sum",
            "/canary/canary",
            "/canary/libbot_engine.so",
        )
        actual_binaries = {
            Path(path).name: digest
            for digest, path in (line.split() for line in binary_output.splitlines())
        }
        assert actual_binaries == expected_binaries
        result["images_verified"] = True
        (work / "runtime-images.json").write_text(
            json.dumps(
                {
                    "images": actual_images,
                    "binary_sha256": actual_binaries,
                    "native_source_revision": args.source_revision,
                    "application_source_revision": app_revision,
                },
                indent=2,
            )
        )
        await asyncio.wait_for(worker, timeout=args.maximum_seconds + 300)
        await asyncio.to_thread(harness.stop_game)
        result["saved_character"] = await asyncio.to_thread(harness.character)
        result["saved_supplies"] = await asyncio.to_thread(supplies)
    except (AssertionError, OSError, RuntimeError, ValueError, TimeoutError) as error:
        result["failure"] = type(error).__name__
    finally:
        stop.set()
        if worker:
            await asyncio.gather(worker, return_exceptions=True)
        try:
            await asyncio.to_thread(harness.close)
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            result["cleanup_error"] = type(error).__name__
        finally:
            cleanup = await asyncio.to_thread(cleanup_evidence, harness.project)
            (work / "resources-cleaned.json").write_text(json.dumps(cleanup, indent=2))
            result["resources_cleaned"] = cleanup["resources_cleaned"]
    if "failure" in result:
        result["goal_accepted"] = False
        (work / "goal-proof.json").write_text(json.dumps(result, indent=2))
        raise SystemExit(1)
    reader = ReplayReader(config.recording.path)
    run = reader.runs()[0]
    samples = [
        event for event in reader.all_events(run["id"]) if event["kind"] == "sample"
    ]
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
    result["checks"]["images_verified"] = result.get("images_verified", False)
    result["checks"]["hunt_mask_effective"] = bool(samples) and not any(
        option["action"] == "hunt"
        for event in samples
        for option in event["data"].get("actions", [])
    )
    result["checks"]["resources_cleaned"] = result["resources_cleaned"]
    result["checks"]["cleanup_succeeded"] = "cleanup_error" not in result
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


async def run_with_signals(args, executor=None):
    with benchmark.campaign_signals() as stopped:
        await (executor or execute)(args, stopped)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--game-image", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--maximum-seconds", type=int, default=300)
    asyncio.run(run_with_signals(parser.parse_args()))


if __name__ == "__main__":
    main()
