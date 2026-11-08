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

REAL_COLLECT = handoff.collect  # the real bounded capture, before setUp patches it

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
ROOT_SECRET = (
    "fake-root-not-a-secret"  # the DB container's MARIADB_ROOT_PASSWORD stand-in
)
VISIBILITY = FIXTURES / "qa-db-process-visibility-20261108.json"  # Pitagoras, read-only
OWN = 24187  # the probe's own CONNECTION_ID in the fake DB
FAKE_MAP = (
    b"stand-in for otservbr.otbm v3.4.1\n"  # its sha256 replaces prepare.MAP_SHA256
)
IPS = {DATABASE: "172.22.0.2", "canary-core-qa-game-1": "172.22.0.3", WEB: "172.22.0.4"}
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
    render["services"]["database"]["environment"]["MARIADB_ROOT_PASSWORD"] = ROOT_SECRET


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
        self.writers = 0  # foreign canary Sleep sessions from the game IP
        self.probe = {
            "account": "root@localhost",
            "process": "1",
            "error": False,
            "drop": None,
            "end_connection": OWN,
            "rows": [],
            "trx": [],
            "own": True,
        }
        self.calls = []
        self.probe_timeouts = []
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

    def probe_output(self, args):
        """The fake root probe: one session, the statements in order, TSV like mariadb -N -B."""
        db = self.containers[DATABASE]["id"]
        assert args[2:6] == (db, "sh", "-c", handoff.DB_PROBE_SCRIPT), args[:6]
        probe = self.probe
        if probe["error"]:
            raise RuntimeError("read-only command failed: docker exec")
        sessions = [
            ["1", "system user", "", "", "Daemon", "-1", "InnoDB purge coordinator"],
            *[
                [
                    str(24116 + i),
                    "canary",
                    f"172.22.0.3:{56590 + i}",
                    "canary",
                    "Sleep",
                    "3",
                    "",
                ]
                for i in range(self.writers)
            ],
            *probe["rows"],
        ]
        if probe["own"]:
            user = probe["account"].split("@")[0]
            sessions.append(
                [str(OWN), user, "localhost", "", "Query", "0", "Filling schema table"]
            )
        rows = [
            ["begin", str(OWN), probe["account"], "2026-11-08 02:00:00.000001"],
            ["privilege", "PROCESS", probe["process"]],
            *[["process", *row] for row in sorted(sessions, key=lambda r: int(r[0]))],
            *[["trx", *row] for row in probe["trx"]],
            ["end", str(probe["end_connection"]), "2026-11-08 02:00:00.000900"],
        ]
        rows = [row for row in rows if row[0] != probe["drop"]]
        return "".join("\t".join(row) + "\n" for row in rows)

    def __call__(self, *args, env=None):
        self.calls.append(args)
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
        if args[1] == "exec" and args[-1] == handoff.DB_PROBE_SQL:
            return self.probe_output(args)
        if args[1] == "inspect" and fmt == handoff.NETWORK_PROBE:
            item = self.find(args[2])
            if not item:
                raise RuntimeError("read-only command failed: docker inspect")
            # even a stopped container's last IP is returned: the adapter must ignore it
            ips = [IPS.get(item["name"], "172.22.0.9"), ""]
            return json.dumps(
                {
                    "id": item["id"],
                    "name": "/" + item["name"],
                    "status": item["status"],
                    "ips": ips,
                }
            )
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
        """The mocked read-only captures with a timeout: the script bytes, the game logs, the DB probe."""
        if argv[-1] == handoff.DB_PROBE_SQL:
            self.calls.append(tuple(argv))
            self.probe_timeouts.append(timeout)
            return self.probe_output(tuple(argv)).encode()
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
            patch("preflight.MAP_SHA256", sha(FAKE_MAP)),
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
        self.map_file = self.project / handoff.MAP_FILE
        self.map_file.parent.mkdir(parents=True, exist_ok=True)
        self.map_file.write_bytes(FAKE_MAP)
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
                    "map_sha256": sha(FAKE_MAP),
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


