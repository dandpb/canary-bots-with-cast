"""A saved/closed attempt is not accepted unless every evidence gate passes."""

import copy
import json
import runpy
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class FinalizationTests(unittest.TestCase):
    def test_each_failed_gate_rejects_completion_and_returns_nonzero(self):
        baseline = {
            "run_id": "fixture",
            "observed_seconds": 1800,
            "metrics": {"gaps": 0, "xp_delta": 10},
            "last_sample": {"data": {"bot": {"xp": 110}}},
            "ledger": {"requests": 0},
        }
        for fault in [None, "gap", "short", "xp", "save", "request", "stop"]:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary)
                data = copy.deepcopy(baseline)
                result = {
                    "phase": "finished",
                    "stop": {"reason": "completed"},
                    "saved_character": {"experience": 110},
                }
                if fault == "gap":
                    data["metrics"]["gaps"] = 1
                if fault == "short":
                    data["observed_seconds"] = 1700
                if fault == "xp":
                    data["metrics"]["xp_delta"] = 0
                if fault == "save":
                    result["saved_character"]["experience"] = 109
                if fault == "request":
                    data["ledger"]["requests"] = 1
                if fault == "stop":
                    result["stop"]["reason"] = "runtime_ended"
                (work / "result.json").write_text(json.dumps(result))
                statuses = []
                store = types.SimpleNamespace(
                    finish=lambda identity, status, saved=statuses: saved.append(status)
                )
                with (
                    patch.dict(
                        sys.modules,
                        {
                            "m5_report": types.SimpleNamespace(
                                report=lambda _, saved=data: saved
                            )
                        },
                    ),
                    patch("canary_brain.recording.RecordingStore", return_value=store),
                    patch.object(sys, "argv", ["finalizer", str(work)]),
                ):
                    if fault:
                        with self.assertRaises(SystemExit) as raised:
                            runpy.run_path(
                                str(Path(__file__).with_name("m5_finalize.py")),
                                run_name="__main__",
                            )
                        self.assertEqual(raised.exception.code, 1)
                    else:
                        runpy.run_path(
                            str(Path(__file__).with_name("m5_finalize.py")),
                            run_name="__main__",
                        )
                self.assertEqual(statuses, ["failed" if fault else "completed"])


if __name__ == "__main__":
    unittest.main()
