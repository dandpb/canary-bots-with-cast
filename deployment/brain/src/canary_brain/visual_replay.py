"""Package recorded game packets and encode frames rendered by OTClient."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from bisect import bisect_right
from itertools import pairwise
from pathlib import Path
from typing import Any

from .recording import ReplayReader, canonical
from .timelapse import publish_video

MAX_TAPE = 128 * 1024 * 1024
MAX_LINE = 2 * 65535 + 32
MAX_DURATION = 30 * 60 * 1000
MAX_EVENTS = 20000
PLAYBACK_HOLD_MS = 1000
PACKET = re.compile(rb"< ([0-9]{1,7}) ([0-9a-f]+)\n")
FRAME = re.compile(r"frame-(\d{7})\.png")


def capture_info(directory: Path) -> dict[str, Any]:
    with (directory / "capture.json").open("rb") as source:
        raw = source.read(4097)
    if len(raw) > 4096:
        raise ValueError("capture receipt is too large")
    info = json.loads(raw)
    if not isinstance(info, dict) or set(info) != {
        "schema",
        "bot_id",
        "protocol",
        "wall_start_ms",
        "last_packet_ms",
        "packets",
        "bootstrap_map",
        "reason",
    }:
        raise ValueError("invalid capture receipt")
    if (
        any(
            type(info[key]) is not int
            for key in (
                "schema",
                "bot_id",
                "protocol",
                "wall_start_ms",
                "last_packet_ms",
                "packets",
            )
        )
        or info["schema"] != 1
        or info["protocol"] != 1500
        or info["bot_id"] <= 0
        or not 0 < info["wall_start_ms"] < 2**53
        or not 0 < info["last_packet_ms"] <= MAX_DURATION
        or not 1 <= info["packets"] <= MAX_TAPE // 6
        or info["bootstrap_map"] is not True
        or type(info["reason"]) is not str
        or info["reason"]
        not in {"player_removed", "time_limit", "queue_limit", "storage_limit"}
    ):
        raise ValueError("capture has no playable, finalized game tape")
    return info


def copy_tape(source: Path, target: Path, info: dict[str, Any]) -> tuple[str, int]:
    checksum = hashlib.sha256()
    count = size = 0
    last = -1
    first_map = None
    bootstrap = [b"43", b"17", b"0f", b"64"]
    with source.open("rb") as tape, target.open("xb") as output:
        while row := tape.readline(MAX_LINE + 1):
            size += len(row)
            match = PACKET.fullmatch(row)
            if size > MAX_TAPE or len(row) > MAX_LINE or not match:
                raise ValueError("invalid game packet line or tape exceeds its limit")
            elapsed = int(match[1])
            payload = match[2]
            if not last <= elapsed <= info["last_packet_ms"] or len(payload) % 2:
                raise ValueError("invalid packet clock or hex length")
            if count == 0 and not payload.startswith(b"0043"):
                raise ValueError(
                    "expected OTClient features with the first-packet padding"
                )
            opcode = payload[2:4] if count == 0 else payload[:2]
            if bootstrap and opcode == bootstrap[0]:
                bootstrap.pop(0)
                if not bootstrap:
                    first_map = elapsed
            checksum.update(row)
            output.write(row)
            count += 1
            last = elapsed
    if first_map is None or count != info["packets"] or last != info["last_packet_ms"]:
        raise ValueError("packet stream does not match the capture receipt")
    return checksum.hexdigest(), first_map


FIELDS = {
    "decision": ("decision_id", "phase", "candidate", "proposed", "selected", "source"),
    "proposal": ("decision_id", "candidate", "source"),
    "intent": (
        "decision_id",
        "action_id",
        "phase",
        "candidate",
        "action",
        "status",
        "mode",
    ),
    "outcome": ("action_id", "status", "reason"),
    "reward": ("action_id", "phase", "status", "reward"),
    "gap": ("reason", "dropped"),
    "segment": ("reason",),
}
CAPTIONS = {
    "decision": "Decisão",
    "proposal": "Proposta",
    "intent": "Ação",
    "outcome": "Servidor",
    "reward": "Recompensa",
    "segment": "Telemetria",
    "gap": "Lacuna",
    "milestone": "Observação",
}


def event_projection(event: dict[str, Any]) -> dict[str, Any] | None:
    kind, data = event["kind"], event["data"]
    if kind == "sample":
        bot = data["bot"]
        return {
            key: bot[key]
            for key in ("position", "xp", "level", "health", "mana", "potions")
            if key in bot
        }
    if kind not in FIELDS:
        return None
    projected = {
        key: data[key][:120] if isinstance(data[key], str) else data[key]
        for key in FIELDS[kind]
        if isinstance(data.get(key), (str, int, float, bool))
    }
    if kind == "outcome" and isinstance(data.get("metrics"), dict):
        projected["metrics"] = {
            key: value
            for key in ("xp_delta", "supply_delta", "deaths", "progress")
            if type(value := data["metrics"].get(key)) in {int, float}
        }
    return projected


def select_events(
    reader: ReplayReader, run: str, info: dict[str, Any], offset_ms: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if abs(offset_ms) > 60000:
        raise ValueError("a clock correction must be within one minute")
    events: list[dict[str, Any]] = []
    with reader.snapshot() as snapshot:
        metadata = snapshot.run(run)
        if metadata["manifest"]["bot_id"] != info["bot_id"]:
            raise ValueError("telemetry and visual capture have different bot IDs")
        for event in snapshot.all_events(run):
            visual_ms = round(event["wall"] * 1000) - info["wall_start_ms"] + offset_ms
            if not 0 <= visual_ms <= info["last_packet_ms"]:
                continue
            payload = event_projection(event)
            if payload is None:
                continue
            if len(events) == MAX_EVENTS:
                raise ValueError("visual timeline exceeds 20,000 events")
            events.append(
                {
                    "visual_ms": visual_ms,
                    "recording_ms": event["t_ms"],
                    "kind": event["kind"],
                    "data": payload,
                }
            )
    events.sort(key=lambda event: event["visual_ms"])
    return metadata, events


def pack_visual(
    capture: Path,
    reader: ReplayReader,
    run: str,
    output: Path,
    *,
    offset_ms: int = 0,
) -> dict[str, Any]:
    info = capture_info(capture)
    metadata, events = select_events(reader, run, info, offset_ms)
    output.mkdir()
    digest, first_map = copy_tape(capture / "game.cam", output / "game.cam", info)
    timeline = canonical(events).encode("utf-8")
    (output / "timeline.json").write_bytes(timeline)
    script = Path(__file__).with_name("visual_capture.lua").read_text(encoding="utf-8")
    script_bytes = (
        f"local firstMapMs, lastPacketMs = {first_map}, {info['last_packet_ms']}\n"
        f'local tapeSha = "{digest}"\n' + script
    ).encode("utf-8")
    (output / "otclientrc.lua").write_bytes(script_bytes)
    manifest = {
        "schema": 1,
        "kind": "otclient-game-replay",
        "capture": info,
        "first_map_ms": first_map,
        "tape_sha256": digest,
        "timeline_sha256": hashlib.sha256(timeline).hexdigest(),
        "player_script_sha256": hashlib.sha256(script_bytes).hexdigest(),
        "run": metadata["id"],
        "synthetic_telemetry": metadata.get("manifest", {}).get("synthetic"),
        "telemetry_status": metadata["status"],
        "telemetry_incomplete": metadata["incomplete"],
        "telemetry_events": len(events),
        "telemetry_gap_markers": sum(event["kind"] == "gap" for event in events),
        "telemetry_segment_markers": sum(
            event["kind"] == "segment" for event in events
        ),
        "clock": {
            "basis": "host wall clock at recorder ingestion",
            "offset_ms": offset_ms,
        },
    }
    # Published last so partial directories never look like complete packages.
    (output / "manifest.json").write_text(canonical(manifest), encoding="utf-8")
    return manifest


def stage_visual_client(
    package: Path, source: Path, output: Path, mode: str
) -> dict[str, Any]:
    source, output = source.resolve(), output.resolve()
    if output == source or source in output.parents:
        raise ValueError(
            "the isolated playback directory must be outside the source runtime"
        )
    manifest = json.loads((package / "manifest.json").read_bytes())
    if manifest["kind"] != "otclient-game-replay" or mode not in {"watch", "frames"}:
        raise ValueError("provide a finalized visual package and valid playback mode")
    trusted_script = (
        Path(__file__).with_name("visual_capture.lua").read_text(encoding="utf-8")
    )
    first, last = manifest["first_map_ms"], manifest["capture"]["last_packet_ms"]
    if (
        type(first) is not int
        or type(last) is not int
        or not 0 <= first < last <= MAX_DURATION
    ):
        raise ValueError("invalid visual window")
    digest = manifest["tape_sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("invalid tape digest")
    script = (
        f"local firstMapMs, lastPacketMs = {first}, {last}\n"
        f'local tapeSha = "{digest}"\n' + trusted_script
    ).encode()
    if hashlib.sha256(script).hexdigest() != manifest["player_script_sha256"]:
        raise ValueError("player script does not match the locally installed version")
    init = (source / "init.lua").read_text(encoding="utf-8")
    config_gate = "g_configs.loadSettings('/config.otml')"
    if (
        init.count(config_gate) != 1
        or init.count("local ENABLE_SERVERS = true") != 1
        or not (source / "data" / "things" / "1500").is_dir()
    ):
        raise ValueError("choose the OTClient runtime with local protocol 1500 assets")
    exe = source / "otclient.exe"
    if not exe.is_file():
        raise ValueError("the supplied runtime has no otclient.exe")
    output.mkdir()
    runtime, profile = output / "runtime", output / "profile"
    runtime.mkdir()
    profile.mkdir()
    (runtime / "records").mkdir()
    tape = runtime / "records" / "game.cam"
    checksum, first_map = copy_tape(package / "game.cam", tape, manifest["capture"])
    if checksum != manifest["tape_sha256"] or first_map != first:
        raise ValueError("game tape does not match the manifest")
    # Hold the final viewport long enough for the screenshot dispatcher to
    # render the last packet. An empty feature list changes no game state.
    with tape.open("ab") as playback:
        playback.write(f"< {last + PLAYBACK_HOLD_MS} 430000\n".encode("ascii"))
    shutil.copytree(source / "modules", runtime / "modules")
    shutil.copytree(
        source / "data",
        runtime / "data",
        ignore=lambda path, names: (
            [name for name in names if name != "1500"]
            if Path(path) == source / "data" / "things"
            else []
        ),
    )
    for binary in [exe, *source.glob("*.dll")]:
        shutil.copy2(binary, runtime / binary.name)
    # Leave the original init, runtime and user's configuration untouched.
    profile_lua = json.dumps(profile.as_posix(), ensure_ascii=False)
    init = init.replace("local ENABLE_SERVERS = true", "local ENABLE_SERVERS = false")
    init = init.replace("g_modules.ensureModuleLoaded('client_mods')", "")
    init = init.replace(
        config_gate,
        f"""
