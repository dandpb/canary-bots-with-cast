import importlib.util
from pathlib import Path


def test_monitor_detects_retreat_stall_despite_xp_and_brief_renewal():
    path = Path(__file__).resolve().parents[2] / "wsl" / "monitor-bot.py"
    spec = importlib.util.spec_from_file_location("monitor_bot", path)
    assert spec and spec.loader
    monitor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(monitor)
    rows = [
        {
            "timestamp": t,
            "world": "a",
            "worker_alive": True,
            "observation_age_seconds": 1,
            "running": True,
            "objective": "follow" if t == 150 else "retreat",
            "position": [100 + t % 2, 100, 7],
            "xp": 1000 + t,
        }
        for t in range(0, 301, 30)
    ]
    assert monitor.assess(rows) == "suspected_retreat_navigation_stall_5_minutes"
    rows[-1]["position"] = [105, 100, 7]
    assert monitor.assess(rows) == "progress_observed"
