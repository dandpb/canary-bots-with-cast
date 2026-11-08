"""Offline tests of the stage-2 handoff adapter. Docker, git and every mutation are mocked; nothing runs."""

import contextlib
import copy
import hashlib
import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import stage1_baseline as gate
import stage2_handoff as handoff
from test_stage1_baseline import QA, FakeDocker

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FIXTURES = HERE / "fixtures/stage2-handoff"
MANIFEST = FIXTURES / "qa-stage2-bundle-manifest-a1d9.json"
RENDER = FIXTURES / "qa-stage2-full-render-sanitized.json"
HOST = "/home/daniel/canary-core-qa-playable-20261106/deployment/core-qa"
GAME, BRAIN = gate.GAME, gate.BRAIN
RESCUE = "64385641c847ad44d6acf1dc7f5d10e206451212b4320973a27ba278e428d608"
CANDIDATE = "4188037d71a5455ef40e76e05d0fa145a9e71d977a10f0774e491286b968b605"
ADAPTER = Path(handoff.__file__).read_bytes()
GAME_ENV = {  # values only for the fake render; the real ones never leave the host
    "BOT_PLAYERS_ONLINE": "50",
    "BOT_POPULATION_REFERENCE_BOTS": "65001,65004,65003",
    "CANARY_BRAIN_CONFIG": "/etc/canary-core-qa/brain/server.json",
    "GAME_DISABLE_GLOBAL_SAVE_SHUTDOWN": "1",
    "GAME_DISABLE_MAP_DOWNLOAD": "1",
    "GAME_LOGIN_PORT": "17171",
    "GAME_PROTOCOL_PORT": "17172",
    "GAME_PUBLIC_IP": "127.0.0.1",
    "GAME_STATUS_PORT": "17173",
    "MARIADB_PASSWORD": "fake-not-a-secret",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def docker_mounts(items):
    return [
        {
            "Type": m["type"],
            "Source": m["source"],
            "Destination": m["destination"],
            "RW": m["rw"],
        }
        for m in items
    ]


class HandoffDocker(FakeDocker):
    """The fake Docker of the stage-1 tests plus brain images, inspect by ID, the render and mutations."""

    def __init__(self, baseline, manifest):
        super().__init__(baseline)
        brain = (handoff.BRAIN_IMAGE_ID, handoff.BRAIN_PLATFORM, handoff.BRAIN_REVISION)
        self.brain = {
            handoff.BRAIN_IMAGE_ID: brain,
            "canary-core-qa-brain:local": brain,
        }
        self.tags["canary-core-qa-brain:local"] = handoff.BRAIN_IMAGE_ID
        for name, item in self.containers.items():
            pinned = manifest["containers"][name]
            item.update(
                exit_code=0, restart="no", mounts=docker_mounts(pinned["mounts"])
            )
        self.others = {
            item["id"]: {
                **item,
                "labels": {},
                "exit_code": 0,
                "restart": item["restart_policy"],
                "mounts": docker_mounts(item["mounts"]),
            }
            for name, item in manifest["containers"].items()
            if name not in self.containers
        }
        self.render = ""
        self.writers = 0
        self.stop_exit = 0
        self.up_fails = False
        self.runs = []

    def find(self, ident):
        for item in [*self.containers.values(), *self.others.values()]:
            if item["id"] == ident:
                return item
        return None

    def __call__(self, *args, env=None):
        if args[:2] == ("git", "rev-parse"):
            return handoff.TOOLING_REVISION + "\n"
        if args[:2] == ("git", "status"):
            return ""
        if args[0] == "env" and "config" in args:
            return self.render
        fmt = args[-1]
        if args[1:3] == ("image", "inspect") and fmt == handoff.BRAIN_INSPECT:
            if args[3] not in self.brain:
                raise RuntimeError("read-only command failed: docker image")
            return "\t".join(self.brain[args[3]]) + "\n"
        if args[1] == "inspect" and fmt == handoff.CONTAINER:
            item = self.find(args[2])
            if not item:
                raise RuntimeError("read-only command failed: docker inspect")
            return json.dumps(
                {
                    **{key: item[key] for key in ("id", "created_at", "image_id")},
                    **{key: item[key] for key in ("status", "exit_code", "restart")},
                    "name": "/" + item["name"],
                    "labels": item["labels"],
                    "mounts": item["mounts"],
                    "config": {"Image": item["image_id"]},
                    "host_config": {"RestartPolicy": {"Name": item["restart"]}},
                }
            )
        if args[1] == "ps" and fmt == handoff.OWNED:
            return "".join(
                f"{i['id']}\t{i['labels']['com.docker.compose.service']}\t{i['status']}\n"
                for i in self.containers.values()
                if i["labels"].get("com.docker.compose.project") == QA
            )
        if args[1] == "exec" and args[-1] == handoff.WRITERS_SQL:
            return f"{self.writers}\n"
        return super().__call__(*args, env=env)

    def run(self, argv):
        """What the mocked exec-step does to the fake host."""
        self.runs.append(argv)
        if argv[:2] == ["docker", "stop"]:
            for ident in argv[4:]:
                self.find(ident).update(status="exited", exit_code=self.stop_exit)
        elif argv[:2] == ["docker", "start"]:
            self.find(argv[2]).update(status="running")
        elif "up" in argv:
            game = copy.deepcopy(self.containers[GAME])
            game.update(
                id="a" * 64, created_at="2026-11-08T03:00:00Z", status="running"
            )
            self.containers[GAME] = game
            self.containers[BRAIN] = {
                "name": BRAIN,
                "id": "e" * 64,
                "image_id": handoff.BRAIN_IMAGE_ID,
                "image_ref": handoff.BRAIN_IMAGE_ID,
                "created_at": "2026-11-08T03:00:01Z",
                "status": "created" if self.up_fails else "running",
                "health": None,
                "exit_code": 0,
                "restart": "no",
                "mounts": [],
                "labels": {
                    "com.docker.compose.project": QA,
                    "com.docker.compose.service": "brain",
                },
            }
            return (1, "", "dependency failed") if self.up_fails else (0, "", "")
        return 0, "", ""


class Clock:
    def __init__(self):
        self.now = datetime(2026, 11, 8, 2, 0, tzinfo=UTC)

    def __call__(self):
        self.now += timedelta(seconds=1)
        return self.now


class HandoffTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.project = self.root / "deploy/core-qa"
        self.baseline = gate.load_baseline()
        self.clock = Clock()
        self.manifest_path = self.write_manifest()
        self.docker = HandoffDocker(self.baseline, self.manifest)
        self.docker.render = self.raw_render
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for mock in (
            patch("preflight.command", side_effect=self.docker),
            patch("stage1_baseline.db_slice", side_effect=self.slice),
            patch("stage2_handoff.git_blob", return_value=ADAPTER),
            patch("stage2_handoff.execute", side_effect=self.docker.run),
            patch("stage2_handoff.utcnow", side_effect=self.clock),
        ):
            self.stack.enter_context(mock)
        self.slice_now = gate.comparable(self.baseline)["db_slice"]

    def slice(self):
        return copy.deepcopy(self.slice_now)

    def write_manifest(self, edit=None, render_edit=None):
        """The real manifest moved to a temporary host, with a stand-in private override and receipts."""
        text = MANIFEST.read_text().replace(HOST, str(self.project))
        manifest = json.loads(text)
        bundle = Path(manifest["bundle_directory"])
        (bundle / "brain").mkdir(parents=True, exist_ok=True)
        (self.project / ".env").write_text("MARIADB_PASSWORD=fake\n")
        for name, entry in manifest["bundle_files"].items():
            path = Path(entry["absolute_path"])
            if name == handoff.PRIVATE_OVERRIDE:
                path.write_text(
                    f"services:\n  brain:\n    image: {handoff.BRAIN_IMAGE_ID}\n"
                )
                entry.update(
                    sha256=sha(path.read_bytes()), bytes=len(path.read_bytes())
                )
            else:
                path.write_bytes((HERE / name).read_bytes())
        render = json.loads(RENDER.read_text().replace(HOST, str(self.project)))
        render["services"]["game"]["environment"] = dict(GAME_ENV)
        for name in ("database", "web"):
            env = render["services"][name]["environment"]
            render["services"][name]["environment"] = {key: "x" for key in env}
        if render_edit:
            render_edit(render)
        self.raw_render = json.dumps(render, indent=1)
        sanitized = handoff.sanitized(render)
        self.render_path = self.root / "render-sanitized.json"
        self.render_path.write_bytes(sanitized)
        manifest["render_private_sha256"] = sha(self.raw_render.encode())
        manifest["render_sanitized_sha256"] = sha(sanitized)
        game = gate.baseline_game_image()
        contents = {
            "stage2_full_preflight": json.dumps(
                {
                    "approved_source_revision": handoff.TOOLING_REVISION,
                    "brain_fake": True,
                    "stage1_upgrade": {"baseline_sha256": gate.BASELINE_SHA256},
                    "game_image_pin": game,
                }
            ),
            "brain_before": "no canary-core-qa-brain image\n",
            "brain_after": f"canary-core-qa-brain:local {handoff.BRAIN_IMAGE_ID}\n",
            "brain_build_log": "#12 writing image done\n",
            "rescue_result": json.dumps({"container": RESCUE}),
        }
        self.receipts = {}
        for key, content in contents.items():
            path = self.root / f"{key}.json"
            path.write_text(content)
            manifest["receipts"][key] = sha(path.read_bytes())
            self.receipts[key] = path
        if edit:
            edit(manifest)
        self.manifest = manifest
        path = self.root / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        return path

    def new(self, manifest=None):
        path = manifest or self.manifest_path
        return handoff.Handoff(
            REPO,
            path,
            sha(path.read_bytes()),
            self.root / "evidence",
            sha(ADAPTER),
            "f" * 40,
        )

    def post_build(self):
        receipts = {key: self.receipts[key] for key in handoff.RECEIPT_KEYS}
        return self.new().post_build(receipts, self.render_path)

    def pre_stop(self):
        path, _sha = self.post_build()
        return self.new().pre_stop(path, "Daniel", self.clock.now.isoformat())

    def stopped(self):
        return self.new().exec_step(*self.pre_stop())

    def post_stop(self):
        return self.new().post_stop(self.stopped()[0])

    def receipt(self, path):
        return json.loads(path.read_text())

    # -- static ----------------------------------------------------------------------------------

    def test_real_manifest_is_the_pinned_four_file_bundle_of_a1d9(self):
        h = handoff.Handoff(
            REPO,
            MANIFEST,
            handoff.MANIFEST_SHA256,
            self.root / "e",
            sha(ADAPTER),
            "f" * 40,
        )
        manifest = json.loads(MANIFEST.read_text())
        self.assertEqual(h.plan["up"], manifest["future_up_argv_not_executed"])
        self.assertEqual(h.plan["render"], manifest["render_argv"])
        self.assertEqual(h.plan["up"].count("-f"), 4)
        self.assertEqual(str(h.plan["project"]), manifest["qa_project_directory"])
        self.assertEqual(sha(RENDER.read_bytes()), manifest["render_sanitized_sha256"])
        render = json.loads(RENDER.read_text())
        self.assertEqual(render["services"]["brain"]["image"], handoff.BRAIN_IMAGE_ID)
        self.assertEqual(
            render["services"]["game"]["image"], gate.baseline_game_image()
        )
        self.assertEqual(handoff.sanitized(render), RENDER.read_bytes())
        self.assertEqual(self.docker.runs, [])

    def test_adapter_copy_manifest_and_checkout_must_be_the_pinned_ones(self):
        with self.assertRaisesRegex(RuntimeError, "not the pinned one"):
            handoff.Handoff(
                REPO, MANIFEST, "0" * 64, self.root / "e", sha(ADAPTER), "f" * 40
            )
        with self.assertRaisesRegex(RuntimeError, "differs from its pinned sha256"):
            handoff.Handoff(
                REPO,
                MANIFEST,
                handoff.MANIFEST_SHA256,
                self.root / "e",
                "0" * 64,
                "f" * 40,
            )
        with (
            patch("stage2_handoff.git_blob", return_value=b"other"),
            self.assertRaisesRegex(RuntimeError, "not the reviewed file"),
        ):
            self.new()
        with (
            patch(
                "preflight.command",
                side_effect=lambda *a, **k: (
                    "?? x\n" if a[1] == "status" else self.docker(*a)
                ),
            ),
            self.assertRaisesRegex(RuntimeError, "clean at a1d9"),
        ):
            self.new()

    def test_three_compose_files_or_paths_in_the_source_checkout_are_refused(self):
        def three(manifest):
            for key in ("render_argv", "future_up_argv_not_executed"):
                at = manifest[key].index("-f", manifest[key].index("-f") + 6)
                del manifest[key][at : at + 2]

        def project_in_source(manifest):
            manifest["qa_project_directory"] = str(HERE)

        def bundle_file_in_source(manifest):
            manifest["bundle_files"]["brain/worker.json"]["absolute_path"] = str(
                HERE / "brain/worker.json"
            )

        cases = {
            three: "not the 4-file argv",
            project_in_source: "inconsistent|inside the source checkout",
            bundle_file_in_source: "missing or outside the bundle",
        }
        for edit, message in cases.items():
            with (
                self.subTest(edit.__name__),
                self.assertRaisesRegex(RuntimeError, message),
            ):
                self.new(self.write_manifest(edit))

    # -- post-build and pre-stop -----------------------------------------------------------------

    def test_full_chain_runs_only_the_sealed_argv_and_keeps_revisions_apart(self):
        path, _ = self.post_stop()
        bundle, bundle_sha = self.new().bundle(path)
        up, _ = self.new().exec_step(bundle, bundle_sha)
        receipt = self.receipt(up)
        self.assertEqual(
            receipt["step"]["argv"], self.manifest["future_up_argv_not_executed"]
        )
        self.assertEqual(
            self.docker.runs,
            [
                ["docker", "stop", "-t", "180", self.baseline["containers"][1]["id"]],
                self.manifest["future_up_argv_not_executed"],
            ],
        )
        self.assertEqual(
            receipt["source_checkout"],
            {"path": str(REPO), "revision": handoff.TOOLING_REVISION},
        )
        self.assertEqual(receipt["deployment_project_directory"], str(self.project))
        provenance = receipt["provenance"]
        self.assertEqual(
            provenance["game_image"]["source_revision"],
            "3431b4046602875b161216ddb7be464eb4842f1a",
        )
        self.assertEqual(
            provenance["brain_image"]["source_revision"], handoff.BRAIN_REVISION
        )
        self.assertEqual(
            provenance["adapter"], {"sha256": sha(ADAPTER), "revision": "f" * 40}
        )
        chain = []
        link = receipt
        while link:
            chain.append(link["phase"])
            previous = link["previous"]
            link = self.receipt(Path(previous["path"])) if previous else None
            if previous:
                self.assertEqual(
                    sha(Path(previous["path"]).read_bytes()), previous["sha256"]
                )
        self.assertEqual(
            chain,
            ["exec-step", "bundle", "post-stop", "exec-step", "pre-stop", "post-build"],
        )

    def test_post_build_refuses_another_brain_image_or_brain_objects(self):
        def wrong_id(docker):
            docker.brain["canary-core-qa-brain:local"] = (
                "sha256:" + "1" * 64,
                "linux/amd64",
                handoff.BRAIN_REVISION,
            )

        def wrong_platform(docker):
            docker.brain[handoff.BRAIN_IMAGE_ID] = (
                handoff.BRAIN_IMAGE_ID,
                "linux/arm64",
                handoff.BRAIN_REVISION,
            )

        def wrong_label(docker):
            docker.brain[handoff.BRAIN_IMAGE_ID] = (
                handoff.BRAIN_IMAGE_ID,
                "linux/amd64",
                "b" * 40,
            )

        def absent(docker):
            docker.brain.clear()

        def container(docker):
            docker.extra.append(("ps", "9" * 64, BRAIN, QA, "brain"))

        def volume(docker):
            docker.extra.append(
                ("volume", gate.LEDGER, gate.LEDGER, QA, "brain-ledger")
            )

        def game_tag(docker):
            docker.tags["canary-core-qa-game:local"] = "sha256:" + "5" * 64

        def slice_drift(docker):
            self.slice_now = {
                **self.slice_now,
                "qa_character_projection_sha256": "0" * 64,
            }

        cases = {
            wrong_id: "brain image canary-core-qa-brain:local is not",
            wrong_platform: "is not .* linux/amd64",
            wrong_label: "labelled",
            absent: "brain image",
            container: "unexpected QA container",
            volume: "unexpected QA volume",
            game_tag: "game image tag",
            slice_drift: "differs from the pinned baseline",
        }
        for change, message in cases.items():
            with self.subTest(change.__name__):
                saved = copy.deepcopy(
                    (
                        self.docker.brain,
                        self.docker.extra,
                        self.docker.tags,
                        self.slice_now,
                    )
                )
                change(self.docker)
                with self.assertRaisesRegex(RuntimeError, message):
                    self.post_build()
                (
                    self.docker.brain,
                    self.docker.extra,
                    self.docker.tags,
                    self.slice_now,
                ) = saved

    def test_post_build_binds_the_manifest_receipts_and_sanitized_render(self):
        self.receipts["brain_after"].write_text("tampered\n")
        with self.assertRaisesRegex(
            RuntimeError, "brain_after receipt .* not the one the manifest pins"
        ):
            self.post_build()

    def test_pre_stop_needs_a_fresh_human_attestation(self):
        path, _ = self.post_build()
        for who, when in (
            ("", self.clock.now.isoformat()),
            ("Daniel", "2026-11-07T00:00:00+00:00"),
            ("Daniel", "2026-11-08T02:00:00"),
        ):
            with (
                self.subTest(who=who, when=when),
                self.assertRaisesRegex(RuntimeError, "human attestation"),
            ):
                self.new().pre_stop(path, who, when)
        stop, _ = self.new().pre_stop(path, "Daniel", self.clock.now.isoformat())
        self.assertEqual(
            self.receipt(stop)["step"]["argv"],
            ["docker", "stop", "-t", "180", self.baseline["containers"][1]["id"]],
        )

    # -- stop and post-stop ----------------------------------------------------------------------

    def test_no_running_gate_after_the_stop(self):
        run, _ = self.stopped()
        h = self.new()
        h.follow(run, ("exec-step",))
        with self.assertRaisesRegex(
            RuntimeError, "running/healthy gate was called after the stop"
        ):
            h.live_gate()
        with self.assertRaisesRegex(RuntimeError, "expected post-build"):
            self.new().pre_stop(run, "Daniel", self.clock.now.isoformat())

    def test_stop_by_name_is_refused(self):
        path, _ = self.pre_stop()
        receipt = self.receipt(path)
        receipt["step"]["argv"] = ["docker", "stop", "-t", "180", GAME]
        receipt["step"]["argv_sha256"] = handoff.digest(receipt["step"]["argv"])
        receipt["content_sha256"] = gate.sealed(receipt)
        forged = path.with_name("pre-stop-forged.json")
        forged.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(RuntimeError, "verified game container ID"):
            self.new().exec_step(forged, sha(forged.read_bytes()))
        self.assertEqual(self.docker.runs, [])

    def test_exec_step_runs_a_receipt_once_and_only_by_its_hash(self):
        path, digest = self.pre_stop()
        with self.assertRaisesRegex(RuntimeError, "not the one given"):
            self.new().exec_step(path, "0" * 64)
        self.new().exec_step(path, digest)
        with self.assertRaisesRegex(RuntimeError, "already ran"):
            self.new().exec_step(path, digest)
        self.assertEqual(len(self.docker.runs), 1)

    def test_post_stop_holds_and_keeps_the_receipt(self):
        def exit_code(docker):
            docker.stop_exit = 137

        def created_at(docker):
            docker.containers[GAME]["created_at"] = "2026-11-08T02:30:00Z"

        def drift(docker):
            self.slice_now = {
                **self.slice_now,
                "counts": {**self.slice_now["counts"], "player_items": 2614},
            }

        cases = {
            exit_code: "graceful save",
            created_at: "created_at changed",
            drift: "drifted after the save",
        }
        for change, message in cases.items():
            with self.subTest(change.__name__):
                self.setUp()
                if (
                    change is exit_code
                ):  # the save itself failed: docker stop killed the game
                    change(self.docker)
                run, _ = self.stopped()
                change(self.docker)
                with self.assertRaisesRegex(RuntimeError, f"HOLD(.|\n)*{message}"):
                    self.new().post_stop(run)
                held = sorted((self.root / "evidence").glob("post-stop-*.json"))
                self.assertEqual(len(held), 1)
                self.assertEqual(self.receipt(held[0])["result"], "hold")
                with self.assertRaisesRegex(RuntimeError, "expected post-stop"):
                    self.new().bundle(held[0])

    # -- bundle ----------------------------------------------------------------------------------

    def test_bundle_refuses_a_changed_file_or_render(self):
        path, _ = self.post_stop()
        worker = Path(
            self.manifest["bundle_files"]["brain/worker.json"]["absolute_path"]
        )
        original = worker.read_bytes()
        worker.write_bytes(original + b" ")
        with self.assertRaisesRegex(
            RuntimeError, "brain/worker.json differs from the pinned manifest"
        ):
            self.new().bundle(path)
        worker.write_bytes(original)
        self.docker.render = self.raw_render.replace(
            '"restart": "no"', '"restart": "always"', 1
        )
        with self.assertRaisesRegex(RuntimeError, "differs from the pinned render"):
            self.new().bundle(path)

    def test_render_mounts_from_the_source_checkout_or_a_scratch_copy_are_refused(self):
        def world_from_source(render):
            render["services"]["game"]["volumes"][0]["source"] = str(
                HERE / "runtime/world/otservbr.otbm"
            )

        def initdb_scratch(render):
            render["services"]["database"]["volumes"][1]["source"] = str(
                self.root / "scratch/initdb"
            )

        def other_bundle_file(render):
            render["services"]["brain"]["volumes"][0]["source"] = str(
                self.project / "runtime/stage2-bundle-a1d9/compose.yaml"
            )

        def config_writable(render):
            render["services"]["game"]["volumes"][3]["read_only"] = False

        cases = {
            world_from_source: "not allowed",
            initdb_scratch: "outside the project directory",
            other_bundle_file: "outside the project directory and the manifest",
            config_writable: "not read-only",
        }
        for edit, message in cases.items():
            with self.subTest(edit.__name__):
                self.setUp()
                self.manifest_path = self.write_manifest(render_edit=edit)
                self.docker.render = self.raw_render
                path, _ = self.post_stop()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().bundle(path)

    # -- fallback --------------------------------------------------------------------------------

    def failed_up(self):
        path, _ = self.post_stop()
        bundle, digest = self.new().bundle(path)
        self.docker.up_fails = True
        with self.assertRaisesRegex(RuntimeError, "HOLD"):
            self.new().exec_step(bundle, digest)
        return min((self.root / "evidence").glob("exec-step-up-*.json"))

    def test_fallback_stops_new_containers_proves_no_writers_and_starts_the_rescue_once(
        self,
    ):
        held = self.failed_up()
        rescue = self.receipts["rescue_result"]
        plan, plan_sha = self.new().fallback_plan(held, RESCUE, rescue)
        self.assertEqual(
            self.receipt(plan)["step"]["argv"],
            ["docker", "stop", "-t", "180", "a" * 64, "e" * 64],
        )
        stopped, _ = self.new().exec_step(plan, plan_sha)
        self.docker.writers = 1
        with self.assertRaisesRegex(RuntimeError, "writers"):
            self.new().fallback_verify(stopped, RESCUE, rescue)
        self.docker.writers = 0
        verify, verify_sha = self.new().fallback_verify(stopped, RESCUE, rescue)
        self.assertEqual(
            self.receipt(verify)["step"]["argv"], ["docker", "start", RESCUE]
        )
        self.new().exec_step(verify, verify_sha)
        self.assertEqual(self.docker.find(RESCUE)["status"], "running")
        self.assertEqual(self.docker.find(CANDIDATE)["status"], "exited")
        with self.assertRaisesRegex(RuntimeError, "already ran"):
            self.new().exec_step(verify, verify_sha)
        self.assertEqual(self.docker.runs[-1], ["docker", "start", RESCUE])
        self.assertEqual(
            sum(run[:2] == ["docker", "start"] for run in self.docker.runs), 1
        )

    def test_fallback_refuses_a_rescue_that_is_not_stopped_with_restart_no(self):
        held = self.failed_up()
        rescue = self.receipts["rescue_result"]
        for change, message in (
            ({"status": "running"}, "stopped with restart=no"),
            ({"restart": "always"}, "differs from the manifest"),
        ):
            with self.subTest(change):
                saved = dict(self.docker.find(RESCUE))
                self.docker.find(RESCUE).update(change)
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().fallback_plan(held, RESCUE, rescue)
                self.docker.find(RESCUE).update(saved)
        with self.assertRaisesRegex(RuntimeError, "not the one the manifest"):
            self.new().fallback_plan(held, CANDIDATE, rescue)
        self.docker.find(CANDIDATE)["status"] = "running"
        with self.assertRaisesRegex(RuntimeError, "not preserved and stopped"):
            self.new().fallback_plan(held, RESCUE, rescue)

    def test_fallback_needs_the_stop_first(self):
        path, _ = self.post_build()
        with self.assertRaisesRegex(RuntimeError, "expected post-stop"):
            self.new().fallback_plan(path, RESCUE, self.receipts["rescue_result"])


if __name__ == "__main__":
    unittest.main()