local replayWriteDir = g_resources.getWriteDir():gsub('\\\\', '/'):gsub('/+$', '')
if replayWriteDir:lower() ~= ({profile_lua}):lower() then
    error("Expected the private replay profile before reading settings")
end
{config_gate}
g_configs.getSettings():setValue('locale', 'pt')""",
    )
    init = init.replace("Servers_init = {}", "Services = {}\nServers_init = {}", 1)
    (runtime / "init.lua").write_text(init, encoding="utf-8")
    (runtime / "otclientrc.lua").write_bytes(script)
    argv = [str(runtime / exe.name), f"--user-dir={profile}", f"--bot-replay={mode}"]
    launch = {
        "argv": argv,
        "working_directory": str(runtime),
        "frames": str(profile / "frames"),
        "playback_hold_ms": PLAYBACK_HOLD_MS,
    }
    (output / "launch.json").write_text(canonical(launch), encoding="utf-8")
    return launch


def timestamp(milliseconds: int) -> str:
    seconds, ms = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"


def milestones(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Show measured progress changes, without attributing them to an action."""
    displayed = []
    previous = None
    for event in events:
        kind, data = event["kind"], event["data"]
        if kind != "sample":
            if kind in {"gap", "segment"}:
                previous = None
            displayed.append(event)
            continue
        if previous is not None:
            old_position, position = previous.get("position"), data.get("position")
            if old_position and position and old_position[2] != position[2]:
                displayed.append(
                    {
                        **event,
                        "kind": "milestone",
                        "data": {"label": f"Andar {old_position[2]} → {position[2]}"},
                    }
                )
            for field, title in (
                ("xp", "XP"),
                ("level", "Nível"),
                ("potions", "Poções"),
            ):
                before, after = previous.get(field), data.get(field)
                if type(before) is int and type(after) is int and before != after:
                    displayed.append(
                        {
                            **event,
                            "kind": "milestone",
                            "data": {"label": f"{title} {before} → {after}"},
                        }
                    )
        previous = data
    return displayed


