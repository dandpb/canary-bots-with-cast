"""Export lifecycle tests use a codec stub; test_timelapse covers real ffmpeg."""

import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
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
    assert first["source_evidence_sha256"] != second["source_evidence_sha256"]
    assert first["render_input_sha256"] != second["render_input_sha256"]
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
    assert not any(
        path.name.startswith(".canary-video-") for path in tmp_path.iterdir()
    )
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
    with pytest.raises(ValueError, match="video export failed"):
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


def crash_publisher(tmp_path, termination, after_link=1):
    encoded = tmp_path / "encoded.bin"
    encoded.write_bytes(b"complete encoded bytes")
    video = tmp_path / "clip.mp4"
    program = """
import os, signal, sys
from pathlib import Path
from canary_brain import timelapse
from canary_brain.timelapse import publish_video
link = os.link
calls = 0
def crash(source, destination):
    global calls
    link(source, destination)
    calls += 1
    if calls == int(sys.argv[4]):
        os.kill(os.getpid(), getattr(signal, sys.argv[3]))
os.link = crash
if int(sys.argv[4]) == 3:
    def cleanup_crash(path):
        (Path(path) / Path(sys.argv[2]).name).unlink()
        os.kill(os.getpid(), getattr(signal, sys.argv[3]))
    timelapse.cleanup_staging = cleanup_crash
publish_video(Path(sys.argv[1]), Path(sys.argv[2]), {'fixture': True})
"""
    env = {**os.environ, "PYTHONPATH": str(Path(timelapse.__file__).parents[1])}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            program,
            str(encoded),
            str(video),
            termination,
            str(after_link),
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == -getattr(signal, termination), result.stderr
    return video


@pytest.mark.parametrize("termination", ["SIGKILL", "SIGTERM"])
@pytest.mark.skipif(os.name != "posix", reason="POSIX process-death regression")
def test_process_death_between_links_is_recovered_before_retry(
    tmp_path, monkeypatch, termination
):
    video = crash_publisher(tmp_path, termination)
    assert video.read_bytes() == b"complete encoded bytes"
    assert not video.with_suffix(".mp4.json").exists()
    stub_codec(monkeypatch)
    recording = tmp_path / "recording.db"
    run = demo(recording)[0]
    evidence = export(ReplayReader(recording), run, video)
    assert video.read_bytes() == b"fixture-video"
    assert json.loads(video.with_suffix(".mp4.json").read_text()) == evidence
    assert not list(tmp_path.glob(".canary-video-*"))


@pytest.mark.parametrize("replacement", ["video", "sidecar"])
@pytest.mark.skipif(os.name != "posix", reason="POSIX process-death regression")
def test_orphan_recovery_preserves_a_foreign_replacement(
    tmp_path, monkeypatch, replacement
):
    video = crash_publisher(tmp_path, "SIGKILL")
    sidecar = video.with_suffix(".mp4.json")
    target = video if replacement == "video" else sidecar
    target.unlink(missing_ok=True)
    target.write_bytes(b"foreign replacement")
    stub_codec(monkeypatch)
    recording = tmp_path / "recording.db"
    run = demo(recording)[0]
    with pytest.raises(ValueError, match="new .mp4"):
        export(ReplayReader(recording), run, video)
    assert target.read_bytes() == b"foreign replacement"
    assert not (sidecar if replacement == "video" else video).exists()
    assert not list(tmp_path.glob(".canary-video-*"))


@pytest.mark.parametrize("after_link", [2, 3])
@pytest.mark.skipif(os.name != "posix", reason="POSIX process-death regression")
def test_process_death_after_both_links_preserves_the_completed_pair(
    tmp_path, monkeypatch, after_link
):
    video = crash_publisher(tmp_path, "SIGKILL", after_link=after_link)
    sidecar = video.with_suffix(".mp4.json")
    original = video.read_bytes(), sidecar.read_bytes()
    stub_codec(monkeypatch)
    recording = tmp_path / "recording.db"
    run = demo(recording)[0]
    with pytest.raises(ValueError, match="new .mp4"):
        export(ReplayReader(recording), run, video)
    assert (video.read_bytes(), sidecar.read_bytes()) == original
    assert not list(tmp_path.glob(".canary-video-*"))


def test_render_identity_separates_parameters_from_source_evidence(
    tmp_path, monkeypatch
):
    stub_codec(monkeypatch)
    recording = tmp_path / "recording.db"
    run = demo(recording)[0]
    reader = ReplayReader(recording)
    baseline = timelapse.export_video(
        reader, run, tmp_path / "base.mp4", fps=1, end_ms=1000
    )
    for index, override in enumerate([{"start_ms": 500}, {"fps": 2}, {"speed": 30}]):
        options = {"fps": 1, "end_ms": 1000, **override}
        changed = timelapse.export_video(
            reader, run, tmp_path / f"changed-{index}.mp4", **options
        )
        assert changed["source_evidence_sha256"] == baseline["source_evidence_sha256"]
        assert changed["render_input_sha256"] != baseline["render_input_sha256"]


