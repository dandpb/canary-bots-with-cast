import hashlib
import json
import shutil
import subprocess

import pytest
from test_protocol import observation

from canary_brain.benchmark import demo
from canary_brain.recording import ReplayReader
from canary_brain.timelapse import Projection, export_video


def sample(at=0):
    return {"t_ms": at, "kind": "sample", "data": observation()}


def metadata():
    return {"manifest": {"participant": "fixture", "model": "fake", "synthetic": True}}


def test_video_holds_only_observed_state_and_marks_gaps_without_interpolation():
    projection = Projection(1000)
    projection.apply(sample())
    projection.apply({"t_ms": 1000, "kind": "gap", "data": {"reason": "missing"}})
    image = projection.frame(metadata(), 1500, 0, 5000, {7: [99, 99, 103, 103]})
    assert "GAP / last known state" in image and "SIMULATED FIXTURE" in image
    assert "XP  1000" in image and projection.bot.position == [100, 100, 7]
    resumed = sample(5000)
    resumed["data"]["bot"]["position"] = [103, 103, 8]
    projection.apply(resumed)
    image = projection.frame(metadata(), 5000, 0, 5000, {8: [103, 103, 103, 103]})
    assert "Observed sample" in image and "Floor 8" in image
    assert (
        "polyline" not in image
    )  # No invented line through an unobserved floor change.


def test_video_deduplicates_settled_cost_and_escapes_recorded_text():
    projection = Projection(1000)
    projection.apply(sample())
    for values in [
        {"reserved_nanousd": 100},
        {"spent_nanousd": 30, "reserved_nanousd": 0},
        {"spent_nanousd": 30, "reserved_nanousd": 0},
    ]:
        projection.apply(
            {"t_ms": 0, "kind": "request", "data": {"request_id": "same", **values}}
        )
    assert projection.spent == 30 and projection.reserved == 0
    projection.apply(
        {
            "t_ms": 0,
            "kind": "operator",
            "data": {"phase": '<image href="http://invalid"/>'},
        }
    )
    image = projection.frame(metadata(), 0, 0, 0, {7: [100, 100, 100, 100]})
    assert "&lt;image" in image and "<image" not in image


def has_renderer():
    return (
        shutil.which("ffmpeg")
        and shutil.which("ffprobe")
        and "librsvg"
        in subprocess.check_output(
            ["ffmpeg", "-hide_banner", "-decoders"], stderr=subprocess.DEVNULL
        ).decode()
    )


@pytest.mark.skipif(
    not has_renderer(), reason="ffmpeg with librsvg and ffprobe required"
)
def test_real_encoder_frames_duration_and_provenance_match_recorded_data(tmp_path):
    recording = tmp_path / "recording.db"
    run = demo(recording)[0]
    video = tmp_path / "clip.mp4"
    before = recording.read_bytes()
    result = export_video(
        ReplayReader(recording), run, video, speed=5, fps=2, end_ms=10000
    )
    assert result["frames"] == 4 and result["video_seconds"] == 2
    assert result["manifest"]["synthetic"] and result["source_events"] > 0
    assert result["video_sha256"] == hashlib.sha256(video.read_bytes()).hexdigest()
    assert json.loads(video.with_suffix(".mp4.json").read_text()) == result
    assert recording.read_bytes() == before
    with pytest.raises(ValueError, match="new .mp4"):
        export_video(ReplayReader(recording), run, video)
    with pytest.raises(ValueError, match="frames"):
        export_video(
            ReplayReader(recording), run, tmp_path / "too-large.mp4", speed=1, fps=60
        )