class QuiescentTests(HandoffTests):
    """The quiescent chain, on the real code paths (exec-step, bundle, up_gate). Docker is mocked."""

    def setUp(self):
        super().setUp()
        self.slice_now["counts"]["player_items"] = 2616  # the moved slice of the smoke
        self.notice_json(-60, 1700)

    def notice_json(self, start, end):
        now = self.clock.now
        body = {
            "window_start_utc": (now + timedelta(seconds=start)).isoformat(),
            "window_end_utc": (now + timedelta(seconds=end)).isoformat(),
            "text": "QA quiescent window; no players",
        }
        self.notice.write_text(json.dumps(body) + "\n")
        return body

    def q_post_build(self):
        receipts = {key: self.receipts[key] for key in handoff.RECEIPT_KEYS}
        return self.new().post_build(receipts, self.render_path, quiescent=True)

    def q_attest(self, path, notice_sha=None):
        return self.new().quiescent_pre_stop(
            path,
            "Daniel",
            self.clock.now.isoformat(),
            self.notice,
            notice_sha or sha(self.notice.read_bytes()),
        )

    def q_pre_stop(self):
        return self.q_attest(self.q_post_build()[0])

    def q_stopped(self):
        return self.new().exec_step(*self.q_pre_stop())

    def q_slice(self):
        return self.new().quiescent_slice(self.q_stopped()[0])

    def approval(self, q_path, q_sha, edit=None, name="approval.json"):
        receipt = self.receipt(q_path)
        body = {
            "schema": handoff.APPROVAL_SCHEMA,
            "reviewer": "Socrates",
            "approved_at_utc": self.clock.now.isoformat(),
            "quiescent_receipt_sha256": q_sha,
            "stop_exec_step": {
                "receipt_sha256": receipt["stop_exec_step"]["sha256"],
                "claim": receipt["stop_exec_step"]["claim"],
            },
            "window": {
                key: receipt["window"][key]
                for key in ("notice_sha256", "start_utc", "end_utc")
            },
            "db_slice": receipt["db_slice"],
            "audit": {
                "auditor": "Aristoteles",
                "audited_at_utc": self.clock.now.isoformat(),
                "explanation": "player_items 2613 -> 2616: bot loot saved before the stop",
            },
        }
        if edit:
            edit(body)
        path = self.root / name
        path.write_text(json.dumps(body, indent=2) + "\n")
        return path, sha(path.read_bytes())

    def q_bundled(self):
        q_path, q_sha = self.q_slice()
        approval, approval_sha = self.approval(q_path, q_sha)
        bundle = self.new().quiescent_bundle(q_path, q_sha, approval, approval_sha)
        return bundle, (q_path, q_sha, approval, approval_sha)

    def ups(self):
        return sum("up" in argv for argv in self.docker.runs)

    def test_quiescent_legitimate_control_activates_once(self):
        (bundle, digest), (q_path, q_sha, _a, _s) = self.q_bundled()
        q = self.receipt(q_path)
        self.assertEqual(q["phase"], "quiescent-slice")
        self.assertEqual(q["result"], "pass")
        self.assertEqual(
            q["db_slice"],
            {
                **self.slice_now,
                "method": gate.DB_SLICE_METHOD,
                "sql_sha256": gate.DB_SLICE_SQL_SHA256,
            },
        )
        self.assertEqual(q["supersedes_db_slice"]["counts"]["player_items"], 2613)
        self.assertFalse(q["historical_slice_equal"])
        self.assertEqual(q["db_writers"]["other_sessions"], 0)
        self.assertEqual(q["db_writers"]["transactions"], 0)
        self.assertTrue(q["corroboration"]["equal"])
        self.assertEqual(q["baseline_sha256"], gate.BASELINE_SHA256)
        self.assertEqual(q["game_start"]["started_at"], GAME_STARTED)
        pre = self.receipt(
            Path(self.receipt(Path(q["previous"]["path"]))["previous"]["path"])
        )
        self.assertEqual(pre["phase"], "quiescent-pre-stop")
        self.assertEqual(pre["step"]["name"], "quiescent-stop-game")
        self.assertIn("never an up", pre["authorizes"])
        self.assertIn("db_slice_waived", pre["stage1"])
        self.assertEqual(self.receipt(bundle)["step"]["name"], "quiescent-up")
        self.new().exec_step(bundle, digest)
        self.assertEqual(self.ups(), 1)
        claims = self.project / handoff.CLAIMS
        self.assertTrue((claims / f"{q_sha}.activate.claim").is_file())
        self.assertTrue((claims / f"{q_sha}.activate.result").is_file())

    def test_quiescent_mode_never_releases_up_without_approval(self):
        q_path, q_sha = self.q_slice()
        self.assertEqual(
            self.docker.runs, [[*handoff.STOP, self.docker.containers[GAME]["id"]]]
        )
        with self.assertRaisesRegex(RuntimeError, "quiescent chain; this normal phase"):
            self.new().bundle(q_path)
        with self.assertRaisesRegex(RuntimeError, "expected pre-stop/bundle"):
            self.new().exec_step(q_path, q_sha)  # the receipt itself seals nothing
        absent = self.root / "no-approval.json"
        with self.assertRaisesRegex(RuntimeError, "approval is absent"):
            self.new().quiescent_bundle(
                q_path, q_sha, absent, q_sha
            )  # the CLI sha alone
        approval, approval_sha = self.approval(q_path, q_sha)
        with self.assertRaisesRegex(RuntimeError, "not the given sha256"):
            self.new().quiescent_bundle(q_path, q_sha, approval, "0" * 64)
        with self.assertRaisesRegex(RuntimeError, "tampered or not the one given"):
            self.new().quiescent_bundle(q_path, "0" * 64, approval, approval_sha)
        wrong, wrong_sha = self.approval(
            q_path, q_sha, lambda b: b.update(schema="other"), "wrong-schema.json"
        )
        with self.assertRaisesRegex(RuntimeError, "not a quiescent approval"):
            self.new().quiescent_bundle(q_path, q_sha, wrong, wrong_sha)
        self.assertEqual(self.ups(), 0)
        self.assertEqual(
            list((self.root / "evidence").glob("quiescent-bundle-*.json")), []
        )

    def test_quiescent_divergent_slice_or_projection_refuses(self):
        def field(key):
            def change():
                self.slice_now["counts"][key] += 1

            change.__name__ = f"count_{key}"
            return change

        def projection():
            self.slice_now["qa_character_projection_sha256"] = "f" * 64

        def method():
            self.local.enter_context(
                patch("stage1_baseline.DB_SLICE_METHOD", "other-v2")
            )

        def query():
            self.local.enter_context(
                patch("stage1_baseline.DB_SLICE_SQL_SHA256", "e" * 64)
            )

        changes = [
            *(field(key) for key in gate.DB_COUNT_KEYS),
            projection,
            method,
            query,
        ]
        for change in changes:
            with (
                self.subTest(f"at the bundle: {change.__name__}"),
                contextlib.ExitStack() as self.local,
            ):
                self.setUp()
                q_path, q_sha = self.q_slice()
                approval, approval_sha = self.approval(q_path, q_sha)
                change()
                with self.assertRaisesRegex(
                    RuntimeError, "drifted since the stop|slice method"
                ):
                    self.new().quiescent_bundle(q_path, q_sha, approval, approval_sha)
            with (
                self.subTest(f"right before the up: {change.__name__}"),
                contextlib.ExitStack() as self.local,
            ):
                self.setUp()
                (bundle, digest), _refs = self.q_bundled()
                change()
                with self.assertRaisesRegex(
                    RuntimeError, "drifted since the stop|slice method"
                ):
                    self.new().exec_step(bundle, digest)
                self.assertEqual(self.ups(), 0)
        with self.subTest("two reads differ: HOLD, never approvable"):
            self.setUp()
            stopped, _ = self.q_stopped()
            reads = iter([0, 1])
            self.stack.enter_context(
                patch(
                    "stage1_baseline.db_slice",
                    side_effect=lambda: {
                        **copy.deepcopy(self.slice_now),
                        "qa_character_projection_sha256": str(next(reads)) * 64,
                    },
                )
            )
            with self.assertRaisesRegex(
                RuntimeError, "two reads of the DB slice differ"
            ):
                self.new().quiescent_slice(stopped)
            held = min((self.root / "evidence").glob("quiescent-slice-*.json"))
            self.assertEqual(self.receipt(held)["result"], "hold")
            approval, approval_sha = self.approval(held, sha(held.read_bytes()))
            with self.assertRaisesRegex(RuntimeError, "quiescent-slice/hold"):
                self.new().quiescent_bundle(
                    held, sha(held.read_bytes()), approval, approval_sha
                )

    def test_quiescent_approval_for_another_receipt_stop_or_window_refuses(self):
        q_path, q_sha = self.q_slice()
        cases = {
            "other_receipt": (
                lambda b: b.update(quiescent_receipt_sha256="1" * 64),
                "another quiescent receipt",
            ),
            "other_stop": (
                lambda b: b["stop_exec_step"].update(receipt_sha256="2" * 64),
                "another stop exec-step",
            ),
            "other_claim": (
                lambda b: b["stop_exec_step"].update(claim="/tmp/other.claim"),
                "another stop exec-step",
            ),
            "other_notice": (
                lambda b: b["window"].update(notice_sha256="3" * 64),
                "another window",
            ),
            "other_start": (
                lambda b: b["window"].update(start_utc="2026-11-08T01:00:00+00:00"),
                "another window",
            ),
            "other_end": (
                lambda b: b["window"].update(end_utc="2026-11-08T09:00:00+00:00"),
                "another window",
            ),
            "other_slice": (
                lambda b: b["db_slice"]["counts"].update(player_items=2613),
                "exact full slice",
            ),
            "no_reviewer": (lambda b: b.update(reviewer=" "), "needs a reviewer"),
            "no_auditor": (lambda b: b["audit"].pop("auditor"), "needs a reviewer"),
            "before_the_receipt": (
                lambda b: b.update(approved_at_utc="2026-11-08T00:00:00+00:00"),
                "approval time",
            ),
            "in_the_future": (
                lambda b: b.update(approved_at_utc="2026-11-08T05:00:00+00:00"),
                "approval time",
            ),
            "not_utc": (
                lambda b: b.update(approved_at_utc="2026-11-08T02:30:00"),
                "approval time",
            ),
        }
        for name, (edit, message) in cases.items():
            with self.subTest(name):
                approval, approval_sha = self.approval(
                    q_path, q_sha, edit, f"{name}.json"
                )
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().quiescent_bundle(q_path, q_sha, approval, approval_sha)
        with self.subTest("an approval of another quiescent receipt"):
            other = self.root / "other-q.json"
            other.write_bytes(q_path.read_bytes())
            approval, approval_sha = self.approval(
                q_path, q_sha, lambda b: b.update(quiescent_receipt_sha256=sha(b"x"))
            )
            with self.assertRaisesRegex(RuntimeError, "another quiescent receipt"):
                self.new().quiescent_bundle(q_path, q_sha, approval, approval_sha)
        with self.subTest("the stop claim has no result naming the exec-step"):
            claim = Path(self.receipt(q_path)["stop_exec_step"]["claim"])
            result = claim.with_suffix(".result")
            saved = result.read_bytes()
            result.write_text(json.dumps({"sha256": "4" * 64, "exit_code": 0}))
            approval, approval_sha = self.approval(q_path, q_sha, name="claim.json")
            with self.assertRaisesRegex(RuntimeError, "stop claim has no result"):
                self.new().quiescent_bundle(q_path, q_sha, approval, approval_sha)
            result.write_bytes(saved)
        with self.subTest("the approval file changed after the bundle"):
            approval, approval_sha = self.approval(q_path, q_sha, name="final.json")
            bundle, digest = self.new().quiescent_bundle(
                q_path, q_sha, approval, approval_sha
            )
            approval.write_text(approval.read_text().replace("Socrates", "Someone"))
            with self.assertRaisesRegex(RuntimeError, "not the given sha256"):
                self.new().exec_step(bundle, digest)
        self.assertEqual(self.ups(), 0)

    def test_quiescent_restart_or_expiry_voids_receipt_and_pending_approval(self):
        def restarted():  # started and stopped again: StartedAt moved
            self.docker.containers[GAME]["started_at"] = "2026-11-08T02:30:00.1Z"

        def restart_count():
            self.docker.containers[GAME]["restart_count"] = 1

        def running():
            self.docker.containers[GAME]["status"] = "running"

        def expired():
            self.clock.now += timedelta(hours=3)

        cases = {
            restarted: "started again|ended",
            restart_count: "started again",
            running: "started again|running again|differs",
            expired: "QA window ended|stale",
        }
        for change, message in cases.items():
            with self.subTest(f"pending approval, at the bundle: {change.__name__}"):
                self.setUp()
                q_path, q_sha = self.q_slice()
                approval, approval_sha = self.approval(q_path, q_sha)
                change()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().quiescent_bundle(q_path, q_sha, approval, approval_sha)
            with self.subTest(f"approved, right before the up: {change.__name__}"):
                self.setUp()
                (bundle, digest), _refs = self.q_bundled()
                change()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().exec_step(bundle, digest)
                self.assertEqual(self.ups(), 0)
        with self.subTest("expiry at the quiescent receipt: HOLD"):
            self.setUp()
            stopped, _ = self.q_stopped()
            self.clock.now += timedelta(hours=3)
            with self.assertRaisesRegex(RuntimeError, "QA window ended"):
                self.new().quiescent_slice(stopped)
        with self.subTest("expiry after the claim: consumed, not executed"):
            self.setUp()
            (bundle, digest), (_q, q_sha, _a, _s) = self.q_bundled()
            original = handoff.Handoff.claim

            def slow_claim(h, claim, body):
                original(h, claim, body)
                self.clock.now += timedelta(hours=3)

            with (
                patch.object(handoff.Handoff, "claim", slow_claim),
                self.assertRaisesRegex(RuntimeError, "QA window ended"),
            ):
                self.new().exec_step(bundle, digest)
            result = self.project / handoff.CLAIMS / f"{q_sha}.activate.result"
            self.assertEqual(
                json.loads(result.read_text()),
                {"executed": False, "reason": "QA window expired"},
            )
            self.assertEqual(self.ups(), 0)
        with self.subTest("the evidence stop also refuses after the window"):
            self.setUp()
            path, digest = self.q_pre_stop()
            self.clock.now += timedelta(hours=3)
            with self.assertRaisesRegex(RuntimeError, "QA window ended|stale"):
                self.new().exec_step(path, digest)
            self.assertEqual(self.docker.runs, [])

    def test_quiescent_window_notice_is_bounded(self):
        path, _ = self.q_post_build()
        cases = {
            "not_json": (
                lambda: self.notice.write_text("window 02:00-03:00\n"),
                "must be JSON",
            ),
            "too_long": (lambda: self.notice_json(-60, 1800), "at most"),
            "not_started": (lambda: self.notice_json(600, 1500), "not started"),
            "ended": (lambda: self.notice_json(-1700, -10), "ended"),
            "not_utc": (
                lambda: self.notice.write_text(
                    json.dumps(
                        {
                            "window_start_utc": "2026-11-08T01:59:00",
                            "window_end_utc": "2026-11-08T03:00:00",
                        }
                    )
                ),
                "must be UTC",
            ),
        }
        for name, (change, message) in cases.items():
            with self.subTest(name):
                change()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.q_attest(path)
        self.assertEqual(
            list((self.root / "evidence").glob("quiescent-pre-stop-*.json")), []
        )

    def test_quiescent_ambiguous_writer_refuses_at_both_points(self):
        with self.subTest("before the receipt: HOLD"):
            stopped, _ = self.q_stopped()
            self.docker.writers = 1
            with self.assertRaisesRegex(RuntimeError, "other connection"):
                self.new().quiescent_slice(stopped)
            held = min((self.root / "evidence").glob("quiescent-slice-*.json"))
            self.assertEqual(self.receipt(held)["result"], "hold")
        with self.subTest("before the approval is used"):
            self.setUp()
            q_path, q_sha = self.q_slice()
            approval, approval_sha = self.approval(q_path, q_sha)
            self.docker.writers = 1
            with self.assertRaisesRegex(RuntimeError, "other connection"):
                self.new().quiescent_bundle(q_path, q_sha, approval, approval_sha)
        with self.subTest("right before the up, inside exec-step"):
            self.setUp()
            (bundle, digest), _refs = self.q_bundled()
            self.docker.writers = 1
            with self.assertRaisesRegex(RuntimeError, "other connection"):
                self.new().exec_step(bundle, digest)
            self.assertEqual(self.ups(), 0)

    def test_quiescent_failure_after_consumption_never_replays(self):
        (bundle, digest), (q_path, q_sha, approval, approval_sha) = self.q_bundled()
        second, second_digest = self.new().quiescent_bundle(
            q_path, q_sha, approval, approval_sha
        )
        victim = self.new()
        with (
            patch.object(victim, "write", side_effect=OSError("evidence disk failure")),
            self.assertRaises(OSError) as failure,
        ):
            victim.exec_step(bundle, digest)
        self.assertIn("HOLD", "".join(failure.exception.__notes__))
        with self.assertRaisesRegex(RuntimeError, "interrupted or uncertain; HOLD"):
            self.new().exec_step(bundle, digest)
        with self.assertRaisesRegex(RuntimeError, "activate.claim is already claimed"):
            self.new().exec_step(second, second_digest)  # another bundle, same receipt
        self.assertEqual(self.ups(), 1)

    def test_quiescent_concurrent_activations_one_claim_wins(self):
        (bundle, digest), (q_path, q_sha, approval, approval_sha) = self.q_bundled()
        second, second_digest = self.new().quiescent_bundle(
            q_path, q_sha, approval, approval_sha
        )
        self.new().exec_step(bundle, digest)
        with self.assertRaisesRegex(RuntimeError, "activate.claim is already claimed"):
            self.new().exec_step(second, second_digest)
        self.assertEqual(self.ups(), 1)

    def test_quiescent_keeps_every_other_gate(self):
        def web_unhealthy():
            self.docker.containers[WEB]["health"] = "unhealthy"

        def game_unhealthy():
            self.docker.containers[GAME]["health"] = "unhealthy"

        def brain_container():
            self.docker.extra.append(("ps", "9" * 64, BRAIN, QA, "brain"))

        def candidate_running():
            self.docker.find(CANDIDATE)["status"] = "running"

        cases = {
            web_unhealthy: "differs from the pinned baseline",
            game_unhealthy: "differs from the pinned baseline",
            brain_container: "unexpected QA container",
            candidate_running: "must be stopped",
        }
        for change, message in cases.items():
            with self.subTest(f"post-build {change.__name__}"):
                self.setUp()
                change()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.q_post_build()
            with self.subTest(f"evidence stop {change.__name__}"):
                self.setUp()
                path, digest = self.q_pre_stop()
                change()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().exec_step(path, digest)
                self.assertEqual(self.docker.runs, [])
        with self.subTest("human absence still gates the evidence stop"):
            self.setUp()
            path, digest = self.q_pre_stop()
            self.docker.sessions = 1
            with self.assertRaisesRegex(RuntimeError, "TCP session"):
                self.new().exec_step(path, digest)
            self.assertEqual(self.docker.runs, [])

    def test_normal_mode_still_compares_the_historical_slice_and_refuses_quiescent_artifacts(
        self,
    ):
        with self.assertRaisesRegex(RuntimeError, "differs from the pinned baseline"):
            self.post_build()  # the moved slice (2616) refuses the normal chain
        h = self.new()
        with self.assertRaisesRegex(RuntimeError, "only in quiescent mode"):
            h.live_gate(historical_slice=False)
        q_build, _ = self.q_post_build()
        with self.assertRaisesRegex(RuntimeError, "quiescent chain; this normal phase"):
            self.attest(self.new(), q_build)
        q_pre, q_pre_sha = self.q_attest(q_build)
        stopped, _ = self.new().exec_step(q_pre, q_pre_sha)
        with self.assertRaisesRegex(RuntimeError, "quiescent chain; this normal phase"):
            self.new().post_stop(stopped)
        q_path, q_sha = self.new().quiescent_slice(stopped)
        with self.assertRaisesRegex(RuntimeError, "quiescent chain; this normal phase"):
            self.new().bundle(q_path)
        with self.assertRaisesRegex(RuntimeError, "quiescent chain; this normal phase"):
            self.attest(self.new(), q_path)
        self.docker.containers[GAME].update(status="running")  # the managed return
        self.slice_now = copy.deepcopy(gate.comparable(self.baseline)["db_slice"])
        normal_build, _ = self.post_build()
        with self.assertRaisesRegex(RuntimeError, "normal chain; this quiescent phase"):
            self.q_attest(normal_build)
        normal_pre, normal_sha = self.attest(self.new(), normal_build)
        self.slice_now["counts"]["player_items"] += 1
        with self.assertRaisesRegex(RuntimeError, "differs from the pinned baseline"):
            self.new().exec_step(
                normal_pre, normal_sha
            )  # the normal stop compares the slice
        approval, approval_sha = self.approval(q_path, q_sha)
        with self.assertRaisesRegex(RuntimeError, "normal chain; this quiescent phase"):
            self.new().quiescent_bundle(normal_pre, normal_sha, approval, approval_sha)
        self.assertEqual(self.ups(), 0)

    def test_quiescent_chain_never_uses_the_adapter_fallback(self):
        """The repro q_slice -> fallback-plan started the mocked rescue; now it never can."""
        stopped, _ = self.q_stopped()
        with self.assertRaisesRegex(RuntimeError, "managed-return procedure"):
            self.new().fallback_plan(stopped, RESCUE, self.receipts["rescue_result"])
        q_path, _ = self.new().quiescent_slice(stopped)
        with self.assertRaisesRegex(RuntimeError, "managed-return procedure"):
            self.new().fallback_plan(q_path, RESCUE, self.receipts["rescue_result"])
        with self.assertRaisesRegex(RuntimeError, "managed-return procedure"):
            self.new().fallback_verify(stopped, RESCUE, self.receipts["rescue_result"])
        with self.assertRaisesRegex(RuntimeError, "managed-return procedure"):
            self.new().rescue_verify(stopped)
        self.assertEqual(self.docker.find(RESCUE)["status"], "exited")
        self.assertEqual(len(self.docker.runs), 1)  # only the evidence stop
        self.assertFalse(list((self.root / "evidence").glob("fallback-*.json")))

    def test_quiescent_probe_timeout_before_the_receipt_holds(self):
        stopped, _ = self.q_stopped()
        real = REAL_COLLECT

        def hung(argv, timeout=handoff.LOG_TIMEOUT):
            if argv[-1] != handoff.DB_PROBE_SQL:
                return self.docker.collect(argv, timeout)
            self.docker.probe_timeouts.append(timeout)
            with patch(
                "stage2_handoff.subprocess.run",
                side_effect=subprocess.TimeoutExpired(argv, timeout),
            ):
                return real(argv, timeout)

        with (
            patch("stage2_handoff.collect", side_effect=hung),
            self.assertRaisesRegex(
                RuntimeError, "HOLD: the DB session probe did not complete"
            ),
        ):
            self.new().quiescent_slice(stopped)
        held = min((self.root / "evidence").glob("quiescent-slice-*.json"))
        receipt = self.receipt(held)
        self.assertEqual(receipt["result"], "hold")
        self.assertIn("timed out", " ".join(receipt["problems"]))
        self.assertIn("no activation", " ".join(receipt["problems"]))
        self.assertEqual(len(self.docker.runs), 1)
        self.assertLessEqual(max(self.docker.probe_timeouts), handoff.DB_PROBE_TIMEOUT)

    def test_quiescent_probe_timeout_is_capped_by_the_window(self):
        h = self.new()
        # under 10 s left in the window: the probe gets only that
        h.window_end = self.clock.now + timedelta(seconds=4)
        h.writers()
        self.assertTrue(0 < self.docker.probe_timeouts[-1] <= 4)
        # the window is over: no probe at all, never past the window
        h.window_end = self.clock.now - timedelta(seconds=1)
        calls = len(self.docker.probe_timeouts)
        with self.assertRaisesRegex(RuntimeError, "HOLD: no time left"):
            h.writers()
        self.assertEqual(len(self.docker.probe_timeouts), calls)

    def test_a_forged_chain_that_mixes_modes_is_refused(self):
        """A resealed receipt cannot graft a normal phase onto a quiescent root (or back)."""
        q_build, _ = self.q_post_build()
        self.docker.containers[GAME].update(status="running")
        self.slice_now = copy.deepcopy(gate.comparable(self.baseline)["db_slice"])
        normal_build, _ = self.post_build()
        normal_pre, _ = self.attest(self.new(), normal_build)
        forged = self.receipt(normal_pre)
        forged["previous"] = {
            "path": str(q_build),
            "sha256": sha(q_build.read_bytes()),
            "phase": "quiescent-post-build",
        }
        forged["content_sha256"] = gate.sealed(forged)
        path = self.root / "evidence" / "forged-pre-stop.json"
        path.write_text(json.dumps(forged, sort_keys=True, indent=2) + "\n")
        with self.assertRaisesRegex(RuntimeError, "mixes normal and quiescent"):
            self.new().exec_step(path, sha(path.read_bytes()))
        self.assertEqual(self.docker.runs, [])

    def test_a_fallback_step_grafted_onto_a_quiescent_chain_never_executes(self):
        """The return exec-step: a resealed fallback-plan on a quiescent head is refused."""
        q_path, _ = self.q_slice()
        forged = self.receipt(q_path)
        forged.update(
            phase="fallback-plan",
            previous={
                "path": str(q_path),
                "sha256": sha(q_path.read_bytes()),
                "phase": "quiescent-slice",
            },
            step={
                "name": "stop-new",
                "argv": [*handoff.STOP, "f" * 64],
                "argv_sha256": handoff.digest([*handoff.STOP, "f" * 64]),
            },
            recorded_at_utc=self.clock.now.isoformat(),
        )
        forged["content_sha256"] = gate.sealed(forged)
        path = self.root / "evidence" / "forged-fallback-plan.json"
        path.write_text(json.dumps(forged, sort_keys=True, indent=2) + "\n")
        runs = len(self.docker.runs)
        with self.assertRaisesRegex(RuntimeError, "managed-return procedure"):
            self.new().exec_step(path, sha(path.read_bytes()))
        self.assertEqual(len(self.docker.runs), runs)
        claims = self.project / "runtime" / "evidence" / "stage2-handoff-claims"
        self.assertFalse(list(claims.glob(f"{sha(path.read_bytes())}*")))


