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
            "ledger": {"requests": 0, "spent_nanousd": 0, "reserved_nanousd": 0},
            "recording_incomplete": False,
            "progression": {
                "window": {"native_seconds": 1800, "xp_delta": 10},
                "errors": [],
            },
        }
        for fault in [
            None,
            "gap",
            "short",
            "native_short",
            "xp",
            "save",
            "request",
            "stop",
            "incomplete",
            "reserved",
            "missing",
        ]:
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
                    data["progression"]["window"]["xp_delta"] = 0
                if fault == "save":
                    data["progression"]["errors"] = ["saved_progress_mismatch"]
                if fault == "request":
                    data["ledger"]["requests"] = 1
                if fault == "native_short":
                    data["progression"]["window"]["native_seconds"] = 1799.999
                if fault == "incomplete":
                    data["recording_incomplete"] = True
                if fault == "reserved":
                    data["ledger"]["reserved_nanousd"] = 1
                if fault == "missing":
                    data.pop("progression")
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


def test_real_sqlite_report_and_finalizer_keep_window_and_saved_progress_separate(
    tmp_path,
):
    """Exercise both fixture scripts against new isolated SQLite files."""
    import importlib.util
    import sqlite3

    from canary_brain.recording import Manifest, RecordingStore

    spec = importlib.util.spec_from_file_location(
        "fixture_report_integration", Path(__file__).with_name("m5_report.py")
    )
    fixture_report = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture_report)
    store = RecordingStore(tmp_path / "recording.sqlite3")
    store.begin(Manifest(run_id="fixture", bot_id=7, lineage="qa", provider="native"))
    bot = {
        "id": 7,
        "level": 20,
        "xp": 100,
        "position": [1, 2, 7],
        "health": 100,
        "mana": 100,
        "potions": 40,
        "alive": True,
        "name": "QA",
        "state": "HUNTING",
        "vocation": 4,
    }

    def append(key, kind, t_ms, data):
        store.append(
            {
                "run": "fixture",
                "key": key,
                "segment": "one",
                "kind": kind,
                "t_ms": t_ms,
                "wall": 1 + t_ms / 1000,
                "data": data,
            }
        )

    first = {
        "world": "qa",
        "sequence": 1,
        "captured_ms": 1000,
        "bot": bot,
        "actions": [],
    }
    end = copy.deepcopy(first)
    end.update(sequence=1801, captured_ms=1801000)
    end["bot"]["xp"] = 110
    later = copy.deepcopy(end)
    later.update(sequence=1802, captured_ms=1801500)
    later["bot"].update(xp=150, level=21)
    append("first", "sample", 0, first)
    append(
        "death-baseline",
        "lifecycle",
        0,
        {
            "world": "qa",
            "captured_ms": 1000,
            "deaths": 0,
            "phase": "alive",
        },
    )
    append("horizon-final-sample", "sample", 1800000, end)
    append(
        "later", "lifecycle", 1800500, {"phase": "post_horizon_sample", "data": later}
    )
    with sqlite3.connect(tmp_path / "worker.sqlite3") as db:
        db.execute("CREATE TABLE requests(spent INTEGER, reserved INTEGER)")
    result = {
        "phase": "finished",
        "stop": {"reason": "completed"},
        "initial_character": {"id": 7, "experience": 100, "level": 20},
    }
    producer_spec = importlib.util.spec_from_file_location(
        "fixture_producer_integration", Path(__file__).with_name("m5_qa.py")
    )
    producer = importlib.util.module_from_spec(producer_spec)
    producer_spec.loader.exec_module(producer)
    calls = []

    class Harness:
        def stop_game(self):
            calls.append("stop")

        def character(self):
            calls.append("sql")
            return {"id": 7, "experience": 150, "level": 21}

    def clock():
        calls.append("clock")
        return next(times)

    times = iter([1801.6, 1802, 1802.5, 1803])
    with patch.object(producer.time, "time", side_effect=clock):
        saved, receipt = producer.stop_and_read_character(Harness(), tmp_path)
    assert calls == ["clock", "stop", "clock", "clock", "sql", "clock"]
    assert receipt == {
        "world": "qa",
        "bot_id": 7,
        "game_stop_started_wall": 1801.6,
        "game_stopped_wall": 1802,
        "sql_read_started_wall": 1802.5,
        "sql_read_wall": 1803,
    }
    result.update(saved_character=saved, persistence=receipt)
    (tmp_path / "result.json").write_text(json.dumps(result))
    report = fixture_report.report(tmp_path)
    assert report["progression"]["window"]["xp_delta"] == 10
    assert report["metrics"]["xp_delta"] == 10
    assert report["progression"]["window"]["final_level"] == 20
    assert report["progression"]["final_saved_character"]["level"] == 21
    assert report["progression"]["errors"] == []
    with (
        patch.dict(sys.modules, {"m5_report": fixture_report}),
        patch.object(sys, "argv", ["finalizer", str(tmp_path)]),
    ):
        runpy.run_path(
            str(Path(__file__).with_name("m5_finalize.py")), run_name="__main__"
        )
    analysis = json.loads((tmp_path / "analysis.json").read_text())
    assert analysis["timed_gate_passed"]
    assert analysis["progression"]["window"]["native_seconds"] == 1800


def test_failed_stop_or_sql_operation_cannot_emit_a_receipt(tmp_path):
    import importlib.util

    import pytest

    spec = importlib.util.spec_from_file_location(
        "fixture_producer_failure", Path(__file__).with_name("m5_qa.py")
    )
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    for failing_operation in ("stop", "sql"):
        calls = []

        class Harness:
            def stop_game(self, calls=calls, failing_operation=failing_operation):
                calls.append("stop")
                if failing_operation == "stop":
                    raise RuntimeError("stop failed")

            def character(self, calls=calls):
                calls.append("sql")
                raise RuntimeError("sql failed")

        with pytest.raises(RuntimeError, match=f"{failing_operation} failed"):
            producer.stop_and_read_character(Harness(), tmp_path)
        assert calls == (["stop"] if failing_operation == "stop" else ["stop", "sql"])
    assert not list(tmp_path.iterdir())
