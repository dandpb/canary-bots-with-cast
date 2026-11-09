"""Offline tests of the MyAAC config attestation per CORE_QA_PROFILE. No Docker: a stand-in entrypoint with
the same escape_lua + heredoc shape is pinned in place of the image's; its bash heredoc really runs."""

import hashlib
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import preflight
import verify_myaac
from test_b1_profile import b1_render
from test_offline import myaac_image_available

FAKE_ENTRYPOINT = rb"""#!/bin/sh
set -eu
escape_lua() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}
cat > /canary/config.lua <<EOF
serverName = "$(escape_lua "$CANARY_SERVER_NAME")"
ip = "$CANARY_SERVER_IP"
loginProtocolPort = $CANARY_LOGIN_PORT
gameProtocolPort = $CANARY_GAME_PORT
statusProtocolPort = $CANARY_STATUS_PORT
statusTimeout = $CANARY_STATUS_TIMEOUT
dataPackDirectory = "$CANARY_DATA_PACK"
mysqlHost = "$CANARY_DB_HOST"
mysqlPort = $CANARY_DB_PORT
mysqlUser = "$CANARY_DB_USER"
mysqlPass = "$(escape_lua "$CANARY_DB_PASSWORD")"
mysqlDatabase = "$CANARY_DB_NAME"
EOF
exec "$@"
"""
REAL_RUN = subprocess.run
STAGE1 = preflight.load_profile("stage1")
B1 = preflight.load_profile("b1")


def sha(data):
    return hashlib.sha256(data).hexdigest()