for _inherited in [name for name in vars(HandoffTests) if name.startswith("test_")]:
    setattr(
        QuiescentTests, _inherited, None
    )  # the quiescent class runs only its own tests


class DbSessionProbeTests(HandoffTests):
    """The strict root probe that replaces zero_writers, on the real bundle path. Docker is mocked."""

    def test_own_connection_and_daemon_only_pass(self):
        bundle, _ = self.bundled()
        record = self.receipt(bundle)["db_writers"]
        self.assertEqual(record["account"], "root@localhost")
        self.assertEqual(record["privilege"], {"PROCESS": True})
        self.assertEqual(record["connection_id"], OWN)
        self.assertEqual(
            record["excluded"], {"own_connection_id": OWN, "daemon_sessions": 1}
        )
        self.assertEqual((record["other_sessions"], record["transactions"]), (0, 0))
        self.assertEqual([step[0] for step in record["sequence"]], list("12345"))
        self.assertIn("not an atomic snapshot", " ".join(record["limitations"]))
        self.assertIn("no automatic retry", " ".join(record["limitations"]))
        self.assertLessEqual(
            record["wall_clock_utc"]["start"], record["wall_clock_utc"]["end"]
        )

    def test_probe_failures_hold(self):
        cases = {
            "no_process_visibility": (
                {"process": "0"},
                "HOLD: .*no PROCESS visibility",
            ),
            "privilege_row_missing": (
                {"drop": "privilege"},
                "HOLD: .*incomplete or malformed",
            ),
            "wrong_account": ({"account": "canary@%"}, "HOLD: .*another account"),
            "query_error": ({"error": True}, "HOLD: .*did not complete"),
            "incomplete_output": ({"drop": "end"}, "HOLD: .*incomplete or malformed"),
            "two_sessions": ({"end_connection": OWN + 1}, "HOLD: .*one session"),
            "does_not_see_itself": ({"own": False}, "HOLD: .*its own session"),
            "malformed_row": (
                {"rows": [["7", "canary", "x"]]},
                "HOLD: .*incomplete or malformed",
            ),
        }
        for name, (change, message) in cases.items():
            with self.subTest(name):
                self.setUp()
                held, _ = self.post_stop()
                self.docker.probe.update(change)
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().bundle(held)
                self.assertEqual(
                    self.docker.runs, [self.docker.runs[0]]
                )  # only the stop

    def test_any_other_session_or_transaction_refuses(self):
        def foreign_sleep():
            self.docker.writers = 1

        def web_sleep():
            self.docker.probe["rows"] = [
                ["24200", "canary", "172.22.0.4:40000", "canary", "Sleep", "5", ""]
            ]

        def system_user_not_daemon():
            self.docker.probe["rows"] = [
                ["2", "system user", "", "", "Query", "0", "x"]
            ]

        def event_scheduler_not_daemon():
            self.docker.probe["rows"] = [
                ["3", "event_scheduler", "localhost", "", "Sleep", "9", "Waiting"]
            ]

        def another_root_session():
            self.docker.probe["rows"] = [
                ["24191", "root", "localhost", "", "Sleep", "1", ""]
            ]

        def healthcheck_collision():
            self.docker.probe["rows"] = [
                ["24190", "healthcheck", "localhost", "", "Query", "0", "starting"]
            ]

        def trx_on_own_session():
            self.docker.probe["trx"] = [[str(OWN), "RUNNING", "0"]]

        def trx_on_daemon():
            self.docker.probe["trx"] = [["1", "RUNNING", "0"]]

        def trx_unknown_thread():
            self.docker.probe["trx"] = [["0", "RUNNING", "3"]]

        cases = {
            foreign_sleep: "1 other connection",
            web_sleep: "1 other connection",
            system_user_not_daemon: "1 other connection",
            event_scheduler_not_daemon: "1 other connection",
            healthcheck_collision: "1 other connection",
            another_root_session: "1 other connection",
            trx_on_own_session: "0 other connection.* and 1 transaction",
            trx_on_daemon: "0 other connection.* and 1 transaction",
            trx_unknown_thread: "0 other connection.* and 1 transaction",
        }
        for change, message in cases.items():
            with self.subTest(change.__name__):
                self.setUp()
                held, _ = self.post_stop()
                change()
                with self.assertRaisesRegex(RuntimeError, message):
                    self.new().bundle(held)

    def test_refused_sessions_carry_only_an_observed_association(self):
        held, _ = self.post_stop()
        self.docker.writers = 1  # from the game IP; the game is stopped now
        self.docker.probe["rows"] = [
            ["24200", "canary", "172.22.0.4:40000", "canary", "Sleep", "5", ""],
            ["24201", "healthcheck", "localhost", "", "Query", "0", ""],
        ]
        with self.assertRaises(RuntimeError) as refused:
            self.new().bundle(held)
        detail = json.loads(str(refused.exception).split("refused: ", 1)[1])
        seen = {row["id"]: row["observed_association"] for row in detail["sessions"]}
        self.assertEqual(
            seen[24116], "unknown"
        )  # a stopped game's IP counts as unknown
        self.assertEqual(seen[24200], WEB)
        self.assertEqual(seen[24201], "database container (local socket or loopback)")
        self.assertIn("observed association", detail["note"])
        self.assertIn("never proof", detail["note"])
        self.assertNotIn("info", json.dumps(detail).lower().replace("information", ""))

    def test_the_measured_visibility_file_refuses_six_game_sessions(self):
        measured = json.loads(VISIBILITY.read_text())
        self.assertEqual(measured["schema"], "qa-db-process-visibility-v1")
        self.assertEqual(sha(VISIBILITY.read_bytes())[:8], "9a0eaeb6")
        own = measured["own_connection_id"]
        rows = [
            [
                str(row["id"]),
                row["user"],
                row["host"],
                row["db"] or "",
                row["command"],
                str(row["time_seconds"]),
                row["state"],
            ]
            for row in measured["processlist"]
            if row["id"] != own
        ]
        self.docker.probe["rows"] = rows  # the game RUNS here, as when it was measured
        with self.assertRaises(RuntimeError) as refused:
            self.new().writers()
        detail = json.loads(str(refused.exception).split("refused: ", 1)[1])
        self.assertEqual(len(detail["sessions"]), 6)
        self.assertEqual(
            {row["observed_association"] for row in detail["sessions"]},
            {"canary-core-qa-game-1"},
        )

    def test_the_credential_never_reaches_argv_or_receipts(self):
        self.bundled()
        probes = [c for c in self.docker.calls if c[-1:] == (handoff.DB_PROBE_SQL,)]
        self.assertTrue(probes)
        for call in self.docker.calls:
            self.assertFalse(any(ROOT_SECRET in str(arg) for arg in call), call[:3])
        for call in probes:
            self.assertIn('MYSQL_PWD="$MARIADB_ROOT_PASSWORD"', call[5])
            self.assertNotIn("INFO", call[6])
        self.assertNotIn(ROOT_SECRET, self.evidence_text())


