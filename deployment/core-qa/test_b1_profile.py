"""Offline tests of CORE_QA_PROFILE: stage 1 unchanged by default, and the B1 project kept apart from it.

Profiles are read when preflight is imported, so each profile runs in its own interpreter, without
docker or git on PATH: a refusal must come before any Docker or git call.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import preflight
import stage1_baseline

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FIXTURES = HERE / "fixtures/stage2-handoff"
MANIFEST = FIXTURES / "qa-stage2-bundle-manifest-a1d9.json"
RENDER = FIXTURES / "qa-stage2-full-render-sanitized.json"
HOST = "/home/daniel/canary-core-qa-playable-20261106/deployment/core-qa"
STAGE1_PORTS = {17171, 17172, 17173, 18080}
# The stage-1 Compose files, byte for byte as before CORE_QA_PROFILE and as the a1d9 bundle manifest pins them.
STAGE1_COMPOSE_SHA256 = {
    "compose.yaml": "7171d1f8e4281cdaf5f0ce0d5ad13c4336150f08c2bfa5ceb90069a2e5ba40e3",
    "compose.brain-fake.yaml": "9be804b20f88aab0e275f0f0274acd67ded544969f68b75074de692b30fb6708",
    "compose.game-pin.yaml": "a465fc92faa566b0b587381ee126073733627b1910ba819d289d1ac3a60acbfe",
}
REFUSED_STAGE1 = "stage-1 baseline schema or project differs; refused"
EXISTING = "refused: QA resources already exist; review before up: "

# Run in a fresh interpreter under a profile: what preflight/stage1_baseline derive, the Compose argv
# assert_compose would run (captured, never executed) and a receipt without its timestamp.
DUMP = """
import json, os, tempfile
from pathlib import Path
from unittest.mock import patch
import preflight as qa, stage1_baseline as s1
calls = []
def capture(*args, **kwargs):
    calls.append(list(args))
    raise RuntimeError("argv captured")
with patch.dict(os.environ, {"SOURCE_REVISION": "0" * 40}), patch("preflight.command", side_effect=capture):
    for brain in (False, True):
        try:
            qa.assert_compose(brain)
        except RuntimeError:
            pass
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "receipt.json"
    qa.write_receipt(path, "a" * 40, "f" * 64, {}, {"entrypoint_sha256": "d", "qa_config_sha256": "e"}, "1" * 64)
    receipt = json.loads(path.read_text())
