"""Gameplay rates use elapsed recording time, independent of calendar adjustments."""

import pytest
from test_protocol import observation

from canary_brain.replay import summarize


def sample(at, xp, wall, segment="a"):
    data = observation()
    data["bot"]["xp"] = xp
    return {
        "kind": "sample",
        "t_ms": at,
        "wall": wall,
        "segment": segment,
        "data": data,
    }


@pytest.mark.parametrize("calendar_adjustment", [3600, -3600])
def test_xp_rate_does_not_change_when_the_calendar_clock_is_adjusted(
    calendar_adjustment,
):
    events = [
        sample(
            index * 2500,
            1000 + 25 * index,
            10000 + 2.5 * index + (calendar_adjustment if index >= 2 else 0),
        )
        for index in range(5)
    ]
    metrics = summarize(events, {"provider": "native"})
    assert metrics["version"] == 2
    assert metrics["wall_ms"] == metrics["active_ms"] == 10000
    assert metrics["xp_per_wall_hour"] == metrics["xp_per_active_hour"] == 36000
    assert metrics["calendar_elapsed_ms"] == (10 + calendar_adjustment) * 1000


def test_elapsed_rate_includes_recorded_restart_gap_but_active_rate_excludes_it():
    events = [
        sample(0, 1000, 10000),
        sample(1000, 1010, 10001),
        {"kind": "gap", "t_ms": 10000, "data": {"reason": "worker_restart"}},
        sample(11000, 1110, 13611, "b"),
        sample(12000, 1120, 13612, "b"),
    ]
    metrics = summarize(events, {"provider": "native"})
    assert metrics["wall_ms"] == 12000
    assert metrics["active_ms"] == 2000
    assert metrics["xp_per_wall_hour"] == 36000
    assert metrics["calendar_elapsed_ms"] == 3612000
