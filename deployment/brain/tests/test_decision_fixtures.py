"""Fixture CLI finalization uses real local recording and a stubbed provider wire."""

import argparse
import json
import threading
import time

import pytest
from test_gateway import client, gateway
from test_protocol import observation

from canary_brain import replay_cli
from canary_brain.recording import Recorder, ReplayReader
from canary_brain.store import Store, month_now


@pytest.mark.parametrize(
    "fault", [None, "blocked_writer", "close_false", "gap", "writer_error", "dropped"]
)
async def test_decision_fixture_completion_requires_closed_valid_recording(
    tmp_path, monkeypatch, fault
):
    fixtures = tmp_path / "fixtures.json"
    fixtures.write_text(json.dumps([{"observation": observation()}]))
    credential = tmp_path / "credential"
    credential.write_text("LITELLM_API_KEY=synthetic-unused-key\n")
    credential.chmod(0o600)
    recording = tmp_path / "replay.db"
    budget = tmp_path / "budget.db"
    config = tmp_path / "worker.json"
    config.write_text(
        json.dumps(
            {
                "provider": "litellm",
                "socket_directory": str(tmp_path / "ipc"),
                "state_file": str(tmp_path / "state.db"),
                "budget_file": str(budget),
                "credential_file": str(credential),
                "bots": [7],
                "run_cap_nanousd": 1000000,
                "gateway": gateway().model_dump(mode="json"),
                "recording": {"path": str(recording), "namespace": "qa"},
            }
        )
    )
    # An unrelated unknown liability must survive failure of this fixture run.
    ledger = Store(budget)
    ledger.reserve("unrelated-unknown", 99, month_now(), "responses")
    wire, calls = client()

    class OfflineClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return wire

        async def __aexit__(self, *args):
            pass

    entered, release = threading.Event(), threading.Event()
    recorders = []

    class FaultRecorder(Recorder):
        def __init__(self, *args):
            super().__init__(*args)
            recorders.append(self)
            self.flush()
            if fault == "blocked_writer":
                append = self.store.append

                def blocked(event):
                    entered.set()
                    release.wait()
                    append(event)

                self.store.append = blocked

        def close(self):
            if fault == "blocked_writer":
                assert entered.wait(2)
                started = time.monotonic()
                closed = super().close(timeout=0.02)
                assert time.monotonic() - started < 0.5
                assert not closed and self.thread.is_alive()
                return closed
            if fault == "gap":
                self.emit(7, "gap", {"reason": "native_telemetry_loss", "missing": 1})
            closed = super().close()
            assert closed
            if fault == "writer_error":
                self.errors += 1
            if fault == "dropped":
                self.dropped[7] = 1
            return False if fault == "close_false" else closed

    monkeypatch.setattr(replay_cli, "AsyncOpenAI", OfflineClient)
    monkeypatch.setattr(replay_cli, "Recorder", FaultRecorder)
    try:
        args = argparse.Namespace(fixtures=fixtures, worker_config=config, live=True)
        if fault:
            with pytest.raises(RuntimeError, match="recording did not close cleanly"):
                await replay_cli.decision_fixtures(args)
        else:
            result = await replay_cli.decision_fixtures(args)
            assert result["decisions"][0]["valid"]
        assert len(calls) == 1
        reader = ReplayReader(recording)
        run = reader.runs()[0]["id"]
        assert reader.run(run)["status"] == ("failed" if fault else "completed")
        # Keep settled usage and unknown reservations even when recording failed.
        assert ledger.budget()["spent"] == 14
        assert ledger.budget()["reserved"] == 99
        if fault == "gap":
            assert reader.run(run)["incomplete"]
            assert any(
                e["kind"] == "gap" and e["data"]["reason"] == "native_telemetry_loss"
                for e in reader.all_events(run)
            )
    finally:
        release.set()
        for recorder in recorders:
            recorder.thread.join(timeout=2)
            assert not recorder.thread.is_alive()
    if fault == "blocked_writer":
        assert reader.run(run)["incomplete"]
        assert any(
            e["kind"] == "gap" and e["data"]["reason"] == "recorder_shutdown_timeout"
            for e in reader.all_events(run)
        )
