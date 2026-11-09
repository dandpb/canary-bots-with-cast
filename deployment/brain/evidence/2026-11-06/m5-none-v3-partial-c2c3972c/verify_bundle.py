"""Verify this closed partial-evidence append using files only; no SQLite/API."""

import hashlib
import json
import math
import sys
import zipfile
from pathlib import Path

FINANCE_SHA = "3b956b89a2b93a53c0d8f483df140b56faad9687904cb5235cb5f5758b7397dd"
SOURCE = "7f2904e5827edc67997d309d453fa1d7371523cc"
# Original immutable outputs at publication 7bd0077f. Later validation cannot
# rewrite the canonical report or either closed probe to erase negative data.
CANONICAL_OUTPUT_SHA256 = {
    "report/report.json": "782a5ed3150491baa08912ae751deb26367874d93602e625f271b9c0d9033298",
    "report/report.md": "dde76924520e42993b0150f9525f59b2e18e62e960ca39e2116faa50ce0b50b0",
    "probe-metrics.json": "39904ccb53f493e115a634620e02704bc1d102939a895fa6199f9a44be135a06",
    "openai-probe-result.json": "51f32ee4159d4500bfc349d77d76eda18aee7cb93481f25c1b6b5a0fa781ef43",
    "gemini-probe-result.json": "3c3bc894373790c016af6c38bd2103c2b6f798085595f3b421fdd4240dbcf98e",
}


def require(value, message):
    if not value:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def amount(value):
    require(type(value) is int and value >= 0, "invalid monetary integer")
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def rendered_event(event):
    """Exact renderer-v2 projection, not a reconstruction of hidden gameplay."""
    kind, data = event["kind"], event["data"]
    if kind == "sample":
        bot = data["bot"]
        used = {
            k: bot[k] for k in ["position", "level", "xp", "health", "mana", "potions"]
        }
        used["name"] = bot["name"][:25]
        payload = {"bot": used}
    else:
        payload = {"phase": str(data.get("phase", kind))[:90]}
        if kind == "request":
            payload.update(
                {
                    k: data[k]
                    for k in ["request_id", "spent_nanousd", "reserved_nanousd"]
                    if k in data
                }
            )
    return {"t_ms": event["t_ms"], "kind": kind, "data": payload}


def verify_video(root, metadata, events):
    sidecar = load(root / "video/native-partial-60x.mp4.json")
    receipt = load(root / "video/verification-receipt.json")
    probe = load(root / "video/ffprobe.json")
    end = max(e["t_ms"] for e in events)
    ordered = sorted(events, key=lambda e: (e["t_ms"], e["id"]))
    raw_hash = hashlib.sha256(
        b"".join(
            canonical({k: v for k, v in e.items() if k != "id"}).encode() + b"\n"
            for e in ordered
        )
    ).hexdigest()
    used_hash = hashlib.sha256(
        b"".join(canonical(rendered_event(e)).encode() + b"\n" for e in ordered)
    ).hexdigest()
    require(
        sidecar["source_metadata"] == metadata
        and sidecar["manifest"] == metadata["manifest"]
        and sidecar["run"] == metadata["id"]
        and sidecar["source_status"] == metadata["status"],
        "video source scope differs",
    )
    require(
        sidecar["source_events"] == len(events)
        and sidecar["source_events_sha256"] == raw_hash
        and sidecar["source_snapshot_sha256"]
        == digest(
            {"metadata": metadata, "events_sha256": raw_hash, "events_until_ms": end}
        ),
        "video source snapshot differs",
    )
    evidence = {
        "manifest": {
            k: metadata["manifest"][k]
            for k in ["participant", "model", "synthetic", "sample_ms"]
        },
        "status": metadata["status"],
        "events_until_ms": end,
        "rendered_events_sha256": used_hash,
    }
    require(
        sidecar["source_evidence"] == evidence
        and sidecar["source_evidence_sha256"] == digest(evidence),
        "video evidence fingerprint differs",
    )
    frames = math.ceil(end / 1000 / 60 * 24)
    render = sidecar["render_input"]
    require(
        render["renderer_version"] == 2
        and render["font"] == "DejaVu Sans,sans-serif"
        and render["codec"]
        == {"name": "libx264", "pixel_format": "yuv420p", "crf": 22},
        "renderer-v2 parameters differ",
    )
    require(
        render["source_evidence_sha256"] == digest(evidence)
        and (
            render["start_ms"],
            render["end_ms"],
            render["fps"],
            render["speed"],
            render["frames"],
            render["width"],
            render["height"],
        )
        == (0, end, 24, 60.0, frames, 1280, 720)
        and sidecar["render_input_sha256"] == digest(render),
        "video render identity differs",
    )
    require(
        (
            sidecar["start_ms"],
            sidecar["end_ms"],
            sidecar["frames"],
            sidecar["fps"],
            sidecar["requested_speed"],
            sidecar["video_seconds"],
        )
        == (0, end, frames, 24, 60.0, frames / 24),
        "partial video duration/frame claims differ",
    )
    stream = probe["streams"][0]
    require(
        sidecar["version"] == 2
        and sidecar["kind"] == "sampled-map-timelapse"
        and (sidecar["width"], sidecar["height"]) == (1280, 720)
        and abs(sidecar["effective_speed"] - end / 1000 / (frames / 24)) < 1e-9,
        "video format/effective speed differs",
    )
    require(
        (
            stream["width"],
            stream["height"],
            stream["avg_frame_rate"],
            int(stream["nb_read_frames"]),
            float(probe["format"]["duration"]),
        )
        == (1280, 720, "24/1", frames, frames / 24),
        "ffprobe disagrees with partial render",
    )
    require(float(stream["duration"]) == frames / 24, "ffprobe stream duration differs")
    require(
        receipt["sidecar_sha256"] == sha(root / "video/native-partial-60x.mp4.json")
        and receipt["video_sha256"] == sidecar["video_sha256"]
        and (
            receipt["sample_span_ms"],
            receipt["recorded_envelope_ms"],
            receipt["frames"],
            receipt["fps"],
            receipt["video_seconds"],
        )
        == (220803, end, frames, 24, frames / 24),
        "video verification receipt differs",
    )
    require(
        receipt["ffprobe_checked"] is True
        and receipt["visual_review"] == "first_middle_final_frames_checked"
        and receipt["visual_frames"] == [0, 48, 95]
        and receipt["rendered_after_all_scored_trials_closed"] is True,
        "video review scope differs",
    )


