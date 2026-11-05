"""Offline regressions for interrupted QA reruns; no Docker or provider calls."""

import contextlib
import gzip
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import party_combat_perf as combat
import party_perf as perf
import party_qa as q
import party_report as report
import party_scenarios as scenarios

EVIDENCE = (
    Path(__file__).resolve().parents[2]
    / "deployment/brain/evidence/2026-11-05/party-technical-acceptance"
)
CURRENT = "11111111-1111-4111-8111-111111111111"
OLDER = "22222222-2222-4222-8222-222222222222"


def tag(value, run_id):
    if isinstance(value, list):
        return [{**row, "run_id": run_id} for row in value]
    return {**value, "run_id": run_id}


def seed(work, identity=CURRENT, population_identity=None, include_population=True):
    work.mkdir(parents=True, exist_ok=True)
    (work / "run.json").write_text(json.dumps({"version": 1, "run_id": identity}))
    for source in EVIDENCE.glob("*.json.gz"):
        name = source.name.removesuffix(".gz")
        if name == "party-population-perf-raw.json" and not include_population:
            continue
        with gzip.open(source, "rt") as stream:
            payload = json.load(stream)
        artifact_id = (
            (population_identity or identity)
            if name == "party-population-perf-raw.json"
            else identity
        )
        (work / name).write_text(json.dumps(tag(payload, artifact_id)))
    for name in [
        "party-environment.json",
        "party-runtime-source-comparison.json",
        "party-datapack-normalized-blobs.json",
        "party-population-load.json",
    ]:
        if name == "party-population-load.json" and not include_population:
            continue
        (work / name).write_text(
            json.dumps(tag(json.loads((EVIDENCE / name).read_text()), identity))
        )


