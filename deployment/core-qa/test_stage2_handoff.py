"""Offline tests of the stage-2 handoff adapter. Docker, git and every mutation are mocked; nothing runs."""

import contextlib
import copy
import hashlib
import json
import os
import re
import stat
import subprocess
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
FAKE_SCRIPT = b"-- stand-in for bot_hibernation.lua at 3431b404\n"
GAME_STARTED = "2026-11-08T00:05:46.123456789Z"
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
        self.sessions = 0  # established on 17172, in /proc/net/tcp
        self.sessions6 = 0  # the same, in /proc/net/tcp6
        self.containers[GAME].update(started_at=GAME_STARTED, restart_count=0)
        self.script = FAKE_SCRIPT
        # anchor diagnostics as (seconds before the collection, anchors); None = no line
        self.anchors = [(40, 0), (22, 0), (4, 0)]
        self.logs = None  # raw text instead of the generated lines
        self.tail = []  # (seconds before, message): lines after the generated ones
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
        if args[1] == "exec" and args[3] == "cat" and args[4] in handoff.TCP_FILES:
            if self.find(args[2])["status"] != "running":
                raise RuntimeError("read-only command failed: docker exec")
            count = self.sessions if args[4] == "/proc/net/tcp" else self.sessions6
            lines = [TCP_HEADER, TCP_LISTEN, TCP_DB, *[TCP_PLAYER] * count]
            return "\n".join(lines) + "\n"
        if args[1] == "inspect" and fmt == handoff.GAME_START:
            item = self.find(args[2])
            if not item:
                raise RuntimeError("read-only command failed: docker inspect")
            return json.dumps(
                {
                    "id": item["id"],
                    "image_id": item["image_id"],
                    "status": item["status"],
                    "started_at": item.get("started_at"),
                    "restart_count": item.get("restart_count", 0),
                }
            )
        return super().__call__(*args, env=env)

    def stamp(self, seconds_before):
        when = self.clock.now - timedelta(seconds=seconds_before)
        return when.strftime("%Y-%m-%dT%H:%M:%S.%f") + "123Z"

    def collect(self, argv, timeout=handoff.LOG_TIMEOUT):
        """The mocked read-only captures with a timeout: the script bytes and the game logs."""
        item = self.find(argv[-1] if argv[1] == "logs" else argv[2])
        if not item or item["status"] != "running":
            raise RuntimeError("read-only command failed: docker; refused")
        if argv[1] == "exec":
            assert argv[3:] == ["cat", handoff.HIBERNATION_SCRIPT]
            return self.script
        assert argv[:5] == ["docker", "logs", "--timestamps", "--since", "120s"]
        if self.logs is not None:
            return self.logs.encode()
        lines = []
        for seconds, anchors in self.anchors:
            stamp = self.stamp(seconds)
            lines.append(
                f"{stamp} [2026-08-11 02:00:00.000] [info] [BotHibernation] tick #60 firing "
            )
            lines.append(
                f"{stamp} [2026-08-11 02:00:00.000] [info] [BotHibernation] 40 bots: "
                f"hibernated=33 awake=7, {anchors} real players "
            )
            lines.append(
                f"{stamp} [2026-08-11 02:00:00.001] [info] [PROXIMITY] near=0 "
            )
        for seconds, message in self.tail:
            lines.append(
                f"{self.stamp(seconds)} [2026-08-11 02:00:00.002] [info] {message}"
            )
        return ("\n".join(lines) + "\n").encode()

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
        self.mono = [100.0]
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for mock in (
            patch("preflight.command", side_effect=self.docker),
            patch("stage1_baseline.db_slice", side_effect=self.slice),
            patch("stage2_handoff.git_blob", return_value=ADAPTER),
            patch("stage2_handoff.execute", side_effect=self.docker.run),
            patch("stage2_handoff.utcnow", side_effect=self.clock),
            patch("stage2_handoff.collect", side_effect=self.docker.collect),
            patch("stage2_handoff.monotonic", side_effect=self.monotonic),
            patch("stage2_handoff.HIBERNATION_SHA256", sha(FAKE_SCRIPT)),
        ):
            self.stack.enter_context(mock)
        self.slice_now = copy.deepcopy(gate.comparable(self.baseline)["db_slice"])

    def monotonic(self):
        self.mono[0] += 0.01
        return self.mono[0]

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

    def attest(self, h, path, notice_sha=None):
        return h.pre_stop(
            path,
            "Daniel",
            self.clock.now.isoformat(),
            self.notice,
            notice_sha or sha(self.notice.read_bytes()),
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
        people = receipt["human_absence"]
        self.assertEqual(people["window_notice"]["sha256"], notice)
        self.assertEqual(people["sql_corroboration"]["online_rows"], 2)
        self.assertEqual(people["sql_corroboration"]["qa_humans_online"], 0)
        self.assertEqual(people["game_port_sessions"], {"tcp": 0, "tcp6": 0})

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
            qa_human: "known QA human",
            god: "known QA human",
            orphan: "known QA human",
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

    def test_hibernation_pin_is_the_3431_bytes(self):
        found = subprocess.run(
            [
                "git",
                "-C",
                str(REPO),
                "cat-file",
                "blob",
                f"{handoff.GAME_REVISION}:data/scripts/globalevents/bot_hibernation.lua",
            ],
            capture_output=True,
            check=False,
        )
        if found.returncode:
            self.skipTest("revision 3431b404 is not in this clone")
        self.assertEqual(
            sha(found.stdout),
            "b2496d782f27b31b4f027ddae2b5b26704c2fc379e66501610a665687f92bf01",
        )
        text = found.stdout.decode()
        self.assertIn(
            "if (not p:isBotPlayer()) or (p:getCastViewerCount() > 0) then", text
        )
        self.assertIn(
            'logger.info(string.format("[BotHibernation] %d bots: hibernated=%d awake=%d, '
            '%d real players",',
            text,
        )

    def test_human_absence_legitimate_control_passes(self):
        """A fresh zero, empty TCP and the QA humans offline: the stop is sealed and runs."""
        path, digest = self.pre_stop()
        people = self.receipt(path)["human_absence"]
        self.assertTrue(people["native_roster_unavailable"])
        self.assertEqual(people["native_anchors"], 0)
        self.assertNotIn("bot_only", json.dumps(people))
        self.assertTrue(people["sql_corroboration"]["potentially_stale"])
        self.assertEqual(people["game"]["id"], self.docker.containers[GAME]["id"])
        self.assertEqual(people["game"]["started_at"], GAME_STARTED)
        self.assertEqual(people["game"]["source_revision"], handoff.GAME_REVISION)
        self.assertEqual(people["script"]["sha256"], sha(FAKE_SCRIPT))
        logs = people["logs"]
        self.assertEqual(logs["sha256"], sha(logs["raw"].encode()))
        self.assertLessEqual(
            logs["wall_clock_utc"]["start"], logs["wall_clock_utc"]["end"]
        )
        self.assertLess(
            logs["monotonic_seconds"]["start"], logs["monotonic_seconds"]["end"]
        )
        self.assertRegex(
            people["last_anchor_diagnostic"]["line"], r", 0 real players ?$"
        )
        self.assertIn("not an independent clock", " ".join(people["limitations"]))
        run, _ = self.new().exec_step(path, digest)
        refreshed = self.receipt(run)["refreshed_human_absence"]
        self.assertNotEqual(refreshed["logs"]["wall_clock_utc"], logs["wall_clock_utc"])
        self.assertEqual(len(self.docker.runs), 1)

    def test_human_absence_refusals(self):
        """One refusal per case, at pre-stop; nothing is sealed."""
        path, _ = self.post_build()

        def old_zero_then_nonzero():
            self.docker.anchors = [(25, 0), (4, 1)]

        def absent():
            self.docker.anchors = []

        def malformed():
            self.docker.logs = (
                f"{self.docker.stamp(4)} [2026-08-11 02:00:00.000] [info] "
                "[BotHibernation] 40 bots: hibernated=33, 0 real players \n"
            )

        def future():
            self.docker.anchors = [(10, 0), (-20, 0)]

        def stale():
            self.docker.anchors = [(35, 0)]

        def before_started_at():
            # StartedAt after the last diagnostic (later than the collection's own clock)
            self.docker.containers[GAME]["started_at"] = self.docker.stamp(-60)

        def script_hash():
            self.docker.script = FAKE_SCRIPT + b"-- edited\n"

        def tcp():
            self.docker.sessions = 1

        def tcp6():
            self.docker.sessions6 = 1

        def qa_human():
            self.docker.roster.append("online\t66102\t65003")

        cases = {
            old_zero_then_nonzero: "shows 1 anchor",
            absent: "no anchor diagnostic",
            malformed: "malformed",
            future: "dated in the future",
            stale: "older than 30 s",
            before_started_at: "not after the game's StartedAt",
            script_hash: "not the 3431b404 bytes",
            tcp: "TCP session.*'tcp': 1",
            tcp6: "TCP session.*'tcp6': 1",
            qa_human: "known QA human",
        }
        for change, message in cases.items():
            with self.subTest(change.__name__):
                saved = copy.deepcopy(
                    (
                        self.docker.anchors,
                        self.docker.logs,
                        self.docker.script,
                        self.docker.sessions,
                        self.docker.sessions6,
                        self.docker.roster,
                        self.docker.containers[GAME],
                    )
                )
                change()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.attest(self.new(), path)
                (
                    self.docker.anchors,
                    self.docker.logs,
                    self.docker.script,
                    self.docker.sessions,
                    self.docker.sessions6,
                    self.docker.roster,
                    self.docker.containers[GAME],
                ) = saved
        self.assertEqual(list((self.root / "evidence").glob("pre-stop-*.json")), [])

    def test_human_absence_is_refreshed_at_the_stop(self):
        """Inside exec-step: logs, SQL, tcp/tcp6, StartedAt and the notice again; no mutation."""

        def nonzero_now():
            self.docker.anchors = [(30, 0), (3, 2)]

        def stale_now():
            self.docker.anchors = [(45, 0)]

        def restarted():
            self.docker.containers[GAME]["started_at"] = self.docker.stamp(60)
            self.docker.containers[GAME]["restart_count"] = 1

        def restart_during_collection():
            original = self.docker.collect

            def collect(argv, timeout=handoff.LOG_TIMEOUT):
                out = original(argv, timeout)
                if argv[1] == "logs":
                    self.docker.containers[GAME]["started_at"] = self.docker.stamp(0)
                return out

            self.stack.enter_context(
                patch("stage2_handoff.collect", side_effect=collect)
            )

        def script_now():
            self.docker.script = b"-- other\n"

        def tcp_now():
            self.docker.sessions = 1

        def tcp6_now():
            self.docker.sessions6 = 2

        def qa_human_now():
            self.docker.roster.append("online\t66100\t65001")

        def notice_now():
            self.notice.write_text("window cancelled\n")

        cases = {
            nonzero_now: "shows 2 anchor",
            stale_now: "older than 30 s",
            restarted: "StartedAt changed",
            restart_during_collection: "StartedAt changed",
            script_now: "not the 3431b404 bytes",
            tcp_now: "'tcp': 1",
            tcp6_now: "'tcp6': 2",
            qa_human_now: "known QA human",
            notice_now: "window notice",
        }
        for change, message in cases.items():
            with self.subTest(change.__name__):
                self.setUp()
                path, digest = self.pre_stop()
                change()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().exec_step(path, digest)
                self.assertEqual(self.docker.runs, [])
                self.assertEqual(
                    list((self.project / handoff.CLAIMS).glob("*"))
                    if (self.project / handoff.CLAIMS).exists()
                    else [],
                    [],
                )

    def test_parser_p2_last_bothibernation_line_is_parsed_strictly(self):
        """Every [BotHibernation] line is a candidate; only the allowlisted tick is skipped."""
        singular = "[BotHibernation] 40 bots: hibernated=0 awake=40, 1 real player"
        truncated = "[BotHibernation] 40 bots: hibernated=0 awake=40, 1"
        unknown = "[BotHibernation] getBotHibernationStates returned nil"
        tick = "[BotHibernation] tick #120 firing "
        refusals = {
            "singular": ([(10, 0)], [(2, singular)], "malformed or unknown"),
            "truncated": ([(10, 0)], [(2, truncated)], "malformed or unknown"),
            "unknown": ([(10, 0)], [(2, unknown)], "malformed or unknown"),
            "tick_after_a_stale_zero": ([(35, 0)], [(2, tick)], "older than 30 s"),
        }
        path, _ = self.post_build()
        for name, (anchors, tail, message) in refusals.items():
            with self.subTest(f"pre-stop {name}"):
                self.docker.anchors, self.docker.tail = anchors, tail
                with self.assertRaisesRegex(RuntimeError, message):
                    self.attest(self.new(), path)
        self.assertEqual(list((self.root / "evidence").glob("pre-stop-*.json")), [])
        for name, (anchors, tail, message) in refusals.items():
            with self.subTest(f"stop {name}"):
                self.setUp()
                stop, digest = self.pre_stop()
                self.docker.anchors, self.docker.tail = anchors, tail
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().exec_step(stop, digest)
                self.assertEqual(self.docker.runs, [])  # no mutation
        with self.subTest("benign tick after a fresh zero passes"):
            self.setUp()
            self.docker.anchors, self.docker.tail = [(10, 0)], [(2, tick)]
            stop, digest = self.pre_stop()
            last = self.receipt(stop)["human_absence"]["last_anchor_diagnostic"]
            self.assertRegex(last["line"], r", 0 real players ?$")
            self.new().exec_step(stop, digest)
            self.assertEqual(len(self.docker.runs), 1)

    def test_privacy_raw_log_is_private_and_bound_to_the_sanitized_copy(self):
        """0600 files in a 0700 directory; the raw is kept; the sanitized copy names its sha256."""
        path, _ = self.pre_stop()
        evidence = self.root / "evidence"
        self.assertEqual(stat.S_IMODE(evidence.stat().st_mode), 0o700)
        files = list(evidence.iterdir())
        self.assertTrue(files)
        for item in files:
            with self.subTest(item.name):
                self.assertEqual(stat.S_IMODE(item.lstat().st_mode), 0o600)
        logs = self.receipt(path)["human_absence"]["logs"]
        self.assertIn(
            "[PROXIMITY]", logs["raw"]
        )  # kept, not replaced by the extracted lines
        raw = Path(logs["raw_file"]["path"])
        self.assertEqual(raw.parent, evidence)
        self.assertEqual(raw.read_bytes(), logs["raw"].encode())
        self.assertEqual(sha(raw.read_bytes()), logs["sha256"])
        self.assertEqual(logs["raw_file"]["sha256"], logs["sha256"])
        sanitized_path = Path(logs["sanitized_file"]["path"])
        self.assertEqual(
            sha(sanitized_path.read_bytes()), logs["sanitized_file"]["sha256"]
        )
        sanitized = json.loads(sanitized_path.read_text())
        self.assertEqual(sanitized["raw_sha256"], logs["sha256"])
        self.assertEqual(logs["sanitized_file"]["raw_sha256"], logs["sha256"])
        self.assertEqual(sanitized["raw_file"], raw.name)
        self.assertTrue(sanitized["lines"])
        self.assertTrue(all("[BotHibernation]" in line for line in sanitized["lines"]))
        self.assertNotIn("[PROXIMITY]", sanitized_path.read_text())

    def test_privacy_unsafe_paths_are_refused_and_never_repaired(self):
        base = self.root / "unsafe"
        base.mkdir(mode=0o700)

        def directory(mode):
            def case():
                target = base / f"dir-{mode:o}"
                target.mkdir()
                target.chmod(mode)
                return target, target / "receipt.json", mode

            return case

        def file_readable():
            target = base / "private"
            target.mkdir(mode=0o700)
            existing = target / "receipt.json"
            existing.write_text("{}")
            existing.chmod(0o640)
            return existing, existing, 0o640

        def symlinked_component():
            real = base / "real"
            real.mkdir(mode=0o700)
            (base / "link").symlink_to(real)
            return real, base / "link" / "evidence" / "receipt.json", 0o700

        def symlink_target():
            target = base / "private2"
            target.mkdir(mode=0o700)
            (target / "receipt.json").symlink_to(self.root / "elsewhere.json")
            return target, target / "receipt.json", 0o700

        def not_owned():
            target = base / "theirs"
            target.mkdir(mode=0o700)
            return target, target / "receipt.json", 0o700

        cases = {
            "group_readable_directory": (
                directory(0o750),
                "group- or world-accessible",
            ),
            "world_writable_directory": (
                directory(0o702),
                "group- or world-accessible",
            ),
            "group_writable_directory": (
                directory(0o720),
                "group- or world-accessible",
            ),
            "group_readable_file": (file_readable, "exists and is group- or world"),
            "symlinked_component": (symlinked_component, "symlinked path component"),
            "symlink_target": (symlink_target, "symlink target"),
            "not_owned_directory": (not_owned, "not owned by the current user"),
        }
        for name, (make, message) in cases.items():
            with self.subTest(name):
                checked, target, mode = make()
                uid = os.getuid() + 1 if name == "not_owned_directory" else os.getuid()
                with (
                    patch("stage2_handoff.os.getuid", return_value=uid),
                    self.assertRaisesRegex(RuntimeError, message),
                ):
                    handoff.write_private(target, b"raw game log")
                self.assertEqual(stat.S_IMODE(checked.lstat().st_mode), mode)
        self.assertFalse((self.root / "elsewhere.json").exists())
        with self.subTest("an --evidence through a symlink refuses the receipt"):
            real = self.root / "real-evidence"
            real.mkdir(mode=0o700)
            (self.root / "evidence-link").symlink_to(real)
            receipts = {key: self.receipts[key] for key in handoff.RECEIPT_KEYS}
            linked = self.new(evidence=self.root / "evidence-link" / "inner")
            with self.assertRaisesRegex(RuntimeError, "symlinked path component"):
                linked.post_build(receipts, self.render_path)
            self.assertEqual(list(real.iterdir()), [])
        with self.subTest("an existing open evidence directory refuses the receipt"):
            (self.root / "evidence").mkdir(mode=0o755)
            (self.root / "evidence").chmod(0o755)
            with self.assertRaisesRegex(RuntimeError, "group- or world-accessible"):
                self.post_build()
            self.assertEqual(list((self.root / "evidence").iterdir()), [])
            self.assertEqual(
                stat.S_IMODE((self.root / "evidence").stat().st_mode), 0o755
            )

    def test_stop_deadline_expired_refuses_without_mutation(self):
        """5 monotonic seconds from the final session check to the stop, checked twice."""
        path, digest = self.pre_stop()
        original = handoff.Handoff.precheck

        def slow_precheck(h, receipt, argv):
            original(h, receipt, argv)
            self.mono[0] += handoff.STOP_DEADLINE + 0.5

        with (
            patch.object(handoff.Handoff, "precheck", slow_precheck),
            self.assertRaisesRegex(RuntimeError, "missed its 5 s deadline"),
        ):
            self.new().exec_step(path, digest)
        self.assertEqual(self.docker.runs, [])
        claims = self.project / handoff.CLAIMS
        self.assertFalse(claims.exists() and any(claims.iterdir()))  # nothing claimed
        original_claim = handoff.Handoff.claim

        def slow_claim(h, claim, body):  # the claim itself overruns the deadline
            original_claim(h, claim, body)
            self.mono[0] += handoff.STOP_DEADLINE + 0.5

        with (
            patch.object(handoff.Handoff, "claim", slow_claim),
            self.assertRaisesRegex(RuntimeError, "missed its 5 s deadline"),
        ):
            self.new().exec_step(path, digest)
        self.assertEqual(self.docker.runs, [])
        result = claims / f"{digest}.stop-game.result"
        self.assertEqual(
            json.loads(result.read_text()),
            {"executed": False, "reason": "stop deadline expired"},
        )
        with self.assertRaisesRegex(RuntimeError, "already claimed"):
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
            qa_human: "known QA human",
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
