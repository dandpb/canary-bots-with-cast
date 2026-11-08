"""Offline tests of the stage-2 handoff adapter. Docker, git and every mutation are mocked; nothing runs."""

import contextlib
import copy
import hashlib
import json
import re
import tempfile
import threading
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
GAME, BRAIN, WEB, DATABASE = gate.GAME, gate.BRAIN, gate.WEB, gate.DATABASE
RESCUE = "64385641c847ad44d6acf1dc7f5d10e206451212b4320973a27ba278e428d608"
CANDIDATE = "4188037d71a5455ef40e76e05d0fa145a9e71d977a10f0774e491286b968b605"
ADAPTER = Path(handoff.__file__).read_bytes()
SECRET = "fake-not-a-secret"
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
    "MARIADB_PASSWORD": SECRET,
}
TCP_HEADER = (
    "  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid"
)
TCP_LISTEN = (
    "   0: 00000000:4313 00000000:0000 0A 00000000:00000000 00:00000000 00000000  1000"
)
TCP_DB = (
    "   1: 0100007F:9C40 0100007F:0CEA 01 00000000:00000000 00:00000000 00000000  1000"
)
TCP_PLAYER = (
    "   2: 0100007F:4314 0100007F:D431 01 00000000:00000000 00:00000000 00000000  1000"
)


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


def fake_config(item):
    """What the fake `docker inspect` returns as .Config and .HostConfig."""
    return {
        "config": {"Image": item["image_id"], "Env": item.get("env", [])},
        "host_config": {"RestartPolicy": {"Name": item["restart"]}},
    }


def render_env(render):
    """The fake render: game values above, the DB password shared, every other value 'x'."""
    render["services"]["game"]["environment"] = dict(GAME_ENV)
    for name in ("database", "web"):
        env = render["services"][name]["environment"]
        render["services"][name]["environment"] = {key: "x" for key in env}
    render["services"]["database"]["environment"]["MARIADB_PASSWORD"] = SECRET