for _inherited in [name for name in vars(HandoffTests) if name.startswith("test_")]:
    setattr(DbSessionProbeTests, _inherited, None)


class SuccessorFixTests(HandoffTests):
    """#90 review fixes: the probe timeout on the real exec path and the map pin. Docker is mocked."""

    def hung_probe(self):
        real = REAL_COLLECT

        def hung(argv, timeout=handoff.LOG_TIMEOUT):
            if argv[-1] != handoff.DB_PROBE_SQL:
                return self.docker.collect(argv, timeout)
            self.docker.probe_timeouts.append(timeout)
            with patch(
                "stage2_handoff.subprocess.run",
                side_effect=subprocess.TimeoutExpired(argv, timeout),
            ):
                return real(argv, timeout)

        return patch("stage2_handoff.collect", side_effect=hung)

    def test_probe_timeout_on_the_real_exec_up_path_holds(self):
        bundle, digest = self.bundled()
        with (
            self.hung_probe(),
            self.assertRaisesRegex(
                RuntimeError, "HOLD: .*timed out after 10 s.*no activation"
            ),
        ):
            self.new().exec_step(bundle, digest)
        self.assertEqual(sum("up" in argv for argv in self.docker.runs), 0)
        self.assertFalse(
            (self.project / handoff.CLAIMS / f"{digest}.up.claim").exists()
        )
        self.assertEqual(self.docker.probe_timeouts[-1], handoff.DB_PROBE_TIMEOUT)
        self.new().exec_step(
            bundle, digest
        )  # nothing claimed, nothing ran: the same receipt
        self.assertEqual(sum("up" in argv for argv in self.docker.runs), 1)

    def test_normal_fallback_contract_is_unchanged(self):
        held = self.failed_up()
        plan, plan_sha = self.new().fallback_plan(
            held, RESCUE, self.receipts["rescue_result"]
        )
        stopped, _ = self.new().exec_step(plan, plan_sha)
        verify, verify_sha = self.new().fallback_verify(stopped)
        self.new().exec_step(verify, verify_sha)
        self.assertEqual(self.docker.find(RESCUE)["status"], "running")

    def test_a_swapped_world_refuses_before_the_stop_and_before_the_up(self):
        def swap():
            self.map_file.write_bytes(b"another world\n")

        with self.subTest("pre-stop"):
            path, _ = self.post_build()
            swap()
            with self.assertRaisesRegex(
                RuntimeError, "QA map at .* is not the approved pin"
            ):
                self.attest(self.new(), path)
        with self.subTest("the stop, inside exec-step"):
            self.setUp()
            path, digest = self.pre_stop()
            self.assertEqual(self.receipt(path)["map"]["sha256"], sha(FAKE_MAP))
            swap()
            with self.assertRaisesRegex(RuntimeError, "not the approved pin"):
                self.new().exec_step(path, digest)
            self.assertEqual(self.docker.runs, [])
        with self.subTest("bundle"):
            self.setUp()
            held, _ = self.post_stop()
            swap()
            with self.assertRaisesRegex(RuntimeError, "not the approved pin"):
                self.new().bundle(held)
        with self.subTest("the up, inside exec-step"):
            self.setUp()
            bundle, digest = self.bundled()
            swap()
            with self.assertRaisesRegex(RuntimeError, "not the approved pin"):
                self.new().exec_step(bundle, digest)
            self.assertEqual(sum("up" in argv for argv in self.docker.runs), 0)
        with self.subTest("a removed world"):
            self.setUp()
            bundle, digest = self.bundled()
            self.map_file.unlink()
            with self.assertRaisesRegex(RuntimeError, "not the approved pin"):
                self.new().exec_step(bundle, digest)

    def test_the_map_pin_is_the_approved_one_never_the_current_file(self):
        path, _ = self.post_build()
        world = self.new()
        self.assertEqual(world.assert_map()["sha256"], sha(FAKE_MAP))
        self.assertIn("prepare.MAP_SHA256", world.assert_map()["pin_source"])
        self.assertEqual(
            world.assert_map()["path"], str(self.project / handoff.MAP_FILE)
        )
        with (
            patch("preflight.MAP_SHA256", sha(b"another approved release\n")),
            self.assertRaisesRegex(
                RuntimeError, "map pin and the a1d9 preflight receipt"
            ),
        ):
            self.attest(
                self.new(), path
            )  # the pin must also be the receipt's map_sha256
        self.map_file.write_bytes(b"current file\n")
        with (
            patch("preflight.MAP_SHA256", sha(b"current file\n")),
            self.assertRaisesRegex(
                RuntimeError, "map pin and the a1d9 preflight receipt"
            ),
        ):
            self.attest(
                self.new(), path
            )  # a pin taken from the current file never passes


