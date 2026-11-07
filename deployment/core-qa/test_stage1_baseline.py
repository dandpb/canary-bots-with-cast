"""Offline stage 1 <-> stage 2 gate and rollback against the reviewed baseline, with a fake Docker CLI.

Fixtures use the schema of stage1-baseline.json with fake IDs; no Docker daemon is contacted.
"""

import contextlib
import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import preflight
import stage1_baseline as gate

QA = "canary-core-qa"
GAME, WEB, DATABASE, BRAIN = gate.GAME, gate.WEB, gate.DATABASE, gate.BRAIN
STAGE1_IMAGES = ("canary-core-qa-game:local", "canary-core-qa-web:local", "mariadb:11.4")
DB_ROWS = ["player\t66100\t65001\tQa Knight\t8\t4\t4200", "player\t66101\t65002\tQa Druid\t8\t2\t4200",
           *(f"item\t{66100 + n % 2}\t{n}\t{100 + n}\t3031\t1" for n in range(10))]


def labels(**keys):
    return {f"com.docker.compose.{key.replace('_', '-')}": value for key, value in keys.items()}


def projection(rows):
    return hashlib.sha256("".join(row + "\n" for row in rows).encode()).hexdigest()


def baseline_fixture():
    """A stage-1 baseline in the schema of the reviewed one, with fake identities."""
    services = (("1", "database", "mariadb:11.4", None), ("2", "game", "canary-core-qa-game:local", "b" * 40),
                ("3", "web", "canary-core-qa-web:local", None))
    return {
        "captured_at_utc": "2026-11-06T22:20:30.000000+00:00",
        "containers": [{
            "compose_labels": labels(config_hash=digit * 64, project=QA, service=service),
            "created_at": f"2026-11-06T21:31:5{digit}.000000001Z", "health": "healthy",
            "historical_comparison": {"created_at_match": True, "id_match": True, "image_id_match": True},
            "id": digit * 64, "image_id": "sha256:" + digit * 63 + "e", "image_ref": ref,
            "image_source_revision": revision, "name": f"{QA}-{service}-1", "status": "running",
        } for digit, service, ref, revision in services],
        "db_logical_snapshot": {
            "counts": {"accounts": 4, "player_items": 2597, "players": 1000, "qa_character_items": 10},
            "qa_character_projection_sha256": projection(DB_ROWS),
            "transaction": "REPEATABLE READ; WITH CONSISTENT SNAPSHOT",
        },
        "historical_receipt": {"checked_at_utc": "2026-11-06T21:50:27+00:00", "filename": "web-rollout-after.json",
                               "sha256": "0" * 64},
        "limits": ["fixture"],
        "network": {"compose_labels": labels(config_hash="4" * 64, network="default", project=QA, version="5.5.1"),
                    "created_at": "2026-11-06T21:31:51.357332385Z", "id": "4" * 64, "name": f"{QA}_default"},
        "project": QA,
        "schema": "stage1-qa-baseline-v1",
        "volumes": [{"compose_labels": labels(config_hash=str(n) * 64, project=QA, version="5.5.1", volume=volume),
                     "created_at": "2026-11-06T21:31:51Z", "name": f"{QA}_{volume}"}
                    for n, volume in enumerate(sorted(preflight.VOLUMES), 5)],
    }


