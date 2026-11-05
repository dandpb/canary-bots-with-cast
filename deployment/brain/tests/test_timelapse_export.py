"""Export lifecycle tests use a codec stub; test_timelapse covers real ffmpeg."""

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest
from test_protocol import observation

from canary_brain import timelapse
from canary_brain.benchmark import demo
from canary_brain.recording import (
    Manifest,
    Recorder,
    RecordingConfiguration,
    ReplayReader,
    digest,
)


def stub_codec(monkeypatch):
    monkeypatch.setattr(timelapse.shutil, "which", lambda tool: f"/fixture/{tool}")

    def encode(args, **kwargs):
        Path(args[-1]).write_bytes(b"fixture-video")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(timelapse.subprocess, "run", encode)
    monkeypatch.setattr(
        timelapse.subprocess,
        "check_output",
        lambda *args, **kwargs: json.dumps(
            {
                "streams": [{"nb_read_frames": "1", "width": 1280, "height": 720}],
                "format": {"duration": "1.0"},
            }
        ).encode(),
    )


def export(reader, run, output):
    return timelapse.export_video(
        reader, run, output, fps=1, end_ms=min(1000, reader.run(run)["duration_ms"])
    )


def test_encoding_active_run_does_not_pin_source_wal_or_drop_live_samples(
    tmp_path, monkeypatch
):
    config = RecordingConfiguration(
        path=tmp_path / "live.db", namespace="video", max_bytes=1024 * 1024
    )
    recorder = Recorder(config, [Manifest(run_id="video:7", bot_id=7, lineage="7")])
    recorder.emit(7, "sample", observation())
    recorder.flush()
    reader = ReplayReader(config.path)
    # Keep WAL open as the live service does, and checkpoint between write batches.
    keeper = sqlite3.connect(config.path, timeout=0.01)
    keeper.execute("PRAGMA wal_autocheckpoint=0")
    stub_codec(monkeypatch)

    def encoding_gate(*args, **kwargs):
        for index in range(120):
            value = observation()
            value["bot"]["xp"] += index
            assert recorder.emit(7, "sample", value)
            recorder.flush()
            if index % 10 == 9:
                keeper.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        events = list(ReplayReader(config.path).all_events("video:7"))
        assert sum(event["kind"] == "sample" for event in events) == 121
        assert not any(
            event["kind"] == "gap" and event["data"].get("reason") == "storage_limit"
            for event in events
        )
        assert keeper.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0] == 0
        raise RuntimeError("encoding gate complete")

    monkeypatch.setattr(timelapse.subprocess, "run", encoding_gate)
    try:
        with pytest.raises(RuntimeError, match="encoding gate complete"):
            export(reader, "video:7", tmp_path / "live.mp4")
    finally:
        recorder.close()
        keeper.close()
    assert not (tmp_path / "live.mp4").exists()


def test_source_digest_covers_recorded_manifest_and_status(tmp_path, monkeypatch):
    stub_codec(monkeypatch)
    recording = tmp_path / "recording.db"
    run = demo(recording)[0]
    first = export(ReplayReader(recording), run, tmp_path / "first.mp4")
    with sqlite3.connect(recording) as db:
        encoded = db.execute(
            "SELECT manifest FROM replay_runs WHERE id=?", (run,)
        ).fetchone()[0]
        manifest = json.loads(encoded)
        manifest["participant"] = "different recorded participant"
        db.execute(
            "UPDATE replay_runs SET manifest=?,status='interrupted' WHERE id=?",
            (json.dumps(manifest), run),
        )
    second = export(ReplayReader(recording), run, tmp_path / "second.mp4")
    assert first["source_snapshot_sha256"] != second["source_snapshot_sha256"]
    assert first["source_events_sha256"] == second["source_events_sha256"]
    assert second["source_snapshot_sha256"] == digest(
        {
            "metadata": second["source_metadata"],
            "events_sha256": second["source_events_sha256"],
            "events_until_ms": second["end_ms"],
        }
    )


