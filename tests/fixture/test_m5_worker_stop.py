"""Real offline worker + private datagram peer; no game or model provider."""

import json
import os
import socket
import sqlite3
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class WorkerStopTests(unittest.TestCase):
    def test_early_runtime_exit_is_not_a_completed_horizon(self):
        for mode in ["native", "fake"]:
            with (
                self.subTest(mode=mode),
                tempfile.TemporaryDirectory(prefix="m5early-") as temporary,
            ):
                work = Path(temporary)
                (work / "worker.json").write_text(
                    json.dumps(
                        {
                            "provider": mode,
                            "mode": "shadow" if mode == "native" else "active",
                            "socket_directory": str(work / "socket"),
                            "state_file": str(work / "state.db"),
                            "bots": [65001],
                        }
                    )
                )
                script = str(ROOT / "tests/fixture/m5_worker.py")
                inject = (
                    "import runpy,sys;from canary_brain import runtime;sys.path.insert(0,"
                    + repr(str(ROOT / "tests/fixture"))
                    + ")\nasync def early(*a,**kw): return None\nruntime.run=early\nsys.argv="
                    + repr([script, str(work), mode])
                    + ";runpy.run_path(sys.argv[0],run_name='__main__')"
                )
                subprocess.run(
                    [os.sys.executable, "-c", inject],
                    env={
                        **os.environ,
                        "PYTHONPATH": str(ROOT / "deployment/brain/src"),
                    },
                    check=True,
                    timeout=10,
                )
                self.assertEqual(
                    json.loads((work / "stop.json").read_text())["reason"],
                    "runtime_ended",
                )

    def exercise(self, mode, fault):
        with tempfile.TemporaryDirectory(prefix="m5stop-") as temporary:
            work = Path(temporary)
            ipc = work / "socket"
            ipc.mkdir()
            peer = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            peer.bind(str(ipc / "server.sock"))
            config = {
                "provider": mode,
                "mode": "shadow" if mode == "native" else "active",
                "socket_directory": str(ipc),
                "state_file": str(work / "worker.sqlite3"),
                "bots": [65001],
                "memory_mode": "frozen",
                "recording": {
                    "path": str(work / "recording.sqlite3"),
                    "namespace": "stop-test",
                },
            }
            (work / "worker.json").write_text(json.dumps(config))
            with (work / "worker.log").open("w") as log:
                launch = [
                    os.sys.executable,
                    str(ROOT / "tests/fixture/m5_worker.py"),
                    str(work),
                    mode,
                ]
                if fault in {"proposal_timeout", "stalled"}:
                    inject = (
                        "import asyncio,runpy,sys;from canary_brain import runtime;"
                        "sys.path.insert(0," + repr(str(ROOT / "tests/fixture")) + ");"
                    )
                    if fault == "proposal_timeout":
                        inject += "\nasync def blocked(self,snapshot):\n self.record(snapshot.bot.id,'decision',{'phase':'requested','observation':snapshot.model_dump()})\n await asyncio.sleep(90)\nruntime.Controller._decide=blocked\n"
                    else:
                        inject += "import m5_stop;original=m5_stop.Stops;m5_stop.Stops=lambda **kw: original(stall_seconds=1.2,**kw)\n"
                    inject += (
                        "sys.argv="
                        + repr(launch[1:])
                        + ";runpy.run_path(sys.argv[0],run_name='__main__')"
                    )
                    launch = [os.sys.executable, "-c", inject]
                process = subprocess.Popen(
                    launch,
                    env={
                        **os.environ,
                        "PYTHONPATH": str(ROOT / "deployment/brain/src"),
                    },
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                try:
                    deadline = time.monotonic() + 10
                    while not (ipc / "worker.sock").exists():
                        self.assertIsNone(
                            process.poll(), (work / "worker.log").read_text()
                        )
                        self.assertLess(time.monotonic(), deadline)
                        time.sleep(0.02)

                    def send(data):
                        peer.sendto(json.dumps(data).encode(), str(ipc / "worker.sock"))

                    send(
                        {
                            "version": 1,
                            "type": "hello",
                            "world": "fixture",
                            "capabilities": {
                                "lifecycle_telemetry": 1,
                                "keep_awake": True,
                            },
                        }
                    )
                    for sequence in range(1, 6):
                        send(
                            {
                                "version": 1,
                                "type": "observation",
                                "world": "fixture",
                                "sequence": sequence,
                                "captured_ms": sequence * 250,
                                "lease": "offline",
                                "objective_generation": 0,
                                "mode": "shadow" if mode == "native" else "active",
                                "autonomous": True,
                                "bot": {
                                    "id": 65001,
                                    "name": "fixture",
                                    "level": 20,
                                    "vocation": 4,
                                    "state": "IDLE",
                                    "position": [1, 2, 7],
                                    "health": 100,
                                    "mana": 100,
                                    "potions": 40,
                                    "xp": 98800,
                                    "alive": True,
                                },
                                "actions": [
                                    {
                                        "id": "continue",
                                        "action": "continue",
                                        "description": "continue",
                                        "ttl_ms": 1500,
                                    }
                                ]
                                + (
                                    [
                                        {
                                            "id": "resupply",
                                            "action": "resupply",
                                            "description": "resupply",
                                            "ttl_ms": 5000,
                                        }
                                    ]
                                    if fault == "proposal_timeout"
                                    else []
                                ),
                            }
                        )
                        time.sleep(0.05)

                    def telemetry(sequence, deaths, world="fixture"):
                        send(
                            {
                                "version": 1,
                                "type": "telemetry",
                                "world": world,
                                "sequence": sequence,
                                "captured_ms": sequence * 250,
                                "bot_id": 65001,
                                "deaths": deaths,
                                "phase": "alive",
                                "model_owned": False,
                            }
                        )

                    telemetry(1, 10)
                    time.sleep(0.1)
                    if fault == "deaths_limit":
                        telemetry(2, 12)
                        time.sleep(0.1)
                        self.assertIsNone(process.poll())
                        telemetry(3, 13)
                    elif fault == "world_changed":
                        telemetry(2, 0, "next-world")
                    elif fault in {"proposal_timeout", "stalled"}:
                        deadline = time.monotonic() + 38
                        sequence = 6
                        while process.poll() is None and time.monotonic() < deadline:
                            # Repeat observations keep liveness separate from missing decisions.
                            packet = {
                                "version": 1,
                                "type": "observation",
                                "world": "fixture",
                                "sequence": sequence,
                                "captured_ms": sequence * 250,
                                "lease": "offline",
                                "objective_generation": 0,
                                "mode": "active",
                                "autonomous": True,
                                "bot": {
                                    "id": 65001,
                                    "name": "fixture",
                                    "level": 20,
                                    "vocation": 4,
                                    "state": "IDLE",
                                    "position": [1, 2, 7],
                                    "health": 100,
                                    "mana": 100,
                                    "potions": 20,
                                    "xp": 98800,
                                    "alive": True,
                                },
                                "actions": [
                                    {
                                        "id": "continue",
                                        "action": "continue",
                                        "description": "continue",
                                        "ttl_ms": 1500,
                                    },
                                    {
                                        "id": "resupply",
                                        "action": "resupply",
                                        "description": "resupply",
                                        "ttl_ms": 5000,
                                    },
                                ],
                            }
                            try:
                                send(packet)
                            except (FileNotFoundError, ConnectionRefusedError):
                                break
                            sequence += 1
                            time.sleep(0.1)
                    elif fault != "observation_stale":
                        raise AssertionError("unknown test fault")
                    self.assertEqual(
                        process.wait(timeout=12), 0, (work / "worker.log").read_text()
                    )
                    stop = json.loads((work / "stop.json").read_text())
                    self.assertEqual(stop["reason"], fault)
                    self.assertLess(
                        stop["elapsed"], 40 if fault == "proposal_timeout" else 10
                    )
                    self.assertFalse((ipc / "worker.sock").exists())
                    with sqlite3.connect(work / "worker.sqlite3") as db:
                        self.assertEqual(
                            db.execute("SELECT COUNT(*) FROM requests").fetchone()[0], 0
                        )
                finally:
                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=10)
                    peer.close()

    def test_native_and_fake_stop_on_cumulative_deaths(self):
        for mode in ("native", "fake"):
            with self.subTest(mode=mode):
                self.exercise(mode, "deaths_limit")

    def test_native_and_fake_stop_on_generation_change(self):
        for mode in ("native", "fake"):
            with self.subTest(mode=mode):
                self.exercise(mode, "world_changed")

    def test_native_and_fake_stop_after_observation_loss(self):
        for mode in ("native", "fake"):
            with self.subTest(mode=mode):
                self.exercise(mode, "observation_stale")

    def test_fake_stops_after_real_thirty_second_missing_proposal_window(self):
        self.exercise("fake", "proposal_timeout")

    def test_fake_stops_on_stall_with_scaled_test_threshold(self):
        self.exercise("fake", "stalled")


if __name__ == "__main__":
    unittest.main()