receipt.pop("checked_at_utc")
print(json.dumps({
    "profile": qa.PROFILE["name"], "project": qa.PROJECT, "ports": qa.PROFILE["ports"],
    "tags": [qa.GAME_TAG, qa.WEB_TAG, qa.BRAIN_IMAGE],
    "receipts": [str(p.relative_to(qa.HERE)) for p in (qa.RECEIPT, qa.UPGRADE_RECEIPT)],
    "argv": calls, "receipt": receipt,
    "stage1_baseline": [s1.GAME, s1.WEB, s1.DATABASE, s1.BRAIN, s1.LEDGER, s1.BRAIN_SOCKET,
                        list(s1.STAGE1), list(s1.STAGE2)],
}, sort_keys=True))
"""
RECEIPT_KEYS = [
    "approved_source_revision",
    "brain_fake",
    "compose_redacted_sha256",
    "entrypoint_sha256",
    "map_sha256",
    "observed_image_ids",
    "project",
    "qa_config_sha256",
    "resources_absent",
    "schema_version",
]
STAGE1_ARGV = ["docker", "compose", "-p", "canary-core-qa", "-f", "compose.yaml"]
STAGE1 = {  # exactly what origin/main derives (README: proof by before/after dump)
    "profile": "stage1",
    "project": "canary-core-qa",
    "ports": {"game": 17172, "login": 17171, "status": 17173, "web": 18080},
    "tags": [
        "canary-core-qa-game:local",
        "canary-core-qa-web:local",
        "canary-core-qa-brain:local",
    ],
    "receipts": [
        "runtime/evidence/preflight-receipt.json",
        "runtime/evidence/stage2-upgrade-receipt.json",
    ],
    "argv": [
        [*STAGE1_ARGV, "--env-file", ".env", "config", "--format", "json"],
        [
            *STAGE1_ARGV,
            "-f",
            "compose.brain-fake.yaml",
            "--env-file",
            ".env",
            "config",
            "--format",
            "json",
        ],
    ],
    "stage1_baseline": [
        "canary-core-qa-game-1",
        "canary-core-qa-web-1",
        "canary-core-qa-database-1",
        "canary-core-qa-brain-1",
        "canary-core-qa_brain-ledger",
        "canary-core-qa_brain-socket",
        [*STAGE1_ARGV, "--env-file", ".env"],
        [*STAGE1_ARGV, "-f", "compose.brain-fake.yaml", "--env-file", ".env"],
    ],
}
B1_ARGV = ["docker", "compose", "-p", "canary-qa-b1", "-f", "compose.yaml"]


def run_profile(code, profile=None, args=None):
    """A fresh interpreter in this directory under CORE_QA_PROFILE=profile (unset for None), without
    docker or git on PATH."""
    env = {key: value for key, value in os.environ.items() if key != "CORE_QA_PROFILE"}
    if profile is not None:
        env["CORE_QA_PROFILE"] = profile
    with tempfile.TemporaryDirectory() as empty:
        env["PATH"] = empty
        argv = [sys.executable, "-B", *(args if args else ["-c", code])]
        return subprocess.run(
            argv,
            cwd=HERE,
            env=env,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )


def dump(profile=None):
    result = run_profile(DUMP, profile)
    if result.returncode:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


def stage1_render():
    """The real stage-1 render (sanitized fixture) with the port values of compose.yaml put back."""
    render = json.loads(RENDER.read_text())
    render["services"]["game"]["environment"].update(
        GAME_LOGIN_PORT="17171", GAME_PROTOCOL_PORT="17172", GAME_STATUS_PORT="17173"
    )
    render["services"]["web"]["environment"].update(
        CANARY_LOGIN_PORT="17171",
        CANARY_GAME_PORT="17172",
        CANARY_STATUS_PORT="17173",
        MYAAC_SITE_URL="http://127.0.0.1:18080",
    )
    return render


def b1_render():
    """That render as compose.b1.yaml and compose.b1-brain.yaml change it."""
    render = json.loads(
        json.dumps(stage1_render()).replace("canary-core-qa_", "canary-qa-b1_")
    )
    render["name"] = "canary-qa-b1"
    services = render["services"]
    services["game"]["environment"].update(
        GAME_LOGIN_PORT="27171", GAME_PROTOCOL_PORT="27172", GAME_STATUS_PORT="27173"
    )
    services["web"]["environment"].update(
        CANARY_LOGIN_PORT="27171",
        CANARY_GAME_PORT="27172",
        CANARY_STATUS_PORT="27173",
        MYAAC_SITE_URL="http://127.0.0.1:28080",
    )
    services["game"]["ports"] = [
        {"host_ip": "127.0.0.1", "published": str(port), "target": port}
        for port in (27171, 27172, 27173)
    ]
    services["web"]["ports"] = [
        {"host_ip": "127.0.0.1", "published": "28080", "target": 80}
    ]
    for name, cpus, memory in (
        ("database", 1, 2),
        ("game", 2, 6),
        ("web", 1, 1),
        ("brain", 0.5, 0.5),
    ):
        services[name].update(cpus=cpus, mem_limit=str(int(memory * 2**30)))
    return render


def fake_docker(objects, images=()):
    """Read-only Docker listings holding objects (kind, name, project, key) and image tags."""
    kinds = {"ps": "container", "volume": "volume", "network": "network"}

    def command(*args, **_kwargs):
        if args[1:3] == ("image", "ls"):
            return "".join(f"{tag}\n" for tag in images)
        kind = kinds[args[1]]
        rows = [item for item in objects if item[0] == kind]
        if "--filter" in args:
            project = args[args.index("--filter") + 1].split("=", 1)[1]
            rows = [item for item in rows if item[2] == project]
        if (
            "\t" in args[-1]
        ):  # stage1_baseline.qa_objects: ID, name, project label, key label
            return "".join(
                f"{name}\t{name}\t{project}\t{key}\n"
                for _kind, name, project, key in rows
            )
        return "".join(f"{item[1]}\n" for item in rows)

    return command


def stack(project, brain=False):
    services = ("database", "game", "web", *(("brain",) if brain else ()))
    volumes = (
        "database",
        "game-logs",
        "authored-data",
        "website-cache",
        *(("brain-socket", "brain-ledger") if brain else ()),
    )
    return (
        [("container", f"{project}-{name}-1", project, name) for name in services]
        + [("volume", f"{project}_{name}", project, name) for name in volumes]
        + [("network", f"{project}_default", project, "default")]
    )


class Stage1DefaultsTests(unittest.TestCase):
    """With CORE_QA_PROFILE unset, stage 1 renders and runs exactly as before."""

    def test_stage1_compose_files_are_the_bytes_the_a1d9_manifest_pins(self):
        pinned = json.loads(MANIFEST.read_text())["bundle_files"]
        for name, expected in STAGE1_COMPOSE_SHA256.items():
            with self.subTest(name):
                actual = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                self.assertEqual(actual, expected)
                self.assertEqual(actual, pinned[name]["sha256"])

    def test_default_profile_derives_exactly_the_stage1_names_argv_and_receipt(self):
        for profile in (None, "stage1"):
            with self.subTest(profile=profile):
                found = dump(profile)
                receipt = found.pop("receipt")
                self.assertEqual(found, STAGE1)
                self.assertEqual(
                    sorted(receipt), RECEIPT_KEYS
                )  # no profile key: the stage-1 receipt is as before
                self.assertEqual(receipt["project"], "canary-core-qa")

    def test_the_real_stage1_render_passes_the_stage1_profile_only(self):
        render = stage1_render()
        preflight.assert_profile_render(render, preflight.load_profile("stage1"))
        with self.assertRaisesRegex(RuntimeError, "is not the b1 project canary-qa-b1"):
            preflight.assert_profile_render(render, preflight.load_profile("b1"))


class B1ProfileTests(unittest.TestCase):
    def test_b1_has_its_own_project_tags_ports_overlays_and_evidence(self):
        found = dump("b1")
        self.assertEqual(found["project"], "canary-qa-b1")
        self.assertEqual(
            found["tags"],
            [
                "canary-qa-b1-game:local",
                "canary-qa-b1-web:local",
                "canary-qa-b1-brain:local",
            ],
        )
        self.assertEqual(
            found["receipts"],
            [
                "runtime/b1/evidence/preflight-receipt.json",
                "runtime/b1/evidence/stage2-upgrade-receipt.json",
            ],
        )
        self.assertEqual(
            found["ports"],
            {"game": 27172, "login": 27171, "status": 27173, "web": 28080},
        )
        self.assertFalse(set(found["ports"].values()) & STAGE1_PORTS)
        self.assertEqual(
            found["argv"],
            [
                [
                    *B1_ARGV,
                    "-f",
                    "compose.b1.yaml",
                    "--env-file",
                    ".env",
                    "config",
                    "--format",
                    "json",
                ],
                [
                    *B1_ARGV,
                    "-f",
                    "compose.brain-fake.yaml",
                    "-f",
                    "compose.b1.yaml",
                    "-f",
                    "compose.b1-brain.yaml",
                    "--env-file",
                    ".env",
                    "config",
                    "--format",
                    "json",
                ],
            ],
        )
        self.assertEqual(
            (found["receipt"]["project"], found["receipt"]["profile"]),
            ("canary-qa-b1", "b1"),
        )
        for name in found["stage1_baseline"][
            :6
        ]:  # derived only; every stage-1 action refuses before using them
            self.assertTrue(name.startswith("canary-qa-b1"))

    def test_b1_never_reuses_the_stage1_identity_of_the_a1d9_manifest(self):
        manifest, b1 = json.loads(MANIFEST.read_text()), preflight.load_profile("b1")
        argv = manifest["render_argv"]
        self.assertEqual(argv[argv.index("-p") + 1], "canary-core-qa")
        self.assertNotEqual(b1["project"], "canary-core-qa")
        self.assertNotEqual(manifest["brain_image"]["tag"], "canary-qa-b1-brain:local")
        self.assertFalse(
            any(name.startswith("canary-qa-b1") for name in manifest["containers"])
        )
        published = {
            int(port["published"])
            for service in json.loads(RENDER.read_text())["services"].values()
            for port in service.get("ports", [])
        }
        self.assertEqual(published, STAGE1_PORTS)
        self.assertFalse(published & set(b1["ports"].values()))
        # Name prefixes are how both gates find their objects: neither project matches the other.
        self.assertFalse(preflight.project_name("canary-qa-b1-game-1"))
        self.assertFalse(preflight.project_name("canary-qa-b1_database"))

    def test_overlays_carry_exactly_the_b1_profile(self):
        text = (HERE / "compose.b1.yaml").read_text()
        brain = (HERE / "compose.b1-brain.yaml").read_text()
        self.assertIn("\nname: canary-qa-b1\n", text)
        bindings = {
            line.strip().removeprefix("- ")
            for line in text.splitlines()
            if "- 127.0.0.1:" in line
        }
        self.assertEqual(
            bindings,
            {
                "127.0.0.1:27171:27171",
                "127.0.0.1:27172:27172",
                "127.0.0.1:27173:27173",
                "127.0.0.1:28080:80",
            },
        )
        self.assertEqual(text.count("ports: !override"), 2)
        values = "".join(
            line for line in (text + brain).splitlines(True) if not line.startswith("#")
        )
        for stage1 in ("1717", "18080", "canary-core-qa"):
            self.assertNotIn(stage1, values)
        for line in (
            "image: canary-qa-b1-game:local",
            "image: canary-qa-b1-web:local",
            "MYAAC_SITE_URL: http://127.0.0.1:28080",
            "GAME_PROTOCOL_PORT: 27172",
            "CANARY_GAME_PORT: 27172",
            "('127.0.0.1',27173)",
        ):
            self.assertIn(line, text)
        self.assertEqual((text.count("cpus:"), text.count("mem_limit:")), (3, 3))
        self.assertIn("image: canary-qa-b1-brain:local", brain)
        self.assertEqual((brain.count("cpus:"), brain.count("mem_limit:")), (1, 1))

    def test_unknown_or_unisolated_profiles_are_refused(self):
        with self.assertRaisesRegex(RuntimeError, "unknown CORE_QA_PROFILE 'b2'"):
            preflight.load_profile("b2")
        result = run_profile("import preflight", "b2")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown CORE_QA_PROFILE 'b2'", result.stderr)
        b1 = preflight.PROFILES["b1"]
        for name, change in (
            ("prefix", {"project": "canary-core-qa-b1"}),
            ("port", {"ports": {**b1["ports"], "web": 18080}}),
            ("evidence", {"evidence": "runtime/evidence"}),
            ("overlay", {"overlays": ()}),
        ):
            with (
                self.subTest(name),
                patch.dict(preflight.PROFILES, {"b1": {**b1, **change}}),
                self.assertRaisesRegex(RuntimeError, "not isolated from stage 1"),
            ):
                preflight.load_profile("b1")


class CrossUseTests(unittest.TestCase):
    """A B1 profile never acts on stage 1, and stage 1 never acts on B1."""

    def test_each_profile_refuses_the_render_of_the_other(self):
        stage1, b1 = preflight.load_profile("stage1"), preflight.load_profile("b1")
        preflight.assert_profile_render(b1_render(), b1)
        with self.assertRaisesRegex(
            RuntimeError, "is not the stage1 project canary-core-qa"
        ):
            preflight.assert_profile_render(b1_render(), stage1)
        merged = (
            b1_render()
        )  # an old Compose merging the port lists instead of honouring !override
        merged["services"]["game"]["ports"] += stage1_render()["services"]["game"][
            "ports"
        ]
        unlimited = b1_render()
        del unlimited["services"]["brain"]["mem_limit"]
        advertised = b1_render()
        advertised["services"]["web"]["environment"]["CANARY_GAME_PORT"] = "17172"
        listening = b1_render()
        listening["services"]["game"]["environment"]["GAME_PROTOCOL_PORT"] = "17172"
        remapped = b1_render()
        remapped["services"]["game"]["ports"][1]["target"] = 17172
        for name, render, message in (
            ("merged stage-1 ports", merged, "game publishes 17171, not a b1 port"),
            ("no limits", unlimited, "needs CPU and memory limits on brain"),
            (
                "stage-1 advertised port",
                advertised,
                "web CANARY_GAME_PORT differ from profile b1",
            ),
            (
                "stage-1 listener",
                listening,
                "game GAME_PROTOCOL_PORT differ from profile b1",
            ),
            (
                "published to another port",
                remapped,
                "game publishes 27172, not a b1 port",
            ),
        ):
            with self.subTest(name), self.assertRaisesRegex(RuntimeError, message):
                preflight.assert_profile_render(render, b1)

    def test_b1_refuses_every_stage1_baseline_action_before_docker(self):
        with tempfile.TemporaryDirectory() as directory:
            historical = Path(directory) / "web-rollout-after.json"
            historical.write_text("{}")
            for args in (
                ["stage1_baseline.py", "check"],
                ["stage1_baseline.py", "rollback"],
                ["stage1_baseline.py", "verify-restored"],
                [
                    "stage1_baseline.py",
                    "capture",
                    "--historical-receipt",
                    str(historical),
                ],
                [
                    "preflight.py",
                    "--upgrade-from-stage1",
                    "--approved-revision",
                    "0" * 40,
                ],
                [
                    "preflight.py",
                    "--capture-stage1-baseline",
                    "--historical-receipt",
                    str(historical),
                ],
            ):
                with self.subTest(args=args):
                    result = run_profile(None, "b1", args)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(REFUSED_STAGE1, result.stderr)
                    self.assertNotIn(
                        "FileNotFoundError", result.stderr
                    )  # never reached docker or git
            stage1 = run_profile(
                None, None, ["stage1_baseline.py", "check"]
            )  # stage 1 gets past the baseline
            self.assertNotIn(REFUSED_STAGE1, stage1.stderr)
            self.assertIn("FileNotFoundError", stage1.stderr)

    def test_b1_handoff_refuses_the_pinned_stage1_manifest(self):
        code = f"""
