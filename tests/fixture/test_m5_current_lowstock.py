"""The separate supply goal cannot pass from phase names or purchase alone."""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from canary_brain.controller import Controller
from canary_brain.runtime import FakeProvider
from canary_brain.store import Store
from m5_current_lowstock import (
    cleanup_evidence,
    derive_lowstock,
    disable_recovery,
    goal_checks,
    native_build_contract,
)


class LowStockGoalTests(unittest.TestCase):
    def test_supply_derivative_freezes_empty_hunt_mask_and_preserves_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            parent = root / "parent"
            (parent / "authored").mkdir(parents=True)
            (parent / "authored/hunt_scripts.csv").write_text(
                "id,name,enabled,min_level\n77,Wasp,1,8\n399,Paw,1,8\n1,Other,0,25\n"
            )
            (parent / "database.sql").write_text("-- frozen database\n")
            (parent / "character.json").write_text('{"health":365,"bank":10000}')
            before = {
                p.relative_to(parent): p.read_bytes()
                for p in parent.rglob("*")
                if p.is_file()
            }
            result = derive_lowstock(parent, root / "derivative")
            self.assertEqual(result["changes"]["hunt_mask_before"], ["77", "399"])
            self.assertEqual(result["changes"]["hunt_mask_after"], [])
            self.assertEqual(
                (root / "derivative/authored/hunt_scripts.csv").read_text(),
                "id,name,enabled,min_level\n77,Wasp,0,8\n399,Paw,0,8\n1,Other,0,25\n",
            )
            self.assertIn("SET count=1", (root / "derivative/database.sql").read_text())
            self.assertEqual(
                (root / "derivative/character.json").read_bytes(),
                before[Path("character.json")],
            )
            self.assertEqual(
                {
                    p.relative_to(parent): p.read_bytes()
                    for p in parent.rglob("*")
                    if p.is_file()
                },
                before,
            )

    def checks(self, purchase=True, returned=True, interventions=0, recoveries=0):
        return goal_checks(
            {"bank": 10000, "potions": 2},
            {"bank": 7986, "potions": 40},
            {"posx": 32371, "posy": 32238, "posz": 7},
            {"posx": 32369, "posy": 32241, "posz": 7},
            {"status": "completed", "metrics": {"supply_delta": 38}}
            if purchase
            else {},
            {"status": "completed", "reason": "party_rejoined"} if returned else {},
            {
                "gaps": 0,
                "deaths": 0,
                "interventions": interventions,
                "automatic_recoveries_requested": recoveries,
            },
            0,
        )

    def test_authoritative_purchase_return_and_saved_state_pass(self):
        self.assertTrue(all(self.checks().values()))

    def test_purchase_alone_is_not_completed_return(self):
        self.assertFalse(all(self.checks(returned=False).values()))

    def test_return_without_observed_purchase_is_not_accepted(self):
        self.assertFalse(all(self.checks(purchase=False).values()))

    def test_operator_rescue_cannot_qualify(self):
        self.assertFalse(all(self.checks(interventions=1).values()))

    def test_automatic_recovery_cannot_qualify(self):
        self.assertFalse(all(self.checks(recoveries=1).values()))

    def test_proof_disables_and_persists_automatic_recovery_before_observations(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = Store(Path(temporary) / "worker.sqlite3")
            controller = Controller(store, FakeProvider(), lambda _: None)
            self.assertTrue(controller.supervisor.state(65001)["automatic"])
            disable_recovery(controller)
            self.assertFalse(controller.supervisor.state(65001)["automatic"])
            self.assertFalse(store.get("supervision", "65001")["automatic"])

    def test_native_revision_is_bound_to_freeze(self):
        revision = "a" * 40
        binaries = {"canary": "b" * 64, "libbot_engine.so": "c" * 64}
        frozen = {
            "image_id": "sha256:" + "d" * 64,
            "native_build": {
                "source_revision": revision,
                "archive_sha256": "e" * 64,
                "binary_sha256": binaries,
            },
        }
        self.assertEqual(
            native_build_contract(frozen, revision, frozen["image_id"]), binaries
        )
        with self.assertRaises(AssertionError):
            native_build_contract(frozen, "f" * 40, frozen["image_id"])

    @patch("m5_current_lowstock.subprocess.check_output")
    def test_cleanup_requires_both_scoped_inspections_empty(self, output):
        output.side_effect = ["", "abc canary-bench-identity_default\n"]
        self.assertFalse(cleanup_evidence("canary-bench-identity")["resources_cleaned"])
        for call in output.call_args_list:
            self.assertIn(
                "label=com.docker.compose.project=canary-bench-identity", call.args[0]
            )
        output.side_effect = ["", ""]
        self.assertTrue(cleanup_evidence("canary-bench-identity")["resources_cleaned"])

    @unittest.skipUnless(os.name == "posix", "fake Docker executable is Linux/WSL")
    def test_hung_cleanup_cli_returns_failed_evidence_and_reaps_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "docker"
            pid_file = root / "child.pid"
            executable.write_text(
                "#!" + sys.executable + "\n"
                "import os,time\nfrom pathlib import Path\n"
                "Path(os.environ['FAKE_DOCKER_PID']).write_text(str(os.getpid()))\n"
                "time.sleep(10)\n"
            )
            executable.chmod(0o700)
            started = time.monotonic()
            with patch.dict(
                os.environ, {"PATH": str(root), "FAKE_DOCKER_PID": str(pid_file)}
            ):
                result = cleanup_evidence(
                    "canary-bench-never-a-real-project", timeout=0.2
                )
            self.assertLess(time.monotonic() - started, 2)
            self.assertFalse(result["resources_cleaned"])
            self.assertEqual(result["inspection_error"], "TimeoutExpired")
            with self.assertRaises(ProcessLookupError):
                os.kill(int(pid_file.read_text()), 0)

    @unittest.skipUnless(
        os.name == "posix", "invalid cwd regression uses Linux semantics"
    )
    def test_cleanup_cli_succeeds_when_parent_working_directory_is_unlinked(self):
        """Exercise the CLI from a genuinely invalid inherited cwd, without Docker."""
        code = """
import json,os,sys
from pathlib import Path
from m5_current_lowstock import cleanup_evidence
directory=Path(sys.argv[1]); directory.mkdir()
os.chdir(directory); directory.rmdir()
try:
    os.getcwd()
except FileNotFoundError:
    invalid=True
else:
    invalid=False
print(json.dumps({'invalid_parent_cwd':invalid,'cleanup':cleanup_evidence('canary-bench-no-real-runtime',timeout=2)}))
"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "docker"
            cwd_log = root / "cli-cwd.jsonl"
            executable.write_text(
                "#!" + sys.executable + "\nimport json,os\nfrom pathlib import Path\n"
                "with Path(os.environ['FAKE_DOCKER_CWD_LOG']).open('a') as stream:\n"
                "    stream.write(json.dumps({'cwd':os.getcwd()})+'\\n')\n"
            )
            executable.chmod(0o700)
            completed = subprocess.run(
                [sys.executable, "-c", code, str(root / "removed-cwd")],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
                env={
                    **os.environ,
                    "PATH": str(root),
                    "FAKE_DOCKER_CWD_LOG": str(cwd_log),
                    "PYTHONPATH": os.pathsep.join(sys.path),
                },
            )
            result = json.loads(completed.stdout)
            self.assertTrue(result["invalid_parent_cwd"])
            self.assertTrue(result["cleanup"]["resources_cleaned"])
            self.assertEqual(
                [json.loads(line)["cwd"] for line in cwd_log.read_text().splitlines()],
                ["/", "/"],
            )

    @unittest.skipUnless(os.name == "posix", "campaign runtime is Linux/WSL")
    def test_sigterm_reaches_executor_finally(self):
        """A real signal must stop an externally supplied Event and reach cleanup."""
        code = """
import asyncio, json, os, signal, sys
from pathlib import Path
from m5_current_lowstock import run_with_signals
async def executor(args, stopped):
    try:
        asyncio.get_running_loop().call_later(0.01, os.kill, os.getpid(), signal.SIGTERM)
        await asyncio.wait_for(stopped.wait(), timeout=2)
    finally:
        Path(sys.argv[1]).write_text(json.dumps({'stopped': stopped.is_set(), 'cleanup': True}))
asyncio.run(run_with_signals(None, executor))
"""
        with tempfile.TemporaryDirectory() as temporary:
            result = Path(temporary) / "result.json"
            subprocess.run(
                [sys.executable, "-c", code, str(result)],
                check=True,
                env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
                timeout=5,
            )
            self.assertEqual(
                json.loads(result.read_text()), {"stopped": True, "cleanup": True}
            )


if __name__ == "__main__":
    unittest.main()