def usage_cost(event, prices):
    usage = event["usage"]
    inputs, outputs = amount(usage["input_tokens"]), amount(usage["output_tokens"])
    details = usage["input_tokens_details"]
    cached, written = (
        amount(details.get("cached_tokens", 0)),
        amount(details.get("cache_write_tokens", 0)),
    )
    require(cached + written <= inputs, "invalid cached input counts")
    require(usage["total_tokens"] == inputs + outputs, "usage token total differs")
    write_price = amount(prices["cache_write_nanousd"]) if written else 0
    require(event["pricing_version"] == prices["version"], "price version differs")
    return (
        (inputs - cached - written) * amount(prices["input_nanousd"])
        + cached * amount(prices["cached_nanousd"])
        + written * write_price
        + outputs * amount(prices["output_nanousd"])
    )


def archive_data(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate archive member")
        require(
            all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in names),
            "unsafe archive name",
        )
        integrity = json.loads(archive.read("integrity.json"))
        require(
            set(integrity["sha256"]) == set(names) - {"integrity.json"},
            "archive inventory differs",
        )
        for name, expected in integrity["sha256"].items():
            require(
                hashlib.sha256(archive.read(name)).hexdigest() == expected,
                "archive hash differs",
            )
        meta = json.loads(archive.read("run.json"))
        events = [
            e
            for n in sorted(names)
            if n not in {"run.json", "integrity.json"}
            for e in json.loads(archive.read(n))
        ]
    require(meta["event_count"] == len(events), "archive event count differs")
    return meta, events


