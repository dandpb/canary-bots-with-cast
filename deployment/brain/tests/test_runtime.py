import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from test_protocol import observation

from canary_brain.recording import ReplayReader
from canary_brain.store import Store


def test_private_datagram_worker_round_trip_without_credentials(tmp_path):
    # Linux Unix addresses are limited to 108 bytes, independent of pytest path length.
    import tempfile

    with tempfile.TemporaryDirectory(prefix="brain-") as directory:
        root = Path(directory)
        server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        server.bind(str(root / "server.sock"))
        server.settimeout(3)
        config = root / "worker.json"
        config.write_text(
            json.dumps(
                {
                    "mode": "active",
                    "provider": "fake",
                    "socket_directory": directory,
                    "state_file": str(tmp_path / "state.db"),
                    "bots": [7],
                    "recording": {"path": str(tmp_path / "replay.db"), "namespace": "test"},
                }
            )
        )
        environment = dict(
            os.environ, PYTHONPATH=str(Path(__file__).parents[1] / "src")
        )
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "canary_brain.cli",
                "serve",
                "--config",
                str(config),
            ],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            deadline = time.monotonic() + 3
            while not (root / "worker.sock").exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            packet = observation()
            packet["mode"] = "active"
            packet["captured_ms"] = int(time.monotonic() * 1000)
            packet["actions"].append(
                {"id": "hold", "action": "hold", "description": "Wait", "ttl_ms": 5000}
            )
            packet["messages"] = [
                {"id": "message-1", "player_id": 9, "text": "Fique aqui."}
            ]
            server.sendto(json.dumps(packet).encode(), str(root / "worker.sock"))
            intent = None
            for _ in range(8):
                incoming = json.loads(server.recv(32768))
                if incoming["type"] == "intent":
                    intent = incoming
                    break
            assert intent and intent["candidate_id"] == "hold"
            outcome = {
                "version": 1,
                "type": "outcome",
                "world": intent["world"],
                "bot_id": 7,
                "action_id": intent["action_id"],
                "status": "completed",
                "reason": "hold_finished",
                "metrics": {"elapsed_seconds": 30.0, "progress": 1.0},
            }
            server.sendto(json.dumps(outcome).encode(), str(root / "worker.sock"))
            deadline = time.monotonic() + 2
            store = Store(tmp_path / "state.db")
            while time.monotonic() < deadline:
                episode = store.get("episode", intent["action_id"])
                if episode and episode.get("terminal"):
                    break
                time.sleep(0.02)
            assert episode["status"] == "completed"
            assert store.budget()["spent"] == 0
        finally:
            process.terminate()
            process.communicate(timeout=3)
            server.close()
        assert not (root / "worker.sock").exists()
        reader = ReplayReader(tmp_path / "replay.db")
        events = list(reader.all_events("test:7:life"))
        assert any(e["kind"] == "outcome" and e["data"]["status"] == "completed" for e in events)
        assert reader.seek("test:7:life", 10**9)["sample"]["data"]["bot"]["id"] == 7