class FakeDocker:
    """Docker CLI over an in-memory stage 1 (optionally stage 2). Mutating calls are logged and applied."""

    def __init__(self, baseline, stage2=False):
        self.containers = {item["name"]: {**copy.deepcopy(item), "labels": {
            **item["compose_labels"], "com.docker.compose.version": "5.5.1"}} for item in baseline["containers"]}
        for item in self.containers.values():
            item.pop("historical_comparison")
            item.pop("compose_labels")
        self.revisions = {item["image_id"]: item["image_source_revision"] for item in baseline["containers"]}
        self.network = copy.deepcopy(baseline["network"])
        self.volumes = {item["name"]: copy.deepcopy(item) for item in baseline["volumes"]}
        self.tags = {item["image_ref"]: item["image_id"] for item in baseline["containers"]}
        self.counts = dict(baseline["db_logical_snapshot"]["counts"])
        self.rows = list(DB_ROWS)
        self.game_env = {**{key: value for key, value in gate.GAME_PORTS.items()},
                         "CANARY_BRAIN_CONFIG": gate.DISABLED_BRAIN, "MARIADB_PASSWORD": "fake-not-a-secret"}
        self.game_mounts = [{"Name": f"{QA}_game-logs"}]
        self.config_ports = ["loginProtocolPort = 17171", "gameProtocolPort = 17172", "statusProtocolPort = 17173"]
        self.integrity = {"tables": ["4"], "qa": ["2", "2"],
                          "check": {table: "OK" for table in gate.DB_TABLES}, "down": False}
        self.extra = []  # (listing, id, name, project, key)
        self.log = []
        self.fail = None  # a mutating command prefix that fails
        if stage2:
            self.stage2()

    def stage2(self):
        """What a stage-2 up leaves: rebuilt game image, recreated game, brain container and volumes."""
        self.tags["canary-core-qa-game:local"] = "sha256:" + "8" * 64
        self.revisions["sha256:" + "8" * 64] = "c" * 40
        self.tags[preflight.BRAIN_IMAGE] = "sha256:" + "9" * 64
        self.containers[GAME].update(id="8" * 64, image_id="sha256:" + "8" * 64, created_at="2026-11-07T01:00:00Z")
        self.containers[GAME]["labels"]["com.docker.compose.config-hash"] = "f" * 64
        self.containers[BRAIN] = {"name": BRAIN, "id": "9" * 64, "image_id": "sha256:" + "9" * 64,
                                  "image_ref": preflight.BRAIN_IMAGE, "created_at": "2026-11-07T01:00:01Z",
                                  "status": "running", "health": None,
                                  "labels": labels(config_hash="9" * 64, project=QA, service="brain")}
        for volume in sorted(preflight.BRAIN_VOLUMES):
            self.volumes[f"{QA}_{volume}"] = {"name": f"{QA}_{volume}", "created_at": "2026-11-07T01:00:00Z",
                                              "compose_labels": labels(project=QA, volume=volume)}
        self.game_env["CANARY_BRAIN_CONFIG"] = "/etc/canary-core-qa/brain/server.json"
        self.game_mounts.append({"Name": gate.BRAIN_SOCKET})

    def rows_for(self, listing):
        if listing == "ps":
            rows = [(item["id"], name, item["labels"]["com.docker.compose.project"],
                     item["labels"]["com.docker.compose.service"]) for name, item in self.containers.items()]
        elif listing == "volume":
            rows = [(name, name, item["compose_labels"].get("com.docker.compose.project", ""),
                     item["compose_labels"].get("com.docker.compose.volume", "")) for name, item in self.volumes.items()]
        else:
            rows = ([(self.network["id"], self.network["name"], QA, "default")] if self.network else [])
            rows.append(("b" * 64, "bridge", "", ""))
        return rows + [row[1:] for row in self.extra if row[0] == listing]

    def mutate(self, args):
        self.log.append(args)
        if self.fail and args[:len(self.fail)] == self.fail:
            raise RuntimeError(f"read-only command failed: {args[0]} {args[1]}")
        if args[:2] == ("docker", "tag"):
            self.tags[args[3]] = args[2]
        elif args[:3] == ("docker", "volume", "rm"):
            self.volumes.pop(args[3])
        elif "rm" in args and args[-1] == "brain":
            self.containers.pop(BRAIN)
        elif "up" in args and "compose.brain-fake.yaml" not in args:
            game = self.containers[GAME]
            game.update(id="7" * 64, image_id=self.tags["canary-core-qa-game:local"], created_at="2026-11-07T02:00:00Z")
            game["labels"]["com.docker.compose.config-hash"] = "2" * 64
            self.game_env["CANARY_BRAIN_CONFIG"] = gate.DISABLED_BRAIN
            self.game_mounts = [mount for mount in self.game_mounts if mount["Name"] != gate.BRAIN_SOCKET]
        return ""

    def __call__(self, *args, env=None):
        fmt = args[-1]
        if args[1] in ("tag", "compose") or args[1:3] == ("volume", "rm"):
            return self.mutate(args)
        if args[1] == "exec" and args[2] == DATABASE and self.integrity["down"]:
            raise RuntimeError("read-only command failed: docker exec")
        if args[1] == "exec" and args[2] == DATABASE and "CHECK TABLE" in args[-1]:
            state = self.integrity
            rows = [["tables", *state["tables"]], ["qa", *state["qa"]]] + [
                [f"canary.{table}", "check", "status", status] for table, status in state["check"].items()]
            return "".join("\t".join(row) + "\n" for row in rows)
        if args[1] == "exec" and args[2] == DATABASE:
            assert "START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY" in args[-1]
            counts = "\t".join(str(self.counts[key]) for key in gate.DB_COUNT_KEYS)
            return "".join(row + "\n" for row in [f"counts\t{counts}", *self.rows])
        if args[1] == "exec" and args[2] == WEB:
            return "".join(line + "\n" for line in self.config_ports)
        if args[1:3] == ("image", "ls"):
            return "".join(f"{ref}\n" for ref in self.tags)
        if args[1:3] == ("image", "inspect"):
            if fmt == "{{.Id}}":
                ident = self.tags.get(args[3], args[3])
                if ident not in self.revisions:
                    raise RuntimeError("read-only command failed: docker image")
                return ident + "\n"
            return "".join(json.dumps({"id": ident, "labels": {gate.REVISION_LABEL: self.revisions[ident]}
                                       if self.revisions[ident] else None}) + "\n"
                           for ident in args[3:-2])
        if args[1:3] == ("network", "inspect"):
            network = self.network
            return json.dumps({"id": network["id"], "name": network["name"], "created_at": network["created_at"],
                               "labels": network["compose_labels"]}) + "\n"
        if args[1:3] == ("volume", "inspect"):
            return "".join(json.dumps({"name": name, "created_at": self.volumes[name]["created_at"],
                                       "labels": self.volumes[name]["compose_labels"]}) + "\n" for name in args[3:-2])
        if args[1] == "inspect" and '"env"' in fmt:
            ports = {f"{port}/tcp": [{"HostIp": "127.0.0.1", "HostPort": port}] for port in gate.GAME_PORTS.values()}
            return json.dumps({"env": [f"{key}={value}" for key, value in self.game_env.items()],
                               "ports": ports, "mounts": self.game_mounts}) + "\n"
        if args[1] == "inspect":
            return "".join(json.dumps({**{key: item[key] for key in (
                "id", "image_id", "image_ref", "created_at", "status", "health", "labels")}, "name": "/" + name})
                + "\n" for name, item in self.containers.items() if name in args[2:-2])
        rows = self.rows_for(args[1])
        if "--filter" in args:
            rows = [row for row in rows if row[2] == QA]
        if "\t" not in fmt:
            return "".join(f"{row[1]}\n" for row in rows)
        return "".join("\t".join(row) + "\n" for row in rows)


