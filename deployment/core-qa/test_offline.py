"""Offline checks for the QA login/port contract and Compose isolation."""

import hashlib
import json
import os
import re
import runpy
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import stage1_baseline
from preflight import (
    BRAIN_IMAGE,
    GAME_TAG,
    IMAGE_LOCK,
    SHUTDOWN_FLAG,
    SHUTDOWN_KEY,
    assert_compose,
    assert_fake_brain,
    assert_game_base,
    assert_game_build,
    assert_game_config,
    assert_image_lock,
    assert_no_resources,
    assert_source,
    lua_setting,
    record_brain_image,
    redact,
    render_game_config,
    run_preflight,
)
from test_stage1_baseline import FAKE_GAME_BASE
from verify_myaac import verify as verify_myaac

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent
FAKE_PIN = "ubuntu:24.04@" + FAKE_GAME_BASE["repo_digest"].split("@")[1]
PLACEHOLDER = {"repo_digest": "ubuntu@sha256:PLACEHOLDER_FROM_HOST_RECEIPT",
               "id": "sha256:PLACEHOLDER_FROM_HOST_RECEIPT"}
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
        lock = IMAGE_LOCK["game_base"]
        self.assertEqual(compose["services"]["game"]["build"]["args"]["BASE_IMAGE"],
                         lock["ref"] + "@" + lock["repo_digest"].split("@")[1])
        self.assertIsNot(compose["services"]["game"]["build"].get("pull"), True)

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
        self.assertEqual(game_env[SHUTDOWN_FLAG], "1")
        self.assertEqual(lua_setting(assert_game_config(game_env), SHUTDOWN_KEY), "false")
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
                    "BOT_PLAYERS_ONLINE": "50", SHUTDOWN_FLAG: "1",
                }
                with patch.dict(os.environ, env, clear=True), patch("os.execv"):
                    runpy.run_path(str(SOURCE / "deployment/wsl/game-entrypoint.py"), run_name="__main__")
                config = Path("config.lua").read_text()
            finally:
                os.chdir(cwd)
        for setting in ("loginProtocolPort = 17171", "gameProtocolPort = 17172",
                        "statusProtocolPort = 17173", "toggleDownloadMap = false",
                        "botPlayersOnline = 50", "globalServerSaveShutdown = false"):
            self.assertIn(setting, config)

    def test_operational_entrypoint_defaults_remain_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path.cwd()
            try:
                os.chdir(directory)
                Path("config.lua.dist").write_text("toggleDownloadMap = true\n")
                with patch.dict(os.environ, {"MARIADB_PASSWORD": "test-only"}, clear=True), \
                     patch("os.execv"):
                    runpy.run_path(str(SOURCE / "deployment/wsl/game-entrypoint.py"), run_name="__main__")
                config = Path("config.lua").read_text()
            finally:
                os.chdir(cwd)
        for setting in ("loginProtocolPort = 7171", "gameProtocolPort = 7172",
                        "statusProtocolPort = 7173", "toggleDownloadMap = true"):
            self.assertIn(setting, config)


QA_GAME_ENV = {"GAME_PUBLIC_IP": "127.0.0.1", "GAME_LOGIN_PORT": "17171", "GAME_PROTOCOL_PORT": "17172",
               "GAME_STATUS_PORT": "17173", "GAME_DISABLE_MAP_DOWNLOAD": "1", "BOT_PLAYERS_ONLINE": "50",
               "CANARY_BRAIN_CONFIG": "/etc/canary-core-qa/disabled-brain.json", SHUTDOWN_FLAG: "1"}


