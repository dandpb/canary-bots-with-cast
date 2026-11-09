"""Offline save-health log contracts; all transport is stubbed."""
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

FILE = Path(__file__).resolve().parents[2] / "wsl/ops-digest.py"
SPEC = importlib.util.spec_from_file_location("ops_digest_save_messages", FILE)
DIGEST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DIGEST)


def scan(messages):
    lines="\n".join(f"[2026-09-11 01:00:{i:02d}.000] [info] {text}" for i,text in enumerate(messages))
    with patch.object(DIGEST,"run",return_value=(lines,"",0)):
        report,error=DIGEST.scan_logs({"game":{"container":"offline-placeholder"}},"game",60)
    assert error is None
    return report


@pytest.mark.parametrize("messages,count,duration",[
    (["Captured 999 players for server save in 4 milliseconds", "Server saved 100 players in 847.417 milliseconds"],100,847.417),
    (["Captured 100 players for server save in 4 milliseconds", "Server saved 0 players in 2 milliseconds"],0,2.0),
    (["Server saved 7 players in 12 milliseconds"],7,12.0),
    (["Saving 12 players", "Players saved in 4.5 milliseconds"],12,4.5),
    (["Saving 0 players", "Players saved in 3 milliseconds"],0,3.0),
    (["Captured 12 players for server save in 1 milliseconds"],None,None),
    (["Saving 12 players"],None,None),
    (["ordinary checkpoint activity"],None,None),
    (["Players saved in 3 milliseconds"],None,3.0),
    (["Saving 9 players", "Players saved in 3 milliseconds", "Captured 200 players for server save in 1 milliseconds"],9,3.0),
    (["Saving 9 players", "Players saved in 3 milliseconds", "Server saved 2 players in 7 milliseconds"],2,7.0),
    (["Server saved 2 players in 7 milliseconds", "Saving 5 players", "Players saved in 3 milliseconds"],5,3.0),
])
def test_completion_is_authoritative_and_legacy_remains_supported(messages,count,duration):
    health=scan(messages)["save_health"]
    assert health["last_save_count"] == count
    assert health["last_save_milliseconds"] == duration


def test_capture_is_separate_from_success():
    health=scan(["Captured 100 players for server save in 1 milliseconds"])["save_health"]
    assert health["last_capture_count"] == 100
    assert health["last_save_count"] is None


def test_outside_window_completion_cannot_be_reused():
    lines=("[2026-09-11 00:00:00.000] [info] Server saved 0 players in 3 milliseconds\n"
           "[2026-09-11 01:00:00.000] [info] Captured 100 players for server save in 1 milliseconds")
    with patch.object(DIGEST,"run",return_value=(lines,"",0)):
        report,error=DIGEST.scan_logs({"game":{"container":"offline-placeholder"}},"game",60)
    assert error is None
    assert report["save_health"]["last_save_count"] is None


def test_real_zero_completion_reaches_warning():
    report={"services":[],"warnings":[],"status":{"players_online":100},
            "logs":{"game":scan(["Server saved 0 players in 2 milliseconds"])}}
    result=DIGEST.evaluate(report)
    assert result["verdict"] != "GREEN"
    assert any("zero" in item.lower() or "0 players" in item.lower() for item in result["findings"])