def subtitles(events: list[dict[str, Any]], start: int, end: int, speed: float) -> str:
    # At high speed group a second's worth of video, preserving the actual
    # action details in timeline.json even when a subtitle must omit lines.
    blocks: dict[int, list[str]] = {}
    for event in events:
        at, kind, data = event["visual_ms"], event["kind"], event["data"]
        if not start <= at < end or kind == "sample":
            continue
        label = {
            "decision": data.get("selected")
            or data.get("candidate")
            or data.get("phase"),
            "proposal": data.get("candidate"),
            "intent": data.get("action") or data.get("phase"),
            "outcome": data.get("status"),
            "reward": data.get("reward"),
            "segment": "novo segmento de telemetria",
            "gap": data.get("reason") or "lacuna de telemetria",
            "milestone": data.get("label"),
        }[kind]
        text = " ".join(str(label or kind).split()).replace("<", "").replace(">", "")
        block = blocks.setdefault(int((at - start) / speed) // 1000 * 1000, [])
        line = f"{CAPTIONS[kind]} — {text}"
        if line not in block:
            block.append(line)
    duration = int((end - start) / speed)
    return "\n\n".join(
        f"{index}\n{timestamp(at)} --> {timestamp(min(duration, at + 1000))}\n"
        + "\n".join(
            lines[:3]
            + ([f"+{len(lines) - 3} eventos na timeline"] if len(lines) > 3 else [])
        )
        for index, (at, lines) in enumerate(blocks.items(), 1)
        if at < duration
    )


def chapter_metadata(
    events: list[dict[str, Any]], start: int, end: int, speed: float
) -> tuple[str, int]:
    duration = max(1, round((end - start) / speed))
    chapters = [(0, "Início")]
    for event in events:
        at, kind, data = event["visual_ms"], event["kind"], event["data"]
        video_ms = round((at - start) / speed)
        if not 0 < video_ms < duration or video_ms - chapters[-1][0] < 1000:
            continue
        if kind == "decision" and data.get("phase") == "selected":
            title = f"Decisão — {data.get('selected', '')}"
        elif kind == "outcome" and data.get("status") in {
            "completed",
            "failed",
            "rejected",
        }:
            title = f"Servidor — {data.get('reason') or data['status']}"
        elif kind == "milestone":
            title = str(data["label"])
        else:
            continue
        escaped = re.sub(r"([\\=;#])", r"\\\1", " ".join(title.split()))
        chapters.append((video_ms, escaped))
    metadata = [";FFMETADATA1"]
    for (at, title), until in zip(chapters, [t for t, _ in chapters[1:]] + [duration]):
        metadata.extend(
            (
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={at}",
                f"END={until}",
                f"title={title}",
            )
        )
    return "\n".join(metadata) + "\n", len(chapters)


def export_visual_video(
    package: Path, frames: Path, output: Path, *, speed: float = 8, fps: int = 24
) -> dict[str, Any]:
    if not math.isfinite(speed) or not 1 <= speed <= 120 or not 1 <= fps <= 60:
        raise ValueError("speed must be 1–120x and FPS must be 1–60")
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe or output.suffix.lower() != ".mp4":
        raise ValueError(
            "visual video requires FFmpeg, FFprobe and an .mp4 destination"
        )
    manifest = json.loads((package / "manifest.json").read_bytes())
    timeline = (package / "timeline.json").read_bytes()
    if (
        manifest["kind"] != "otclient-game-replay"
        or hashlib.sha256(timeline).hexdigest() != manifest["timeline_sha256"]
    ):
        raise ValueError("visual timeline does not match the manifest")
    if (frames / "tape-sha256.txt").read_text(encoding="ascii") != manifest[
        "tape_sha256"
    ]:
        raise ValueError("OTClient frames belong to a different tape")
    selected = sorted(
        (int(match[1]), path)
        for path in frames.iterdir()
        if (match := FRAME.fullmatch(path.name)) and path.is_file()
    )
    if not 2 <= len(selected) <= 14400:
        raise ValueError("provide two to 14,400 OTClient frame screenshots")
    start, end = selected[0][0], selected[-1][0]
    expected_start, expected_end = (
        manifest["first_map_ms"],
        manifest["capture"]["last_packet_ms"],
    )
    max_gap = max(right[0] - left[0] for left, right in pairwise(selected))
    if not expected_start <= start < end <= expected_end or max_gap > 500:
        raise ValueError("frames are out of capture bounds or have a gap above 500 ms")
    if start - expected_start > 1000 or expected_end - end > 500:
        raise ValueError("frames do not cover the recorded viewport window")
    count = max(1, math.ceil((end - start) * fps / (1000 * speed)))
    if count > 14400:
        raise ValueError("visual video exceeds 14,400 output frames")
    with tempfile.TemporaryDirectory() as scratch:
        work = Path(scratch)
        times = [at for at, _ in selected]
        images = hashlib.sha256()
        last_source = None
        staged: Path | None = None
        total_bytes = 0
        for index in range(count):
            at = start + index * 1000 * speed / fps
            source = selected[bisect_right(times, at) - 1][1]
            target = work / f"image-{index:05d}.png"
            if source != last_source:
                size = source.stat().st_size
                total_bytes += size
                if size > 16 * 1024 * 1024 or total_bytes > 4 * 1024**3:
                    raise ValueError("frame staging size exceeds its limit")
                shutil.copyfile(source, target)
                with target.open("rb") as image:
                    images.update(source.name.encode("ascii"))
                    images.update(hashlib.file_digest(image, "sha256").digest())
                staged, last_source = target, source
            else:
                assert staged is not None
                os.link(staged, target)
        events = milestones(json.loads(timeline))
        caption = subtitles(events, start, end, speed)
        chapters, chapter_count = chapter_metadata(events, start, end, speed)
        (work / "chapters.txt").write_text(chapters, encoding="utf-8")
        args = [ffmpeg, "-v", "error", "-framerate", str(fps), "-i", "image-%05d.png"]
        if caption:
            (work / "timeline.srt").write_text(caption + "\n", encoding="utf-8")
            args += ["-i", "timeline.srt"]
        args += [
            "-f",
            "ffmetadata",
            "-i",
            "chapters.txt",
            "-map_chapters",
            "2" if caption else "1",
        ]
        if caption:
            args += ["-c:s", "mov_text", "-disposition:s:0", "default"]
        encoded = work / "rendered.mp4"
        subprocess.run(
            [
                *args,
                "-vf",
                "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                "-frames:v",
                str(count),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(encoded),
            ],
            cwd=work,
            check=True,
            timeout=300,
        )
        probe = json.loads(
            subprocess.check_output(
                [
                    ffprobe,
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-count_frames",
                    "-show_entries",
                    "stream=nb_read_frames,width,height,duration:chapter=id",
                    "-of",
                    "json",
                    str(encoded),
                ],
                timeout=180,
            )
        )
        verified = probe["streams"][0]
        if (
            int(verified["nb_read_frames"]) != count
            or abs(float(verified["duration"]) - count / fps) > 1 / fps
            or len(probe.get("chapters", ())) != chapter_count
        ):
            raise ValueError(
                "encoded video does not match the requested frames/duration"
            )
        with encoded.open("rb") as artifact:
            video_digest = hashlib.file_digest(artifact, "sha256").hexdigest()
        evidence = {
            **manifest,
            "kind": "otclient-timelapse",
            "start_ms": start,
            "end_ms": end,
            "input_frames": len(selected),
            "max_frame_gap_ms": max_gap,
            "unrendered_lead_ms": start - expected_start,
            "unrendered_tail_ms": expected_end - end,
            "frames": count,
            "fps": fps,
            "speed": speed,
            "video_seconds": count / fps,
            "width": verified["width"],
            "height": verified["height"],
            "subtitles": bool(caption),
            "chapters": chapter_count,
            "frame_sha256": images.hexdigest(),
            "video_sha256": video_digest,
        }
        publish_video(encoded, output, evidence)
        return evidence