def entered(stack, *managers):
    for manager in managers:
        stack.enter_context(manager)
    return stack


def playable_mocks(port_error=None, login_error=None, myaac_error=None):
    login = MagicMock()
    login.__enter__.return_value.read.return_value = b'{"playersonline": 50}'
    return (patch("stage1_baseline.socket.create_connection", side_effect=port_error),
            patch("stage1_baseline.urllib.request.urlopen", side_effect=login_error, return_value=login),
            patch("stage1_baseline.verify_myaac", side_effect=myaac_error, return_value={"qa_config_sha256": "q"}))


class Stage1BaselineGateTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.baseline = baseline_fixture()
        self.path = self.root / "stage1-baseline.json"
        self.path.write_text(json.dumps(self.baseline, indent=2, sort_keys=True) + "\n")
        self.sha = hashlib.sha256(self.path.read_bytes()).hexdigest()

    def upgrade(self, docker):
        with patch("preflight.command", side_effect=docker):
            return gate.assert_stage1_upgrade(self.path, self.sha)

    def test_committed_baseline_is_pinned_sanitized_and_classified(self):
        content = gate.BASELINE.read_bytes()
        self.assertEqual(hashlib.sha256(content).hexdigest(), gate.BASELINE_SHA256)
        baseline = gate.load_baseline()
        self.assertNotRegex(content.decode(), r"(?i)password|secret|token|api[_-]?key|credential")
        self.assertEqual(set(gate.PROVENANCE), {"historical", "captured_now"})
        self.assertEqual(set(gate.comparable(baseline)), {"containers", "network", "volumes", "db_slice"})
        self.assertEqual(set(baseline["db_logical_snapshot"]["counts"]), set(gate.DB_COUNT_KEYS))
        self.assertEqual({item["name"] for item in baseline["volumes"]}, {f"{QA}_{v}" for v in preflight.VOLUMES})
        self.assertIn("REPEATABLE READ", gate.DB_SLICE_SQL)
        self.assertNotRegex(gate.DB_SLICE_SQL, r"(?i)\b(insert|update|delete|drop|alter|create|replace)\b")

    def test_committed_baseline_passes_its_own_gate(self):
        """The real baseline fits the gate's schema; its DB slice is patched (its rows are not in the repo)."""
        baseline = gate.load_baseline()
        docker = FakeDocker(baseline)
        with patch("preflight.command", side_effect=docker), \
             patch("stage1_baseline.db_slice", return_value=gate.comparable(baseline)["db_slice"]):
            receipt = gate.assert_stage1_upgrade()
        self.assertEqual(receipt["baseline_sha256"], gate.BASELINE_SHA256)
        docker.containers[GAME]["id"] = "6" * 64
        with patch("preflight.command", side_effect=docker), \
             patch("stage1_baseline.db_slice", return_value=gate.comparable(baseline)["db_slice"]), \
             self.assertRaisesRegex(RuntimeError, "upgrade refused"):
            gate.assert_stage1_upgrade()

    def test_happy_path_accepts_the_reviewed_stage1_and_keeps_provenance_apart(self):
        receipt = self.upgrade(FakeDocker(self.baseline))
        self.assertEqual(receipt["baseline_sha256"], self.sha)
        self.assertEqual(receipt["observed"], gate.comparable(self.baseline))
        self.assertEqual(receipt["provenance"]["historical"]["fields"],
                         ["containers[].id", "containers[].image_id", "containers[].created_at"])
        self.assertEqual(receipt["provenance"]["historical"]["receipt"]["filename"], "web-rollout-after.json")
        self.assertIn("volumes[].created_at", receipt["provenance"]["captured_now"]["fields"])
        self.assertEqual(receipt["provenance"]["captured_now"]["db_slice_method"], gate.DB_SLICE_METHOD)

    def test_same_name_same_label_substitutions_are_refused_with_a_diff(self):
        def game_replaced(docker):
            docker.containers[GAME]["id"] = "6" * 64

        def game_image_rebuilt(docker):
            docker.containers[GAME]["image_id"] = "sha256:" + "6" * 64
            docker.revisions["sha256:" + "6" * 64] = "b" * 40

        def db_volume_recreated(docker):
            docker.volumes[f"{QA}_database"]["created_at"] = "2026-11-07T03:00:00Z"

        def network_recreated(docker):
            docker.network.update(id="6" * 64, created_at="2026-11-07T03:00:00.1Z")

        def db_rows_differ(docker):
            docker.rows[0] = docker.rows[0].replace("\t8\t", "\t9\t")

        def db_count_differs(docker):
            docker.counts["players"] = 1001

        cases = {
            "game container replaced": (game_replaced, f"/containers/{GAME}/id"),
            "game image rebuilt": (game_image_rebuilt, f"/containers/{GAME}/image_id"),
            "DB volume recreated": (db_volume_recreated, f"/volumes/{QA}_database/created_at"),
            "network recreated": (network_recreated, "/network/id"),
            "DB slice hash differs": (db_rows_differ, "/db_slice/qa_character_projection_sha256"),
            "DB count differs": (db_count_differs, "/db_slice/counts/players"),
        }
        for name, (change, path) in cases.items():
            docker = FakeDocker(self.baseline)
            change(docker)
            with self.subTest(name), self.assertRaisesRegex(
                    RuntimeError, "differs from the reviewed baseline; upgrade refused:\n(.|\n)*" + re.escape(path)):
                self.upgrade(docker)

    def test_upgrade_refuses_a_substituted_or_missing_web_tag_with_unchanged_container(self):
        for image_id in ("sha256:" + "6" * 64, None):
            docker = FakeDocker(self.baseline)
            if image_id:
                docker.tags["canary-core-qa-web:local"] = image_id
                docker.revisions[image_id] = None
            else:
                docker.tags.pop("canary-core-qa-web:local")
            with self.subTest(image_id=image_id), self.assertRaisesRegex(RuntimeError, "refused|absent"):
                self.upgrade(docker)
            self.assertEqual(docker.containers[WEB]["image_id"], self.baseline["containers"][2]["image_id"])
            self.assertEqual(docker.log, [])

    def test_baseline_hash_mismatch_is_refused(self):
        with patch("preflight.command", side_effect=FakeDocker(self.baseline)) as docker, \
             self.assertRaisesRegex(RuntimeError, "differs from the pinned"):
            gate.assert_stage1_upgrade(self.path, "0" * 64)
        docker.assert_not_called()
        tampered = self.root / "tampered.json"
        tampered.write_bytes(self.path.read_bytes().replace(b"healthy", b"Healthy", 1))
        with self.assertRaisesRegex(RuntimeError, "differs from the pinned"):
            gate.load_baseline(tampered, self.sha)
        with self.assertRaisesRegex(RuntimeError, "absent"):
            gate.load_baseline(self.root / "missing.json", self.sha)

    def test_preexisting_brain_objects_are_refused(self):
        cases = {
            "brain container": ("ps", "9" * 64, BRAIN, QA, "brain"),
            "brain ledger": ("volume", gate.LEDGER, gate.LEDGER, QA, "brain-ledger"),
            "brain socket": ("volume", gate.BRAIN_SOCKET, gate.BRAIN_SOCKET, QA, "brain-socket"),
        }
        for name, row in cases.items():
            docker = FakeDocker(self.baseline)
            docker.extra.append(row)
            with self.subTest(name), self.assertRaisesRegex(RuntimeError, f"unexpected QA .*{row[2]}.*refused"):
                self.upgrade(docker)
        docker = FakeDocker(self.baseline)
        docker.tags[preflight.BRAIN_IMAGE] = "sha256:" + "9" * 64
        with self.assertRaisesRegex(RuntimeError, "brain:local already exists"):
            self.upgrade(docker)

    def test_foreign_or_missing_objects_are_refused(self):
        cases = {
            "foreign project, QA name": ("ps", "5" * 64, f"{QA}-web-2", "other", "web"),
            "QA label, foreign name": ("volume", "scratch", "scratch", QA, "scratch"),
            "extra QA network": ("network", "5" * 64, f"{QA}_other", QA, "other"),
            "wrong service label": ("ps", "5" * 64, f"{QA}-extra-1", QA, "extra"),
        }
        for name, row in cases.items():
            docker = FakeDocker(self.baseline)
            docker.extra.append(row)
            with self.subTest(name), self.assertRaisesRegex(RuntimeError, "unexpected QA .*refused"):
                self.upgrade(docker)
        docker = FakeDocker(self.baseline)
        docker.volumes.pop(f"{QA}_game-logs")
        with self.assertRaisesRegex(RuntimeError, "incomplete .*game-logs.*refused"):
            self.upgrade(docker)
        docker = FakeDocker(self.baseline)
        docker.tags.pop("canary-core-qa-web:local")
        with self.assertRaisesRegex(RuntimeError, "game/web are absent"):
            self.upgrade(docker)

    def test_preflight_upgrade_uses_the_pinned_baseline_and_fresh_gates_do_not(self):
        common = (patch("preflight.assert_compose", return_value="f" * 64),
                  patch("preflight.assert_image_lock", return_value={"brain_base": "sha256:base"}),
                  patch("preflight.verify_myaac", return_value={"entrypoint_sha256": "d", "qa_config_sha256": "e"}),
                  patch("preflight.assert_source", return_value="a" * 40),
                  patch("preflight.assert_map", return_value="1" * 64))
        for mock in common:
            mock.start()
            self.addCleanup(mock.stop)
        with patch("stage1_baseline.assert_stage1_upgrade", return_value={"baseline_sha256": "s"}) as upgrade, \
             patch("preflight.assert_no_resources") as fresh:
            preflight.run_preflight(approved_revision="a" * 40, receipt_path=self.root / "up.json", upgrade=True)
        upgrade.assert_called_once_with()
        fresh.assert_not_called()
        receipt = json.loads((self.root / "up.json").read_text())
        self.assertEqual((receipt["stage1_upgrade"], receipt["resources_absent"], receipt["brain_fake"]),
                         ({"baseline_sha256": "s"}, False, True))
        for brain_fake in (False, True):
            with self.subTest(brain_fake=brain_fake), \
                 patch("stage1_baseline.assert_stage1_upgrade") as upgrade, \
                 patch("preflight.assert_no_resources") as fresh:
                preflight.run_preflight(approved_revision="a" * 40, receipt_path=self.root / "fresh.json",
                                        brain_fake=brain_fake)
            upgrade.assert_not_called()
            fresh.assert_called_once_with(brain_fake)


