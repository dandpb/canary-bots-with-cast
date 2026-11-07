"""Opt-in fixture-owned final XP/level witness. Never changes native completion."""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
import time

PROFILE = "fixture_shutdown_v1"
MAX_BYTES = 4 * 1024**2
BINDING_KEYS = {
    "run_id",
    "stop_nonce",
    "bot_id",
    "native_source",
    "worker_source",
    "fixture_sha256",
    "canary_sha256",
    "engine_sha256",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    return json.loads(
        data,
        object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")),
    )


def integer(value):
    return type(value) is int and 0 <= value <= 2**53 - 1


def binding_bytes(binding):
    if (
        set(binding) != BINDING_KEYS
        or not integer(binding["bot_id"])
        or binding["bot_id"] == 0
    ):
        raise ValueError("invalid persistence binding")
    import re

    for key in BINDING_KEYS - {"bot_id"}:
        value = binding[key]
        pattern = (
            r"[A-Za-z0-9:_-]{1,160}"
            if key == "run_id"
            else r"[a-f0-9]{40}"
            if key in {"native_source", "worker_source"}
            else r"[a-f0-9]{64}"
        )
        if not isinstance(value, str) or not re.fullmatch(pattern, value):
            raise ValueError("invalid binding " + key)
    return json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()


def read_private(path, maximum=MAX_BYTES):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > maximum:
            raise ValueError("invalid or oversized persistence file")
        data = stream.read(maximum + 1)
        if len(data) > maximum:
            raise ValueError("oversized persistence file")
        return data


def exclusive(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def publish_request(directory, binding):
    binding_bytes(binding)
    started = {"wall": time.time(), "monotonic": time.monotonic()}
    body = (
        "q72-stop-v1\n" + binding["run_id"] + "\n" + binding["stop_nonce"] + "\n"
    ).encode()
    partial = directory / "stop.request.partial"
    exclusive(partial, body)
    os.link(partial, directory / "stop.request", follow_symlinks=False)
    partial.unlink()
    sync_directory(directory)
    return {
        "started": started,
        "published": {"wall": time.time(), "monotonic": time.monotonic()},
        "request_sha256": digest(body),
    }


def parse_journal(raw, binding, world):
    binding_bytes(binding)
    if len(raw) > MAX_BYTES or not raw.endswith(b"\n"):
        raise ValueError("truncated or oversized audit")
    lines = raw.splitlines(keepends=True)
    if not 3 <= len(lines) <= 8192:
        raise ValueError("missing audit coverage")
    rows = [strict_json(line) for line in lines]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("audit records must be objects")
    runtime_id = rows[0].get("runtime_id")
    if not integer(runtime_id) or runtime_id == 0:
        raise ValueError("missing runtime identity")
    previous = None
    for index, row in enumerate(rows, 1):
        if (
            type(row.get("version")) is not int
            or row.get("version") != 1
            or row.get("binding") != binding
            or row.get("sequence") != index
            or not integer(row.get("sequence"))
            or not integer(row.get("runtime_id"))
            or row.get("runtime_id") != runtime_id
            or row.get("clock") != "unix_epoch_ms"
            or not all(
                integer(row.get(k)) for k in ("epoch_ms", "xp", "level", "deaths")
            )
        ):
            raise ValueError("audit identity/schema/sequence changed")
        if row["kind"] != "post_remove" and row.get("removed") is not False:
            raise ValueError("player removed before terminal boundary")
        if row["deaths"] != 0 or row.get("kind") == "death":
            raise ValueError("zero-death persistence profile violated")
        if previous:
            if any(row[key] < previous[key] for key in ("epoch_ms", "xp", "level")):
                raise ValueError("audit clock/progression reset")
            if (
                row["kind"] != "post_remove"
                and row["epoch_ms"] - previous["epoch_ms"] > 5000
            ):
                raise ValueError("audit coverage gap")
        if row["kind"] != "attached":
            status = strict_json(row["native_status_json"])
            if (
                not isinstance(status, dict)
                or status.get("world") != world
                or status.get("roster") != [binding["bot_id"]]
                or status.get("mode") != "shadow"
            ):
                raise ValueError("native world/roster changed")
        previous = row
    if rows[0]["kind"] != "attached" or any(
        row["kind"] != "heartbeat" for row in rows[1:-2]
    ):
        raise ValueError("unexpected lifecycle or reattachment")
    pre, post = rows[-2:]
    if pre["kind"] != "pre_shutdown" or post["kind"] != "post_remove":
        raise ValueError("terminal pair missing")
    if (
        pre.get("game_state") != "normal"
        or pre.get("removed") is not False
        or post.get("game_state") != "shutdown"
        or post.get("removed") is not True
        or post.get("roster_absent") is not True
        or not integer(post.get("pre_sequence"))
        or post.get("pre_sequence") != pre["sequence"]
        or post.get("pre_sha256") != digest(lines[-2])
        or post["epoch_ms"] - pre["epoch_ms"] > 210000
        or any(post[key] != pre[key] for key in ("xp", "level", "deaths"))
    ):
        raise ValueError("shutdown changed character or lacks removed-player seal")
    return rows


def durable_complete(directory, binding, world, request, exit_code):
    """Called only after owned game exit; fsync is not a SQL-derived observation."""
    if type(exit_code) is not int or exit_code != 0:
        raise ValueError("unclean game exit")
    stopped = {"wall": time.time(), "monotonic": time.monotonic()}
    path = directory / "audit.jsonl"
    raw = read_private(path)
    rows = parse_journal(raw, binding, world)
    expected_request = (
        "q72-stop-v1\n" + binding["run_id"] + "\n" + binding["stop_nonce"] + "\n"
    ).encode()
    if read_private(directory / "stop.request", 512) != expected_request or request[
        "request_sha256"
    ] != digest(expected_request):
        raise ValueError("stop request changed")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    sync_directory(directory)
    receipt = {
        "version": 1,
        "profile": PROFILE,
        "binding_sha256": digest(binding_bytes(binding)),
        "journal_sha256": digest(raw),
        "journal_bytes": len(raw),
        "terminal_sequence": rows[-1]["sequence"],
        "game_exit_code": exit_code,
        "request": request,
        "stopped": stopped,
        "durable": {"wall": time.time(), "monotonic": time.monotonic()},
    }
    partial = directory / "durable-complete.json.partial"
    exclusive(partial, (json.dumps(receipt, sort_keys=True) + "\n").encode())
    os.link(partial, directory / "durable-complete.json", follow_symlinks=False)
    partial.unlink()
    sync_directory(directory)
    return receipt


def verify_native_zero_deaths(events, admitted):
    """Reconcile the independent zero-death journal with ALL native diagnostics.

    Do not score/filter/sort this stream: post-horizon counters can contradict D0.
    Recorder omits telemetry bot_id/sequence from data, preserving them in its key.
    """
    previous = None
    frame = None
    seen = {}
    for event in events:
        data = event.get("data")
        if not isinstance(data, dict):
            raise TypeError("native evidence must be an object")
        wrapped = data.get("phase") == "post_horizon_telemetry"
        if wrapped or data.get("phase") == "post_horizon_sample":
            data = data.get("data")
            if not isinstance(data, dict):
                raise TypeError("post-horizon telemetry must be an object")
        native_frame = (
            wrapped
            or event.get("key", "").startswith("native:")
            or data.get("phase") in {"alive", "dead", "hibernated", "unavailable"}
        )
        bot = data.get("bot")
        if (
            isinstance(bot, dict)
            and "deaths" in bot
            and (
                not integer(bot["deaths"])
                or bot["deaths"] != 0
                or data.get("world") != admitted["world"]
                or not integer(bot.get("id"))
                or bot["id"] != admitted["bot_id"]
                or not integer(data.get("captured_ms"))
            )
        ):
            raise ValueError("native observation contradicts zero-death audit")
        if "deaths" not in data and not native_frame:
            continue
        wall = event.get("wall")
        if (
            not integer(data.get("deaths"))
            or not integer(data.get("captured_ms"))
            or data.get("world") != admitted["world"]
            or (
                "bot_id" in data
                and (
                    not integer(data["bot_id"]) or data["bot_id"] != admitted["bot_id"]
                )
            )
            or type(wall) not in (int, float)
            or not math.isfinite(wall)
            or wall < 0
        ):
            raise ValueError("native zero-death evidence invalid")
        if data["deaths"] != 0 or data.get("phase") in {
            "dead",
            "hibernated",
            "unavailable",
        }:
            raise ValueError("native death evidence contradicts zero-death audit")
        if previous and (data["captured_ms"] < previous[0] or wall < previous[1]):
            raise ValueError("native death evidence chronology regressed")
        previous = data["captured_ms"], wall
        if native_frame:
            prefix = f"native:{admitted['world']}:{admitted['bot_id']}:"
            key = event.get("key", "")
            suffix = key.removeprefix(prefix)
            if (
                not key.startswith(prefix)
                or not suffix.isascii()
                or not suffix.isdecimal()
            ):
                raise ValueError("native telemetry identity missing")
            sequence = int(suffix)
            if "sequence" in data and (
                not integer(data["sequence"]) or data["sequence"] != sequence
            ):
                raise ValueError("native telemetry sequence conflict")
            if sequence in seen:
                if seen[sequence] != data:
                    raise ValueError("native telemetry identity conflict")
                continue
            if frame is not None and sequence != frame + 1:
                raise ValueError("native telemetry chronology/gap conflict")
            seen[sequence] = data
            frame = sequence


def verify_terminal(events, trial):
    """Validate opt-in terminal evidence, returning an independent final-state pair."""
    bundle = trial["persistence"]["terminal"]
    if not isinstance(bundle, dict) or not isinstance(
        bundle.get("durable_complete"), dict
    ):
        raise TypeError("terminal evidence must be objects")
    binding = bundle["binding"]
    binding_bytes(binding)
    admitted_event = next(e for e in events if e.get("key") == "native-admission")
    admitted = next(e["data"] for e in events if e.get("key") == "native-admission")
    frozen = next(e["data"] for e in events if e.get("key") == "horizon-final-sample")
    fence = next(e["data"] for e in events if e.get("key") == "native-terminal-fence")
    seal = next(
        e["data"] for e in events if e.get("key") == "supervisor-native-qualified"
    )
    if (
        admitted["source"] != binding["native_source"]
        or admitted["source_dirty"] is not False
        or admitted["bot_id"] != binding["bot_id"]
        or type(admitted["deaths"]) is not int
        or admitted["deaths"] != 0
        or seal.get("after_flush") is not True
        or seal.get("reason") != "completed"
        or fence.get("world") != admitted["world"]
        or fence.get("bot_id") != binding["bot_id"]
        or not fence.get("fence_nonce")
        or fence["fence_nonce"] == admitted["nonce"]
        or frozen["captured_ms"] - admitted["captured_ms"] < 1800000
    ):
        raise ValueError("native completion prerequisite missing")
    verify_native_zero_deaths(events, admitted)
    # These identities are supplied by the actual replay/fixture consumer, not SQL.
    if (
        binding["run_id"] != trial["persistence_run_id"]
        or binding["fixture_sha256"] != trial["persistence_fixture_sha256"]
    ):
        raise ValueError("replay/fixture identity mismatch")
    if not isinstance(bundle.get("journal"), str):
        raise TypeError("journal must be raw UTF8 text")
    raw = bundle["journal"].encode("utf8")
    rows = parse_journal(raw, binding, admitted["world"])
    seal_event = next(
        e for e in events if e.get("key") == "supervisor-native-qualified"
    )
    if rows[0]["epoch_ms"] > math.ceil(admitted_event["wall"] * 1000):
        raise ValueError("death audit attached after admission")
    if (
        trial["persistence"]["terminal"]["durable_complete"]["request"]["started"][
            "wall"
        ]
        < seal_event["wall"]
    ):
        raise ValueError("shutdown requested before native post-close seal")
    receipt = bundle["durable_complete"]
    if (
        type(receipt.get("version")) is not int
        or receipt.get("profile") != PROFILE
        or receipt.get("version") != 1
        or receipt.get("binding_sha256") != digest(binding_bytes(binding))
        or receipt.get("journal_sha256") != digest(raw)
        or receipt.get("journal_bytes") != len(raw)
        or receipt.get("terminal_sequence") != rows[-1]["sequence"]
        or type(receipt.get("game_exit_code")) is not int
        or receipt.get("game_exit_code") != 0
    ):
        raise ValueError("durability receipt mismatch")
    request_body = (
        "q72-stop-v1\n" + binding["run_id"] + "\n" + binding["stop_nonce"] + "\n"
    ).encode()
    if receipt["request"]["request_sha256"] != digest(request_body):
        raise ValueError("request hash mismatch")
    clock = trial["persistence"]
    stages = [
        receipt["request"]["started"],
        receipt["request"]["published"],
        receipt["stopped"],
        receipt["durable"],
    ]
    for domain in ("wall", "monotonic"):
        if any(not isinstance(stage, dict) for stage in stages):
            raise ValueError("host timing stages must be objects")
        values = [s[domain] for s in stages]
        if any(
            type(v) not in (int, float) or not math.isfinite(v) for v in values
        ) or values != sorted(values):
            raise ValueError("host stop timing invalid")
    mono = [
        receipt["request"]["started"]["monotonic"],
        receipt["request"]["published"]["monotonic"],
        clock["game_stopped_monotonic"],
        receipt["stopped"]["monotonic"],
        receipt["durable"]["monotonic"],
        clock["sql_read_started_monotonic"],
        clock["sql_read_monotonic"],
    ]
    if any(
        type(v) not in (int, float) or not math.isfinite(v) for v in mono
    ) or mono != sorted(mono):
        raise ValueError("host monotonic SQL timing invalid")
    pre, post = rows[-2:]
    if not (
        receipt["request"]["started"]["wall"] == clock["game_stop_started_wall"]
        and clock["game_stopped_wall"]
        <= receipt["stopped"]["wall"]
        <= receipt["durable"]["wall"]
        and math.floor(clock["game_stop_started_wall"] * 1000)
        <= pre["epoch_ms"]
        <= post["epoch_ms"]
        <= math.ceil(clock["game_stopped_wall"] * 1000)
        and clock["game_stopped_wall"]
        <= receipt["durable"]["wall"]
        <= clock["sql_read_started_wall"]
        <= clock["sql_read_wall"]
        and clock["world"] == admitted["world"]
        and clock["bot_id"] == binding["bot_id"]
    ):
        raise ValueError("witness/stop/SQL timing invalid")
    saved = trial["saved_character"]
    if not isinstance(saved, dict):
        raise TypeError("saved character must be an object")
    if any(
        type(saved.get(sql)) is not int or saved[sql] != value
        for sql, value in (
            ("id", binding["bot_id"]),
            ("experience", post["xp"]),
            ("level", post["level"]),
        )
    ):
        raise ValueError("saved_progress_mismatch")
    return {"source": PROFILE, "pre": pre, "post": post, "durable_complete": receipt}
