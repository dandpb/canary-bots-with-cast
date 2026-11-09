"""Actual supervised run(), real Unix datagrams, synthetic native capture clock."""

import asyncio
import json
import os
import socket
from copy import deepcopy
from pathlib import Path

import pytest
from test_protocol import observation
from test_supervised_admission import CAPS, SOURCE

from canary_brain.benchmark_stops import Stops
from canary_brain.recording import (
    Manifest,
    Recorder,
    RecordingConfiguration,
    ReplayReader,
)
from canary_brain.runtime import Configuration, run
from canary_brain.store import Store
from canary_brain.supervised_native import SupervisedNative


@pytest.mark.parametrize(
    "mode",
    [
        "complete",
        "drop_b",
        "wrong_nonce",
        "reload",
        "peer_crash",
        "missing_capability",
        "operator_close",
        "close_false",
        "operator_proof",
        "cutoff_stalled",
        "cutoff_proposal_timeout",
    ],
)
async def test_real_supervised_worker_native_contract(tmp_path, mode, monkeypatch):
    descriptor = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    # procfs alias fits sockaddr_un; actual files remain entirely under TMPDIR.
    directory = Path(f"/proc/self/fd/{descriptor}/ipc")
    directory.mkdir()
    peer = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    peer.setblocking(False)
    peer.bind(str(directory / "server.sock"))
    config = Configuration(
        provider="native",
        bots=[7],
        socket_directory=directory,
        state_file=tmp_path / "state.sqlite",
        run_seconds=10,
        benchmark_supervision=True,
        native_source_revision=SOURCE,
        recording=RecordingConfiguration(
            path=tmp_path / "replay.sqlite",
            namespace="qa",
            manifests=[
                Manifest(
                    run_id="qa:7", bot_id=7, lineage="qa:7", source_revision=SOURCE
                )
            ],
        ),
    )
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    original_observe = Stops.observe
    cutoff_reasons = []

    def observe_at_cutoff(stops, packet, now):
        original_observe(stops, packet, now)
        if packet["type"] == "observation" and packet["captured_ms"] == 1801000:
            if mode == "cutoff_stalled":
                stops.progress_at = now - 601
            elif mode == "cutoff_proposal_timeout":
                stops.opportunity = now - 31
            cutoff_reasons.append(stops.check(now))

    monkeypatch.setattr(Stops, "observe", observe_at_cutoff)
    original_close = Recorder.close
    original_proof = SupervisedNative.durable_complete

    def proof_probe(native):
        result = original_proof(native)
        if mode == "operator_proof":
            loop.call_soon_threadsafe(stopped.set)
        return result

    monkeypatch.setattr(SupervisedNative, "durable_complete", proof_probe)

    def close_probe(recorder):
        if mode in {"complete", "operator_close", "close_false", "operator_proof"}:
            ending = Store(config.state_file).get("run_stop", "end")
            assert ending["reason"] == "native_finalizing"
            assert not any(
                e["data"].get("reason") == "completed"
                for e in ReplayReader(config.recording.path).all_events("qa:7")
            )
            if mode == "operator_close":
                loop.call_soon_threadsafe(stopped.set)
        result = original_close(recorder)
        return False if mode == "close_false" else result

    monkeypatch.setattr(Recorder, "close", close_probe)
    worker = asyncio.create_task(run(config, stopped))

    async def send(packet):
        await loop.sock_sendto(
            peer, json.dumps(packet).encode(), str(directory / "worker.sock")
        )

    async def receive(kind):
        async with asyncio.timeout(5):
            while True:
                value = json.loads(await loop.sock_recv(peer, 32768))
                if value["type"] == kind:
                    return value

    try:
        # run() creates its socket before yielding to its stop wait.
        await asyncio.sleep(0)
        await send(
            {
                "version": 1,
                "type": "hello",
                "world": "world-a",
                "capabilities": {} if mode == "missing_capability" else CAPS,
            }
        )
        if mode != "missing_capability":
            request = await receive("telemetry_admit")
            initial = observation()
            boundary = {
                "version": 1,
                "type": "telemetry",
                "world": "world-a",
                "bot_id": 7,
                "sequence": 220,
                "captured_ms": 1000,
                "deaths": 2,
                "phase": "alive",
                "run_nonce": request["nonce"],
            }
            if mode != "drop_b":
                await send(boundary)
            await send(
                {
                    "version": 1,
                    "type": "telemetry_admitted",
                    "world": "world-a",
                    "bot_id": 7,
                    "nonce": "wrong" if mode == "wrong_nonce" else request["nonce"],
                    "begin_sequence": 220,
                    "captured_ms": 1000,
                    "deaths": 2,
                    "observation": initial,
                    "source": SOURCE,
                    "source_dirty": False,
                    "fault": "",
                }
            )
            await send(
                boundary
                | {
                    "sequence": 221,
                    "run_nonce": "",
                    "captured_ms": 1100,
                    "deaths": 3,
                    "phase": "dead",
                }
            )
            first = deepcopy(initial)
            first.update(sequence=11, captured_ms=1801000)
            await send(first)
            later = deepcopy(first)
            later.update(sequence=12, captured_ms=1802000)
            later["bot"]["xp"] = 999999
            await send(later)
            if mode in {
                "complete",
                "peer_crash",
                "reload",
                "operator_close",
                "close_false",
                "operator_proof",
                "cutoff_stalled",
                "cutoff_proposal_timeout",
            }:
                fence = await receive("telemetry_fence")
                if mode == "peer_crash":
                    peer.close()  # Kernel has no receiver; cached periodic status cannot finish.
                elif mode == "reload":
                    await send(
                        {
                            "version": 1,
                            "type": "hello",
                            "world": "new-world",
                            "capabilities": CAPS,
                        }
                    )
                else:
                    await send(
                        {
                            "version": 1,
                            "type": "telemetry_status",
                            "world": "world-a",
                            "bot_id": 7,
                            "captured_ms": 1802000,
                            "issued_sequence": 221,
                            "accepted_sequence": 221,
                            "pending_frames": 0,
                            "pending_bytes": 0,
                            "overflow_frames": 0,
                            "discarded_frames": 0,
                            "fence_nonce": fence["nonce"],
                        }
                    )
        await asyncio.wait_for(worker, timeout=7)
        ending = Store(config.state_file).get("run_stop", "end")
        assert ending is not None
        if mode == "complete":
            assert ending["reason"] == "completed"
            assert ending["observed_seconds"] == 1800
            events = list(ReplayReader(config.recording.path).all_events("qa:7"))
            assert (
                next(e for e in events if e["key"] == "horizon-final-sample")["data"][
                    "bot"
                ]["xp"]
                == 1000
            )
            assert any(e["key"] == "native-terminal-fence" for e in events)
        else:
            assert ending["reason"] != "completed", ending
            if mode.startswith("cutoff_"):
                expected = mode.removeprefix("cutoff_")
                assert cutoff_reasons == [expected]
                assert ending["reason"] == expected
                reader = ReplayReader(config.recording.path)
                assert not reader.run("qa:7")["incomplete"]
                assert any(
                    e["key"] == "native-terminal-fence"
                    for e in reader.all_events("qa:7")
                )
    finally:
        stopped.set()
        if not worker.done():
            await asyncio.wait_for(worker, timeout=7)
        peer.close()
        os.close(descriptor)