import hashlib
from pathlib import Path
from unittest.mock import patch
import stage2_handoff as handoff
adapter = Path(handoff.__file__).read_bytes()
with patch("stage2_handoff.git_blob", return_value=adapter):
    try:
        handoff.Handoff(Path({str(REPO)!r}), Path({str(MANIFEST)!r}), handoff.MANIFEST_SHA256, None,
                        hashlib.sha256(adapter).hexdigest(), "f" * 40)
    except RuntimeError as error:
        print("refused:", error)
"""
        refused = run_profile(code, "b1")
        self.assertEqual(
            refused.stdout.strip(), f"refused: {REFUSED_STAGE1}", refused.stderr
        )
        # The managed return builds this same Handoff before any gate, so it refuses with it.
        self.assertIn(
            "handoff = adapter.Handoff(", (HERE / "qa_return_attempt.py").read_text()
        )

    def test_receipts_of_one_project_are_refused_by_the_other(self):
        code = """
import json, sys
from pathlib import Path
import preflight
path = Path(sys.argv[1])
owner = {"project": sys.argv[2]} if sys.argv[2] else {}  # none: a receipt from before profiles, stage 1's
path.write_text(json.dumps({**owner, "approved_source_revision": "a" * 40}))
preflight.assert_source = lambda revision: revision
try:
    preflight.record_brain_image("a" * 40, path)
