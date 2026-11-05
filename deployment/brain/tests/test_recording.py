import sqlite3
import threading
import zipfile

import pytest
from test_protocol import observation

from canary_brain.protocol import Observation
from canary_brain.recording import (
    Manifest,
    Recorder,
    RecordingConfiguration,
    RecordingStore,
    ReplayReader,
)
from canary_brain.replay import export_archive, import_archive, summary


def recorder(tmp_path, **kwargs):
    config = RecordingConfiguration(
        path=tmp_path / "replay.db", namespace="qa", **kwargs
    )
    manifest = Manifest(
        run_id="qa:7",
        bot_id=7,
        lineage="qa:7",
        provider="fake",
        model="none",
        synthetic=True,
    )
    return Recorder(config, [manifest])


def test_history_survives_restart_and_seek_never_needs_a_model(tmp_path):
    r = recorder(tmp_path)
    packet = observation()
    r.observe(Observation.model_validate(packet))
    r.emit(7, "decision", {"phase": "model_proposed", "candidate": "continue"})
    r.close()
    restored = recorder(tmp_path)
    packet["sequence"] += 1
    packet["bot"]["xp"] += 50
    restored.observe(Observation.model_validate(packet))
    restored.close()
    read = ReplayReader(tmp_path / "replay.db")
    events = list(read.all_events("qa:7"))
    assert read.seek("qa:7", events[-1]["t_ms"])["sample"]["data"]["bot"]["xp"] == 1050
    assert summary(read, "qa:7")["metrics"]["xp_delta"] == 50
    assert read.run("qa:7")["incomplete"]
    assert any(
        e["kind"] == "gap" and e["data"]["reason"] == "worker_restart" for e in events
    )


def test_bounded_queue_exposes_loss_without_blocking_the_caller(tmp_path, monkeypatch):
    r = recorder(tmp_path, queue_size=16)
    entered, release = threading.Event(), threading.Event()
    original = r.store.append

    def slow(event):
        entered.set()
        assert release.wait(5)
        original(event)

    monkeypatch.setattr(r.store, "append", slow)
    r.emit(7, "decision", {"candidate": "continue"})
    assert entered.wait(2)
    for index in range(100):
        r.emit(7, "decision", {"index": index})
    assert r.health()["dropped"] > 0
    assert r.queue.qsize() <= 16
    release.set()
    r.close()
    assert ReplayReader(r.config.path).run("qa:7")["incomplete"]


def test_native_deaths_are_cumulative_deduplicated_and_not_inferred_from_hp(tmp_path):
    r = recorder(tmp_path)
    packet = observation()
    packet["bot"]["health"] = 0
    r.observe(Observation.model_validate(packet))
    r.native_event(7, "world-a", 0, {"deaths": 0, "phase": "alive"})
    r.native_event(7, "world-a", 2, {"deaths": 3, "phase": "alive"})
    r.native_event(7, "world-a", 1, {"deaths": 1, "phase": "dead"})
    r.native_event(7, "world-a", 3, {"deaths": 3, "phase": "alive"})
    r.native_event(7, "world-b", 1, {"deaths": 1, "phase": "alive"})
    r.close()
    metrics = summary(ReplayReader(r.config.path), "qa:7")["metrics"]
    assert metrics["deaths"] == 4
    assert metrics["spent_nanousd"] == 0
    assert metrics["xp_per_dollar"] is None


def test_archive_round_trip_verifies_integrity_before_import(tmp_path):
    r = recorder(tmp_path)
    r.observe(Observation.model_validate(observation()))
    r.close()
    archive = tmp_path / "run.zip"
    export_archive(ReplayReader(r.config.path), "qa:7", archive)
    destination = tmp_path / "imported.db"
    assert import_archive(archive, destination) == "qa:7"
    assert (
        ReplayReader(destination).seek("qa:7", 10**9)["sample"]["data"]["bot"]["xp"]
        == 1000
    )
    broken = tmp_path / "broken.zip"
    with zipfile.ZipFile(archive) as src, zipfile.ZipFile(broken, "w") as dst:
        for name in src.namelist():
            dst.writestr(name, b"[]" if name.startswith("events-") else src.read(name))
    with pytest.raises(ValueError, match="integrity"):
        import_archive(broken, tmp_path / "should-not-exist.db")
    assert not (tmp_path / "should-not-exist.db").exists()


def test_recording_store_refuses_closed_or_reassigned_run_identity(tmp_path):
    r = recorder(tmp_path)
    r.close()
    r.store.finish("qa:7", "completed")
    with pytest.raises(ValueError, match="identity"):
        recorder(tmp_path)
    store = RecordingStore(tmp_path / "other.db")
    store.begin(Manifest(run_id="one", bot_id=7, lineage="a"))
    with pytest.raises(ValueError, match="identity"):
        store.begin(Manifest(run_id="one", bot_id=8, lineage="b"))


def archive_fixture(tmp_path):
    store = RecordingStore(tmp_path / "source.db")
    manifest = Manifest(run_id="import:7", bot_id=7, lineage="source")
    store.begin(manifest)
    for index, key in enumerate(("first", "second")):
        store.append(
            {
                "run": manifest.run_id,
                "key": key,
                "segment": "a",
                "t_ms": index,
                "wall": 1.0,
                "kind": "decision",
                "data": {"choice": key},
            }
        )
    return store, manifest


def test_export_uses_one_snapshot_during_concurrent_recording(tmp_path, monkeypatch):
    store, manifest = archive_fixture(tmp_path)
    original = zipfile.ZipFile.writestr

    def write(archive, name, data, **kwargs):
        if name == "run.json":
            store.append(
                {
                    "run": manifest.run_id,
                    "key": "late",
                    "segment": "a",
                    "t_ms": 2,
                    "wall": 2.0,
                    "kind": "decision",
                    "data": {},
                }
            )
        return original(archive, name, data, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "writestr", write)
    archive = tmp_path / "snapshot.zip"
    export_archive(ReplayReader(store.path), manifest.run_id, archive)
    destination = tmp_path / "imported.db"
    import_archive(archive, destination)
    assert ReplayReader(destination).run(manifest.run_id)["event_count"] == 2
    assert ReplayReader(store.path).run(manifest.run_id)["event_count"] == 3


def test_import_never_merges_an_existing_run_even_for_lifetime_manifests(tmp_path):
    store, manifest = archive_fixture(tmp_path)
    archive = tmp_path / "conflict.zip"
    export_archive(ReplayReader(store.path), manifest.run_id, archive)
    destination = RecordingStore(tmp_path / "existing.db")
    destination.begin(manifest.model_copy(update={"participant": "another-history"}))
    with pytest.raises(ValueError, match="identity"):
        import_archive(archive, destination.path)
    assert ReplayReader(destination.path).run(manifest.run_id)["event_count"] == 0


def test_import_sql_failure_rolls_back_the_entire_new_run(tmp_path):
    store, manifest = archive_fixture(tmp_path)
    archive = tmp_path / "atomic.zip"
    export_archive(ReplayReader(store.path), manifest.run_id, archive)
    destination = RecordingStore(tmp_path / "atomic.db")
    with destination.connect() as db:
        db.execute(
            "CREATE TRIGGER reject_second BEFORE INSERT ON replay_events "
            "WHEN NEW.event_key='second' BEGIN SELECT RAISE(ABORT,'isolated failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="isolated failure"):
        import_archive(archive, destination.path)
    assert ReplayReader(destination.path).runs() == []
    with destination.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM replay_events").fetchone()[0] == 0