class PartyRunTests(unittest.TestCase):
    def test_interrupted_rerun_rejects_stale_population_before_publishing(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            work.mkdir()
            root = Path(tmp) / "repo"
            destination = (
                root / "deployment/brain/evidence/2026-11-05/party-technical-acceptance"
            )
            destination.mkdir(parents=True)
            summary = destination / "summary.json"
            summary.write_text('{"previous_report":true}')
            before = summary.read_bytes()
            seed(work, population_identity=OLDER)
            stale = (work / "party-population-perf-raw.json").read_bytes()
            with (
                patch.object(q, "WORK", work),
                patch.object(q, "ROOT", root),
                contextlib.redirect_stdout(io.StringIO()),
                self.assertRaisesRegex(ValueError, "run"),
            ):
                report.main()
            self.assertEqual(summary.read_bytes(), before)
            self.assertEqual(
                (work / "party-population-perf-raw.json").read_bytes(), stale
            )
            self.assertEqual(list(destination.iterdir()), [summary])

    def test_create_refuses_retained_partial_directory_without_mutating_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            work.mkdir()
            (work / "party-population-perf-raw.json").write_text('{"old_round":true}')
            (work / "party-perf-raw.json").write_text("[]")
            before = {p.name: p.read_bytes() for p in work.iterdir()}
            calls = []

            def fake_docker(*args, **kwargs):
                calls.append(args)
                if args[0] == "logs":
                    return "Canary party QA server online!"
                if "mariadb" in args:
                    return "1"
                return ""

            with (
                patch.object(q, "WORK", work),
                patch.object(q, "docker", fake_docker),
                contextlib.redirect_stdout(io.StringIO()),
                self.assertRaises(FileExistsError),
            ):
                q.create()
            self.assertEqual({p.name: p.read_bytes() for p in work.iterdir()}, before)
            self.assertEqual(calls, [])

    def test_matching_run_publishes_original_numbers_in_its_own_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            root = Path(tmp) / "repo"
            seed(work)
            with (
                patch.object(q, "WORK", work),
                patch.object(q, "ROOT", root),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                report.main()
                destination = q.report_directory()
            result = json.loads((destination / "summary.json").read_text())
            self.assertEqual(result["run_id"], CURRENT)
            self.assertEqual(
                sum(
                    row["native_ticks"]
                    for phase in ["idle_follow", "combat", "population_combat"]
                    for row in result[phase].values()
                ),
                8556,
            )
            with gzip.open(
                destination / "party-population-perf-raw.json.gz", "rt"
            ) as stream:
                self.assertTrue(
                    all(row["run_id"] == CURRENT for row in json.load(stream))
                )

    def test_new_three_bot_run_cannot_publish_previous_runs_population_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            seed(first)
            seed(second, identity=OLDER, include_population=False)
            with (
                patch.object(q, "ROOT", root),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                with patch.object(q, "WORK", first):
                    report.main()
                    old_dir = q.report_directory()
                    before = (old_dir / "summary.json").read_bytes()
                with patch.object(q, "WORK", second):
                    report.main()
                    new_dir = q.report_directory()
            self.assertNotIn(
                "population_combat", json.loads((new_dir / "summary.json").read_text())
            )
            self.assertFalse((new_dir / "party-population-perf-raw.json.gz").exists())
            self.assertEqual((old_dir / "summary.json").read_bytes(), before)

    def test_report_rejects_foreign_metadata_and_untagged_raws(self):
        for name in ["party-environment.json", "party-perf-raw.json"]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                work = Path(tmp) / "work"
                root = Path(tmp) / "repo"
                seed(work)
                data = json.loads((work / name).read_text())
                if isinstance(data, list):
                    data[4].pop("run_id")
                else:
                    data["run_id"] = OLDER
                (work / name).write_text(json.dumps(data))
                with (
                    patch.object(q, "WORK", work),
                    patch.object(q, "ROOT", root),
                    self.assertRaisesRegex(ValueError, "run"),
                ):
                    report.main()
                self.assertFalse(root.exists())

    def test_interrupted_producers_cannot_overwrite_their_previous_attempt(self):
        for function, name, args in [
            (perf.main, "party-perf-raw.json", ()),
            (
                combat.main,
                "party-population-perf-raw.json",
                ("party-population-perf-raw.json", 997),
            ),
            (scenarios.main, "party-scenarios-raw.json", ()),
        ]:
            with (
                self.subTest(name=name),
                tempfile.TemporaryDirectory() as tmp,
                patch.object(q, "WORK", Path(tmp)),
            ):
                q.initialize_run()
                q.reserve_output(name)
                before = (Path(tmp) / name).read_bytes()
                with (
                    patch.object(q, "verify") as verify,
                    self.assertRaises(FileExistsError),
                ):
                    function(*args)
                verify.assert_not_called()
                self.assertEqual((Path(tmp) / name).read_bytes(), before)

    def test_interrupted_atomic_write_preserves_previous_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(q, "WORK", Path(tmp)):
            q.initialize_run()
            q.reserve_output("checkpoint.json")
            q.write_json("checkpoint.json", [{"window": 1}])
            before = (Path(tmp) / "checkpoint.json").read_bytes()
            with (
                patch.object(q.os, "replace", side_effect=OSError("interrupted")),
                self.assertRaises(OSError),
            ):
                q.write_json("checkpoint.json", [{"window": 2}])
            self.assertEqual((Path(tmp) / "checkpoint.json").read_bytes(), before)
            self.assertFalse(list(Path(tmp).glob("*.tmp")))

    def test_resume_and_writer_refuse_to_relabel_foreign_rounds(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(q, "WORK", Path(tmp)):
            identity = q.initialize_run()
            (Path(tmp) / "party-scenarios-raw.json").write_text(
                json.dumps({"run_id": OLDER, "phases": []})
            )
            with (
                patch.object(q, "verify") as verify,
                self.assertRaisesRegex(ValueError, "run"),
            ):
                scenarios.main(resume=True)
            verify.assert_not_called()
            with self.assertRaisesRegex(ValueError, "run"):
                q.write_json("foreign.json", {"run_id": OLDER})
            self.assertFalse((Path(tmp) / "foreign.json").exists())
            self.assertEqual(q.run_id(), identity)

    def test_fresh_create_copies_separate_build_inputs_and_labels_every_resource(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "round"
            build = Path(tmp) / "build"
            build.mkdir()
            for name in ["canary", "libbot_engine.so", "party_acceptance.so"]:
                (build / name).write_bytes(b"build-input")
            calls = []

            def fake_docker(*args, **kwargs):
                calls.append(args)
                if args[0] == "logs":
                    return "Canary party QA server online!"
                return "1" if "mariadb" in args else ""

            with (
                patch.object(q, "WORK", work),
                patch.object(q, "BUILD", build),
                patch.object(q, "docker", fake_docker),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                q.create()
                identity = q.run_id()
            self.assertTrue(
                all(
                    (work / name).read_bytes() == b"build-input"
                    for name in ["canary", "libbot_engine.so", "party_acceptance.so"]
                )
            )
            self.assertEqual(
                sum(f"canary.qa.run_id={identity}" in args for args in calls), 4
            )
            before = {p.name: p.read_bytes() for p in build.iterdir()}
            self.assertEqual(before, {name: b"build-input" for name in before})

    def test_existing_empty_directory_gets_one_immutable_identity(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(q, "WORK", Path(tmp)):
            identity = q.initialize_run()
            before = (Path(tmp) / "run.json").read_bytes()
            self.assertEqual(q.run_id(), identity)
            with self.assertRaises(FileExistsError):
                q.initialize_run()
            self.assertEqual((Path(tmp) / "run.json").read_bytes(), before)

    def test_foreign_container_run_is_rejected_before_commands_or_stop(self):
        details = {
            "Config": {"Labels": {"canary.qa": "party", "canary.qa.run_id": OLDER}},
            "NetworkSettings": {"Networks": {q.PREFIX: {}}},
            "HostConfig": {"PortBindings": {}},
            "State": {"Running": True},
            "Mounts": [{"Name": q.PREFIX + "-data", "Destination": "/var/lib/mysql"}],
        }
        for action in [q.verify, lambda: q.sql("SELECT 1"), q.stop]:
            with (
                self.subTest(action=action),
                tempfile.TemporaryDirectory() as tmp,
                patch.object(q, "WORK", Path(tmp)),
            ):
                q.initialize_run()
                with (
                    patch.object(
                        q, "docker", return_value=json.dumps([details])
                    ) as docker,
                    self.assertRaisesRegex(AssertionError, "another run"),
                ):
                    action()
                self.assertTrue(
                    all(call.args[0] == "inspect" for call in docker.call_args_list)
                )


if __name__ == "__main__":
    unittest.main()