except RuntimeError as error:
    print("refused:", error)
"""
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "stage2-upgrade-receipt.json")
            for profile, owner, project in (
                (None, "canary-qa-b1", "canary-core-qa"),
                ("b1", "canary-core-qa", "canary-qa-b1"),
                ("b1", "", "canary-qa-b1"),
            ):
                with self.subTest(profile=profile, owner=owner):
                    result = run_profile(None, profile, ["-c", code, path, owner])
                    self.assertEqual(
                        result.stdout.strip(),
                        f"refused: receipt stage2-upgrade-receipt.json is not "
                        f"of project {project}; refused",
                        result.stderr,
                    )

    def test_a_running_b1_is_invisible_to_the_stage1_gates_and_vice_versa(self):
        b1, live = stack("canary-qa-b1", brain=True), stack("canary-core-qa")
        b1_images = [
            "canary-qa-b1-game:local",
            "canary-qa-b1-web:local",
            "canary-qa-b1-brain:local",
        ]
        stage1_images = ["canary-core-qa-game:local", "canary-core-qa-web:local"]
        if preflight.PROFILE["name"] != "stage1":
            self.skipTest("this interpreter runs another CORE_QA_PROFILE")
        with patch(
            "preflight.command",
            side_effect=fake_docker(live + b1, stage1_images + b1_images),
        ):
            found = stage1_baseline.qa_objects()
            stage1_baseline.assert_images(brain_allowed=False)
        self.assertEqual(
            found["container"],
            {f"canary-core-qa-{s}-1" for s in ("database", "game", "web")},
        )
        self.assertFalse(
            any("b1" in name for names in found.values() for name in names)
        )
        with patch("preflight.command", side_effect=fake_docker(b1, b1_images)):
            preflight.assert_no_resources(
                True
            )  # stage 1 may still be installed fresh next to B1
        code = """
import json, sys
from unittest.mock import patch
import preflight
from test_b1_profile import fake_docker
objects, images = json.loads(sys.argv[1])
with patch("preflight.command", side_effect=fake_docker([tuple(item) for item in objects], images)):
    try:
        preflight.assert_no_resources(True)
        print("clean")
    except RuntimeError as error:
        print("refused:", error)
"""
        for objects, images, expected in (
            (live, stage1_images, "clean"),  # the live stage 1 is not B1's
            (
                live + b1[:1],
                stage1_images,
                EXISTING + "container:canary-qa-b1-database-1",
            ),
            (
                live,
                stage1_images + b1_images[2:],
                EXISTING + "image:canary-qa-b1-brain:local",
            ),
        ):
            with self.subTest(expected=expected):
                result = run_profile(
                    None, "b1", ["-c", code, json.dumps([objects, images])]
                )
                self.assertEqual(result.stdout.strip(), expected, result.stderr)


if __name__ == "__main__":
    unittest.main()
