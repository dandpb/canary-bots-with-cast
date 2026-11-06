"""Offline checks for the QA login/port contract and Compose isolation."""

import hashlib
import json
import os
import runpy
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from preflight import assert_no_resources, assert_source, redact, run_preflight
from verify_myaac import verify as verify_myaac

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent


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


if __name__ == "__main__":
    unittest.main()