class MyaacProfileTests(unittest.TestCase):
    def setUp(self):
        self.script = FAKE_ENTRYPOINT
        self.stage1_config = verify_myaac.rendered_config(FAKE_ENTRYPOINT)
        self.b1_config = verify_myaac.rendered_config(
            FAKE_ENTRYPOINT, verify_myaac.profile_fixture(B1)
        )

    def verify(self, profile=None, script=None, render=None, pin=None):
        """verify() against the stand-in: the image ID answers, the entrypoint and stage-1 render are pinned."""
        script = script or self.script
        pins = pin or {
            "entrypoint_sha256": sha(script),
            "qa_config_sha256": sha(self.stage1_config),
        }

        def run(argv, *args, **kwargs):
            if argv[0] == "docker":
                return subprocess.CompletedProcess(
                    argv, 0, verify_myaac.LOCK["id"] + "\n", ""
                )
            return REAL_RUN(argv, *args, **kwargs)

        with (
            patch("verify_myaac.subprocess.run", side_effect=run),
            patch("verify_myaac.entrypoint_from_image", return_value=script),
            patch.dict(verify_myaac.LOCK, pins),
        ):
            if render is None:
                return verify_myaac.verify(profile)
            with patch("verify_myaac.rendered_config", side_effect=render):
                return verify_myaac.verify(profile)

    def test_stage1_contract_is_unchanged(self):
        for profile in (None, STAGE1):
            with self.subTest(profile=profile and profile["name"]):
                self.assertEqual(
                    self.verify(profile),
                    {
                        "image_id": verify_myaac.LOCK["id"],
                        "entrypoint_sha256": sha(FAKE_ENTRYPOINT),
                        "qa_config_sha256": sha(self.stage1_config),
                    },
                )
        self.assertIn(b"gameProtocolPort = 17172\n", self.stage1_config)
        # The public fixture is the literal stage-1 env of before, and the stage-1 row reproduces it.
        self.assertEqual(
            verify_myaac.profile_fixture(STAGE1), verify_myaac.PUBLIC_FIXTURE
        )
        self.assertEqual(
            verify_myaac.PUBLIC_FIXTURE["CANARY_DB_PASSWORD"], "qa-test-only"
        )
        self.assertEqual(
            verify_myaac.LOCK["qa_config_sha256"],
            "a94fa69f36a5fbe59623e7ff0d4e34191f1e41295f018c8e6a9bb06adef42f63",
        )
        self.assertEqual(
            verify_myaac.LOCK["entrypoint_sha256"],
            "a007f92ec02398d05205c447c9645ab1add7cfb74603d3284e9f03eaf38c43e9",
        )

    def test_b1_attests_its_own_generated_config(self):
        found = self.verify(B1)
        fixture = verify_myaac.profile_fixture(B1)
        self.assertEqual(
            {
                key
                for key in fixture
                if fixture[key] != verify_myaac.PUBLIC_FIXTURE[key]
            },
            set(verify_myaac.PROFILE_KEYS),
        )
        self.assertEqual(found["qa_config_sha256"], sha(self.b1_config))
        self.assertEqual(
            found["attestation"],
            {
                "profile": "b1",
                "fixture": "verify_myaac.PUBLIC_FIXTURE with the profile's "
                + ", ".join(verify_myaac.PROFILE_KEYS),
                "fixture_sha256": verify_myaac.fixture_sha256(fixture),
                "stage1_fixture_sha256": verify_myaac.fixture_sha256(
                    verify_myaac.PUBLIC_FIXTURE
                ),
                "stage1_config_sha256": sha(self.stage1_config),
                "config_sha256": sha(self.b1_config),
                "game_protocol_port": 27172,
            },
        )
        for line in (
            b'serverName = "Canary QA B1"',
            b"loginProtocolPort = 27171",
            b"gameProtocolPort = 27172",
            b"statusProtocolPort = 27173",
        ):
            self.assertIn(line + b"\n", self.b1_config)
        self.assertNotIn(b"1717", self.b1_config)

    def test_cross_profile_configs_are_refused(self):
        b1, stage1 = self.b1_config, self.stage1_config
        with self.assertRaisesRegex(
            RuntimeError, "does not advertise QA game port 17172"
        ):
            self.verify(STAGE1, render=lambda script, fixture=None: b1)
        with self.assertRaisesRegex(
            RuntimeError, "does not advertise b1 game port 27172"
        ):
            self.verify(B1, render=lambda script, fixture=None: stage1)

    def test_wrong_port_or_divergent_config_is_refused(self):
        def altered(old, new):
            return lambda script, fixture=None: (
                self.stage1_config
                if fixture is None
                else self.b1_config.replace(old, new)
            )

        for name, render, message in (
            (
                "wrong game port",
                altered(b"gameProtocolPort = 27172", b"gameProtocolPort = 27174"),
                "beyond the profile",
            ),
            (
                "stage-1 port left",
                altered(b"gameProtocolPort = 27172", b"gameProtocolPort = 17172"),
                "does not advertise b1 game port 27172",
            ),
            (
                "other line changed",
                altered(b'mysqlHost = "database"', b'mysqlHost = "operational"'),
                "beyond the profile",
            ),
            (
                "line added",
                altered(b"mysqlDatabase", b"extra = 1\nmysqlDatabase"),
                "other lines",
            ),
        ):
            with self.subTest(name), self.assertRaisesRegex(RuntimeError, message):
                self.verify(B1, render=render)

    def test_template_ignoring_the_port_is_refused(self):
        script = FAKE_ENTRYPOINT.replace(
            b"gameProtocolPort = $CANARY_GAME_PORT", b"gameProtocolPort = 17172"
        )
        pins = {
            "entrypoint_sha256": sha(script),
            "qa_config_sha256": sha(verify_myaac.rendered_config(script)),
        }
        self.assertEqual(
            self.verify(STAGE1, script, pin=pins)["entrypoint_sha256"], sha(script)
        )
        with self.assertRaisesRegex(
            RuntimeError, "does not advertise b1 game port 27172"
        ):
            self.verify(B1, script, pin=pins)

    def test_pins_are_not_loosened_for_b1(self):
        with self.assertRaisesRegex(RuntimeError, "entrypoint differs"):
            self.verify(
                B1,
                pin={
                    "entrypoint_sha256": "0" * 64,
                    "qa_config_sha256": sha(self.stage1_config),
                },
            )
        with self.assertRaisesRegex(
            RuntimeError, "generated config differs from image-lock.json"
        ):
            self.verify(
                B1,
                pin={
                    "entrypoint_sha256": sha(FAKE_ENTRYPOINT),
                    "qa_config_sha256": "0" * 64,
                },
            )
        with self.assertRaisesRegex(RuntimeError, "pins no stage-1 qa_config_sha256"):
            self.verify(
                B1,
                pin={"entrypoint_sha256": sha(FAKE_ENTRYPOINT), "qa_config_sha256": ""},
            )

    def test_profile_row_is_what_the_compose_render_carries(self):
        for profile, name in ((STAGE1, "compose.yaml"), (B1, "compose.b1.yaml")):
            text = (verify_myaac.HERE / name).read_text()
            self.assertIn(f"CANARY_SERVER_NAME: {profile['server_name']}\n", text)
        render = b1_render()
        render["services"]["web"]["environment"]["CANARY_SERVER_NAME"] = STAGE1[
            "server_name"
        ]
        with self.assertRaisesRegex(
            RuntimeError, "web CANARY_SERVER_NAME differ from profile b1"
        ):
            preflight.assert_profile_render(render, B1)
        preflight.assert_profile_render(b1_render(), B1)

    def test_preflight_attests_with_its_profile_and_records_it(self):
        attested = {
            "entrypoint_sha256": "d",
            "qa_config_sha256": "e",
            "attestation": {"profile": "b1"},
        }
        with (
            patch("preflight.assert_compose", return_value="f" * 64),
            patch("preflight.assert_no_resources"),
            patch("preflight.assert_image_lock", return_value={}),
            patch("preflight.verify_myaac", return_value=attested) as verify,
        ):
            self.assertIsNone(preflight.run_preflight(resources_only=True))
        verify.assert_called_once_with(preflight.PROFILE)
        with self.subTest("receipt"), tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            preflight.write_receipt(path, "a" * 40, "f" * 64, {}, attested, "1" * 64)
            self.assertEqual(
                json.loads(path.read_text())["myaac_attestation"], {"profile": "b1"}
            )

    @unittest.skipUnless(
        myaac_image_available(), "otbr-myaac:latest absent on this host"
    )
    def test_pinned_image_renders_the_b1_config(self):
        found = verify_myaac.verify(B1)
        self.assertEqual(
            found["attestation"]["stage1_config_sha256"],
            verify_myaac.LOCK["qa_config_sha256"],
        )
        self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", found["qa_config_sha256"]))


if __name__ == "__main__":
    unittest.main()
