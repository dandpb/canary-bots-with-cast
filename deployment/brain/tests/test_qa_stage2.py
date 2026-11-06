"""QA stage 2: the shipped fake worker, a fake native peer; no Docker or network."""

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest
from test_protocol import observation

from canary_brain.recording import ReplayReader
from canary_brain.runtime import Configuration
from canary_brain.store import Store

DEPLOYMENT = Path(__file__).parents[2]
SHIPPED_ROOT = "/var/lib/canary-human-qa-stage2"
PILOT, LEADER = 65004, 9


def receive(peer: socket.socket, seconds: float) -> list[dict[str, Any]]:
    packets, end = [], time.monotonic() + seconds
    while (left := end - time.monotonic()) > 0:
        peer.settimeout(left)
        try:
            packets.append(json.loads(peer.recv(32768)))
        except TimeoutError:
            break
    return packets


def ask(world: str, sequence: int, sender: int, text: str) -> bytes:
    packet = observation()
    packet.update(world=world, sequence=sequence, mode="active", lease="lease-qa")
    packet.update(captured_ms=int(time.monotonic() * 1000))
    packet["bot"]["id"] = PILOT
    packet["party"] = {"leader_id": LEADER, "members": [LEADER, PILOT]}
    hold = {"id": "hold", "action": "hold", "description": "Wait", "ttl_ms": 5000}
    packet["actions"].append(hold)
    packet["messages"] = [{"id": f"m{sequence}", "player_id": sender, "text": text}]
    return json.dumps(packet).encode()


def test_brain_command_reaches_native_ack_and_stops_on_kill_switch() -> None:
    shipped = (DEPLOYMENT / "core-qa/brain/worker.json").read_text()
    loaded = Configuration.model_validate_json(shipped)
    assert loaded.provider == "fake" and not (loaded.credential_file or loaded.gateway)
    with tempfile.TemporaryDirectory(prefix="qa2-") as directory:
        root = Path(directory)
        (root / "worker.json").write_text(shipped.replace(SHIPPED_ROOT, directory))
        (root / "socket").mkdir()
        endpoint = str(root / "socket/worker.sock")
        peer = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        peer.bind(str(root / "socket/server.sock"))
        environment = dict(os.environ, PYTHONPATH=str(DEPLOYMENT / "brain/src"))
        serve = ["-m", "canary_brain.cli", "serve", "--config", f"{root}/worker.json"]
        worker = subprocess.Popen([sys.executable, *serve], env=environment)
        try:
            deadline = time.monotonic() + 5
            while not Path(endpoint).exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            world = f"{os.getpid()}-qa2"
            hello = {"version": 1, "type": "hello", "world": world, "capabilities": {}}
            peer.sendto(json.dumps(hello).encode(), endpoint)
            assert {"type": "heartbeat", "world": world} in [
                {"type": p["type"], "world": p.get("world")} for p in receive(peer, 1)
            ]

            # Negative: a non-leader's order gets a reply but never an intent.
            peer.sendto(ask(world, 10, 8, "fique aqui"), endpoint)
            packets = receive(peer, 1.5)
            assert any("proposta continue" in p.get("text", "") for p in packets)
            assert not [p for p in packets if p["type"] == "intent"]

            # Command -> reply -> intent offered by the leader's /brain message.
            peer.sendto(ask(world, 11, LEADER, "fique aqui"), endpoint)
            packets = receive(peer, 1.5)
            reply = next(p for p in packets if p["type"] == "reply")
            assert reply["text"].startswith("Teste: proposta hold;")
            intent = next(p for p in packets if p["type"] == "intent")
            assert len(intent) == 10 and intent["candidate_id"] == "hold"
            assert intent["bot_id"] == PILOT and intent["observation_sequence"] == 11

            # Native ack and terminal outcome, the terminal one duplicated.
            outcome = {"version": 1, "type": "outcome", "world": world, "metrics": {}}
            outcome.update(bot_id=PILOT, action_id=intent["action_id"])
            ack = dict(outcome, status="accepted", reason="objective_started")
            done = dict(outcome, status="completed", reason="hold_finished")
            for packet in (ack, done, done):
                peer.sendto(json.dumps(packet).encode(), endpoint)
            time.sleep(0.5)
            episode = Store(root / "state.sqlite3").get("episode", intent["action_id"])
            assert episode and episode["status"] == "completed" and episode["terminal"]

            # Kill switch: `compose stop brain` is SIGTERM; no further intents.
            worker.send_signal(signal.SIGTERM)
            assert worker.wait(timeout=10) == 0
            assert not Path(endpoint).exists()
            with pytest.raises(OSError):
                peer.sendto(ask(world, 12, LEADER, "fique aqui"), endpoint)
            assert {p["type"] for p in receive(peer, 0.5)} <= {"heartbeat"}
        finally:
            worker.kill()
            worker.wait()
            peer.close()
        budget = Store(root / "ledger.sqlite3").budget()
        assert (budget["spent"], budget["reserved"]) == (0, 0)
        replay = ReplayReader(root / "replay.sqlite3")
        events = replay.all_events(f"core-qa-stage2:{PILOT}:life")
        outcomes = [e["data"]["status"] for e in events if e["kind"] == "outcome"]
        assert outcomes.count("completed") == 1 and "accepted" in outcomes
    # The native side resumes when heartbeats stop (5 s) or on `brain disable`.
    native = (DEPLOYMENT.parent / "src/creatures/players/bot/bot_brain.cpp").read_text()
    assert "botMonoMs() - brain_->heartbeat > 5000" in native
    assert 'return "Brain disabled; native behavior retained.";' in native
