"""Real supervised CLI worker with a synthetic private Unix datagram peer."""

import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest
from test_protocol import observation

from canary_brain.recording import RecordingStore, ReplayReader


def exercise_supervised_worker(provider, reason):
    with tempfile.TemporaryDirectory(prefix="bench-stop-") as temporary:
        work = Path(temporary)
        peer = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        peer.bind(str(work / "server.sock"))
        peer.setblocking(False)
        config = {
            "provider": provider,
            "mode": "shadow" if provider == "native" else "active",
            "socket_directory": str(work),
            "state_file": str(work / "state.db"),
            "bots": [7],
            "memory_mode": "frozen",
            "run_seconds": 60 if reason == "proposal_timeout" else 10,
            "benchmark_supervision": True,
            "recording": {"path": str(work / "replay.db"), "namespace": "stops"},
        }
        path = work / "config.json"
        path.write_text(json.dumps(config))
        with (work / "worker.log").open("w") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "canary_brain.cli",
                    "serve",
                    "--config",
                    str(path),
                ],
                env={
                    **os.environ,
                    "PYTHONPATH": str(Path(__file__).parents[1] / "src"),
                },
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                deadline = time.monotonic() + 4
                while not (work / "worker.sock").exists():
                    assert process.poll() is None, (work / "worker.log").read_text()
                    assert time.monotonic() < deadline
                    time.sleep(0.02)
                # Deliberate delay after readiness: the observed horizon starts afterward.
                if reason == "completed":
                    time.sleep(2)
                packet = observation()
                packet.update(
                    party=None, autonomous=True, mode=config["mode"], sequence=0
                )
                packet["bot"].update(
                    state="IDLE", objective_running=False, xp=98800, health=100
                )
                packet["actions"] = [
                    {
                        "id": "continue",
                        "action": "continue",
                        "description": "continue",
                        "ttl_ms": 1500,
                    }
                ]
                if reason == "proposal_timeout":
                    packet["actions"] += [
                        {
                            "id": "resupply",
                            "action": "resupply",
                            "description": "resupply",
                            "ttl_ms": 5000,
                        },
                        {
                            "id": "hunt:399",
                            "action": "hunt",
                            "description": "hunt",
                            "ttl_ms": 5000,
                        },
                    ]
                started = time.monotonic()
                telemetry_sequence = 0
                injected = False
                while process.poll() is None and time.monotonic() - started < (
                    36 if reason == "proposal_timeout" else 14
                ):
                    elapsed = time.monotonic() - started
                    if reason == "recording_gap" and elapsed > 0.3 and not injected:
                        run = ReplayReader(work / "replay.db").runs()[0]["id"]
                        RecordingStore(work / "replay.db").append(
                            {
                                "run": run,
                                "key": "injected-gap",
                                "segment": "test",
                                "t_ms": 100,
                                "wall": time.time(),
                                "kind": "gap",
                                "data": {"reason": "storage_limit"},
                            }
                        )
                        injected = True
                    if reason != "observation_stale" or elapsed < 0.4:
                        packet["sequence"] += 1
                        packet["captured_ms"] = int(time.monotonic() * 1000)
                        if reason == "world_changed" and elapsed > 0.3:
                            packet["world"] = "changed"
                        try:
                            peer.sendto(
                                json.dumps(packet).encode(), str(work / "worker.sock")
                            )
                            telemetry_sequence += 1
                            telemetry = {
                                "version": 1,
                                "type": "telemetry",
                                "world": packet["world"],
                                "bot_id": 7,
                                "captured_ms": packet["captured_ms"],
                                "sequence": telemetry_sequence,
                                "deaths": 13
                                if reason == "deaths_limit" and elapsed > 0.3
                                else 10,
                                "phase": "alive",
                                "model_owned": False,
                            }
                            peer.sendto(
                                json.dumps(telemetry).encode(),
                                str(work / "worker.sock"),
                            )
                        except (FileNotFoundError, ConnectionRefusedError):
                            break
                    try:
                        while peer.recv(32768):
                            pass
                    except BlockingIOError:
                        pass
                    time.sleep(0.05)
                assert process.wait(timeout=3) == 0, (work / "worker.log").read_text()
                with sqlite3.connect(work / "state.db") as db:
                    stopped = json.loads(
                        db.execute(
                            "SELECT data FROM records WHERE kind='run_stop' AND key='end'"
                        ).fetchone()[0]
                    )
                    assert (
                        db.execute("SELECT COUNT(*) FROM requests").fetchone()[0] == 0
                    )
                assert stopped["reason"] == reason, stopped
                if reason == "proposal_timeout":
                    assert 30 < stopped["elapsed_seconds"] <= 32.2
                assert not (work / "worker.sock").exists()
                if reason == "completed":
                    assert 10 <= stopped["elapsed_seconds"] <= 11.2
                    reader = ReplayReader(work / "replay.db")
                    run = reader.runs()[0]["id"]
                    samples = [
                        e for e in reader.all_events(run) if e["kind"] == "sample"
                    ]
                    assert (
                        9 <= (samples[-1]["t_ms"] - samples[0]["t_ms"]) / 1000 <= 11.2
                    )
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=4)
                peer.close()


@pytest.mark.parametrize("provider", ["native", "fake"])
@pytest.mark.parametrize(
    "reason",
    [
        "completed",
        "deaths_limit",
        "world_changed",
        "observation_stale",
        "recording_gap",
    ],
)
def test_supervised_worker_stops_and_closes_ipc_without_inference(provider, reason):
    exercise_supervised_worker(provider, reason)


def test_invalid_fake_choices_do_not_reset_the_real_proposal_deadline():
    exercise_supervised_worker("fake", "proposal_timeout")