def verify(root):
    index = load(root / "checksums.json")
    files = {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and p != root / "checksums.json"
    }
    require(set(index) == files, "public inventory differs")
    for name, expected in index.items():
        path = root / name
        require(
            path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(),
            "unsafe public path",
        )
        require(sha(path) == expected, "public hash differs: " + name)
    for name, expected in CANONICAL_OUTPUT_SHA256.items():
        require(
            sha(root / name) == expected, "original canonical output changed: " + name
        )
    summary = load(root / "summary.json")
    report = load(root / "report/report.json")
    closure = load(root / "closure-projection.json")
    provenance = load(root / "input-and-source-provenance.json")
    acceptance = load(root / "report/acceptance.json")
    require(
        acceptance
        == {
            key: report[key]
            for key in [
                "ready_for_review",
                "financial_totals_complete",
                "financial_final",
                "findings",
                "verdict",
            ]
        },
        "acceptance contradicts canonical report",
    )
    require(
        summary["source_revision"] == provenance["source_revision"] == SOURCE,
        "producer differs",
    )
    require(
        summary["comparative_pilot_completed"] is False
        and summary["completed_game_runs"] == 0
        and summary["ai_game_runs_started"] == 0
        and summary["partial_native_runs"] == 1,
        "partial campaign forged as completed/AI gameplay",
    )
    require(
        len(summary["expected_runs"]) == 9
        and len(summary["not_started_reported_by_owner"]) == 8
        and summary["not_started_gameplay_metrics"] is None,
        "missing games forged as observations",
    )
    require(
        (
            report["expected_attempts"],
            report["recorded_attempts"],
            report["reviewed_attempts"],
        )
        == (9, 1, 1)
        and report["ready_for_review"] is False
        and len(report["findings"]) == 12,
        "canonical reporter findings erased",
    )
    require(
        sum(f["code"] == "missing_attempt_evidence" for f in report["findings"]) == 8,
        "eight missing attempts erased",
    )
    require(
        closure["execution_exit_code"] == 1
        and closure["campaign_result"]["campaign"] is None
        and closure["remaining_eight_not_started_reported_by_owner"] is True,
        "closed invocation scope differs",
    )
    require(
        len(closure["exact_projects_after_close"]) == 9
        and all(
            p["containers"] == p["networks"] == []
            for p in closure["exact_projects_after_close"]
        )
        and closure["native_trial"]["resources_cleaned"] is True
        and closure["native_trial"]["images_verified"] is True,
        "cleanup/actual image evidence differs",
    )
    require(
        summary["financial_final"] is report["financial_final"] is False
        and report["financial_totals_complete"] is True,
        "unknown liability finalized or totals changed",
    )
    financial_path = root / "finance-2000/none-v3-postclosure-financial.public.json"
    require(
        sha(financial_path) == FINANCE_SHA, "original final Finance receipt changed"
    )
    finance = load(financial_path)
    rows = load(root / "closed-executor-ledger.json")["requests"]
    by_id = {r["id"]: r for r in rows}
    financial = {r["request_id"]: r for r in finance["selected_requests"]}
    require(
        len(rows) == len(by_id) == len(financial) == 18
        and set(by_id) == set(financial),
        "eighteen financial identities differ",
    )
    for key, row in by_id.items():
        other = financial[key]
        amount(row["reserved"])
        if row["spent"] is not None:
            amount(row["spent"])
        require(
            (row["run_id"], row["reserved"], row["spent"])
            == (other["run_id"], other["reserved_nanousd"], other["spent_nanousd"]),
            "per-request Finance mismatch",
        )
    known = sum(r["spent"] for r in rows if r["spent"] is not None)
    unknown = sum(r["reserved"] for r in rows if r["spent"] is None)
    require((known, unknown) == (1981700, 5245675), "known/unknown liability differs")
    require(
        (
            amount(summary["known_spent_nanousd"]),
            amount(summary["unknown_reserved_nanousd"]),
            amount(summary["complete_liability_nanousd"]),
        )
        == (known, unknown, known + unknown),
        "summary financial partition differs",
    )
    require(
        (amount(report["settled_nanousd"]), amount(report["unknown_nanousd"]))
        == (known, unknown),
        "report financial totals differ",
    )
    require(
        amount(summary["complete_cap_nanousd"])
        == amount(report["total_cap_nanousd"])
        == 7000000000,
        "complete cap differs",
    )
    require(
        not any(r["run_id"].startswith(summary["campaign"] + ":") for r in rows),
        "game charges invented",
    )
    for claim in finance["claims"].values():
        require(
            type(claim["count"]) is int
            and claim["count"] == 1
            and claim["not_a_billable_request"] is True,
            "consumed nonbillable claim reclassified",
        )
    require(
        len(list((root / "replays").glob("*.zip"))) == 3,
        "unavailable game archives fabricated",
    )
    native, events = archive_data(root / "replays/native-partial.replay.zip")
    gaps = [e for e in events if e["kind"] == "gap"]
    samples = [e for e in events if e["kind"] == "sample"]
    require(
        native["status"] == "failed"
        and native["incomplete"] is True
        and native["manifest"]["source_revision"] == SOURCE
        and len(events) == 411,
        "native incomplete history relabelled",
    )
    require(
        len(gaps) == 1
        and gaps[0]["data"] == {"missing": 1, "reason": "native_telemetry_loss"}
        and len(samples) == 183
        and samples[-1]["t_ms"] - samples[0]["t_ms"] == 220803,
        "native critical gap/horizon changed",
    )
    gap_projection = load(root / "native-gap.safe-projection.json")
    native_row = report["runs"][0]
    require(
        len(report["runs"]) == 1
        and native_row["run_id"] == native["id"]
        and (
            native_row["participant"],
            native_row["repetition"],
            native_row["status"],
            native_row["stop_reason"],
            native_row["observed_span_ms"],
        )
        == ("native", 0, "failed", "recording_gap", 220803),
        "native report scope differs",
    )
    require(
        amount(native_row["ledger_spent_nanousd"])
        == amount(native_row["ledger_unknown_nanousd"])
        == 0
        and native_row["metrics"]["xp_delta"]
        == samples[-1]["data"]["bot"]["xp"] - samples[0]["data"]["bot"]["xp"]
        == 0
        and native_row["metrics"]["gaps"] == len(gaps),
        "native metrics/cost attributed from other scope",
    )
    require(
        summary["native_fragment"]["worker_clocks"] == gap_projection["worker_run_stop"]
        and summary["native_fragment"]["sample_span_ms"] == 220803
        and summary["native_fragment"]["final_saved_character_available"] is False,
        "partial summary evidence differs",
    )
    fragment = summary["native_fragment"]
    require(
        fragment["run_id"] == native["id"]
        and fragment["status"] == "failed"
        and fragment["stop_reason"] == "recording_gap"
        and fragment["requested_seconds"] == 1800
        and fragment["sample_count"] == len(samples)
        and fragment["recorded_envelope_ms"] == native["duration_ms"]
        and fragment["xp_delta_observed"]
        == fragment["deaths_observed_fragment"]
        == fragment["interventions_observed_fragment"]
        == 0
        and fragment["llm_requests"] == amount(fragment["usage_settled_nanousd"]) == 0
        and fragment["gaps"] == 1,
        "partial fragment metrics/scope changed",
    )
    verify_video(root, native, events)
    require(
        not any(e["kind"] == "request" for e in events), "native AI calls fabricated"
    )
    current_ids = set()
    execution = load(root / "execution-result.json")
    require(
        {key: value for key, value in execution.items() if key != "probes"}
        == closure["campaign_result"],
        "execution result contradicts closed invocation",
    )
    execution_probes = execution["probes"]
    metric_probes = load(root / "probe-metrics.json")["probes"]
    for provider, expected_count in [("openai", 3), ("gemini", 5)]:
        probe = load(root / (provider + "-probe-result.json"))
        require(
            execution_probes[provider] == probe
            and metric_probes[provider]["qualification"] == probe["qualification"],
            "duplicate probe outputs contradict closed qualification",
        )
        require(
            probe["qualification"]["accepted_for_game"] is True
            and probe["qualification"]["evidence_reconciled"] is True,
            "real probe acceptance erased",
        )
        meta, events = archive_data(root / "replays" / (provider + "-probe.replay.zip"))
        require(
            meta["status"] == ("failed" if provider == "openai" else "completed")
            and meta["incomplete"] is False,
            "probe recorder state relabelled",
        )
        require(
            meta["manifest"]["synthetic"] is True
            and meta["manifest"]["source_revision"] == "unknown"
            and meta["manifest"]["configuration_sha256"] is None,
            "synthetic manifest relabelled as gameplay/source",
        )
        groups = {}
        for event in events:
            if event["kind"] == "request":
                data = event["data"]
                groups.setdefault(data["request_id"], {})[data["phase"]] = data
        reserved = {
            key: phases for key, phases in groups.items() if "reserved" in phases
        }
        require(len(reserved) == expected_count, "probe attempt count changed")
        selected = [by_id[key] for key in reserved]
        settled = sum(r["spent"] for r in selected if r["spent"] is not None)
        liability = sum(r["reserved"] for r in selected if r["spent"] is None)
        qualification = probe["qualification"]
        require(
            amount(qualification["ledger_requests"]) == len(reserved)
            and amount(qualification["unknown_nanousd"]) == liability
            and amount(qualification["liability_nanousd"]) == settled + liability
            and qualification["financial_final"] is (liability == 0),
            "probe qualification cost partition differs",
        )
        for key, phases in reserved.items():
            require(key not in current_ids, "duplicate current financial identity")
            current_ids.add(key)
            row = by_id[key]
            require(
                row["run_id"] == meta["id"]
                and row["reserved"] == amount(phases["reserved"]["reserved_nanousd"]),
                "probe reservation/run differs",
            )
            if "finished" in phases:
                finished = phases["finished"]
                require(
                    row["spent"]
                    == amount(finished["spent_nanousd"])
                    == usage_cost(
                        finished, provenance["probe_routes"][provider]["prices"]
                    ),
                    "usage-priced settlement differs",
                )
            else:
                require(
                    row["spent"] is None
                    and phases["failed"]["unsettled"] is True
                    and row["reserved"] == phases["failed"]["reserved_nanousd"],
                    "unknown probe reservation lost",
                )
        for key, phases in groups.items():
            if "skipped" in phases:
                require(
                    key not in by_id and phases["skipped"]["reserved_nanousd"] == 0,
                    "local skip became paid attempt",
                )
    require(len(current_ids) == 8, "new probe identity set differs")
    return {
        "files_verified": len(index),
        "planned_games": 9,
        "partial_games": 1,
        "not_started_reported_by_owner": 8,
        "ai_game_runs": 0,
        "replays": 3,
        "selected_financial_rows": 18,
        "known_nanousd": known,
        "unknown_nanousd": unknown,
        "financial_final": False,
        "comparative_pilot_completed": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(verify(Path(__file__).resolve().parent), sort_keys=True))
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile) as error:
        print("Evidence verification failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
