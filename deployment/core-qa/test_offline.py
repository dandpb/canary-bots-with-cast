"""Offline checks for the QA login/port contract and Compose isolation."""

import hashlib
import json
import os
import runpy
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from preflight import (
    IMAGE_LOCK,
    assert_fake_brain,
    assert_image_lock,
    assert_no_resources,
    assert_source,
    record_brain_image,
    redact,
    run_preflight,
)
from verify_myaac import verify as verify_myaac

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent
needs_docker = unittest.skipUnless(shutil.which("docker"), "docker CLI absent: Compose renders only on a Docker host")


def myaac_image_available():
    try:
        return subprocess.run(
            ["docker", "image", "inspect", "otbr-myaac:latest"],
            capture_output=True, check=False,
        ).returncode == 0
    except OSError:
        return False


class CoreQaOfflineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("docker"):
            return
        env = os.environ.copy()
        env.update(COMPOSE_PROJECT_NAME="canary-bots-wsl",
                   COMPOSE_FILE=str(SOURCE / "deployment/wsl/compose.yaml"),
                   COMPOSE_ENV_FILES="/nonexistent/operational.env",
                   MARIADB_PASSWORD="operational-sentinel",
                   MARIADB_ROOT_PASSWORD="operational-sentinel",
                   BOT_PLAYERS_ONLINE="997",
                   SOURCE_REVISION="0" * 40)
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("MARIADB_PASSWORD=qa-test-only\nMARIADB_ROOT_PASSWORD=qa-test-only\n")
            result = subprocess.run(
                ["env", "-u", "MARIADB_PASSWORD", "-u", "MARIADB_ROOT_PASSWORD",
                 "-u", "BOT_PLAYERS_ONLINE", "docker", "compose",
                 "-p", "canary-core-qa", "-f", "compose.yaml",
                 "--env-file", str(env_file), "config", "--format", "json"],
                cwd=HERE, env=env, text=True, capture_output=True, check=True,
            )
        cls.compose = json.loads(result.stdout)

    @needs_docker
    def test_project_and_resources_are_isolated(self):
        compose = self.compose
        self.assertEqual(compose["name"], "canary-core-qa")
        self.assertEqual(set(compose["services"]), {"database", "game", "web"})
        self.assertEqual(set(compose["volumes"]),
                         {"database", "game-logs", "authored-data", "website-cache"})
        for volume in compose["volumes"].values():
            self.assertTrue(volume["name"].startswith("canary-core-qa_"))
        for service in compose["services"].values():
            for mount in service.get("volumes", []):
                if mount["type"] == "bind":
                    self.assertTrue(Path(mount["source"]).is_relative_to(HERE / "runtime"))
            for port in service.get("ports", []):
                self.assertEqual(port["host_ip"], "127.0.0.1")
        self.assertNotIn("brain", compose["services"])
        self.assertNotIn("litellm", compose["services"])
        self.assertEqual(compose["services"]["database"]["environment"]["MARIADB_PASSWORD"],
                         "qa-test-only")
        self.assertEqual(compose["services"]["game"]["environment"]["BOT_PLAYERS_ONLINE"],
                         "50")
        self.assertEqual(compose["services"]["database"]["pull_policy"], "never")
        self.assertIsNot(compose["services"]["web"]["build"].get("pull"), True)
        self.assertEqual(compose["services"]["game"]["build"]["args"]["SOURCE_REVISION"],
                         "0" * 40)

    def test_preflight_rejects_existing_qa_resource_by_label_or_name(self):
        for match in ("name", "label"):
            with self.subTest(match=match):
                def fake_command(*args, **_kwargs):
                    if args[:3] == ("docker", "volume", "ls"):
                        labeled = "--filter" in args
                        if labeled == (match == "label"):
                            return "canary-core-qa_database\n"
                    return ""

                with patch("preflight.command", side_effect=fake_command):
                    with self.assertRaisesRegex(RuntimeError, "QA resources already exist"):
                        assert_no_resources()

    def test_preflight_requires_approved_clean_source(self):
        sha = "a" * 40
        with patch.dict(os.environ, {"SOURCE_REVISION": sha}):
            with patch("preflight.command", side_effect=[sha + "\n", ""]):
                assert_source(sha)
            with patch("preflight.command", side_effect=[sha + "\n", " M changed.py\n"]):
                with self.assertRaisesRegex(RuntimeError, "uncommitted"):
                    assert_source(sha)
            with patch("preflight.command", return_value=sha + "\n"):
                with self.assertRaisesRegex(RuntimeError, "must match"):
                    assert_source("b" * 40)

    def test_receipt_is_sanitized_and_only_written_after_full_success(self):
        sha = "a" * 40
        image_ids = {"database": "sha256:" + "b" * 64,
                     "web_base": "sha256:" + "c" * 64}
        myaac = {"entrypoint_sha256": "d" * 64,
                 "qa_config_sha256": "e" * 64}
        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "preflight-receipt.json"
            with patch("preflight.assert_compose", return_value="f" * 64), \
                 patch("preflight.assert_no_resources"), \
                 patch("preflight.assert_image_lock", return_value=image_ids), \
                 patch("preflight.verify_myaac", return_value=myaac), \
                 patch("preflight.assert_source", return_value=sha), \
                 patch("preflight.assert_map", side_effect=RuntimeError("bad map")):
                with self.assertRaisesRegex(RuntimeError, "bad map"):
                    run_preflight(approved_revision=sha, receipt_path=receipt_path)
            self.assertFalse(receipt_path.exists())
            with patch("preflight.assert_compose", return_value="f" * 64), \
                 patch("preflight.assert_no_resources"), \
                 patch("preflight.assert_image_lock", return_value=image_ids), \
                 patch("preflight.verify_myaac", return_value=myaac), \
                 patch("preflight.assert_source", return_value=sha), \
                 patch("preflight.assert_map", return_value="1" * 64):
                digest = run_preflight(approved_revision=sha, receipt_path=receipt_path)
            payload = receipt_path.read_text()
            self.assertEqual(json.loads(payload)["approved_source_revision"], sha)
            self.assertEqual(json.loads(payload)["observed_image_ids"], image_ids)
            self.assertEqual(json.loads(payload)["compose_redacted_sha256"], "f" * 64)
            self.assertNotIn("operational-sentinel", payload)
            self.assertEqual(digest, hashlib.sha256(payload.encode()).hexdigest())
        redacted = redact({"services": {"database": {"environment": {
            "MARIADB_PASSWORD": "operational-sentinel", "CANARY_GAME_PORT": "17172"}}}})
        self.assertNotIn("operational-sentinel", json.dumps(redacted))
        self.assertEqual(redacted["services"]["database"]["environment"]["CANARY_GAME_PORT"], "17172")

    @needs_docker
    def test_compose_rejects_missing_source_revision(self):
        env = os.environ.copy()
        env.pop("SOURCE_REVISION", None)
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("MARIADB_PASSWORD=qa-test-only\nMARIADB_ROOT_PASSWORD=qa-test-only\n")
            result = subprocess.run(
                ["docker", "compose", "-p", "canary-core-qa", "-f", "compose.yaml",
                 "--env-file", str(env_file), "config", "-q"],
                cwd=HERE, env=env, text=True, capture_output=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOURCE_REVISION", result.stderr)

    @unittest.skipUnless(myaac_image_available(),
                         "otbr-myaac:latest absent on this host; the full preflight never skips")
    def test_pinned_myaac_entrypoint_generates_qa_game_port(self):
        env = os.environ.copy()
        env.pop("TMPDIR", None)
        with patch.dict(os.environ, env, clear=True):
            receipt = verify_myaac()
        self.assertEqual(receipt["qa_config_sha256"],
                         "a94fa69f36a5fbe59623e7ff0d4e34191f1e41295f018c8e6a9bb06adef42f63")

    @needs_docker
    def test_login_advertises_the_game_listener(self):
        services = self.compose["services"]
        game_env = services["game"]["environment"]
        web_env = services["web"]["environment"]
        self.assertEqual(int(game_env["GAME_PROTOCOL_PORT"]), int(web_env["CANARY_GAME_PORT"]))
        self.assertEqual(int(game_env["GAME_LOGIN_PORT"]), int(web_env["CANARY_LOGIN_PORT"]))
        self.assertEqual(int(game_env["GAME_STATUS_PORT"]), int(web_env["CANARY_STATUS_PORT"]))
        self.assertEqual(int(game_env["GAME_PROTOCOL_PORT"]), 17172)
        self.assertEqual(int(web_env["CANARY_GAME_PORT"]), 17172)
        self.assertIn("$port = $config['lua']['gameProtocolPort'];",
                      (SOURCE / "deployment/web/login.php").read_text())
        self.assertEqual(web_env["MYAAC_SITE_URL"], "http://127.0.0.1:18080")
        self.assertEqual(game_env["GAME_DISABLE_MAP_DOWNLOAD"], "1")
        self.assertEqual(game_env["CANARY_BRAIN_CONFIG"],
                         "/etc/canary-core-qa/disabled-brain.json")
        published = {int(port["published"]) for service in services.values()
                     for port in service.get("ports", [])}
        self.assertEqual(published, {17171, 17172, 17173, 18080})

    def test_game_entrypoint_renders_real_qa_listeners(self):
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path.cwd()
            try:
                os.chdir(directory)
                Path("config.lua.dist").write_text("toggleDownloadMap = true\n")
                env = {
                    "MARIADB_PASSWORD": "qa-test-only", "GAME_PUBLIC_IP": "127.0.0.1",
                    "GAME_LOGIN_PORT": "17171", "GAME_PROTOCOL_PORT": "17172",
                    "GAME_STATUS_PORT": "17173", "GAME_DISABLE_MAP_DOWNLOAD": "1",
                    "BOT_PLAYERS_ONLINE": "50",
                }
                with patch.dict(os.environ, env, clear=True), patch("os.execv"):
                    runpy.run_path(str(SOURCE / "deployment/wsl/game-entrypoint.py"))
                config = Path("config.lua").read_text()
            finally:
                os.chdir(cwd)
        for setting in ("loginProtocolPort = 17171", "gameProtocolPort = 17172",
                        "statusProtocolPort = 17173", "toggleDownloadMap = false",
                        "botPlayersOnline = 50"):
            self.assertIn(setting, config)

    def test_operational_entrypoint_defaults_remain_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path.cwd()
            try:
                os.chdir(directory)
                Path("config.lua.dist").write_text("toggleDownloadMap = true\n")
                with patch.dict(os.environ, {"MARIADB_PASSWORD": "test-only"}, clear=True), \
                     patch("os.execv"):
                    runpy.run_path(str(SOURCE / "deployment/wsl/game-entrypoint.py"))
                config = Path("config.lua").read_text()
            finally:
                os.chdir(cwd)
        for setting in ("loginProtocolPort = 7171", "gameProtocolPort = 7172",
                        "statusProtocolPort = 7173", "toggleDownloadMap = true"):
            self.assertIn(setting, config)


class BrainFakeStageTests(unittest.TestCase):
    """Stage 2 add-on: fake worker only; the base stack keeps the brain disabled."""

    def test_worker_is_fake_offline_and_matches_the_bridge(self):
        worker = json.loads((HERE / "brain/worker.json").read_text())
        server = json.loads((HERE / "brain/server.json").read_text())
        self.assertEqual((server["mode"], server["bots"]), ("active", worker["bots"]))
        self.assertEqual(server["socket_directory"], worker["socket_directory"])
        self.assertIn(server["autonomous_bot"], server["bots"])
        good = {"image": "canary-core-qa-brain:local", "network_mode": "none",
                "build": {"args": {"SOURCE_REVISION": "a" * 40}}}
        assert_fake_brain(good, "a" * 40)
        for bad in ({"network_mode": "bridge"}, {"ports": [{"published": "8091"}]},
                    {"environment": {"OPENAI_API_KEY": "x"}}, {"env_file": ["x.env"]}):
            with self.subTest(bad=bad), self.assertRaisesRegex(RuntimeError, "offline fake"):
                assert_fake_brain({**good, **bad}, "a" * 40)
        with patch("preflight.json.loads", return_value={**worker, "provider": "litellm"}), \
             self.assertRaisesRegex(RuntimeError, "fake provider"):
            assert_fake_brain(good, "a" * 40)

    def test_entrypoint_loads_the_pilots_and_rejects_injection(self):
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path.cwd()
            try:
                os.chdir(directory)
                Path("config.lua.dist").write_text("")
                env = {"MARIADB_PASSWORD": "t", "BOT_POPULATION_REFERENCE_BOTS": "65001,65004,65003"}
                with patch.dict(os.environ, env, clear=True), patch("os.execv"):
                    runpy.run_path(str(SOURCE / "deployment/wsl/game-entrypoint.py"))
                self.assertIn('botPopulationReferenceBots = "65001,65004,65003"', Path("config.lua").read_text())
                env["BOT_POPULATION_REFERENCE_BOTS"] = '1"; os.exit()'
                with patch.dict(os.environ, env, clear=True), patch("os.execv"), self.assertRaises(ValueError):
                    runpy.run_path(str(SOURCE / "deployment/wsl/game-entrypoint.py"))
            finally:
                os.chdir(cwd)

    def test_stage2_commands_are_scoped_and_rollback_spares_shared_volumes(self):
        section = (HERE / "README.md").read_text().split("## Etapa 2", 1)[1]
        prefix = "docker compose -p canary-core-qa -f compose.yaml -f compose.brain-fake.yaml --env-file .env"
        lines = [line for line in section.splitlines() if "docker " in line or line.startswith("$QA")]
        self.assertIn(f'QA="env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE {prefix}"', lines)
        stage1 = "docker compose -p canary-core-qa -f compose.yaml --env-file .env up -d --no-build --wait"
        self.assertIn("python3 stage1_baseline.py rollback", section)
        self.assertIn(stage1, section)
        self.assertIn("272c35fbab6496376a366565ac81368e8885297c1cc9febf7ef73e7cdd554789", section)
        for line in lines:
            self.assertNotRegex(line, r" (-v|--volumes)\b|docker volume (prune|rm -f)")
            if "docker compose" in line and stage1 not in line:
                self.assertIn(prefix, line)

    @needs_docker
    def test_override_renders_isolated_under_adverse_compose_env(self):
        env = dict(os.environ, COMPOSE_PROJECT_NAME="canary-bots-wsl", COMPOSE_PROFILES="ai",
                   COMPOSE_FILE=str(SOURCE / "deployment/wsl/compose.yaml"),
                   COMPOSE_ENV_FILES="/nonexistent/operational.env", OPENAI_API_KEY="sk-sentinel",
                   LITELLM_API_KEY="sk-sentinel", SOURCE_REVISION="0" * 40)
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("MARIADB_PASSWORD=qa-test-only\nMARIADB_ROOT_PASSWORD=qa-test-only\n")
            result = subprocess.run(
                ["docker", "compose", "-p", "canary-core-qa", "-f", "compose.yaml",
                 "-f", "compose.brain-fake.yaml", "--env-file", str(env_file), "config", "--format", "json"],
                cwd=HERE, env=env, text=True, capture_output=True, check=True)
        compose = json.loads(result.stdout)
        self.assertEqual(set(compose["services"]), {"database", "game", "web", "brain"})
        assert_fake_brain(compose["services"]["brain"], "0" * 40)
        self.assertNotIn("sk-sentinel", result.stdout)
        published = {int(port["published"]) for service in compose["services"].values()
                     for port in service.get("ports", [])}
        self.assertEqual(published, {17171, 17172, 17173, 18080})
        for kind in ("volumes", "networks"):
            for item in compose.get(kind, {}).values():
                self.assertTrue(item["name"].startswith("canary-core-qa_"))


def docker_shim(*changes):
    """Fake read-only Docker CLI holding a running stage-1 QA; changes are (kind, name, value|None)."""
    qa = "canary-core-qa"
    state = {"ps": {f"{qa}-{s}-1": (qa, s) for s in ("database", "game", "web")},
             "volume": {f"{qa}_{v}": (qa, v) for v in ("database", "game-logs", "authored-data", "website-cache")},
             "network": {f"{qa}_default": (qa, "default"), "bridge": ("", "")},
             "image": {"canary-core-qa-game:local": 1, "canary-core-qa-web:local": 1, "mariadb:11.4": 1}}
    for kind, name, value in changes:
        state[kind].pop(name, None) if value is None else state[kind].__setitem__(name, value)

    def command(*args, **_kwargs):
        if args[1:3] == ("image", "ls"):
            return "".join(f"{ref}\n" for ref in state["image"])
        rows = state[args[1]].items()
        if "--filter" in args:
            rows = [(name, row) for name, row in rows if row[0] == qa]
        return "".join(f"{name}\n" for name, _ in rows)
    return command


class FreshInstallGateTests(unittest.TestCase):
    """Stage 1 and stage 2 first up on a clean host: unchanged by the stage-1 -> 2 upgrade gate."""

    def test_fresh_gates_are_unchanged(self):
        for brain_fake in (False, True):
            with self.subTest(brain_fake=brain_fake), patch("preflight.command", side_effect=docker_shim()), \
                 self.assertRaisesRegex(RuntimeError, "QA resources already exist"):
                assert_no_resources(brain_fake)
        empty = [(kind, f"canary-core-qa{sep}{name}", None) for kind, sep, names in (
            ("ps", "-", ("database-1", "game-1", "web-1")), ("network", "_", ("default",)),
            ("volume", "_", ("database", "game-logs", "authored-data", "website-cache")))
            for name in names] + [("image", "canary-core-qa-game:local", None), ("image", "canary-core-qa-web:local", None)]
        for brain_fake in (False, True):
            with patch("preflight.command", side_effect=docker_shim(*empty)):
                assert_no_resources(brain_fake)
        brain = [*empty, ("image", "canary-core-qa-brain:local", 1)]
        with patch("preflight.command", side_effect=docker_shim(*brain)):
            assert_no_resources(False)
            with self.assertRaisesRegex(RuntimeError, "image:canary-core-qa-brain:local"):
                assert_no_resources(True)
        for change in (("volume", "canary-core-qa_brain-ledger", ("canary-core-qa", "brain-ledger")),
                       ("ps", "canary-core-qa-brain-1", ("canary-core-qa", "brain"))):
            with self.subTest(change=change), patch("preflight.command", side_effect=docker_shim(*empty, change)), \
                 self.assertRaisesRegex(RuntimeError, "QA resources already exist"):
                assert_no_resources(True)


class BrainImageProvenanceTests(unittest.TestCase):
    """The brain base is pulled by digest only, and the built image is bound to the approved HEAD."""

    def test_fresh_stage2_receipt_can_record_the_built_brain(self):
        sha = "a" * 40
        with tempfile.TemporaryDirectory() as directory, \
             patch("preflight.UPGRADE_RECEIPT", Path(directory) / "stage2.json"), \
             patch("preflight.assert_compose", return_value="f" * 64), \
             patch("preflight.assert_no_resources"), \
             patch("preflight.assert_image_lock", return_value={"brain_base": "sha256:base"}), \
             patch("preflight.verify_myaac", return_value={"entrypoint_sha256": "d", "qa_config_sha256": "e"}), \
             patch("preflight.assert_source", return_value=sha), \
             patch("preflight.assert_map", return_value="1" * 64), \
             patch("preflight.command", side_effect=lambda *a, **k:
                   f"sha256:brain\t{sha}" if a[1] == "image" else "sha256:brain"):
            run_preflight(approved_revision=sha, brain_fake=True)
            record_brain_image(sha)
            receipt = json.loads((Path(directory) / "stage2.json").read_text())
        self.assertTrue(receipt["brain_fake"] and receipt["resources_absent"])
        self.assertEqual(receipt["brain_image"], {"id": "sha256:brain", "source_revision": sha})


    def test_brain_base_is_locked_and_the_built_image_matches_head(self):
        locked = IMAGE_LOCK["brain_base"]["repo_digest"]
        ids = {"database": IMAGE_LOCK["database"]["id"], "web_base": IMAGE_LOCK["web_base"]["id"]}

        def inspect(digest):
            return lambda *a, **_k: f"sha256:base\t[{json.dumps(digest)}]" if "RepoDigests" in a[-1] else (
                ids["database"] if a[3] == "mariadb:11.4" else ids["web_base"])
        with patch("preflight.command", side_effect=inspect(locked)):
            self.assertEqual(assert_image_lock(brain=True)["brain_base"], "sha256:base")
        with patch("preflight.command", side_effect=inspect("python@sha256:" + "0" * 64)), \
             self.assertRaisesRegex(RuntimeError, "brain base"):
            assert_image_lock(brain=True)
        sha = "a" * 40
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "receipt.json"
            receipt.write_text(json.dumps({"approved_source_revision": sha}))
            for label, running in ((sha, "sha256:b"), ("c" * 40, "sha256:b"), (sha, "sha256:old")):
                answers = lambda *a, **_k: f"sha256:b\t{label}" if a[1] == "image" else running  # noqa: B023
                with self.subTest(label=label, running=running), \
                     patch("preflight.assert_source", return_value=sha), \
                     patch("preflight.command", side_effect=answers):
                    if (label, running) == (sha, "sha256:b"):
                        record_brain_image(sha, receipt)
                        self.assertEqual(json.loads(receipt.read_text())["brain_image"],
                                         {"id": "sha256:b", "source_revision": sha})
                    else:
                        with self.assertRaisesRegex(RuntimeError, "approved HEAD"):
                            record_brain_image(sha, receipt)


if __name__ == "__main__":
    unittest.main()