class HandoffDocker(FakeDocker):
    """The fake Docker of the stage-1 tests plus brain images, inspect by ID, the render and mutations."""

    def __init__(self, baseline, manifest, render, clock):
        super().__init__(baseline)
        self.clock = clock
        brain = (handoff.BRAIN_IMAGE_ID, handoff.BRAIN_PLATFORM, handoff.BRAIN_REVISION)
        self.brain = {
            handoff.BRAIN_IMAGE_ID: brain,
            "canary-core-qa-brain:local": brain,
        }
        self.tags["canary-core-qa-brain:local"] = handoff.BRAIN_IMAGE_ID
        env = {
            name: [
                f"{k}={v}"
                for k, v in render["services"][service]["environment"].items()
            ]
            for name, service in ((DATABASE, "database"), (WEB, "web"))
        }
        stage1_game = {**GAME_ENV, "CANARY_BRAIN_CONFIG": gate.DISABLED_BRAIN}
        stage1_game.pop("BOT_POPULATION_REFERENCE_BOTS")
        env[GAME] = [f"{k}={v}" for k, v in stage1_game.items()]
        for name, item in self.containers.items():
            pinned = manifest["containers"][name]
            item.update(
                exit_code=0,
                restart="no",
                mounts=docker_mounts(pinned["mounts"]),
                env=["PATH=/usr/local/bin:/usr/bin", *env[name]],
            )
        self.others = {
            item["id"]: {
                **item,
                "labels": {},
                "exit_code": 0,
                "restart": item["restart_policy"],
                "mounts": docker_mounts(item["mounts"]),
                "env": ["PATH=/usr/bin", "GAME_LOGIN_PORT=17171"],
                "started_at": "2026-11-07T23:01:12.1Z",
                "health_log": [{"End": "2026-11-07T23:04:30.5Z", "ExitCode": 1}],
            }
            for name, item in manifest["containers"].items()
            if name not in self.containers
        }
        self.render = ""
        self.writers = 0
        self.stop_exit = 0
        self.up_fails = False
        self.roster = ["online\t100\t65000", "online\t101\t65000"]
        self.sessions = 0
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
        if args[1] == "inspect" and fmt in (handoff.CONTAINER, handoff.HEALTH_PROBE):
            item = self.find(args[2])
            if not item:
                raise RuntimeError("read-only command failed: docker inspect")
            if fmt == handoff.HEALTH_PROBE:
                health = item.get("health")
                return json.dumps(
                    {
                        "status": item["status"],
                        "started_at": item.get("started_at", "2026-11-08T00:05:46Z"),
                        "health": health
                        and {"Status": health, "Log": item.get("health_log", [])},
                    }
                )
            return json.dumps(
                {
                    **{key: item[key] for key in ("id", "created_at", "image_id")},
                    **{key: item[key] for key in ("status", "exit_code", "restart")},
                    "health": item.get("health"),
                    "name": "/" + item["name"],
                    "labels": item["labels"],
                    "mounts": item["mounts"],
                    **fake_config(item),
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
        if args[1] == "exec" and args[-1] == handoff.ROSTER_SQL:
            return "".join(row + "\n" for row in self.roster)
        if args[1] == "exec" and tuple(args[3:]) == handoff.TCP_PROBE:
            if self.find(args[2])["status"] != "running":
                raise RuntimeError("read-only command failed: docker exec")
            players = [TCP_PLAYER] * self.sessions
            return (
                "\n".join([TCP_HEADER, TCP_LISTEN, TCP_DB, *players, TCP_HEADER]) + "\n"
            )
        return super().__call__(*args, env=env)

    def run(self, argv):
        """What the mocked exec-step does to the fake host."""
        self.runs.append(argv)
        if argv[:2] == ["docker", "stop"]:
            for ident in argv[4:]:
                self.find(ident).update(status="exited", exit_code=self.stop_exit)
        elif argv[:2] == ["docker", "start"]:
            started = (self.clock.now + timedelta(seconds=1)).isoformat()
            self.find(argv[2]).update(
                status="running", started_at=started, health="starting", health_log=[]
            )
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
        self.docker = None
        self.manifest_path = self.write_manifest()
        self.write_native()
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
        self.slice_now = copy.deepcopy(gate.comparable(self.baseline)["db_slice"])

    def slice(self):
        return copy.deepcopy(self.slice_now)

    def write_manifest(self, edit=None, render_edit=None):
        """The real manifest moved to a temporary host, with a stand-in private override and receipts."""
        text = MANIFEST.read_text().replace(HOST, str(self.project))
        original = json.loads(RENDER.read_text())
        for service in original[
            "services"
        ].values():  # Docker Desktop names binds by path hash
            for mount in service.get("volumes", []):
                if mount["type"] == "bind":
                    moved = mount["source"].replace(HOST, str(self.project))
                    text = text.replace(
                        sha(mount["source"].encode()), sha(moved.encode())
                    )
        manifest = json.loads(text)
        bundle = Path(manifest["bundle_directory"])
        (bundle / "brain").mkdir(parents=True, exist_ok=True)
        env_file = self.project / ".env"
        env_file.write_text("MARIADB_PASSWORD=fake\n")
        manifest["env_file"]["sha256"] = sha(env_file.read_bytes())
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
        render_env(render)
        if render_edit:
            render_edit(render)
        self.render_dict = render
        self.raw_render = json.dumps(render, indent=1)
        sanitized = handoff.sanitized(render)
        self.render_path = self.root / "render-sanitized.json"
        self.render_path.write_bytes(sanitized)
        manifest["render_private_sha256"] = sha(self.raw_render.encode())
        manifest["verification"]["render_private_recomputed_sha256"] = sha(
            self.raw_render.encode()
        )
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
            "brain_before": json.dumps(
                {"images": {"canary-core-qa-brain:local": None}}
            ),
            "brain_after": json.dumps(
                {"images": {"canary-core-qa-brain:local": handoff.BRAIN_IMAGE_ID}}
            ),
            "brain_build_log": "#12 writing image done\n",
            "rescue_result": json.dumps({"container": RESCUE}),
            "game_rollout_after": json.dumps({"game": "3431b404"}),
            "stage1_baseline": gate.BASELINE.read_text(),
        }
        self.receipts = {}
        for key, content in contents.items():
            path = self.root / "receipts" / f"{key}.json"
            path.parent.mkdir(exist_ok=True)
            path.write_text(content)
            manifest["receipts"][key] = sha(path.read_bytes())
            manifest["receipt_files"][key] = {
                "absolute_path": str(path),
                "sha256": sha(path.read_bytes()),
            }
            self.receipts[key] = path
        if (
            self.docker is None
        ):  # one fake host per setUp; a rewritten manifest keeps its state
            self.docker = HandoffDocker(self.baseline, manifest, render, self.clock)
            self.docker.render = self.raw_render
        rescue_config = handoff.config_digest(fake_config(self.docker.find(RESCUE)))
        manifest["rescue_container_config"].update(
            config_sha256=rescue_config, adapter_config_sha256=rescue_config
        )
        if edit:
            edit(manifest)
        self.manifest = manifest
        self.notice = self.root / "window-notice.txt"
        self.notice.write_text("Coordinator: QA window 02:00-03:00 UTC, no players.\n")
        path = self.root / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        return path

    def new(self, manifest=None, evidence=None):
        path = manifest or self.manifest_path
        return handoff.Handoff(
            REPO,
            path,
            sha(path.read_bytes()),
            evidence or self.root / "evidence",
            sha(ADAPTER),
            "f" * 40,
        )

    def post_build(self):
        receipts = {key: self.receipts[key] for key in handoff.RECEIPT_KEYS}
        return self.new().post_build(receipts, self.render_path)

    def write_native(self, online=None, **fields):
        """The native GUID -> bot/human roster a collector would write (contract of the adapter)."""
        roster = {
            "game_container_id": self.docker.containers[GAME]["id"],
            "collected_at_utc": self.clock.now.isoformat(),
            "source": "fake native roster for the offline tests",
            "online": [
                {"guid": 100, "type": "bot"},
                {"guid": 101, "type": "bot"},
            ]
            if online is None
            else online,
            **fields,
        }
        self.native = self.root / "native-roster.json"
        self.native.write_text(json.dumps(roster))
        return self.native

    def attest(self, h, path, notice_sha=None, native=None, native_sha=None):
        native = native or self.native
        return h.pre_stop(
            path,
            "Daniel",
            self.clock.now.isoformat(),
            self.notice,
            notice_sha or sha(self.notice.read_bytes()),
            native,
            native_sha or (sha(native.read_bytes()) if native.is_file() else None),
        )

    def pre_stop(self):
        path, _sha = self.post_build()
        return self.attest(self.new(), path)

    def stopped(self):
        return self.new().exec_step(*self.pre_stop())

    def post_stop(self):
        return self.new().post_stop(self.stopped()[0])

    def bundled(self):
        return self.new().bundle(self.post_stop()[0])

    def receipt(self, path):
        return json.loads(path.read_text())

    def evidence_text(self):
        return "".join(p.read_text() for p in (self.root / "evidence").glob("*.json"))

    # -- static ----------------------------------------------------------------------------------

    def test_real_manifest_is_the_pinned_four_file_bundle_of_a1d9(self):
        self.assertEqual(sha(MANIFEST.read_bytes()), handoff.MANIFEST_SHA256)
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
        self.assertEqual(h.claims, Path(HOST) / handoff.CLAIMS)
        self.assertEqual(sha(RENDER.read_bytes()), manifest["render_sanitized_sha256"])
        render = json.loads(RENDER.read_text())
        self.assertEqual(render["services"]["brain"]["image"], handoff.BRAIN_IMAGE_ID)
        self.assertEqual(
            render["services"]["game"]["image"], gate.baseline_game_image()
        )
        self.assertEqual(handoff.sanitized(render), RENDER.read_bytes())
        self.assertEqual(self.docker.runs, [])

    def test_real_manifest_new_fields_are_consumed(self):
        h = handoff.Handoff(
            REPO,
            MANIFEST,
            handoff.MANIFEST_SHA256,
            self.root / "e",
            sha(ADAPTER),
            "f" * 40,
        )
        self.assertEqual(
            h.plan["brain"],
            {
                "id": "sha256:9ea0a34688db0443dabfa6c64736f78b53e954a19c9ead8c61d52f2bbdefa0cd",
                "platform": "linux/amd64",
                "source_revision_label": "a1d9fe803c77da63f4aa1bf943d3d488d3117850",
                "tag": "canary-core-qa-brain:local",
            },
        )
        self.assertEqual(
            h.plan["rescue_config_sha256"],
            "626ceb4905042d9410effb4a76da5b9c97432ab831cdccd4766ed6608482f4d2",
        )
        self.assertEqual(
            h.plan["env_sha256"],
            "4cda5ef63dedbbaf8790e2527f2aaaf5c902cb35ad2f0d836027ba1a184a15a2",
        )
        self.assertEqual(
            h.manifest["render_private_sha256"],
            "adcbd2dea69f4e18141fdb4aec4102edbb7d8231d6b1de772f410f7d1ea90f29",
        )
        self.assertEqual(
            {key: entry["sha256"] for key, entry in h.plan["receipts"].items()},
            h.manifest["receipts"],
        )
        self.assertTrue(
            all(
                Path(e["absolute_path"]).is_absolute()
                for e in h.plan["receipts"].values()
            )
        )
        self.assertEqual(h.plan["rescue"][0], "qa-old-rescue-20261107")
        self.assertEqual(h.plan["candidate"][0], "qa-game-candidate-3431b404")

    def test_real_manifest_binds_are_desktop_equivalent_to_the_render_host_paths(self):
        """The initial equivalence on the real data: every pinned bind names the render's host path."""
        manifest, render = (
            json.loads(MANIFEST.read_text()),
            json.loads(RENDER.read_text()),
        )
        services = {
            "canary-core-qa-database-1": "database",
            "canary-core-qa-game-1": "game",
            "qa-old-rescue-20261107": "game",
            "qa-game-candidate-3431b404": "game",
        }
        checked = 0
        for name, service in services.items():
            wanted = {
                m["target"]: m["source"]
                for m in render["services"][service]["volumes"]
                if m["type"] == "bind"
            }
            for mount in manifest["containers"][name]["mounts"]:
                if mount["type"] == "bind":
                    form = handoff.desktop_form(
                        mount["source"], wanted[mount["destination"]]
                    )
                    self.assertEqual(form, "desktop-hash", name)
                    checked += 1
        self.assertEqual(checked, 4)

    def test_desktop_bind_mapping_is_explicit(self):
        host = "/home/daniel/canary-core-qa-playable-20261106/deployment/core-qa/runtime/initdb"
        hashed = f"{handoff.DESKTOP_BINDS}/Ubuntu/{sha(host.encode())}"
        cases = {
            host: "host",
            f"/run/desktop/mnt/host/wsl/Ubuntu{host}": "desktop-path",
            hashed: "desktop-hash",
            f"/run/desktop/mnt/host/wsl/Debian{host}": None,
            f"{handoff.DESKTOP_BINDS}/Debian/{sha(host.encode())}": None,
            f"{handoff.DESKTOP_BINDS}/Ubuntu/{sha((host + '/').encode())}": None,
            f"{handoff.DESKTOP_BINDS}/Ubuntu/{sha(b'/home/daniel/other')}": None,
            host + "/": None,
            "/home/daniel/other": None,
        }
        for inspected, form in cases.items():
            with self.subTest(inspected):
                self.assertEqual(handoff.desktop_form(inspected, host), form)
        self.assertIsNone(handoff.desktop_form(host, host + "/../initdb"))
        self.assertIsNone(handoff.desktop_form("runtime/initdb", "runtime/initdb"))

    def test_rescue_config_hash_uses_exactly_the_adapter_serialization(self):
        """Pinned: sha256(json.dumps({config, host_config}, sort_keys=True)) with Python defaults."""
        config = fake_config(self.docker.find(RESCUE))
        right = handoff.config_digest(config)
        config_only = sha(
            json.dumps(
                config["config"],
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
        )
        compact = sha(
            json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
        )
        self.assertEqual(right, sha(json.dumps(config, sort_keys=True).encode()))
        self.assertEqual(len({right, config_only, compact}), 3)
        for wrong in (config_only, compact):
            with self.subTest(wrong=wrong):

                def pin(manifest, value=wrong):
                    manifest["rescue_container_config"].update(
                        config_sha256=value, adapter_config_sha256=value
                    )

                with self.assertRaisesRegex(
                    RuntimeError,
                    "qa-old-rescue-20261107 differs from the manifest \\(config_sha256\\)",
                ):
                    self.new(self.write_manifest(pin)).rescue()
        self.manifest_path = self.write_manifest()
        self.assertEqual(self.new().rescue()["config_sha256"], right)

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

    def test_manifest_fields_that_are_not_the_reviewed_ones_are_refused(self):
        def brain_platform(manifest):
            manifest["brain_image"]["platform"] = "linux/arm64"

        def receipt_path_relative(manifest):
            manifest["receipt_files"]["brain_after"]["absolute_path"] = (
                "brain-after.json"
            )

        def receipt_hash_other(manifest):
            manifest["receipt_files"]["brain_after"]["sha256"] = "0" * 64

        def receipt_missing(manifest):
            del manifest["receipt_files"]["rescue_result"]

        def env_hash_missing(manifest):
            del manifest["env_file"]["sha256"]

        def rescue_config_legacy(manifest):
            manifest["rescue_container_config"]["config_sha256"] = manifest[
                "rescue_container_config"
            ]["legacy_config_only_sha256"]

        def rescue_other_id(manifest):
            manifest["rescue_container_config"]["container_id"] = CANDIDATE

        def candidate_running(manifest):
            manifest["containers"]["qa-game-candidate-3431b404"]["status"] = "running"

        cases = {
            brain_platform: "brain_image is not the reviewed",
            receipt_path_relative: "no absolute path",
            receipt_hash_other: "another sha256",
            receipt_missing: "do not cover",
            env_hash_missing: "raw-bytes sha256",
            rescue_config_legacy: "rescue config hash",
            rescue_other_id: "rescue config hash",
            candidate_running: "qa-game-candidate-",
        }
        for edit, message in cases.items():
            with (
                self.subTest(edit.__name__),
                self.assertRaisesRegex(RuntimeError, message),
            ):
                self.new(self.write_manifest(edit))

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
        bundle, bundle_sha = self.bundled()
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
        self.assertNotIn(SECRET, self.evidence_text())  # values never reach a receipt
        claims = sorted(p.name for p in (self.project / handoff.CLAIMS).iterdir())
        self.assertEqual(len(claims), 4)  # 2 claims and their 2 results

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

    def test_post_build_binds_every_receipt_by_absolute_path_and_hash(self):
        receipts = {key: self.receipts[key] for key in handoff.RECEIPT_KEYS}
        other = self.root / "elsewhere/brain_after.json"
        other.parent.mkdir()
        other.write_bytes(self.receipts["brain_after"].read_bytes())
        with self.assertRaisesRegex(
            RuntimeError, "not at the manifest's absolute path"
        ):
            self.new().post_build({**receipts, "brain_after": other}, self.render_path)
        for key in (
            "brain_after",
            "rescue_result",
            "game_rollout_after",
            "stage1_baseline",
        ):
            with self.subTest(key):
                original = self.receipts[key].read_bytes()
                self.receipts[key].write_bytes(original + b" ")
                with self.assertRaisesRegex(
                    RuntimeError, f"{key} receipt at .* not the one the manifest pins"
                ):
                    self.new().post_build(None, self.render_path)
                self.receipts[key].write_bytes(original)
        path, _ = self.new().post_build(None, self.render_path)
        self.assertEqual(
            set(self.receipt(path)["receipts"]), set(self.manifest["receipt_files"])
        )

    def test_post_build_reads_brain_before_and_after_by_structure(self):
        cases = {
            "brain_before": (
                json.dumps(
                    {"images": {"canary-core-qa-brain:local": handoff.BRAIN_IMAGE_ID}}
                ),
                json.dumps({"images": {}}),
                "no images\n",
            ),
            "brain_after": (
                json.dumps({"images": {"canary-core-qa-brain:local": None}}),
            ),
        }
        for key, contents in cases.items():
            for content in contents:
                with self.subTest(key=key, content=content):
                    self.setUp()
                    self.receipts[key].write_text(content)
                    self.manifest["receipts"][key] = sha(content.encode())
                    self.manifest["receipt_files"][key]["sha256"] = sha(
                        content.encode()
                    )
                    self.manifest_path.write_text(json.dumps(self.manifest))
                    with self.assertRaisesRegex(
                        RuntimeError, "brain_before/brain_after"
                    ):
                        self.post_build()

    def test_env_file_raw_bytes_are_checked_and_a_mismatch_is_refused(self):
        env = self.project / ".env"
        env.write_text(
            "MARIADB_PASSWORD=fake \n"
        )  # one byte more: same names, other bytes
        with self.assertRaisesRegex(
            RuntimeError, r"\.env is absent or its raw bytes differ"
        ):
            self.post_build()
        env.write_text("MARIADB_PASSWORD=fake\n")
        bundle, digest = self.bundled()
        env.write_bytes(b"MARIADB_PASSWORD=fake\r\n")
        with self.assertRaisesRegex(
            RuntimeError, r"\.env is absent or its raw bytes differ"
        ):
            self.new().exec_step(bundle, digest)
        self.assertEqual(len(self.docker.runs), 1)

    def test_pre_stop_needs_a_fresh_human_attestation(self):
        path, _ = self.post_build()
        notice = sha(self.notice.read_bytes())
        for who, when in (
            ("", self.clock.now.isoformat()),
            ("Daniel", "2026-11-07T00:00:00+00:00"),
            ("Daniel", "2026-11-08T02:00:00"),
        ):
            with (
                self.subTest(who=who, when=when),
                self.assertRaisesRegex(RuntimeError, "human attestation"),
            ):
                self.new().pre_stop(path, who, when, self.notice, notice)
        stop, _ = self.attest(self.new(), path)
        receipt = self.receipt(stop)
        self.assertEqual(
            receipt["step"]["argv"],
            ["docker", "stop", "-t", "180", self.baseline["containers"][1]["id"]],
        )
        people = receipt["human_exclusion"]
        self.assertEqual(people["window_notice"]["sha256"], notice)
        self.assertEqual(people["roster"]["online"], 2)
        self.assertEqual(
            (people["qa_humans_online"], people["game_port_sessions"]), (0, 0)
        )

    def test_p2_4_pre_stop_binds_roster_sessions_and_window_notice(self):
        """P2 #4: the human exclusion is evidence, not a name and a time."""
        path, _ = self.post_build()

        def qa_human(docker):
            docker.roster.append("online\t66100\t65001")

        def god(docker):
            docker.roster.append("online\t1\t1")

        def orphan(docker):
            docker.roster.append("online\t5\t-1")

        def tcp_session(docker):
            docker.sessions = 1

        def bad_roster(docker):
            docker.roster = ["oops"]

        cases = {
            qa_human: "non-bot character",
            god: "non-bot character",
            orphan: "non-bot character",
            tcp_session: "TCP session",
            bad_roster: "unexpected shape",
        }
        for change, message in cases.items():
            with self.subTest(change.__name__):
                saved = (list(self.docker.roster), self.docker.sessions)
                change(self.docker)
                with self.assertRaisesRegex(RuntimeError, message):
                    self.attest(self.new(), path)
                self.docker.roster, self.docker.sessions = saved
        with self.assertRaisesRegex(RuntimeError, "window notice"):
            self.attest(self.new(), path, "0" * 64)
        self.assertEqual(list((self.root / "evidence").glob("pre-stop-*.json")), [])

    def test_native_roster_backs_every_online_guid(self):
        """Account 65000 is no proof of a bot: each players_online GUID needs fresh native evidence."""
        path, _ = self.post_build()
        stop, _ = self.attest(self.new(), path)
        people = self.receipt(stop)["human_exclusion"]
        native = people["native_roster"]
        self.assertEqual(native["sha256"], sha(self.native.read_bytes()))
        self.assertEqual(
            native["game_container_id"], self.docker.containers[GAME]["id"]
        )
        self.assertEqual(native["bots"], [100, 101])
        self.assertTrue(people["roster"]["bot_only"])
        # an empty players_online passes only with a native empty set and its explanation
        self.docker.roster = []
        self.write_native([], empty_explanation="no bots loaded; no player online")
        empty, _ = self.attest(self.new(), path)
        self.assertEqual(self.receipt(empty)["human_exclusion"]["roster"]["online"], 0)

    def test_native_roster_refusals(self):
        path, _ = self.post_build()
        game = self.docker.containers[GAME]["id"]
        now = self.clock.now

        def hash_mismatch():
            native = self.write_native()
            return {"native": native, "native_sha": "0" * 64}

        def missing():
            self.native.unlink()
            return {}

        def other_container():
            self.write_native(game_container_id=CANDIDATE)
            return {}

        def short_container_id():
            self.write_native(game_container_id=game[:12])
            return {}

        def stale():
            self.write_native(
                collected_at_utc=(now - timedelta(minutes=16)).isoformat()
            )
            return {}

        def future():
            self.write_native(collected_at_utc=(now + timedelta(minutes=5)).isoformat())
            return {}

        def unknown_guid():
            self.docker.roster.append("online\t42\t65000")
            return {}

        def native_human():
            self.write_native(
                [{"guid": 100, "type": "bot"}, {"guid": 7, "type": "human"}]
            )
            return {}

        def empty_sql_native_not_empty():
            self.docker.roster = []
            return {}

        def empty_sql_without_explanation():
            self.docker.roster = []
            self.write_native([])
            return {}

        def not_the_contract():
            self.write_native([{"guid": "100", "type": "bot"}])
            return {}

        cases = {
            hash_mismatch: "native roster is not the given sha256",
            missing: "needs native roster evidence",
            other_container: "not collected from the current game container",
            short_container_id: "not collected from the current game container",
            stale: "stale or dated in the future",
            future: "stale or dated in the future",
            unknown_guid: "not in the native roster",
            native_human: "human\\(s\\) online; bot_only is required",
            empty_sql_native_not_empty: "players_online is empty without a native empty roster",
            empty_sql_without_explanation: "players_online is empty without a native empty roster",
            not_the_contract: "does not follow the contract",
        }
        for change, message in cases.items():
            with self.subTest(change.__name__):
                saved = list(self.docker.roster)
                self.write_native()
                self.clock.now = now
                given = change()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.attest(self.new(), path, **given)
                self.docker.roster = saved
        self.assertEqual(list((self.root / "evidence").glob("pre-stop-*.json")), [])
        with self.assertRaisesRegex(RuntimeError, "needs native roster evidence"):
            self.new().pre_stop(
                path,
                "Daniel",
                now.isoformat(),
                self.notice,
                sha(self.notice.read_bytes()),
            )

    def test_native_roster_is_refreshed_at_the_stop(self):
        def stale():
            self.clock.now += timedelta(minutes=16)

        def unknown_guid():
            self.docker.roster.append("online\t42\t65000")

        def file_changed():
            self.write_native([{"guid": 100, "type": "bot"}])

        def emptied():
            self.docker.roster = []

        cases = {
            stale: "stale",
            unknown_guid: "not in the native roster",
            file_changed: "native roster is not the given sha256",
            emptied: "players_online is empty",
        }
        for change, message in cases.items():
            with self.subTest(change.__name__):
                self.setUp()
                path, digest = self.pre_stop()
                change()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().exec_step(path, digest)
                self.assertEqual(self.docker.runs, [])

    def test_p2_4_human_exclusion_is_refreshed_at_the_stop(self):
        def qa_human():
            self.docker.roster.append("online\t66101\t65002")

        def tcp_session():
            self.docker.sessions = 2

        def notice_changed():
            self.notice.write_text("window cancelled\n")

        cases = {
            qa_human: "non-bot character",
            tcp_session: "TCP session",
            notice_changed: "window notice",
        }
        for change, message in cases.items():
            with self.subTest(change.__name__):
                self.setUp()
                path, digest = self.pre_stop()
                change()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().exec_step(path, digest)
                self.assertEqual(self.docker.runs, [])

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
            self.attest(self.new(), run)

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
        with self.assertRaisesRegex(RuntimeError, "already claimed: it ran"):
            self.new().exec_step(path, digest)
        self.assertEqual(len(self.docker.runs), 1)

    def test_p2_1_concurrent_exec_steps_one_claim_wins(self):
        """P2 #1: two exec-steps past their prechecks at once; the atomic claim lets one run."""
        path, digest = self.pre_stop()
        barrier, errors = threading.Barrier(2), []
        original = handoff.Handoff.precheck

        def precheck(h, receipt, argv):
            original(h, receipt, argv)
            barrier.wait(timeout=5)

        def run(h):
            try:
                h.exec_step(path, digest)
            except RuntimeError as error:
                errors.append(str(error))

        workers = [self.new(), self.new()]
        with patch.object(handoff.Handoff, "precheck", precheck):
            threads = [threading.Thread(target=run, args=(w,)) for w in workers]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
        self.assertEqual(len(self.docker.runs), 1)
        self.assertEqual(len(errors), 1)
        self.assertRegex(errors[0], "already claimed")

    def test_p2_1_claim_is_canonical_and_ignores_evidence(self):
        """P2 #1: another --evidence directory does not make a sealed step runnable again."""
        path, digest = self.pre_stop()
        self.new().exec_step(path, digest)
        with self.assertRaisesRegex(RuntimeError, "already claimed"):
            self.new(evidence=self.root / "other-evidence").exec_step(path, digest)
        other = self.new()
        other.evidence = self.root / "third-evidence"
        with self.assertRaisesRegex(RuntimeError, "already claimed"):
            other.exec_step(path, digest)
        self.assertEqual(len(self.docker.runs), 1)

    def test_p2_1_crash_after_the_mutation_stays_consumed_and_holds(self):
        """P2 #1: the claim is durable before the command; a lost result is HOLD, never a retry."""
        path, digest = self.pre_stop()
        claim = self.project / handoff.CLAIMS / f"{digest}.stop-game.claim"
        seen = []

        def mutate_then_crash(argv):
            seen.append(claim.is_file())
            self.docker.run(argv)
            raise KeyboardInterrupt("power loss after the mutation")

        with (
            patch("stage2_handoff.execute", side_effect=mutate_then_crash),
            self.assertRaises(KeyboardInterrupt) as crash,
        ):
            self.new().exec_step(path, digest)
        self.assertEqual(seen, [True])
        self.assertIn("HOLD", "".join(crash.exception.__notes__))
        with self.assertRaisesRegex(
            RuntimeError, "without a result: interrupted or uncertain; HOLD"
        ):
            self.new().exec_step(path, digest)
        self.assertEqual(len(self.docker.runs), 1)
        self.assertEqual(json.loads(claim.read_text())["receipt_sha256"], digest)

    def test_p2_1_receipt_write_failure_after_the_mutation_holds(self):
        bundle, digest = self.bundled()
        victim = self.new()
        with (
            patch.object(victim, "write", side_effect=OSError("evidence disk failure")),
            self.assertRaises(OSError),
        ):
            victim.exec_step(bundle, digest)
        with self.assertRaisesRegex(RuntimeError, "interrupted or uncertain; HOLD"):
            self.new().exec_step(bundle, digest)
        self.assertEqual(sum("up" in argv for argv in self.docker.runs), 1)

    def test_p2_2_receipt_dated_in_the_future_is_refused(self):
        path, digest = self.pre_stop()
        self.clock.now -= timedelta(minutes=5)
        with self.assertRaisesRegex(RuntimeError, "dated in the future"):
            self.new().exec_step(path, digest)
        self.clock.now += timedelta(minutes=30)
        with self.assertRaisesRegex(RuntimeError, "stale"):
            self.new().exec_step(path, digest)
        self.assertEqual(self.docker.runs, [])

    def test_p2_2_stop_refreshes_the_live_gate(self):
        """P2 #2: drift after pre-stop sealing never reaches the stop."""

        def slice_drift():
            self.slice_now["counts"]["player_items"] += 1

        def web_unhealthy():
            self.docker.containers[WEB]["health"] = "unhealthy"

        def brain_container():
            self.docker.extra.append(("ps", "9" * 64, BRAIN, QA, "brain"))

        cases = {
            slice_drift: "differs from the pinned baseline",
            web_unhealthy: "differs from the pinned baseline",
            brain_container: "unexpected QA container",
        }
        for change, message in cases.items():
            with self.subTest(change.__name__):
                self.setUp()
                path, digest = self.pre_stop()
                change()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().exec_step(path, digest)
                self.assertEqual(self.docker.runs, [])

    def test_p2_2_up_refreshes_post_stop_state_slice_and_render(self):
        """P2 #2: DB drift, render drift, env value drift after the bundle never reach the up."""

        def slice_drift():
            self.slice_now["counts"]["player_items"] += 1

        def render_drift():
            self.docker.render = self.raw_render.replace(SECRET, "changed-value")

        def db_unhealthy():
            self.docker.containers[DATABASE]["health"] = "unhealthy"

        def live_env_value():
            env = self.docker.containers[DATABASE]["env"]
            self.docker.containers[DATABASE]["env"] = [
                "MARIADB_PASSWORD=rotated" if e.startswith("MARIADB_PASSWORD=") else e
                for e in env
            ]

        def worker_file():
            path = Path(
                self.manifest["bundle_files"]["brain/worker.json"]["absolute_path"]
            )
            path.write_bytes(path.read_bytes() + b" ")

        cases = {
            slice_drift: "DB slice drifted since the stop",
            render_drift: "differs from the pinned render",
            db_unhealthy: "running/healthy exactly",
            live_env_value: "live database environment values differ",
            worker_file: "worker.json differs from the pinned manifest",
        }
        for change, message in cases.items():
            with self.subTest(change.__name__):
                self.setUp()
                bundle, digest = self.bundled()
                change()
                with self.assertRaisesRegex(RuntimeError, message) as refused:
                    self.new().exec_step(bundle, digest)
                self.assertNotIn("rotated", str(refused.exception))
                self.assertEqual(len(self.docker.runs), 1)  # only the stop ran

    def test_p2_3_forward_path_needs_the_rescue_and_a_stopped_candidate(self):
        """P2 #3: rescue present/stopped/restart=no/config and candidate stopped before stop and up."""

        def candidate_running():
            self.docker.find(CANDIDATE)["status"] = "running"

        def rescue_missing():
            self.docker.others.pop(RESCUE)

        def rescue_restart():
            self.docker.find(RESCUE)["restart"] = "always"

        def rescue_exit():
            self.docker.find(RESCUE)["exit_code"] = 137

        def rescue_config():
            self.docker.find(RESCUE)["env"] = ["PATH=/usr/bin", "INJECTED=1"]

        cases = {
            candidate_running: "qa-game-candidate-3431b404 must be stopped",
            rescue_missing: "qa-old-rescue-20261107 .* is absent",
            rescue_restart: "differs from the manifest \\(restart, config_sha256\\)",
            rescue_exit: "must be stopped \\(exited, exit code 0\\)",
            rescue_config: "differs from the manifest \\(config_sha256\\)",
        }
        for change, message in cases.items():
            for where in ("post-build", "stop", "up"):
                with self.subTest(change.__name__, where=where):
                    self.setUp()
                    if where == "post-build":
                        change()
                        with self.assertRaisesRegex(RuntimeError, message):
                            self.post_build()
                        runs = 0
                    elif where == "stop":
                        path, digest = self.pre_stop()
                        change()
                        with self.assertRaisesRegex(RuntimeError, message):
                            self.new().exec_step(path, digest)
                        runs = 0
                    else:
                        bundle, digest = self.bundled()
                        change()
                        with self.assertRaisesRegex(RuntimeError, message):
                            self.new().exec_step(bundle, digest)
                        runs = 1
                    self.assertEqual(len(self.docker.runs), runs)

    def test_p2_3_up_needs_zero_writers_and_no_new_containers(self):
        def writer():
            self.docker.writers = 1

        def new_game():
            self.docker.containers["canary-core-qa-game-2"] = {
                **copy.deepcopy(self.docker.containers[GAME]),
                "name": "canary-core-qa-game-2",
                "id": "c" * 64,
            }

        for change, message in (
            (writer, "writers"),
            (new_game, "unexpected QA container|new game/brain containers"),
        ):
            with self.subTest(change.__name__):
                self.setUp()
                bundle, digest = self.bundled()
                change()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().exec_step(bundle, digest)
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

        def web_stopped(docker):
            docker.containers[WEB]["status"] = "exited"

        def db_unhealthy(docker):
            docker.containers[DATABASE]["health"] = "unhealthy"

        cases = {
            exit_code: "graceful save",
            created_at: "created_at changed",
            drift: "drifted after the save",
            web_stopped: f"{WEB}/status: baseline 'running' != now 'exited'",
            db_unhealthy: f"{DATABASE}/health: baseline 'healthy' != now 'unhealthy'",
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
                with self.assertRaisesRegex(
                    RuntimeError, f"HOLD(.|\n)*{re.escape(message)}"
                ):
                    self.new().post_stop(run)
                held = sorted((self.root / "evidence").glob("post-stop-*.json"))
                self.assertEqual(len(held), 1)
                self.assertEqual(self.receipt(held[0])["result"], "hold")
                with self.assertRaisesRegex(RuntimeError, "expected post-stop"):
                    self.new().bundle(held[0])

    def test_p2_5_post_stop_keeps_db_and_web_running_and_healthy_exactly(self):
        """P2 #5: only the game may move to exited; its stale health alone is left out."""
        run, _ = self.stopped()
        self.docker.containers[GAME]["health"] = (
            "unhealthy"  # stale after the stop: ignored
        )
        path, _ = self.new().post_stop(run)
        self.assertEqual(self.receipt(path)["result"], "pass")
        self.setUp()
        run, _ = self.stopped()
        self.docker.containers[WEB]["status"] = "exited"
        with self.assertRaisesRegex(
            RuntimeError, "HOLD(.|\n)*canary-core-qa-web-1/status"
        ):
            self.new().post_stop(run)

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

    def test_item_6_environment_values_are_compared_privately_per_key(self):
        """Item 6: live vs render VALUES per key, as sha256(KEY=VALUE); names alone are not enough."""
        bundle, _ = self.bundled()
        env = self.receipt(bundle)["environment_sha256"]
        self.assertEqual(env["game"]["different"], ["CANARY_BRAIN_CONFIG"])
        self.assertEqual(env["game"]["missing"], ["BOT_POPULATION_REFERENCE_BOTS"])
        self.assertEqual(
            env["database"]["render"]["MARIADB_PASSWORD"],
            sha(f"MARIADB_PASSWORD={SECRET}".encode()),
        )
        self.assertNotIn(SECRET, self.evidence_text())
        for service, name, key in (
            ("database", DATABASE, "MARIADB_USER"),
            ("web", WEB, "CANARY_SERVER_NAME"),
        ):
            with self.subTest(service):
                self.setUp()
                path, _ = self.post_stop()
                item = self.docker.containers[name]
                item["env"] = [
                    f"{key}=same-name-other-value" if e.startswith(key + "=") else e
                    for e in item["env"]
                ]
                with self.assertRaisesRegex(
                    RuntimeError, f"live {service} environment values differ"
                ) as refused:
                    self.new().bundle(path)
                self.assertNotIn("same-name-other-value", str(refused.exception))
                self.assertEqual(
                    list((self.root / "evidence").glob("bundle-*.json")), []
                )

    def test_item_7_a_live_bind_that_is_not_the_host_path_is_refused(self):
        """Item 7: each bind must name the render's host path (path, translated path or its hash)."""
        world = "/canary/data-otservbr-global/world/otservbr.otbm"

        def other_hash(item):
            for mount in item["mounts"]:
                if mount["Destination"] == world:
                    mount["Source"] = (
                        f"{handoff.DESKTOP_BINDS}/Ubuntu/{sha(b'/home/daniel/old-world.otbm')}"
                    )

        def translated(item):
            for mount in item["mounts"]:
                if mount["Destination"] == world:
                    host = str(self.project / "runtime/world/otservbr.otbm")
                    mount["Source"] = f"{handoff.DESKTOP_ROOT}/Ubuntu{host}"

        for ident in (CANDIDATE, RESCUE):
            with self.subTest(ident=ident[:12]):
                self.setUp()
                other_hash(self.docker.find(ident))
                with self.assertRaisesRegex(
                    RuntimeError, "is not the host path|differs from the manifest"
                ):
                    self.post_build()
        self.setUp()
        item = self.docker.containers[GAME]
        other_hash(item)
        self.manifest["containers"][GAME]["mounts"] = [
            {
                "destination": m["Destination"],
                "rw": m["RW"],
                "source": m["Source"],
                "type": m["Type"],
            }
            for m in item["mounts"]
        ]
        self.manifest_path.write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(
            RuntimeError, "game bind at .*otservbr.otbm is not the host path"
        ):
            self.post_build()
        self.setUp()
        translated(self.docker.containers[GAME])
        self.manifest["containers"][GAME]["mounts"] = [
            {
                "destination": m["Destination"],
                "rw": m["RW"],
                "source": m["Source"],
                "type": m["Type"],
            }
            for m in self.docker.containers[GAME]["mounts"]
        ]
        self.manifest_path.write_text(json.dumps(self.manifest))
        path, _ = self.post_build()
        forms = {(b["container"], b["form"]) for b in self.receipt(path)["binds"]}
        self.assertIn(("game", "desktop-path"), forms)
        self.assertIn(("database", "desktop-hash"), forms)

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
        for (
            edit,
            message,
        ) in cases.items():  # what bundle and the up precheck run on the live render
            with self.subTest(edit.__name__):
                render = copy.deepcopy(self.render_dict)
                edit(render)
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().validate_render(render)

    # -- fallback --------------------------------------------------------------------------------

    def failed_up(self):
        bundle, digest = self.bundled()
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
        verify, verify_sha = self.new().fallback_verify(stopped)
        self.assertEqual(
            self.receipt(verify)["step"]["argv"], ["docker", "start", RESCUE]
        )
        self.assertEqual(
            self.docker.find(RESCUE)["health"], "unhealthy"
        )  # stale, ignored
        self.new().exec_step(verify, verify_sha)
        self.assertEqual(self.docker.find(RESCUE)["status"], "running")
        self.assertEqual(self.docker.find(CANDIDATE)["status"], "exited")
        with self.assertRaisesRegex(RuntimeError, "already claimed"):
            self.new().exec_step(verify, verify_sha)
        self.assertEqual(self.docker.runs[-1], ["docker", "start", RESCUE])
        self.assertEqual(
            sum(run[:2] == ["docker", "start"] for run in self.docker.runs), 1
        )
        self.assertTrue(
            (self.project / handoff.CLAIMS / f"start-rescue.{RESCUE}.claim").is_file()
        )

    def test_a_started_fallback_counts_only_after_a_fresh_health_check(self):
        """The stale Health is ignored while stopped; after a start only a fresh check counts."""
        held = self.failed_up()
        plan, plan_sha = self.new().fallback_plan(held)
        stopped, _ = self.new().exec_step(plan, plan_sha)
        verify, verify_sha = self.new().fallback_verify(stopped)
        started, _ = self.new().exec_step(verify, verify_sha)
        rescue = self.docker.find(RESCUE)
        start = rescue["started_at"]
        for health, log in (
            ("starting", []),
            ("unhealthy", [{"End": start, "ExitCode": 1}]),
            (
                "healthy",
                [{"End": "2026-11-07T23:04:30.5Z", "ExitCode": 0}],
            ),  # before the start
        ):
            with self.subTest(health=health, log=log):
                rescue.update(health=health, health_log=log)
                with self.assertRaisesRegex(
                    RuntimeError, "HOLD(.|\n)*no fresh healthy check"
                ):
                    self.new().rescue_verify(started)
        fresh = (datetime.fromisoformat(start) + timedelta(seconds=20)).isoformat()
        rescue.update(health="healthy", health_log=[{"End": fresh, "ExitCode": 0}])
        path, _ = self.new().rescue_verify(started)
        self.assertEqual(self.receipt(path)["health"]["last_check_end"], fresh)
        # the same rule for the candidate, which this handoff never starts
        h = self.new()
        since = self.clock.now
        candidate = self.docker.find(CANDIDATE)
        with self.assertRaisesRegex(RuntimeError, "no fresh healthy check"):
            h.fresh_health(CANDIDATE, since)  # exited with a stale unhealthy
        candidate.update(
            status="running", started_at=since.isoformat(), health="unhealthy"
        )
        with self.assertRaisesRegex(RuntimeError, "no fresh healthy check"):
            h.fresh_health(CANDIDATE, since)
        candidate.update(
            health="healthy",
            health_log=[
                {"End": (since + timedelta(seconds=5)).isoformat(), "ExitCode": 0}
            ],
        )
        self.assertEqual(h.fresh_health(CANDIDATE, since)["health"], "healthy")

    def test_fallback_refuses_a_rescue_that_is_not_stopped_with_restart_no(self):
        held = self.failed_up()
        rescue = self.receipts["rescue_result"]
        for change, message in (
            ({"status": "running"}, "must be stopped"),
            ({"restart": "always"}, "differs from the manifest"),
            ({"exit_code": 1}, "must be stopped \\(exited, exit code 0\\)"),
        ):
            with self.subTest(change):
                saved = dict(self.docker.find(RESCUE))
                self.docker.find(RESCUE).update(change)
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().fallback_plan(held, RESCUE, rescue)
                self.docker.find(RESCUE).update(saved)
        with self.assertRaisesRegex(RuntimeError, "not the one the manifest"):
            self.new().fallback_plan(held, CANDIDATE, rescue)
        with self.assertRaisesRegex(RuntimeError, "not the one the manifest"):
            self.new().fallback_plan(held, RESCUE, self.receipts["brain_after"])
        self.docker.find(CANDIDATE)["status"] = "running"
        with self.assertRaisesRegex(RuntimeError, "not preserved and stopped"):
            self.new().fallback_plan(held, RESCUE, rescue)

    def test_fallback_needs_the_stop_first(self):
        path, _ = self.post_build()
        with self.assertRaisesRegex(RuntimeError, "expected post-stop"):
            self.new().fallback_plan(path, RESCUE, self.receipts["rescue_result"])


if __name__ == "__main__":
    unittest.main()