class QuiescentSuccessorTests(QuiescentTests):
    def test_quiescent_swapped_world_refuses_at_the_stop_and_before_the_up(self):
        with self.subTest("evidence stop"):
            path, digest = self.q_pre_stop()
            self.map_file.write_bytes(b"another world\n")
            with self.assertRaisesRegex(RuntimeError, "not the approved pin"):
                self.new().exec_step(path, digest)
            self.assertEqual(self.docker.runs, [])
        with self.subTest("quiescent up"):
            self.setUp()
            (bundle, digest), _refs = self.q_bundled()
            self.map_file.write_bytes(b"another world\n")
            with self.assertRaisesRegex(RuntimeError, "not the approved pin"):
                self.new().exec_step(bundle, digest)
            self.assertEqual(self.ups(), 0)

    def test_quiescent_probe_timeout_right_before_the_up_holds(self):
        (bundle, digest), (_q, q_sha, _a, _s) = self.q_bundled()
        with (
            SuccessorFixTests.hung_probe(self),
            self.assertRaisesRegex(RuntimeError, "HOLD: .*timed out"),
        ):
            self.new().exec_step(bundle, digest)
        self.assertEqual(self.ups(), 0)
        self.assertFalse(
            (self.project / handoff.CLAIMS / f"{q_sha}.activate.claim").exists()
        )


for _successor in (SuccessorFixTests, QuiescentSuccessorTests):
    for _inherited in [
        name
        for name in {*vars(HandoffTests), *vars(QuiescentTests)}
        if name.startswith("test_")
    ]:
        setattr(_successor, _inherited, None)
del _successor

if __name__ == "__main__":
    unittest.main()