def test_unused_envelopes_and_later_events_do_not_change_window_identity(
    tmp_path, monkeypatch
):
    stub_codec(monkeypatch)
    recording = tmp_path / "recording.db"
    run = demo(recording)[0]
    first = export(ReplayReader(recording), run, tmp_path / "first.mp4")
    with sqlite3.connect(recording) as db:
        db.execute(
            "UPDATE replay_events SET event_key='audit-'||id,segment='other',wall=wall+10 WHERE run=?",
            (run,),
        )
        db.execute("UPDATE replay_runs SET updated=updated+10 WHERE id=?", (run,))
        db.execute(
            "INSERT INTO replay_events(run,event_key,segment,t_ms,wall,kind,data) SELECT run,'later-event',segment,999999,wall,kind,data FROM replay_events WHERE run=? AND kind='sample' LIMIT 1",
            (run,),
        )
    second = export(ReplayReader(recording), run, tmp_path / "second.mp4")
    for field in ["source_evidence_sha256", "render_input_sha256"]:
        assert first[field] == second[field]


def test_recovery_does_not_remove_a_live_publishers_first_link(tmp_path):
    video = tmp_path / "clip.mp4"
    encoded = tmp_path / "encoded.bin"
    encoded.write_bytes(b"live publication")
    ready = tmp_path / "ready"
    program = """
import os, sys, time
from pathlib import Path
from canary_brain.timelapse import publish_video
link = os.link
def pause(source, destination):
    link(source, destination)
    Path(sys.argv[3]).touch()
    time.sleep(30)
os.link = pause
publish_video(Path(sys.argv[1]), Path(sys.argv[2]), {'fixture': True})
"""
    child = subprocess.Popen(
        [sys.executable, "-c", program, str(encoded), str(video), str(ready)],
        env={**os.environ, "PYTHONPATH": str(Path(timelapse.__file__).parents[1])},
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists():
            assert child.poll() is None and time.monotonic() < deadline
            time.sleep(0.02)
        with pytest.raises(ValueError, match="active publisher"):
            timelapse.publish_video(encoded, video, {"other": True})
        assert video.read_bytes() == b"live publication"
        assert list(tmp_path.glob(".canary-video-*"))
    finally:
        child.kill()
        child.wait(timeout=5)
    timelapse.publish_video(encoded, video, {"retry": True})
    assert json.loads(video.with_suffix(".mp4.json").read_text()) == {"retry": True}


def test_hash_contracts_are_recomputable_and_track_visible_evidence(
    tmp_path, monkeypatch
):
    stub_codec(monkeypatch)
    recording = tmp_path / "recording.db"
    run = demo(recording)[0]
    first = export(ReplayReader(recording), run, tmp_path / "first.mp4")
    assert first["source_evidence_sha256"] == digest(first["source_evidence"])
    assert first["render_input_sha256"] == digest(first["render_input"])
    with sqlite3.connect(recording) as db:
        row = db.execute(
            "SELECT id,data FROM replay_events WHERE run=? AND kind='sample' ORDER BY t_ms,id LIMIT 1",
            (run,),
        ).fetchone()
        data = json.loads(row[1])
        data["bot"]["xp"] += 1
        db.execute(
            "UPDATE replay_events SET data=? WHERE id=?", (json.dumps(data), row[0])
        )
    changed = export(ReplayReader(recording), run, tmp_path / "changed.mp4")
    for field in ["source_evidence_sha256", "render_input_sha256"]:
        assert first[field] != changed[field]
    monkeypatch.setattr(timelapse, "RENDERER_VERSION", 999)
    renderer = export(ReplayReader(recording), run, tmp_path / "renderer.mp4")
    assert changed["source_evidence_sha256"] == renderer["source_evidence_sha256"]
    assert changed["render_input_sha256"] != renderer["render_input_sha256"]


@pytest.mark.parametrize("failure", ["snapshot", "ffmpeg", "ffprobe"])
def test_export_deadlines_and_codec_errors_are_reported_without_cli_tracebacks(
    tmp_path, monkeypatch, failure
):
    stub_codec(monkeypatch)
    recording = tmp_path / "recording.db"
    run = demo(recording)[0]
    if failure == "snapshot":

        def fail(*args, **kwargs):
            raise TimeoutError("snapshot deadline")

        monkeypatch.setattr(timelapse, "materialized_snapshot", fail)
    elif failure == "ffmpeg":

        def fail(*args, **kwargs):
            raise subprocess.TimeoutExpired("ffmpeg", 600)

        monkeypatch.setattr(timelapse.subprocess, "run", fail)
    else:

        def fail(*args, **kwargs):
            raise subprocess.CalledProcessError(1, "ffprobe")

        monkeypatch.setattr(timelapse.subprocess, "check_output", fail)
    video = tmp_path / "clip.mp4"
    with pytest.raises(ValueError, match="video export failed"):
        export(ReplayReader(recording), run, video)
    assert not video.exists() and not video.with_suffix(".mp4.json").exists()
