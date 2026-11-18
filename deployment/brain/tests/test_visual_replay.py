import hashlib
import json
import shutil
import struct
import subprocess
import zlib
from pathlib import Path

import pytest

from canary_brain import visual_replay as replay


def visual_fixture(path):
    path.mkdir()
    info = {
        "schema": 1,
        "bot_id": 7,
        "protocol": 1500,
        "wall_start_ms": 1_000_000,
        "last_packet_ms": 1000,
        "packets": 5,
        "bootstrap_map": True,
        "reason": "player_removed",
    }
    tape = b"< 0 00430000\n< 1 17\n< 2 0f\n< 10 64\n< 1000 83\n"
    (path / "capture.json").write_text(json.dumps(info))
    (path / "game.cam").write_bytes(tape)
    return info, tape


def test_visual_pack_binds_timeline_and_keeps_clock_limit(tmp_path, monkeypatch):
    info, tape = visual_fixture(tmp_path / "native")
    sample = {
        "visual_ms": 15,
        "recording_ms": 250,
        "kind": "gap",
        "data": {"reason": "dropped"},
    }
    calls = []

    def select(reader, run, capture, offset):
        calls.append((run, capture, offset))
        return {"id": run, "status": "closed", "incomplete": True}, [sample]

    monkeypatch.setattr(replay, "select_events", select)
    box = tmp_path / "package"
    manifest = replay.pack_visual(tmp_path / "native", None, "run", box, offset_ms=4)
    assert calls == [("run", info, 4)]
    assert manifest["first_map_ms"] == 10
    assert manifest["telemetry_gap_markers"] == 1
    assert manifest["tape_sha256"] == hashlib.sha256(tape).hexdigest()
    assert (box / "game.cam").read_bytes() == tape
    assert json.loads((box / "timeline.json").read_bytes()) == [sample]
    assert (
        (box / "otclientrc.lua")
        .read_text()
        .startswith("local firstMapMs, lastPacketMs = 10, 1000")
    )
    with pytest.raises(FileExistsError):
        replay.pack_visual(tmp_path / "native", None, "run", box)


def test_stage_uses_new_profile_and_excludes_live_inputs(tmp_path, monkeypatch):
    visual_fixture(tmp_path / "native")
    monkeypatch.setattr(
        replay,
        "select_events",
        lambda *args: ({"id": "fixture", "status": "closed", "incomplete": False}, []),
    )
    package = tmp_path / "package"
    replay.pack_visual(tmp_path / "native", None, "fixture", package)
    source = tmp_path / "original"
    for name in ("data/things/1500", "data/things/1525", "modules", "mods"):
        (source / name).mkdir(parents=True)
    init = (
        "local ENABLE_SERVERS = true\n"
        "Servers_init = {}\n"
        "g_configs.loadSettings('/config.otml')\n"
        "g_modules.ensureModuleLoaded('client_mods')"
    )
    (source / "init.lua").write_text(init)
    (source / "otclient.exe").write_bytes(b"fixture")
    (source / "config.otml").write_text("original profile")
    target = tmp_path / "isolated"
    launch = replay.stage_visual_client(package, source, target, "watch")
    assert launch["argv"][1] == f"--user-dir={target / 'profile'}"
    staged = target / "runtime"
    original = (package / "game.cam").read_bytes()
    assert (
        staged / "records" / "game.cam"
    ).read_bytes() == original + b"< 2000 430000\n"
    rewritten = (staged / "init.lua").read_text()
    assert rewritten.index("getWriteDir") < rewritten.index("loadSettings")
    assert "ENABLE_SERVERS = false" in rewritten and "client_mods" not in rewritten
    assert not (staged / "config.otml").exists()
    assert not (staged / "data/things/1525").exists()
    assert not (staged / "mods").exists()
    assert (source / "init.lua").read_text() == init


@pytest.mark.parametrize(
    "fault",
    [
        lambda tape: tape.replace(b"< 1000", b"> 1000"),
        lambda tape: tape.replace(b"0f", b"0ff"),
        lambda tape: tape.replace(b"0043", b"43"),
        lambda tape: tape.replace(b"< 1000 ", b"< 9 "),
        lambda tape: tape[:-1],
        lambda tape: tape.replace(b"< 1 ", b"< 3 "),
        lambda tape: tape.replace(b" 0f", b" 1a"),
    ],
)
def test_packet_verification_rejects_bad_bootstrap_or_stream(tmp_path, fault):
    info, tape = visual_fixture(tmp_path / "capture")
    source = tmp_path / "bad.cam"
    source.write_bytes(fault(tape))
    with pytest.raises(ValueError):
        replay.copy_tape(source, tmp_path / "copy.cam", info)


def test_select_events_joins_clock_and_drops_private_fields():
    from contextlib import nullcontext

    class Reader:
        def snapshot(self):
            return nullcontext(self)

        def run(self, run):
            return {"id": run, "manifest": {"bot_id": 7}}

        def all_events(self, _run):
            yield {
                "wall": 1000.5,
                "t_ms": 21,
                "kind": "decision",
                "data": {"selected": "retreat", "private": "never export"},
            }
            yield {
                "wall": 1002,
                "t_ms": 55,
                "kind": "outcome",
                "data": {"status": "accepted"},
            }

    info = {"bot_id": 7, "wall_start_ms": 1_000_000, "last_packet_ms": 1000}
    _, events = replay.select_events(Reader(), "run", info, offset_ms=25)
    assert events == [
        {
            "visual_ms": 525,
            "recording_ms": 21,
            "kind": "decision",
            "data": {"selected": "retreat"},
        }
    ]
    with pytest.raises(ValueError, match="different bot IDs"):
        replay.select_events(Reader(), "run", {**info, "bot_id": 8}, 25)