def test_materialized_source_stays_consistent_without_locking_live_database(tmp_path):
    recording = tmp_path / "recording.db"
    run = demo(recording)[0]
    with timelapse.materialized_snapshot(ReplayReader(recording)) as copy:
        copied_path = copy.path
        metadata = copy.run(run)
        events = list(copy.all_events(run))
        with sqlite3.connect(recording, timeout=0.01) as db:
            db.execute("UPDATE replay_runs SET status='interrupted' WHERE id=?", (run,))
            db.execute("DELETE FROM replay_events WHERE run=?", (run,))
            db.commit()
            assert db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0] == 0
        assert copy.run(run) == metadata
        assert list(copy.all_events(run)) == events
        assert copied_path != recording
    assert not copied_path.exists()


@pytest.mark.parametrize("failure", ["video_copy", "sidecar_write"])
def test_failed_publication_leaves_no_final_artifacts_and_can_retry(
    tmp_path, monkeypatch, failure
):
    stub_codec(monkeypatch)
    recording = tmp_path / "recording.db"
    run = demo(recording)[0]
    video = tmp_path / "clip.mp4"
    sidecar = video.with_suffix(".mp4.json")

    with monkeypatch.context() as fault:
        if failure == "video_copy":

            def fail_copy(source, target, *args, **kwargs):
                target.write(source.read(3))
                raise OSError("injected partial video copy")

            fault.setattr(timelapse.shutil, "copyfileobj", fail_copy)
        else:
            original = Path.open

            def fail_sidecar(path, mode="r", *args, **kwargs):
                if path.name.endswith(".mp4.json") and any(c in mode for c in "wx"):
                    raise OSError("injected sidecar write failure")
                return original(path, mode, *args, **kwargs)

            fault.setattr(Path, "open", fail_sidecar)
        with pytest.raises(OSError, match="injected"):
            export(ReplayReader(recording), run, video)

    assert not video.exists()
    assert not sidecar.exists()
    assert not any(path.name.startswith(".canary-video-") for path in tmp_path.iterdir())
    evidence = export(ReplayReader(recording), run, video)
    assert video.read_bytes() == b"fixture-video"
    assert json.loads(sidecar.read_text()) == evidence


@pytest.mark.parametrize("occupied", ["video", "sidecar"])
def test_publication_collision_preserves_existing_artifact_and_rolls_back_its_own(
    tmp_path, monkeypatch, occupied
):
    stub_codec(monkeypatch)
    recording = tmp_path / "recording.db"
    run = demo(recording)[0]
    video = tmp_path / "clip.mp4"
    sidecar = video.with_suffix(".mp4.json")
    target = video if occupied == "video" else sidecar
    encode = timelapse.subprocess.run

    def race(*args, **kwargs):
        result = encode(*args, **kwargs)
        target.write_bytes(b"existing artifact")
        return result

    monkeypatch.setattr(timelapse.subprocess, "run", race)
    with pytest.raises(FileExistsError):
        export(ReplayReader(recording), run, video)
    assert target.read_bytes() == b"existing artifact"
    assert not (sidecar if occupied == "video" else video).exists()


@pytest.mark.parametrize("interrupted", ["video", "sidecar"])
def test_interruption_just_after_publishing_a_name_cleans_both_outputs(
    tmp_path, monkeypatch, interrupted
):
    stub_codec(monkeypatch)
    recording = tmp_path / "recording.db"
    run = demo(recording)[0]
    video = tmp_path / "clip.mp4"
    sidecar = video.with_suffix(".mp4.json")
    target = video if interrupted == "video" else sidecar
    link = timelapse.os.link

    def interrupt(source, destination):
        link(source, destination)
        if destination == target:
            raise KeyboardInterrupt("injected publication interrupt")

    monkeypatch.setattr(timelapse.os, "link", interrupt)
    with pytest.raises(KeyboardInterrupt, match="injected"):
        export(ReplayReader(recording), run, video)
    assert not video.exists()
    assert not sidecar.exists()
