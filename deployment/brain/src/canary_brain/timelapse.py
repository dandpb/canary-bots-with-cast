"""Offline sampled-map video, from one consistent recording snapshot. No model calls."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
from collections import deque
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from .protocol import Bot
from .recording import ReplayReader, canonical, digest

WIDTH, HEIGHT = 1280, 720
MAX_FRAMES = 14400
RENDERER_VERSION = 2


def sync_directory(path: Path) -> None:
    """Persist directory entries on POSIX; Windows does not expose this API."""
    if os.name == "posix":
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def destination_key(output: Path) -> str:
    return hashlib.sha256(os.fsencode(os.path.normcase(output.name))).hexdigest()


@contextmanager
def publication_lock(output: Path) -> Iterator[None]:
    """A persistent lock inode prevents recovery from racing a live publisher."""
    output.parent.mkdir(parents=True, exist_ok=True)
    path = output.parent / f".canary-publish-{destination_key(output)}.lock"
    with path.open("a+b") as handle:
        if sys.platform == "win32":
            import msvcrt

            if path.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise ValueError("video destination has an active publisher") from error
        else:
            import fcntl

            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ValueError("video destination has an active publisher") from error
        try:
            yield
        finally:
            if sys.platform == "win32":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def linked_to(staged: Path, final: Path) -> bool:
    try:
        source, destination = staged.lstat(), final.lstat()
        return stat.S_ISREG(source.st_mode) and os.path.samestat(source, destination)
    except FileNotFoundError:
        return False


def recover_publications(output: Path) -> None:
    """Called under the destination lock; journal paths never choose deletions."""
    sidecar = output.with_suffix(output.suffix + ".json")
    expected = {"version": 1, "video": output.name, "sidecar": sidecar.name}
    prefix = f".canary-video-{destination_key(output)}-"
    for directory in output.parent.glob(prefix + "*"):
        if directory.is_symlink() or not directory.is_dir():
            continue
        journal = directory / "transaction.json"
        try:
            transaction = json.loads(journal.read_text())
        except (FileNotFoundError, ValueError):
            # Before a durable journal there cannot be any published name.
            # Leave unrecognised staging alone rather than guessing ownership.
            continue
        if transaction not in (expected, {**expected, "committed": True}):
            continue
        pairs = [(directory / output.name, output), (directory / sidecar.name, sidecar)]
        owned = [linked_to(staged, final) for staged, final in pairs]
        if not transaction.get("committed") and not all(owned):
            for (staged, final), ours in zip(pairs, owned, strict=True):
                if ours and linked_to(staged, final):
                    final.unlink()
        # Both matching final names are a completed publication; retain them.
        sync_directory(output.parent)
        shutil.rmtree(directory)
        sync_directory(output.parent)


@contextmanager
def materialized_snapshot(reader: ReplayReader) -> Iterator[ReplayReader]:
    """Release the live database before rendering or waiting for the encoder."""
    with tempfile.TemporaryDirectory(prefix="canary-video-source-") as directory:
        path = Path(directory) / "recording.sqlite3"
        started = time.monotonic()

        def progress(status: int, remaining: int, total: int) -> None:
            if time.monotonic() - started > 10:
                raise TimeoutError("video source snapshot exceeded ten seconds")

        with reader.connect() as source, closing(sqlite3.connect(path)) as target:
            source.backup(target, pages=256, progress=progress)
        yield ReplayReader(path)


def publish_video(encoded: Path, output: Path, evidence: dict[str, Any]) -> None:
    """Recover a dead publisher, stage complete files and publish exclusively."""
    with publication_lock(output):
        recover_publications(output)
        _publish_video(encoded, output, evidence)


def _publish_video(encoded: Path, output: Path, evidence: dict[str, Any]) -> None:
    sidecar = output.with_suffix(output.suffix + ".json")
    with tempfile.TemporaryDirectory(
        prefix=f".canary-video-{destination_key(output)}-", dir=output.parent
    ) as directory:
        staged_video = Path(directory) / output.name
        staged_sidecar = Path(directory) / sidecar.name
        with (Path(directory) / "transaction.json").open(
            "x", encoding="utf-8"
        ) as journal:
            journal.write(
                canonical({"version": 1, "video": output.name, "sidecar": sidecar.name})
            )
            journal.flush()
            os.fsync(journal.fileno())
        with encoded.open("rb") as source, staged_video.open("xb") as target:
            shutil.copyfileobj(source, target)
            target.flush()
            os.fsync(target.fileno())
        with staged_sidecar.open("x", encoding="utf-8") as target_manifest:
            target_manifest.write(canonical(evidence))
            target_manifest.flush()
            os.fsync(target_manifest.fileno())
        sync_directory(Path(directory))
        sync_directory(output.parent)
        attempted: list[tuple[Path, Path]] = []
        try:
            for staged, final in ((staged_video, output), (staged_sidecar, sidecar)):
                # Same-filesystem links expose complete files without overwriting a
                # destination created after the initial existence check.
                # Register first so an interrupt immediately after link creation
                # still rolls back the new name; inode checks protect collisions.
                attempted.append((staged, final))
                os.link(staged, final)
                sync_directory(output.parent)
            # Recovery must not mistake interrupted staging cleanup for a partial
            # publication after either staged hard link has already been removed.
            marker = Path(directory) / "committed.tmp"
            with marker.open("x", encoding="utf-8") as committed:
                committed.write(
                    canonical(
                        {
                            "version": 1,
                            "video": output.name,
                            "sidecar": sidecar.name,
                            "committed": True,
                        }
                    )
                )
                committed.flush()
                os.fsync(committed.fileno())
            os.replace(marker, Path(directory) / "transaction.json")
            sync_directory(Path(directory))
        except BaseException:
            for staged, final in reversed(attempted):
                try:
                    if linked_to(staged, final):
                        final.unlink()
                except FileNotFoundError:
                    pass
            sync_directory(output.parent)
            raise
    sync_directory(output.parent)


def rendered_event(event: dict[str, Any]) -> dict[str, Any]:
    """Only values read by Projection/apply/frame or map bounds, in stream order."""
    kind, data = event["kind"], event["data"]
    if kind == "sample":
        bot = data["bot"]
        used = {
            key: bot[key]
            for key in ["position", "level", "xp", "health", "mana", "potions"]
        }
        used["name"] = bot["name"][:25]
        payload: dict[str, Any] = {"bot": used}
    else:
        payload = {"phase": str(data.get("phase", kind))[:90]}
        if kind == "request":
            for key in ["request_id", "spent_nanousd", "reserved_nanousd"]:
                if key in data:
                    payload[key] = data[key]
    return {"t_ms": event["t_ms"], "kind": kind, "data": payload}


def clock(milliseconds: int) -> str:
    seconds = max(0, milliseconds) // 1000
    return f"{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02}"


class Projection:
    def __init__(self, sample_ms: int) -> None:
        self.sample_ms = sample_ms
        self.bot: Bot | None = None
        self.sampled_at = -1
        self.uncertain = False
        self.trail: deque[list[int] | None] = deque(maxlen=300)
        self.requests: dict[str, tuple[int, int]] = {}
        self.spent = self.reserved = self.operators = 0
        self.last_event = "recording begins"

    def apply(self, event: dict[str, Any]) -> None:
        kind, data, at = event["kind"], event["data"], event["t_ms"]
        if kind == "sample":
            bot = Bot.model_validate(data["bot"])
            if (
                self.uncertain
                or self.sampled_at < 0
                or at - self.sampled_at > 3 * self.sample_ms
                or (self.bot and bot.position[2] != self.bot.position[2])
            ):
                self.trail.append(None)
            self.bot, self.sampled_at, self.uncertain = bot, at, False
            self.trail.append(bot.position)
        else:
            self.last_event = str(data.get("phase", kind))[:90]
        if kind in {"gap", "segment"}:
            self.uncertain = True
        if kind == "operator":
            self.operators += 1
        if kind == "request" and isinstance(data.get("request_id"), str):
            key = data["request_id"]
            old_spent, old_reserved = self.requests.get(key, (0, 0))
            spent, reserved = (
                data.get("spent_nanousd", old_spent),
                data.get("reserved_nanousd", old_reserved),
            )
            if (
                type(spent) is int
                and type(reserved) is int
                and spent >= 0
                and reserved >= 0
            ):
                self.requests[key] = spent, reserved
                self.spent += spent - old_spent
                self.reserved += reserved - old_reserved

    def frame(
        self,
        metadata: dict[str, Any],
        at: int,
        start: int,
        end: int,
        bounds: dict[int, list[int]],
    ) -> str:
        bot = self.bot
        stale = (
            self.uncertain
            or self.sampled_at < 0
            or at - self.sampled_at > 3 * self.sample_ms
        )
        floor = bot.position[2] if bot else next(iter(bounds))
        x0, y0, x1, y1 = bounds.get(floor, next(iter(bounds.values())))
        scale = min(810 / max(8, x1 - x0 + 6), 450 / max(8, y1 - y0 + 6))
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

        def xy(position: list[int]) -> tuple[float, float]:
            return 455 + (position[0] - cx) * scale, 370 + (position[1] - cy) * scale

        def text(
            x: int, y: int, content: str, size: int = 18, color: str = "#dbe7f4"
        ) -> str:
            return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}">{escape(content)}</text>'

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
            '<rect width="1280" height="720" fill="#0b1220"/>',
            '<g font-family="DejaVu Sans,sans-serif">',
            '<rect x="24" y="110" width="862" height="510" rx="16" fill="#132236"/>',
            '<rect x="906" y="110" width="350" height="510" rx="16" fill="#132236"/>',
        ]
        manifest = metadata["manifest"]
        parts.append(text(28, 42, "BOT BIOGRAPHY / TIMELAPSE", 24))
        label = (
            "SIMULATED FIXTURE" if manifest["synthetic"] else "SAMPLED POSITION REPLAY"
        )
        parts.append(
            text(
                28,
                76,
                f"{label}  |  {manifest['participant'][:36]} / {manifest['model'][:36]}",
                16,
                "#91a8bf",
            )
        )
        step = max(1, math.ceil(35 / scale))
        for x in range(
            math.floor((cx - 405 / scale) / step) * step,
            math.ceil(cx + 405 / scale),
            step,
        ):
            px, _ = xy([x, 0])
            parts.append(f'<path d="M {px:.1f},145 V 595" stroke="#20334a"/>')
        for y in range(
            math.floor((cy - 225 / scale) / step) * step,
            math.ceil(cy + 225 / scale),
            step,
        ):
            _, py = xy([0, y])
            parts.append(f'<path d="M 50,{py:.1f} H 860" stroke="#20334a"/>')
        points: list[str] = []
        for position in [*self.trail, None]:
            if position is None or position[2] != floor:
                if len(points) > 1:
                    parts.append(
                        f'<polyline points="{" ".join(points)}" fill="none" stroke="#39c9ae" stroke-width="3"/>'
                    )
                points = []
            else:
                px, py = xy(position)
                points.append(f"{px:.1f},{py:.1f}")
        if bot:
            px, py = xy(bot.position)
            color = "#738497" if stale else "#f2bd56"
            parts.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="9" fill="{color}" stroke="#fff" stroke-width="2"/>'
            )
            parts.append(
                text(
                    48,
                    138,
                    f"Floor {floor}  |  x={bot.position[0]}  y={bot.position[1]}",
                    16,
                )
            )
        parts.append(
            text(930, 152, bot.name[:25] if bot else "No observed position", 21)
        )
        parts.append(text(930, 190, f"Recorded clock  {clock(at)}", 17, "#f2bd56"))
        rows = [
            f"Level  {bot.level if bot else '?'}",
            f"XP  {bot.xp if bot else '?'}",
            f"Health  {bot.health if bot else '?'}%",
            f"Mana  {bot.mana if bot else '?'}%",
            f"Potions  {bot.potions if bot else '?'}",
            f"Settled  ${self.spent / 1e9:.6f}",
            f"Reserved  ${self.reserved / 1e9:.6f}",
            f"Operator events  {self.operators}",
        ]
        parts.extend(text(930, 238 + i * 34, value, 18) for i, value in enumerate(rows))
        parts.append(
            text(
                930,
                544,
                "GAP / last known state" if stale else "Observed sample",
                17,
                "#f2bd56" if stale else "#39c9ae",
            )
        )
        parts.append(
            text(930, 577, f"Sample at {clock(self.sampled_at)}", 16, "#91a8bf")
        )
        progress = (at - start) / max(1, end - start)
        parts.extend(
            [
                '<rect x="28" y="644" width="1224" height="5" fill="#20334a"/>',
                f'<rect x="28" y="644" width="{1224 * progress:.1f}" height="5" fill="#39c9ae"/>',
                text(28, 678, f"Last recorded event: {self.last_event}", 16),
                text(
                    28,
                    706,
                    "Sampled coordinates, no client footage. Missing observations are not reconstructed.",
                    14,
                    "#91a8bf",
                ),
                "</g></svg>",
            ]
        )
        return "".join(parts)


def export_video(
    reader: ReplayReader,
    run: str,
    output: Path,
    *,
    speed: float = 60,
    fps: int = 24,
    start_ms: int = 0,
    end_ms: int | None = None,
) -> dict[str, Any]:
    try:
        return _export_video(
            reader, run, output, speed=speed, fps=fps, start_ms=start_ms, end_ms=end_ms
        )
    except (TimeoutError, subprocess.SubprocessError) as error:
        raise ValueError("video export failed: " + str(error)[-1500:]) from error


def _export_video(
    reader: ReplayReader,
    run: str,
    output: Path,
    *,
    speed: float = 60,
    fps: int = 24,
    start_ms: int = 0,
    end_ms: int | None = None,
) -> dict[str, Any]:
    if not math.isfinite(speed) or not 1 <= speed <= 10000 or not 1 <= fps <= 60:
        raise ValueError("video speed must be 1..10000 and fps 1..60")
    sidecar = output.with_suffix(output.suffix + ".json")
    if output.suffix.lower() != ".mp4":
        raise ValueError("choose a new .mp4 output and sidecar path")
    with publication_lock(output):
        recover_publications(output)
        if output.exists() or sidecar.exists():
            raise ValueError("choose a new .mp4 output and sidecar path")
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise ValueError(
            "video export requires ffmpeg with librsvg/libx264 and ffprobe"
        )
    with materialized_snapshot(reader) as snapshot:
        metadata = snapshot.run(run)
        end = metadata["duration_ms"] if end_ms is None else end_ms
        if not 0 <= start_ms <= end <= metadata["duration_ms"]:
            raise ValueError("video window is outside the recorded timeline")
        count = max(1, math.ceil((end - start_ms) / (1000 * speed) * fps))
        if count > MAX_FRAMES or count / fps > 600:
            raise ValueError(
                "video exceeds 14400 frames or 600 seconds; shorten the window or increase speed"
            )
        bounds: dict[int, list[int]] = {}
        checksum = hashlib.sha256()
        used_checksum = hashlib.sha256()
        event_count = 0
        prior: Bot | None = None

        def bound(bot: Bot) -> None:
            x, y, z = bot.position
            value = bounds.setdefault(z, [x, y, x, y])
            value[:] = [
                min(value[0], x),
                min(value[1], y),
                max(value[2], x),
                max(value[3], y),
            ]

        for event in snapshot.ordered_events(run, end):
            checksum.update(
                canonical({k: v for k, v in event.items() if k != "id"}).encode()
                + b"\n"
            )
            used_checksum.update(canonical(rendered_event(event)).encode() + b"\n")
            event_count += 1
            if event["kind"] == "sample":
                bot = Bot.model_validate(event["data"]["bot"])
                if event["t_ms"] < start_ms:
                    prior = bot
                else:
                    bound(bot)
        if prior:
            bound(prior)
        if not bounds:
            raise ValueError("video requires at least one actual recorded position")
        with tempfile.TemporaryDirectory(prefix="canary-timelapse-") as directory:
            root = Path(directory)
            projection = Projection(metadata["manifest"]["sample_ms"])
            events = iter(snapshot.ordered_events(run, end))
            pending = next(events, None)
            for index in range(count):
                at = (
                    end
                    if count == 1
                    else start_ms + round((end - start_ms) * index / (count - 1))
                )
                while pending is not None and pending["t_ms"] <= at:
                    projection.apply(pending)
                    pending = next(events, None)
                (root / f"frame-{index:06d}.svg").write_text(
                    projection.frame(metadata, at, start_ms, end, bounds),
                    encoding="utf-8",
                )
            encoded = root / "timelapse.mp4"
            result = subprocess.run(
                [
                    ffmpeg,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-framerate",
                    str(fps),
                    "-threads",
                    "1",
                    "-filter_threads",
                    "1",
                    "-i",
                    str(root / "frame-%06d.svg"),
                    "-frames:v",
                    str(count),
                    "-c:v",
                    "libx264",
                    "-threads",
                    "2",
                    "-pix_fmt",
                    "yuv420p",
                    "-crf",
                    "22",
                    "-movflags",
                    "+faststart",
                    str(encoded),
                ],
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
            if result.returncode:
                raise ValueError(
                    "ffmpeg video rendering failed: " + result.stderr[-1500:]
                )
            verified = json.loads(
                subprocess.check_output(
                    [
                        ffprobe,
                        "-v",
                        "error",
                        "-count_frames",
                        "-show_entries",
                        "stream=nb_read_frames,width,height:format=duration",
                        "-of",
                        "json",
                        str(encoded),
                    ],
                    timeout=180,
                )
            )
            stream = verified["streams"][0]
            if (
                int(stream["nb_read_frames"]) != count
                or stream["width"] != WIDTH
                or stream["height"] != HEIGHT
                or abs(float(verified["format"]["duration"]) - count / fps) > 1 / fps
            ):
                raise ValueError(
                    "encoded video does not match the requested frames/duration"
                )
            manifest = metadata["manifest"]
            source_evidence = {
                "manifest": {
                    "participant": manifest["participant"][:36],
                    "model": manifest["model"][:36],
                    "synthetic": manifest["synthetic"],
                    "sample_ms": manifest["sample_ms"],
                },
                "status": metadata["status"],
                "events_until_ms": end,
                "rendered_events_sha256": used_checksum.hexdigest(),
            }
            render_input = {
                "renderer_version": RENDERER_VERSION,
                "source_evidence_sha256": digest(source_evidence),
                "start_ms": start_ms,
                "end_ms": end,
                "fps": fps,
                "speed": float(speed),
                "frames": count,
                "width": WIDTH,
                "height": HEIGHT,
                "font": "DejaVu Sans,sans-serif",
                "codec": {"name": "libx264", "pixel_format": "yuv420p", "crf": 22},
            }
            evidence = {
                "version": 2,
                "kind": "sampled-map-timelapse",
                "source_evidence": source_evidence,
                "source_evidence_sha256": digest(source_evidence),
                "render_input": render_input,
                "render_input_sha256": digest(render_input),
                "run": run,
                "manifest": metadata["manifest"],
                "source_status": metadata["status"],
                "source_metadata": metadata,
                "source_events_sha256": checksum.hexdigest(),
                "source_snapshot_sha256": digest(
                    {
                        "metadata": metadata,
                        "events_sha256": checksum.hexdigest(),
                        "events_until_ms": end,
                    }
                ),
                "source_events": event_count,
                "start_ms": start_ms,
                "end_ms": end,
                "frames": count,
                "fps": fps,
                "requested_speed": speed,
                "video_seconds": count / fps,
                "effective_speed": (end - start_ms) / 1000 / (count / fps),
                "width": WIDTH,
                "height": HEIGHT,
                "limitations": [
                    "sampled coordinates, not client capture",
                    "no interpolation across observation gaps",
                ],
            }
            with encoded.open("rb") as artifact:
                evidence["video_sha256"] = hashlib.file_digest(
                    artifact, "sha256"
                ).hexdigest()
            publish_video(encoded, output, evidence)
            return evidence