def test_video_milestones_are_observed_and_do_not_bridge_a_gap():
    def sample(at, floor, xp):
        return {
            "kind": "sample",
            "visual_ms": at,
            "data": {"position": [1, 1, floor], "xp": xp},
        }

    gap = {"kind": "gap", "visual_ms": 2000, "data": {"reason": "missing"}}
    events = replay.milestones(
        [sample(0, 7, 500), sample(1500, 6, 510), gap, sample(2500, 5, 1000)]
    )
    caption = replay.subtitles(events, 0, 3000, 1)
    assert "Andar 7 → 6" in caption and "XP 500 → 510" in caption
    assert "missing" in caption and "510 → 1000" not in caption
    metadata, count = replay.chapter_metadata(events, 0, 3000, 1)
    assert "title=Andar 7 → 6" in metadata and count == 2


def png(value: int) -> bytes:
    def chunk(name, data):
        return (
            struct.pack(">I", len(data))
            + name
            + data
            + struct.pack(">I", zlib.crc32(name + data))
        )

    row = b"\0" + bytes([value, 0, 128]) * 32
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 32, 16, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(row * 16))
        + chunk(b"IEND", b"")
    )


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="requires real FFmpeg and FFprobe",
)
def test_visual_video_uses_client_frames_and_subtitles(tmp_path):
    frames, box = tmp_path / "frames", tmp_path / "package"
    frames.mkdir()
    box.mkdir()
    events = b'[{"visual_ms":500,"kind":"outcome","data":{"status":"accepted"}}]'
    (box / "timeline.json").write_bytes(events)
    manifest = {
        "kind": "otclient-game-replay",
        "timeline_sha256": hashlib.sha256(events).hexdigest(),
        "tape_sha256": "ab" * 32,
        "first_map_ms": 0,
        "capture": {"last_packet_ms": 1000},
    }
    (box / "manifest.json").write_text(json.dumps(manifest))
    (frames / "tape-sha256.txt").write_text(manifest["tape_sha256"])
    for at in range(0, 1001, 125):
        (frames / f"frame-{at:07}.png").write_bytes(png(at % 255))
    output = tmp_path / "visual.mp4"
    result = replay.export_visual_video(box, frames, output, speed=2, fps=24)
    assert result["subtitles"]
    assert result["chapters"] == 1
    assert (result["width"], result["height"], result["frames"]) == (32, 16, 12)
    assert hashlib.sha256(output.read_bytes()).hexdigest() == result["video_sha256"]
    assert json.loads((tmp_path / "visual.mp4.json").read_bytes()) == result
    for at in (125, 250, 375, 500):
        (frames / f"frame-{at:07}.png").unlink()
    with pytest.raises(ValueError, match="have a gap"):
        replay.export_visual_video(box, frames, tmp_path / "gap.mp4")


@pytest.mark.skipif(not shutil.which("g++"), reason="requires native C++ compiler")
def test_native_queue_creates_compatible_tape_and_omits_chat(tmp_path, monkeypatch):
    src = Path(__file__).resolve().parents[3] / "src"
    harness = tmp_path / "main.cpp"
    harness.write_text(
        """
#include "server/network/protocol/visual_replay.hpp"
#include <array>
#include <cassert>

int main() {
    assert(!VisualReplay::start(8, 1500));
    auto writer = VisualReplay::start(7, 1500);
    assert(writer);
    assert(!VisualReplay::start(7, 1500));
    writer->record(std::array<uint8_t, 3>{0x43, 0, 0});
    writer->record(std::array<uint8_t, 1>{0x17});
    writer->record(std::array<uint8_t, 1>{0xAA});
    writer->record(std::array<uint8_t, 1>{0x0F});
    writer->record(std::array<uint8_t, 1>{0x64});
    std::this_thread::sleep_for(std::chrono::milliseconds(5));
    writer->record(std::array<uint8_t, 1>{0x83});
    writer->finish();
    writer->record(std::array<uint8_t, 1>{0x85});
    assert(!writer->active());
}
"""
    )
    exe = tmp_path / "harness"
    subprocess.run(
        [
            "g++",
            "-std=c++20",
            "-pthread",
            "-Wall",
            "-Wextra",
            "-Werror",
            f"-I{src}",
            str(harness),
            str(src / "server/network/protocol/visual_replay.cpp"),
            "-o",
            str(exe),
        ],
        timeout=25,
        check=True,
    )
    capture = tmp_path / "camera"
    monkeypatch.setenv("CANARY_VISUAL_REPLAY_BOT", "7")
    monkeypatch.setenv("CANARY_VISUAL_REPLAY_DIR", str(capture))
    subprocess.run([exe], timeout=5, check=True)
    info = replay.capture_info(capture)
    assert info["packets"] == 5
    assert info["reason"] == "player_removed"
    replay.copy_tape(capture / "game.cam", tmp_path / "verified.cam", info)
    tape = (capture / "game.cam").read_text()
    assert " aa\n" not in tape
    assert " 85\n" not in tape