class Stage1RecaptureTests(unittest.TestCase):
    """Stage 1 changed before the upgrade: a new candidate baseline, reviewed and pinned, is the only path."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.baseline = baseline_fixture()
        self.path = self.root / "stage1-baseline.json"
        self.path.write_text(json.dumps(self.baseline))
        self.sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.historical = self.root / "web-rollout-after.json"
        self.historical.write_text(json.dumps({"checked_at_utc": "2026-11-06T21:50:27Z", "containers": [
            {"name": item["name"], "id": item["id"][:12], "image": item["image_id"], "created": item["created_at"]}
            for item in self.baseline["containers"]], "network": f"{QA}_default"}))
        self.played = FakeDocker(self.baseline)  # the QA character played after the first capture
        self.played.rows[0] = self.played.rows[0].replace("\t4200", "\t9100")

    def capture(self, docker, output="candidate.json"):
        with patch("preflight.command", side_effect=docker):
            return gate.capture(self.historical, self.root / output)

    def test_recapture_after_play_is_a_reviewed_candidate_the_gate_accepts_only_once_pinned(self):
        with patch("preflight.command", side_effect=self.played), \
             self.assertRaisesRegex(RuntimeError, "upgrade refused:\n/db_slice/qa_character_projection_sha256"):
            gate.assert_stage1_upgrade(self.path, self.sha)
        path, sha = self.capture(self.played)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), sha)
        candidate = json.loads(path.read_text())
        self.assertEqual(set(candidate["provenance"]), {"historical", "captured_now"})
        self.assertIn("volumes[].created_at", candidate["provenance"]["captured_now"])
        self.assertRegex(candidate["captured_at_utc"], r"^\d{4}-\d\d-\d\dT.*\+00:00$")
        self.assertEqual(candidate["historical_receipt"]["sha256"],
                         hashlib.sha256(self.historical.read_bytes()).hexdigest())
        self.assertTrue(all(all(item["historical_comparison"].values()) and len(item["historical_comparison"]) == 3
                            for item in candidate["containers"]))
        self.assertEqual(candidate["db_logical_snapshot"]["method"], gate.DB_SLICE_METHOD)
        self.assertNotIn("fake-not-a-secret", path.read_text())
        with patch("preflight.command", side_effect=self.played):
            self.assertEqual(gate.assert_stage1_upgrade(path, sha)["baseline_sha256"], sha)
            with self.assertRaisesRegex(RuntimeError, "differs from the pinned"):
                gate.assert_stage1_upgrade(path, self.sha)  # the pin must change in a reviewed commit
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            self.capture(self.played)

    def test_recapture_refuses_containers_that_differ_from_the_historical_receipt(self):
        cases = {"id": "6" * 64, "image_id": "sha256:" + "6" * 64, "created_at": "2026-11-07T03:00:00Z"}
        for field, value in cases.items():
            docker = FakeDocker(self.baseline)
            docker.containers[GAME][field] = value
            docker.revisions.setdefault(docker.containers[GAME]["image_id"], "b" * 40)
            with self.subTest(field), self.assertRaisesRegex(
                    RuntimeError, f"{GAME} differs from web-rollout-after.json .*{field}_match': False.*capture refused"):
                self.capture(docker, f"{field}.json")
            self.assertFalse((self.root / f"{field}.json").exists())

    def test_recapture_refuses_brain_objects_or_a_missing_receipt(self):
        docker = FakeDocker(self.baseline)
        docker.extra.append(("volume", gate.LEDGER, gate.LEDGER, QA, "brain-ledger"))
        with self.assertRaisesRegex(RuntimeError, "unexpected QA volume"):
            self.capture(docker)
        self.historical.unlink()
        with self.assertRaisesRegex(RuntimeError, "historical receipt .* absent"):
            self.capture(FakeDocker(self.baseline))

    def test_preflight_flag_runs_the_capture(self):
        argv = ["preflight.py", "--capture-stage1-baseline", "--historical-receipt", str(self.historical)]
        with patch("sys.argv", argv), patch("stage1_baseline.capture", return_value=(self.root / "c.json", "s")) as capture, \
             patch("builtins.print"):
            preflight.main()
        capture.assert_called_once_with(self.historical)


class Stage1RollbackTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.baseline = baseline_fixture()
        # The stage-1 up with compose.yaml recreates game with the stage-1 config-hash of the baseline.
        self.baseline["containers"][1]["compose_labels"]["com.docker.compose.config-hash"] = "2" * 64
        self.path = self.root / "stage1-baseline.json"
        self.path.write_text(json.dumps(self.baseline))
        self.sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.receipt = self.root / "restored.json"
        for mock in (patch.dict("os.environ", {"SOURCE_REVISION": "c" * 40, "MARIADB_PASSWORD": "host-value"}),
                     patch("stage1_baseline.qa.HERE", self.root), patch("builtins.print")):
            mock.start()
            self.addCleanup(mock.stop)

    def rollback(self, docker, *mocks):
        with entered(contextlib.ExitStack(), patch("preflight.command", side_effect=docker), *(mocks or playable_mocks())):
            return gate.rollback(self.path, self.sha, self.receipt)

    def test_rollback_runs_the_exact_steps_and_restores_a_playable_stage1(self):
        docker = FakeDocker(self.baseline, stage2=True)
        self.rollback(docker)
        stage2 = ("docker", "compose", "-p", QA, "-f", "compose.yaml", "-f", "compose.brain-fake.yaml",
                  "--env-file", ".env")
        stage1 = ("docker", "compose", "-p", QA, "-f", "compose.yaml", "--env-file", ".env")
        game_image = self.baseline["containers"][1]["image_id"]
        self.assertEqual(docker.log, [
            (*stage2, "stop", "-t", "180", "brain", "game"),
            (*stage2, "cp", "brain:/var/lib/canary-human-qa-stage2/.", "runtime/evidence/brain/"),
            (*stage2, "rm", "-f", "brain"),
            ("docker", "volume", "rm", f"{QA}_brain-ledger"),
            ("docker", "tag", game_image, "canary-core-qa-game:local"),
            (*stage1, "up", "-d", "--no-build", "--no-deps", "--wait", "game"),
            ("docker", "volume", "rm", f"{QA}_brain-socket"),
        ])
        for args in docker.log:
            self.assertNotIn("-v", args)
            self.assertNotIn("--volumes", args)
            self.assertNotIn("down", args)
        self.assertEqual(set(docker.volumes), {f"{QA}_{v}" for v in preflight.VOLUMES})
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt["observed"]["containers"][GAME]["image_id"], game_image)
        self.assertNotIn("db_slice", receipt["observed"])
        self.assertEqual(receipt["db"]["integrity"], "ok")
        self.assertTrue(receipt["db"]["slice_equals_baseline"])
        self.assertEqual(receipt["game_recreated"], "7" * 64)
        self.assertEqual(set(receipt["provenance"]), {"historical", "captured_now"})

    def test_rollback_refuses_a_substituted_or_missing_web_tag_before_any_mutation(self):
        for image_id in ("sha256:" + "6" * 64, None):
            docker = FakeDocker(self.baseline, stage2=True)
            if image_id:
                docker.tags["canary-core-qa-web:local"] = image_id
                docker.revisions[image_id] = None
            else:
                docker.tags.pop("canary-core-qa-web:local")
            with self.subTest(image_id=image_id), self.assertRaisesRegex(RuntimeError, "web image tag.*refused"):
                self.rollback(docker)
            self.assertEqual(docker.log, [])
            self.assertIn(BRAIN, docker.containers)
            self.assertIn(gate.LEDGER, docker.volumes)
            self.assertFalse(self.receipt.exists())

    def test_rollback_accepts_a_played_db_when_volumes_are_the_same_and_intact(self):
        docker = FakeDocker(self.baseline, stage2=True)
        docker.rows[0] = docker.rows[0].replace("\t4200", "\t9100")  # XP gained in stage 2
        docker.rows.append("item\t66100\t99\t200\t3031\t5")
        docker.counts.update(player_items=2598, qa_character_items=11)
        self.rollback(docker)
        receipt = json.loads(self.receipt.read_text())
        self.assertFalse(receipt["db"]["slice_equals_baseline"])
        self.assertEqual(receipt["db"]["slice_now_informational"]["counts"]["qa_character_items"], 11)

    def test_rollback_refuses_a_recreated_volume_even_with_an_intact_db(self):
        docker = FakeDocker(self.baseline, stage2=True)
        docker.volumes[f"{QA}_database"]["created_at"] = "2026-11-07T01:30:00Z"
        with self.assertRaisesRegex(RuntimeError, "not restored:\n(.|\n)*" + re.escape(f"/volumes/{QA}_database/created_at")):
            self.rollback(docker)
        self.assertFalse(self.receipt.exists())

    def test_compose_runs_without_host_secrets_and_needs_source_revision(self):
        docker = FakeDocker(self.baseline, stage2=True)
        envs = []

        def spy(*args, env=None):
            if args[1] == "compose":
                envs.append(env)
            return docker(*args, env=env)
        self.rollback(spy)
        self.assertTrue(envs and all("MARIADB_PASSWORD" not in env and env["SOURCE_REVISION"] == "c" * 40
                                     for env in envs))
        with patch.dict("os.environ", {"SOURCE_REVISION": ""}), \
             self.assertRaisesRegex(RuntimeError, "SOURCE_REVISION"):
            self.rollback(FakeDocker(self.baseline, stage2=True))

    def test_rollback_refuses_before_any_change_without_the_stage1_game_image_or_a_pinned_baseline(self):
        docker = FakeDocker(self.baseline, stage2=True)
        docker.revisions.pop(self.baseline["containers"][1]["image_id"])
        with self.assertRaisesRegex(RuntimeError, "stage-1 game image .* gone; rollback refused"):
            self.rollback(docker)
        self.assertEqual(docker.log, [])
        docker = FakeDocker(self.baseline, stage2=True)
        with patch("preflight.command", side_effect=docker), self.assertRaisesRegex(RuntimeError, "pinned"):
            gate.rollback(self.path, "0" * 64, self.receipt)
        docker.extra.append(("ps", "5" * 64, f"{QA}-web-2", "other", "web"))
        with self.assertRaisesRegex(RuntimeError, "unexpected QA"):
            self.rollback(docker)
        self.assertEqual(docker.log, [])

    def test_a_failed_step_stops_the_rollback(self):
        docker = FakeDocker(self.baseline, stage2=True)
        docker.fail = ("docker", "compose", "-p", QA, "-f", "compose.yaml", "--env-file", ".env", "up")
        with self.assertRaisesRegex(RuntimeError, "failed"):
            self.rollback(docker)
        self.assertEqual(docker.log[-1][-6:], ("up", "-d", "--no-build", "--no-deps", "--wait", "game"))
        self.assertIn(gate.BRAIN_SOCKET, docker.volumes)
        self.assertFalse(self.receipt.exists())

    def test_restore_checks_fail_closed(self):
        def web_recreated(docker):
            docker.containers[WEB]["id"] = "6" * 64

        def network_recreated(docker):
            docker.network["id"] = "6" * 64

        def db_volume_recreated(docker):
            docker.volumes[f"{QA}_database"]["created_at"] = "2026-11-07T01:30:00Z"

        def table_corrupt(docker):
            docker.integrity["check"]["player_items"] = "Table is marked as crashed"

        def table_missing(docker):
            docker.integrity["tables"] = ["3"]

        def no_qa_players(docker):
            docker.integrity["qa"] = ["2", "0"]

        def db_down(docker):
            docker.integrity["down"] = True

        def wrong_game_port(docker):
            docker.config_ports = ["gameProtocolPort = 7172"]

        def brain_still_configured(docker):
            docker.game_env["CANARY_BRAIN_CONFIG"] = "/etc/canary-core-qa/brain/server.json"

        def ledger_left(docker):
            docker.volumes[gate.LEDGER] = {"name": gate.LEDGER, "created_at": "x",
                                           "compose_labels": labels(project=QA, volume="brain-ledger")}

        def stage2_config(docker):
            docker.containers[GAME]["labels"]["com.docker.compose.config-hash"] = "f" * 64

        def game_unhealthy(docker):
            docker.containers[GAME]["health"] = "starting"

        cases = {
            "web recreated": (web_recreated, (), f"/containers/{WEB}/id"),
            "network recreated": (network_recreated, (), "/network/id"),
            "DB volume recreated": (db_volume_recreated, (), f"/volumes/{QA}_database/created_at"),
            "CHECK TABLE fails": (table_corrupt, (), "CHECK TABLE is not OK for player_items"),
            "table missing": (table_missing, (), "expected tables"),
            "no QA player": (no_qa_players, (), "no QA account or QA player"),
            "DB unreachable": (db_down, (), "database: not reachable"),
            "config.lua port": (wrong_game_port, (), "gameProtocolPort = 17172"),
            "brain config kept": (brain_still_configured, (), "CANARY_BRAIN_CONFIG"),
            "ledger left": (ledger_left, (), "brain object still present"),
            "stage-2 game config": (stage2_config, (), "config-hash"),
            "game not healthy": (game_unhealthy, (), "/health"),
            "game port closed": (None, playable_mocks(port_error=OSError("refused")), "17172 is not listening"),
            "login down": (None, playable_mocks(login_error=OSError("down")), "login.php is not reachable"),
            "MyAAC contract": (None, playable_mocks(myaac_error=RuntimeError("port")), "verify_myaac: port"),
        }
        for name, (change, mocks, message) in cases.items():
            docker = FakeDocker(self.baseline)  # stage 1 as rollback leaves it, game recreated
            docker.containers[GAME].update(id="7" * 64, created_at="2026-11-07T02:00:00Z")
            if change:
                change(docker)
            with self.subTest(name), \
                 entered(contextlib.ExitStack(), patch("preflight.command", side_effect=docker), *(mocks or playable_mocks())), \
                 self.assertRaisesRegex(RuntimeError, "stage 1 is not restored:\n(.|\n)*" + re.escape(message)):
                gate.verify_restored(self.path, self.sha, self.receipt)
            self.assertFalse(self.receipt.exists())


if __name__ == "__main__":
    unittest.main()
