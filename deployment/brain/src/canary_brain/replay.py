"""Evidence-based replay metrics and portable, integrity-checked archives."""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
import zipfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .protocol import Bot
from .recording import Manifest, RecordingStore, ReplayReader, canonical, public_data

METRICS_VERSION = 2


class ArchivedEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    id: int = Field(gt=0)
    key: str = Field(min_length=1, max_length=256)
    segment: str = Field(min_length=1, max_length=128)
    t_ms: int = Field(ge=0, le=2**63 - 1)
    wall: float = Field(ge=0)
    kind: str
    data: dict[str, Any]


class ArchivedRun(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    id: str
    manifest: dict[str, Any]
    status: str
    incomplete: bool
    started: float = Field(ge=0)
    updated: float = Field(ge=0)
    event_count: int = Field(ge=0)
    duration_ms: int = Field(ge=0)


def summarize(
    events: Iterable[dict[str, Any]], manifest: dict[str, Any]
) -> dict[str, Any]:
    first: dict[str, Any] | None = None
    last: dict[str, Any] | None = None
    active_ms = 0
    deaths: dict[str, int] = {}
    death_baselines: dict[str, int] = {}
    requests: dict[str, dict[str, Any]] = {}
    proposals: set[str] = set()
    decisions: set[str] = set()
    accepted: set[str] = set()
    terminal: dict[str, str] = {}
    gaps = interventions = overrides = recovery = 0
    gap_times: list[int] = []
    first_help: int | None = None
    latency: list[int] = []
    levels: list[dict[str, Any]] = []
    milestones: list[dict[str, Any]] = []
    end = 0
    prior: dict[str, Any] | None = None
    native_samples = 0
    native_control_ms = 0
    native_active_ms = 0
    previous_native: dict[str, Any] | None = None
    defeats = 0
    stalled_ms = 0
    progress_since = 0
    last_progress_sample: dict[str, Any] | None = None
    stall_observable = False
    for event in events:
        kind, data, t = event["kind"], event["data"], event["t_ms"]
        end = max(end, t)
        if kind == "sample":
            first = first or event
            last = event
            if prior and prior["segment"] == event["segment"]:
                elapsed = t - prior["t_ms"]
                if 0 <= elapsed <= 5000 and data["world"] == prior["data"]["world"]:
                    active_ms += elapsed
            prior = event
            bot = data["bot"]
            if last_progress_sample is not None:
                old = last_progress_sample["data"]["bot"]
                interval = t - last_progress_sample["t_ms"]
                same_goal = data.get("objective_generation") == last_progress_sample[
                    "data"
                ].get("objective_generation")
                progressed = (
                    bot["position"] != old["position"]
                    or bot["xp"] != old["xp"]
                    or bot.get("objective_defeats", 0) > old.get("objective_defeats", 0)
                )
                working = (
                    bot.get("objective_running", False)
                    and bot.get("objective") in {"hunt", "resupply", "retreat"}
                    and not data.get("nearby")
                    and bot["health"] >= 80
                )
                if interval > 5000 or not same_goal or progressed or not working:
                    progress_since = t
                elif 0 <= interval <= 5000:
                    stall_observable = True
                    stalled_ms += min(interval, max(0, t - progress_since - 300000))
            else:
                progress_since = t
            last_progress_sample = event
        elif kind == "gap":
            gaps += 1
            gap_times.append(t)
            prior = None
            last_progress_sample = None
            previous_native = None
        elif kind == "lifecycle" and "deaths" in data:
            native_samples += 1
            if (
                previous_native
                and previous_native["segment"] == event["segment"]
                and previous_native["data"]["world"] == data["world"]
            ):
                interval = t - previous_native["t_ms"]
                if (
                    0 <= interval <= 2000
                    and previous_native["data"].get("phase") == "alive"
                ):
                    native_active_ms += interval
                    if previous_native["data"].get("model_owned") is False:
                        native_control_ms += interval
            previous_native = event
            world = data["world"]
            if world not in deaths:
                death_baselines[world] = (
                    int(data["deaths"])
                    if not deaths and not manifest.get("experiment")
                    else 0
                )
            old = deaths.get(world, death_baselines[world])
            deaths[world] = max(old, int(data["deaths"]))
            if deaths[world] > old:
                milestones.append(
                    {
                        "t_ms": t,
                        "kind": "death",
                        "text": "Morte confirmada pelo servidor",
                    }
                )
            if data.get("phase") == "alive" and old > 0:
                # Phase transitions are inspected directly in the event stream.
                pass
        elif kind == "level":
            levels.append(dict(t_ms=t, **data))
            milestones.append(
                {"t_ms": t, "kind": "level", "text": f"Nível {data['to']}"}
            )
        elif kind == "decision":
            identity = data.get("decision_id", "")
            if data.get("phase") == "requested":
                decisions.add(identity)
            if (
                data.get("phase") == "model_proposed"
                and data.get("source") != "single_candidate_rule"
            ):
                proposals.add(identity)
            if data.get("phase") == "selected" and data.get("source") == "policy":
                overrides += 1
        elif kind == "request":
            identity = data["request_id"]
            requests.setdefault(identity, {}).update(data)
            if data.get("phase") == "finished":
                latency.append(data.get("elapsed_ms", 0))
        elif kind == "outcome":
            identity = data["action_id"]
            if data["status"] in {"accepted", "running"}:
                accepted.add(identity)
            elif identity not in terminal:
                terminal[identity] = data["status"]
                defeats += max(0, int(data.get("metrics", {}).get("defeats_delta", 0)))
                if data["status"] == "completed":
                    milestones.append(
                        {
                            "t_ms": t,
                            "kind": "completed",
                            "text": data.get("reason", "Ação concluída"),
                        }
                    )
        elif kind == "operator":
            if data.get("operation") in {
                "pause",
                "resume",
                "recover",
                "retreat",
                "avoid",
                "note",
                "allow_route",
                "chat_act",
            } and not data.get("automatic"):
                interventions += 1
                first_help = t if first_help is None else first_help
                milestones.append(
                    {
                        "t_ms": t,
                        "kind": "operator",
                        "text": "Intervenção humana: " + data["operation"],
                    }
                )
            if data.get("operation") == "recover" and data.get("automatic"):
                recovery += 1
    xp = (
        last["data"]["bot"]["xp"] - first["data"]["bot"]["xp"]
        if first and last
        else None
    )
    wall_ms = max(0, last["t_ms"] - first["t_ms"]) if first and last else 0
    calendar_elapsed_ms = (
        int((last["wall"] - first["wall"]) * 1000) if first and last else None
    )
    spent = sum(int(r.get("spent_nanousd", 0)) for r in requests.values())
    reserved = sum(int(r.get("reserved_nanousd", 0)) for r in requests.values())
    failures = sum(r.get("phase") == "failed" for r in requests.values())
    no_inference = manifest.get("provider") in {"native", "fake"}
    money_known = bool(requests) or no_inference
    if native_samples:
        active_ms = native_active_ms
    return {
        "version": METRICS_VERSION,
        "xp_delta": xp,
        "xp_per_wall_hour": xp * 3600000 / wall_ms
        if xp is not None and wall_ms
        else None,
        "xp_per_active_hour": xp * 3600000 / active_ms
        if xp is not None and active_ms
        else None,
        "active_ms": active_ms,
        "wall_ms": wall_ms,
        "calendar_elapsed_ms": calendar_elapsed_ms,
        "duration_ms": end,
        "deaths": sum(value - death_baselines[world] for world, value in deaths.items())
        if native_samples
        else None,
        "initial_native_deaths_excluded": sum(death_baselines.values()),
        "deaths_observed": bool(native_samples),
        "interventions": interventions,
        "intervention_free_ms": first_help if first_help is not None else end,
        "intervention_free_censored": first_help is None,
        "automatic_recoveries_requested": recovery,
        "model_decisions": len(decisions),
        "valid_proposals": len(proposals),
        "policy_overrides": overrides,
        "accepted_actions": len(accepted),
        "completed_actions": sum(s == "completed" for s in terminal.values()),
        "failed_actions": sum(s == "failed" for s in terminal.values()),
        "provider_failures": failures,
        "spent_nanousd": spent if money_known else None,
        "reserved_nanousd": reserved if money_known else None,
        "xp_per_dollar": xp * 1e9 / spent
        if xp is not None and spent and not reserved
        else None,
        "latency_p50_ms": statistics.median(latency) if latency else None,
        "latency_p95_ms": sorted(latency)[max(0, math.ceil(len(latency) * 0.95) - 1)]
        if latency
        else None,
        "gaps": gaps,
        "gap_times": gap_times,
        "levels": levels,
        "milestones": milestones,
        "native_control_ms": native_control_ms if native_samples else None,
        "native_fallback_ms": (0 if no_inference else native_control_ms)
        if native_samples
        else None,
        "stalled_ms": stalled_ms if stall_observable else None,
        "confirmed_objective_defeats": defeats,
        "limitations": [
            "Sampled observations; hidden events are not reconstructed.",
            "Elapsed rates use the recorded monotonic timeline; restart gaps retain their recorded estimates.",
            "Fallback coverage and stalled duration require explicit timed evidence; unavailable is not zero.",
        ],
    }


def summary(reader: ReplayReader, run: str) -> dict[str, Any]:
    metadata = reader.run(run)
    return {
        **metadata,
        "metrics": summarize(reader.all_events(run), metadata["manifest"]),
    }


def campaign(reader: ReplayReader, runs: list[str]) -> dict[str, Any]:
    if not runs or len(runs) > 100:
        raise ValueError("select one to 100 independent runs")
    rows = [summary(reader, run) for run in dict.fromkeys(runs)]
    signatures = {
        (
            r["manifest"]["scenario"],
            r["manifest"]["initial_sha256"],
            r["manifest"]["memory_mode"],
        )
        for r in rows
    }
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(row["manifest"]["participant"], []).append(row)
    aggregates = []
    for participant, samples in groups.items():
        values = [
            s["metrics"]["xp_per_wall_hour"]
            for s in samples
            if s["metrics"]["xp_per_wall_hour"] is not None
        ]
        n = len(values)
        aggregates.append(
            {
                "participant": participant,
                "attempts": len(samples),
                "usable_progress_runs": n,
                "xp_per_wall_hour_mean": statistics.mean(values) if values else None,
                "xp_per_wall_hour_std": statistics.stdev(values) if n > 1 else None,
                "statuses": [s["status"] for s in samples],
                "incomplete": sum(s["incomplete"] for s in samples),
            }
        )
    return {
        "runs": rows,
        "participants": aggregates,
        "comparable": len(signatures) == 1
        and all(r["manifest"]["initial_sha256"] for r in rows),
        "verdict": "descriptive_only",
        "warning": "Independent runs are the experimental units. No winner is inferred from this summary.",
    }


def export_archive(reader: ReplayReader, run: str, output: Path) -> None:
    with reader.snapshot() as snapshot:
        _export_archive(snapshot, run, output)


def _export_archive(reader: ReplayReader, run: str, output: Path) -> None:
    metadata = reader.run(run)
    hashes: dict[str, str] = {}
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:

        def write(name: str, value: Any) -> None:
            encoded = canonical(public_data(value)).encode()
            archive.writestr(name, encoded)
            hashes[name] = hashlib.sha256(encoded).hexdigest()

        write("run.json", metadata)
        batch = []
        segment = 0
        for event in reader.all_events(run):
            batch.append(event)
            if len(batch) == 1000:
                write(f"events-{segment:06d}.json", batch)
                segment += 1
                batch = []
        if batch:
            write(f"events-{segment:06d}.json", batch)
        archive.writestr("integrity.json", canonical({"version": 1, "sha256": hashes}))


def import_archive(path: Path, destination: Path) -> str:
    # Validate everything before mutating the destination. Never extract member paths.
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if (
            len(infos) > 10002
            or len({i.filename for i in infos}) != len(infos)
            or sum(i.file_size for i in infos) > 512 * 1024 * 1024
        ):
            raise ValueError("archive exceeds bounds or repeats members")
        integrity = json.loads(archive.read("integrity.json"))
        if integrity.get("version") != 1 or not isinstance(
            integrity.get("sha256"), dict
        ):
            raise ValueError("unsupported archive")
        hashes = integrity["sha256"]
        if set(hashes) != {i.filename for i in infos} - {"integrity.json"}:
            raise ValueError("archive member manifest mismatch")
        decoded = {}
        for name, expected in hashes.items():
            if name != "run.json" and not re_event_name(name):
                raise ValueError("unexpected archive member")
            encoded = archive.read(name)
            if hashlib.sha256(encoded).hexdigest() != expected:
                raise ValueError("archive integrity failure")
            decoded[name] = json.loads(encoded)
    metadata = ArchivedRun.model_validate(decoded["run.json"]).model_dump()
    if metadata.get("status") not in {
        "running",
        "completed",
        "failed",
        "budget_stop",
        "interrupted",
    }:
        raise ValueError("invalid archived run state")
    manifest = Manifest.model_validate(metadata["manifest"])
    if metadata["id"] != manifest.run_id:
        raise ValueError("archived run identity mismatch")
    all_events = [
        event
        for name in sorted(decoded)
        if re_event_name(name)
        for event in decoded[name]
    ]
    for event in all_events:
        ArchivedEvent.model_validate(event)
        canonical(event)
        if not isinstance(event, dict) or event.get("kind") not in {
            "sample",
            "decision",
            "proposal",
            "intent",
            "outcome",
            "request",
            "operator",
            "lifecycle",
            "gap",
            "segment",
            "level",
            "configuration",
        }:
            raise ValueError("invalid archived event")
        if (
            type(event.get("t_ms")) is not int
            or event["t_ms"] < 0
            or not isinstance(event.get("data"), dict)
        ):
            raise ValueError("invalid archived time or payload")
        if event["kind"] == "sample":
            Bot.model_validate(event["data"]["bot"])
        if (
            event["kind"] == "lifecycle"
            and "deaths" in event["data"]
            and (
                type(event["data"]["deaths"]) is not int
                or event["data"]["deaths"] < 0
                or not isinstance(event["data"].get("world"), str)
            )
        ):
            raise ValueError("invalid native lifecycle evidence")
    if len({event["key"] for event in all_events}) != len(all_events) or metadata.get(
        "event_count"
    ) != len(all_events):
        raise ValueError("archive repeats or omits events")
    if metadata["duration_ms"] != max((e["t_ms"] for e in all_events), default=0):
        raise ValueError("archive duration differs from its events")
    store = RecordingStore(destination)
    store.import_run(manifest, metadata, all_events)
    return manifest.run_id


def re_event_name(name: str) -> bool:
    return (
        name.startswith("events-")
        and name.endswith(".json")
        and len(name) == 18
        and name[7:13].isdigit()
    )


def export_report(reader: ReplayReader, runs: list[str], output: Path) -> None:
    with reader.snapshot() as snapshot:
        _export_report(snapshot, runs, output)


def _export_report(reader: ReplayReader, runs: list[str], output: Path) -> None:
    """Standalone HTML for bounded reports; ZIP keeps full, potentially large history."""
    if not 1 <= len(runs) <= 4:
        raise ValueError("a portable report compares one to four runs")
    metadata = [reader.run(run) for run in runs]
    if sum(r["event_count"] for r in metadata) > 20000:
        raise ValueError(
            "HTML report exceeds 20,000 events; export the full ZIP archive instead"
        )
    payload = {
        "runs": metadata,
        "events": {run: list(reader.all_events(run)) for run in runs},
        "summaries": {run: summary(reader, run) for run in runs},
    }
    assets = Path(__file__).parent / "dashboard"
    html = (assets / "replay.html").read_text()
    css = (assets / "replay.css").read_text()
    js = (assets / "replay.js").read_text()
    encoded = (
        canonical(public_data(payload))
        .replace("<", "\\u003c")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    html = re.sub(
        r'<link[^>]+href="/replay.css"[^>]*>',
        lambda _match: "<style>" + css + "</style>",
        html,
    )
    html = html.replace('<script src="/replay.js" defer></script>', "")
    html = html.replace(
        "</body>",
        "<script>window.REPLAY_ARCHIVE="
        + encoded
        + ";</script><script>"
        + js.replace("</script", "<\\/script")
        + "</script></body>",
    )
    with output.open("x", encoding="utf-8") as destination:
        destination.write(html)