class DailyShutdownContractTests(unittest.TestCase):
    """QA only: the daily global save must not shut the game down; production keeps the repo default."""

    def test_qa_render_disables_the_daily_shutdown_and_keeps_the_save(self):
        config = assert_game_config(QA_GAME_ENV)
        dist = (SOURCE / "config.lua.dist").read_text()
        self.assertEqual(lua_setting(config, SHUTDOWN_KEY), "false")
        self.assertEqual(lua_setting(config, "globalServerSaveClose"), "false")  # -> the event calls saveServer()
        self.assertEqual(lua_setting(dist, SHUTDOWN_KEY), "true")  # the repo default stays
        for key in ("globalServerSaveTime", "globalServerSaveNotifyMessage", "globalServerSaveCleanMap",
                    "globalServerSaveClose", "toggleSaveInterval"):
            self.assertEqual(lua_setting(config, key), lua_setting(dist, key))

    def test_production_render_is_byte_for_byte_the_default(self):
        dist = (SOURCE / "config.lua.dist").read_text()
        for env in ({}, {"GAME_PUBLIC_IP": "203.0.113.7", "BOT_PLAYERS_ONLINE": "997",
                         "BOT_POPULATION_REFERENCE_BOTS": "65001,65004"}):
            with self.subTest(env=env):
                config = render_game_config(env)
                self.assertEqual(config, render_game_config({**env, SHUTDOWN_FLAG: ""}))
                self.assertEqual(config.count(SHUTDOWN_KEY), dist.count(SHUTDOWN_KEY))
                self.assertTrue(config.startswith(dist))
                self.assertEqual(lua_setting(config, SHUTDOWN_KEY), "true")
        wsl = (SOURCE / "deployment/wsl/compose.yaml").read_text()
        self.assertNotIn(SHUTDOWN_FLAG, wsl)
        self.assertNotIn(SHUTDOWN_FLAG, (SOURCE / "deployment/wsl/Dockerfile").read_text())

    @unittest.skipUnless(shutil.which("luajit") or shutil.which("lua"), "no Lua interpreter on this host")
    def test_daily_event_still_saves_without_close_or_shutdown(self):
        result = subprocess.run([shutil.which("luajit") or shutil.which("lua"), "tests/lua/global_server_save_test.lua"],
                                cwd=SOURCE, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no close and no shutdown still saves the world", result.stdout)

    def test_daily_event_has_the_explicit_save_branch(self):
        script = (SOURCE / "data/scripts/globalevents/global_server_save.lua").read_text()
        self.assertRegex(script, r"GAME_STATE_SHUTDOWN\)\n\telseif not configManager\.getBoolean\("
                                 r"configKeys\.GLOBAL_SERVER_SAVE_CLOSE\) then\n(?:\t\t--[^\n]*\n)?\t\tsaveServer\(\)")

    def test_contract_fails_closed_when_the_key_is_true_or_missing(self):
        for env in ({**QA_GAME_ENV, SHUTDOWN_FLAG: None}, {key: value for key, value in QA_GAME_ENV.items()
                                                          if key != SHUTDOWN_FLAG}):
            with self.subTest(env=env), self.assertRaisesRegex(RuntimeError, SHUTDOWN_FLAG):
                assert_game_config(env)
        with self.assertRaisesRegex(ValueError, SHUTDOWN_FLAG):  # the entrypoint refuses ambiguous values
            render_game_config({**QA_GAME_ENV, SHUTDOWN_FLAG: "true"})
        cases = {"true": "globalServerSaveShutdown = true\n", "missing": ""}
        for name, tail in cases.items():
            def render(_environ, config, tail=tail):  # an entrypoint that ignores the flag
                return config.replace("globalServerSaveShutdown = true", "") + tail
            with self.subTest(name), patch("preflight.CONFIG_DIST", **{"read_text.return_value": "a = 1\n"}), \
                 patch("importlib.util.module_from_spec") as module, patch("importlib.util.spec_from_file_location"):
                module.return_value.render = render
                with self.assertRaisesRegex(RuntimeError, "globalServerSaveShutdown = false"):
                    assert_game_config(QA_GAME_ENV)
        with self.subTest("close"), patch("preflight.CONFIG_DIST", **{"read_text.return_value": "a = 1\n"}), \
             patch("importlib.util.module_from_spec") as module, patch("importlib.util.spec_from_file_location"):
            module.return_value.render = lambda _environ, config: (
                config + "globalServerSaveShutdown = false\nglobalServerSaveClose = true\n")
            with self.assertRaisesRegex(RuntimeError, "globalServerSaveClose = false so the daily event saves"):
                assert_game_config(QA_GAME_ENV)
        self.assertIsNone(lua_setting("-- globalServerSaveShutdown = false\n", SHUTDOWN_KEY))
        self.assertEqual(lua_setting("globalServerSaveShutdown = false\nglobalServerSaveShutdown = true\n",
                                     SHUTDOWN_KEY), "true")

    def test_preflight_compose_gate_refuses_a_qa_game_without_the_contract(self):
        def rendered(game_env):
            build = {"dockerfile": "deployment/wsl/Dockerfile",
                     "args": {"SOURCE_REVISION": "0" * 40, "BASE_IMAGE": FAKE_PIN}}
            return json.dumps({"name": "canary-core-qa", "volumes": {
                name: {"name": f"canary-core-qa_{name}"} for name in ("database", "game-logs", "authored-data",
                                                                     "website-cache")}, "services": {
                "database": {"image": IMAGE_LOCK["database"]["ref"], "pull_policy": "never"},
                "game": {"image": "canary-core-qa-game:local", "build": build, "environment": game_env},
                "web": {"image": "canary-core-qa-web:local",
                        "build": {"dockerfile": "deployment/wsl/Web.Dockerfile"}}}})

        with patch.dict(os.environ, {"SOURCE_REVISION": "0" * 40}), \
             patch.dict(IMAGE_LOCK["game_base"], FAKE_GAME_BASE):
            with patch("preflight.command", return_value=rendered(QA_GAME_ENV)):
                self.assertRegex(assert_compose(), r"^[0-9a-f]{64}$")
            without = {key: value for key, value in QA_GAME_ENV.items() if key != SHUTDOWN_FLAG}
            with patch("preflight.command", return_value=rendered(without)), \
                 self.assertRaisesRegex(RuntimeError, f"QA game must set {SHUTDOWN_FLAG}=1"):
                assert_compose()


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
                    runpy.run_path(str(SOURCE / "deployment/wsl/game-entrypoint.py"), run_name="__main__")
                self.assertIn('botPopulationReferenceBots = "65001,65004,65003"', Path("config.lua").read_text())
                env["BOT_POPULATION_REFERENCE_BOTS"] = '1"; os.exit()'
                with patch.dict(os.environ, env, clear=True), patch("os.execv"), self.assertRaises(ValueError):
                    runpy.run_path(str(SOURCE / "deployment/wsl/game-entrypoint.py"), run_name="__main__")
            finally:
                os.chdir(cwd)

    STAGE2 = "docker compose -p canary-core-qa -f compose.yaml -f compose.brain-fake.yaml"
    UNSET = "env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE"

    def stage2_commands(self):
        section = (HERE / "README.md").read_text().split("## Etapa 2", 1)[1]
        block = section.split("```bash\n", 1)[1].split("```", 1)[0]
        return section, [line.strip() for line in block.splitlines() if line.strip().startswith("$QA")]

    def test_stage2_commands_are_scoped_and_rollback_spares_shared_volumes(self):
        section, _ = self.stage2_commands()
        plain = f"{self.STAGE2} --env-file .env"
        pinned = f"{self.STAGE2} -f compose.game-pin.yaml --env-file .env"
        lines = [line for line in section.splitlines() if "docker " in line or line.startswith("$QA")]
        self.assertIn(f'QA="{self.UNSET} {plain}"', lines)
        self.assertIn(f'QA_UP="{self.UNSET} {pinned}"', lines)
        stage1 = "docker compose -p canary-core-qa -f compose.yaml --env-file .env up -d --no-build --no-deps --wait game"
        self.assertIn("python3 stage1_baseline.py rollback", section)
        self.assertIn(stage1, section)
        self.assertIn(stage1_baseline.BASELINE_SHA256, section)
        self.assertIn(stage1_baseline.PREVIOUS_BASELINE_SHA256, section)  # named as previous_baseline_sha256
        for line in lines:
            self.assertNotRegex(line, r" (-v|--volumes)\b|docker volume (prune|rm -f)")
            if "docker compose" in line and stage1 not in line:
                self.assertTrue(plain in line or pinned in line, line)

    def test_stage2_up_never_builds_or_pulls_and_never_touches_database_or_web(self):
        _, commands = self.stage2_commands()
        upgrade = "$QA_UP up -d --no-build --no-deps --pull never --wait game brain"
        self.assertIn(upgrade, commands)
        self.assertIn("$QA_UP build brain", commands)  # only the brain is built, at the approved HEAD
        ups = [command for command in commands if command.split()[1:2] == ["up"]]
        self.assertGreaterEqual(len(ups), 2)
        for command in commands:
            tokens = command.split()
            with self.subTest(command=command):
                self.assertNotIn("--build", tokens)
                self.assertNotRegex(command.replace("--pull never", ""), r"pull")
                if tokens[0] == "$QA_UP" and tokens[1] == "build":
                    self.assertEqual(tokens[2:], ["brain"])  # never the game: its image is the baseline's
                if tokens[1] == "up":
                    self.assertIn("--no-build", tokens)
                    self.assertIn("--no-deps", tokens)
                    self.assertIn("--pull never", command)
        self.assertEqual(upgrade.split()[-2:], ["game", "brain"])  # database and web are not reconciled

    def test_game_pin_override_pins_exactly_the_baseline_game_image(self):
        text = (HERE / "compose.game-pin.yaml").read_text()
        body = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
        image = stage1_baseline.baseline_game_image()
        self.assertEqual(body, ["services:", "  game:", f"    image: {image}", "    pull_policy: never"])
        self.assertEqual(image, "sha256:358ee666db065a79625f5b5491efa363f0fc491fba04d14d5c176715f0930181")

    def test_upgrade_compose_gate_requires_the_pin_of_the_baseline_game_image(self):
        image = stage1_baseline.baseline_game_image()
        calls = []

        def rendered(game_image, pull_policy="never"):
            def command(*args, **_kwargs):
                calls.append(args)
                volumes = ("database", "game-logs", "authored-data", "website-cache", "brain-socket", "brain-ledger")
                game = {"image": game_image, "environment": {
                    **QA_GAME_ENV, "CANARY_BRAIN_CONFIG": "/etc/canary-core-qa/brain/server.json"},
                    "build": {"dockerfile": "deployment/wsl/Dockerfile",
                              "args": {"SOURCE_REVISION": "0" * 40, "BASE_IMAGE": FAKE_PIN}}}
                if pull_policy:
                    game["pull_policy"] = pull_policy
                return json.dumps({"name": "canary-core-qa", "volumes": {
                    name: {"name": f"canary-core-qa_{name}"} for name in volumes}, "services": {
                    "database": {"image": IMAGE_LOCK["database"]["ref"], "pull_policy": "never"},
                    "game": game,
                    "web": {"image": "canary-core-qa-web:local", "build": {"dockerfile": "deployment/wsl/Web.Dockerfile"}},
                    "brain": {"image": BRAIN_IMAGE, "network_mode": "none",
                              "build": {"pull": False, "args": {"SOURCE_REVISION": "0" * 40}}}}})
            return command

        self.enterContext(patch.dict(os.environ, {"SOURCE_REVISION": "0" * 40}))
        self.enterContext(patch.dict(IMAGE_LOCK["game_base"], FAKE_GAME_BASE))
        with patch("preflight.command", side_effect=rendered(image)):
            self.assertRegex(assert_compose(True, game_pin=image), r"^[0-9a-f]{64}$")
        self.assertEqual(calls[-1][calls[-1].index("compose.brain-fake.yaml") + 1:][:2], ("-f", "compose.game-pin.yaml"))
        with patch("preflight.command", side_effect=rendered(image)) as docker, \
             patch("preflight.GAME_PIN", HERE / "missing-game-pin.yaml"), \
             self.assertRaisesRegex(RuntimeError, "missing-game-pin.yaml is absent"):
            assert_compose(True, game_pin=image)
        docker.assert_not_called()
        for name, game_image, pull_policy, message in (
                ("another ID", "sha256:" + "6" * 64, "never", "does not pin the baseline game image"),
                ("the mutable tag", GAME_TAG, "never", "does not pin the baseline game image"),
                ("pull allowed", image, None, "pull_policy: never")):
            with self.subTest(name), patch("preflight.command", side_effect=rendered(game_image, pull_policy)), \
                 self.assertRaisesRegex(RuntimeError, message):
                assert_compose(True, game_pin=image)
        with patch("preflight.command", side_effect=rendered(image)), \
             self.assertRaisesRegex(RuntimeError, "QA image tags differ"):
            assert_compose(True)  # the fresh stage-2 render never carries the pin

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
        self.assertNotIn("stage2_game", receipt)

    def test_upgrade_receipt_records_the_game_before_and_after(self):
        sha = "a" * 40
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stage2.json"
            upgrade = {"baseline_sha256": "s", "observed": {}}
            path.write_text(json.dumps({"approved_source_revision": sha, "stage1_upgrade": upgrade}))
            with patch("preflight.assert_source", return_value=sha), \
                 patch("preflight.command", side_effect=lambda *a, **k:
                       f"sha256:brain\t{sha}" if a[1] == "image" else "sha256:brain"), \
                 patch("stage1_baseline.stage2_game", return_value={"before": "b", "after": "c"}) as game:
                record_brain_image(sha, path)
            game.assert_called_once_with(upgrade)
            self.assertEqual(json.loads(path.read_text())["stage2_game"], {"before": "b", "after": "c"})
            with patch("preflight.assert_source", return_value=sha), \
                 patch("preflight.command", side_effect=lambda *a, **k:
                       f"sha256:brain\t{sha}" if a[1] == "image" else "sha256:brain"), \
                 patch("stage1_baseline.stage2_game", side_effect=RuntimeError("no rebuild; refused")), \
                 self.assertRaisesRegex(RuntimeError, "no rebuild"):
                record_brain_image(sha, path)


    def test_brain_base_is_locked_and_the_built_image_matches_head(self):
        locked = IMAGE_LOCK["brain_base"]["repo_digest"]
        ids = {"database": IMAGE_LOCK["database"]["id"], "web_base": IMAGE_LOCK["web_base"]["id"]}

        def inspect(digest):
            return lambda *a, **_k: base_shim(FAKE_GAME_BASE)(*a) if a[3].startswith("ubuntu@") else (
                f"sha256:base\t[{json.dumps(digest)}]" if "RepoDigests" in a[-1] else (
                    ids["database"] if a[3] == "mariadb:11.4" else ids["web_base"]))
        self.enterContext(patch.dict(IMAGE_LOCK["game_base"], FAKE_GAME_BASE))
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


def base_shim(local):
    """Fake read-only `docker image inspect` for the Ubuntu base; local=None means the image is absent."""
    def command(*args, **_kwargs):
        assert args[:3] == ("docker", "image", "inspect") and "pull" not in args
        if local is None or args[3] != local["repo_digest"]:
            raise RuntimeError("read-only command failed: docker image")
        return f"{local['id']}\t{local['platform']}\t{json.dumps([local['repo_digest']])}\n"
    return command


class GameBaseImageTests(unittest.TestCase):
    """QA builds the game FROM ubuntu:24.04 pinned by digest and platform; production keeps the tag default."""

    DOCKERFILE = SOURCE / "deployment/wsl/Dockerfile"

    def stages(self, build_args):
        """The FROM of each stage of the shared Dockerfile, resolved like BuildKit with these build args."""
        lines = self.DOCKERFILE.read_text().splitlines()
        first = next(index for index, line in enumerate(lines) if line.startswith("FROM "))
        defaults = dict(line.split()[1].split("=", 1) for line in lines[:first] if line.startswith("ARG "))
        values = {**defaults, **build_args}
        return {line.split()[-1]: re.sub(r"\$\{(\w+)\}", lambda m: values[m[1]], line.split()[1])
                for line in lines if line.startswith("FROM ")}

    def test_qa_render_uses_the_digest_pinned_base(self):
        lock = IMAGE_LOCK["game_base"]
        pinned = lock["ref"] + "@" + lock["repo_digest"].split("@")[1]
        compose = (HERE / "compose.yaml").read_text()
        game = compose[compose.index("\n  game:"):compose.index("\n  web:")]
        self.assertIn("\n      pull: false\n", game)
        self.assertEqual(re.findall(r"\n        BASE_IMAGE: (\S+)", game), [pinned])
        self.assertEqual(lock["ref"], "ubuntu:24.04")
        self.assertEqual(lock["platform"], "linux/amd64")  # the Dockerfile builds the x64-linux vcpkg triplet
        self.assertEqual(self.stages({"BASE_IMAGE": pinned}),
                         {"build": pinned, "game": pinned, "brain": "python:3.12-slim"})
        with patch.dict(IMAGE_LOCK["game_base"], FAKE_GAME_BASE):
            assert_game_build({"dockerfile": "deployment/wsl/Dockerfile", "args": {"BASE_IMAGE": FAKE_PIN}})
            for build in ({"dockerfile": "deployment/wsl/Dockerfile", "args": {"BASE_IMAGE": "ubuntu:24.04"}},
                          {"dockerfile": "deployment/wsl/Dockerfile", "args": {}},
                          {"dockerfile": "deployment/wsl/Dockerfile", "pull": True, "args": {"BASE_IMAGE": FAKE_PIN}},
                          {"dockerfile": "docker/Dockerfile.x86", "args": {"BASE_IMAGE": FAKE_PIN}}):
                with self.subTest(build=build), self.assertRaisesRegex(RuntimeError, "digest-pinned base"):
                    assert_game_build(build)

    def test_production_default_is_unchanged(self):
        self.assertEqual(self.stages({}),
                         {"build": "ubuntu:24.04", "game": "ubuntu:24.04", "brain": "python:3.12-slim"})
        production = (SOURCE / "deployment/wsl/compose.yaml").read_text()
        self.assertNotIn("BASE_IMAGE", production)
        self.assertNotIn("PLACEHOLDER", production + self.DOCKERFILE.read_text())

    def test_preflight_refuses_an_absent_or_mismatched_base(self):
        self.enterContext(patch.dict(IMAGE_LOCK["game_base"], FAKE_GAME_BASE))
        with patch("preflight.command", side_effect=base_shim(FAKE_GAME_BASE)):
            self.assertEqual(assert_game_base(), FAKE_GAME_BASE["id"])
        cases = (("absent", None, "absent locally"),
                 ("other digest", {**FAKE_GAME_BASE, "repo_digest": "ubuntu@sha256:" + "d" * 64}, "absent locally"),
                 ("other ID", {**FAKE_GAME_BASE, "id": "sha256:" + "c" * 64}, "differs from image-lock"),
                 ("other platform", {**FAKE_GAME_BASE, "platform": "linux/arm64"}, "differs from image-lock"))
        for name, local, message in cases:
            with self.subTest(name), patch("preflight.command", side_effect=base_shim(local)), \
                 self.assertRaisesRegex(RuntimeError, message):
                assert_game_base()
        ids = {"mariadb:11.4": IMAGE_LOCK["database"]["id"], "otbr-myaac:latest": IMAGE_LOCK["web_base"]["id"]}
        with patch("preflight.command", side_effect=lambda *a, **k: ids.get(a[3]) or base_shim(None)(*a)), \
             self.assertRaisesRegex(RuntimeError, "game base image is absent"):
            assert_image_lock()  # the full preflight (and its receipt) stops here

    def test_placeholder_digest_fails_closed_without_docker(self):
        for name, pin in (("placeholder", PLACEHOLDER), ("short", {"repo_digest": "ubuntu@sha256:abc"}),
                          ("other repo", {"repo_digest": "debian@" + FAKE_GAME_BASE["repo_digest"].split("@")[1]}),
                          ("no platform", {"platform": ""})):
            with self.subTest(name), patch.dict(IMAGE_LOCK["game_base"], {**FAKE_GAME_BASE, **pin}), \
                 patch("preflight.command") as docker:
                with self.assertRaisesRegex(RuntimeError, "not a reviewed digest pin"):
                    assert_game_base()
                compose_pin = "ubuntu:24.04@" + pin.get("repo_digest", "@").split("@")[1]
                with self.assertRaisesRegex(RuntimeError, "not a reviewed digest pin"):
                    assert_game_build({"dockerfile": "deployment/wsl/Dockerfile", "args": {"BASE_IMAGE": compose_pin}})
                docker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
