"""Exercise the operational digest's application-log date contract without Docker."""

import importlib.util
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

FILE = Path(__file__).resolve().parents[2] / "wsl/ops-digest.py"
SPEC = importlib.util.spec_from_file_location("ops_digest", FILE)
assert SPEC is not None and SPEC.loader is not None
DIGEST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DIGEST)


@pytest.mark.parametrize(
    ("stamp", "expected"),
    [
        ("2026-08-11 11:38:03", datetime(2026, 11, 8, 11, 38, 3)),
        ("2026-27-11 12:00:00", datetime(2026, 11, 27, 12)),
        ("2026-01-12 00:00:00", datetime(2026, 12, 1)),
        ("2026-31-12 23:59:59", datetime(2026, 12, 31, 23, 59, 59)),
    ],
)
def test_canary_logger_uses_year_day_month(stamp, expected):
    assert DIGEST.app_time(f"[{stamp}.123] [info] message") == expected


def test_invalid_application_month_is_rejected():
    assert DIGEST.app_time("[2026-01-13 00:00:00.000] [info] invalid") is None


def test_month_boundary_log_window_keeps_only_current_minute():
    lines = (
        "[2026-30-11 23:50:00.000] [error] old\n"
        "[2026-30-11 23:59:40.000] [info] failed=0\n"
        "[2026-01-12 00:00:00.000] [warning] current"
    )
    with patch.object(DIGEST, "run", return_value=(lines, "", 0)) as command:
        report, error = DIGEST.scan_logs(
            {"game": {"container": "fake-game"}}, "game", 60
        )
    assert error is None
    assert report["lines_in_window"] == 2
    assert report["error_lines"] == 0
    assert report["warning_lines"] == 1
    assert report["log_clock"]["newest_entry"] == "2026-12-01T00:00:00"
    assert command.call_args.args[0] == [
        "docker",
        "logs",
        "--tail",
        "5000",
        "fake-game",
    ]
