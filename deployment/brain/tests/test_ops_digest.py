"""Exercise the operational digest's application-log date contract without Docker."""

import importlib.util
from datetime import UTC, datetime
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
        "--timestamps",
        "--tail",
        "5000",
        "fake-game",
    ]


def test_worker_fatal_stderr_is_counted_using_docker_utc_time():
    stderr = "2026-11-08T12:03:07.198960060Z Companion service stopped: RuntimeError\n"
    with patch.object(DIGEST, "run", return_value=("", stderr, 0)):
        report, error = DIGEST.scan_logs(
            {"brain": {"container": "fake-brain"}}, "brain", 60
        )
    assert error is None
    assert report["error_lines"] == 1
    assert report["lines_in_window"] == 1
    assert report["log_clock"]["newest_entry"] == "2026-11-08T12:03:07.198960"


def test_unscannable_worker_failure_degrades_collector_instead_of_zero_errors():
    with patch.object(
        DIGEST, "run", return_value=("", "Companion service stopped: RuntimeError\n", 0)
    ):
        report, error = DIGEST.scan_logs(
            {"brain": {"container": "fake-brain"}}, "brain", 60
        )
    assert report is None
    assert "timestamp" in error


def healthy_report():
    return {
        "services": [
            {"service": "game", "state": "running", "health": "healthy", "restarts": 0}
        ],
        "warnings": [],
        "status": {"players_online": 997},
        "grizzle_live": {
            "xp": 100,
            "level": 2,
            "last_observation": datetime.now(UTC).timestamp(),
        },
        "grizzle_persisted": {"experience": 100, "level": 2},
    }


def test_persisted_read_failure_cannot_report_green():
    assert DIGEST.evaluate(healthy_report())["verdict"] == "GREEN"
    report = healthy_report()
    report["grizzle_persisted"] = None
    report["warnings"] = ["persisted player row unreadable: access denied"]
    assert DIGEST.evaluate(report)["verdict"] == "AMBER"


@pytest.mark.parametrize("key", ["last_observation", "xp", "level"])
def test_missing_live_progress_evidence_cannot_report_green(key):
    report = healthy_report()
    del report["grizzle_live"][key]
    assert DIGEST.evaluate(report)["verdict"] == "AMBER"
