"""M5 decision deadlines through real pinned LiteLLM and a latency-injecting fake upstream.

Never contacts a real model. Each scenario sends one GatewayProvider.decide through
LiteLLM to a local upstream that sleeps for the injected delay before answering.
It reports the deadline actually passed to the request path, the outcome, the
recorded failure class and the ledger/replay accounting, including late responses
that the upstream still completes after the worker gave up.
"""

import asyncio
import json
import os
import re
import secrets
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from canary_brain.gateway import GatewayConfiguration, GatewayProvider
from canary_brain.protocol import Observation
from canary_brain.provider import Prices
from canary_brain.recording import (
    Manifest,
    Recorder,
    RecordingConfiguration,
    ReplayReader,
    attribution,
    digest,
)
from canary_brain.replay import summarize
from canary_brain.store import Store

DELAYS_MS = (500, 1190, 1210, 1850, 3000)
# Runtime default, the proposed M5 value and the benchmark Experiment default.
CONFIGURED_S = (1.2, 2.5, 10.0)
PROFILES = {
    # Server TTLs from src/creatures/players/bot/bot_brain.cpp (default 5000 ms).
    "strategic": [("hunt:1", "hunt", 5000), ("resupply", "resupply", 5000)],
    "retreat": [("retreat", "retreat", 1500), ("resupply", "resupply", 5000)],
    "target": [("target:9", "target", 1000), ("resupply", "resupply", 5000)],
}
INPUT_TOKENS, OUTPUT_TOKENS = 400, 20
PRICES = Prices(  # Luna's published rates; only the arithmetic matters offline.
    version="deadline-fixture",
    input_nanousd=100,
    cached_nanousd=10,
    cache_write_nanousd=125,
    output_nanousd=500,
)
SPEND = INPUT_TOKENS * PRICES.input_nanousd + OUTPUT_TOKENS * PRICES.output_nanousd


def free_port() -> int:
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        port: int = server.getsockname()[1]
        return port


def observation(name: str, profile: str) -> Observation:
    return Observation.model_validate(
        {
            "version": 1,
            "type": "observation",
            "world": "deadline-fixture",
            "sequence": 1,
            "captured_ms": 0,
            "lease": "offline",
            "objective_generation": 1,
            "autonomous": True,
            "bot": {
                "id": 7,
                "name": name,
                "level": 20,
                "vocation": 4,
                "state": "HUNTING",
                "position": [100, 100, 7],
                "health": 90,
                "mana": 40,
                "potions": 5,
                "xp": 1000,
                "alive": True,
            },
            "actions": [
                {"id": i, "action": a, "description": a, "ttl_ms": ttl}
                for i, a, ttl in PROFILES[profile]
            ],
        }
    )


def main() -> None:
    if "--inside" not in sys.argv:
        source = Path(__file__).resolve().parents[3]
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--entrypoint",
                "python",
                "-v",
                f"{source}:/source:ro",
                "-e",
                "PYTHONPATH=/source/deployment/brain/src:/app",
                "canary-litellm:1.108.0",
                "/source/deployment/brain/tools/deadline_smoke.py",
                "--inside",
            ],
            check=True,
        )
        return
    upstream_log: dict[str, dict[str, Any]] = {}

    class Upstream(BaseHTTPRequestHandler):
        def log_message(self, *_args: Any) -> None:
            pass

        def do_POST(self) -> None:
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            body = json.loads(raw)
            marker = re.search(rb"deadline-case-(\d+)-(\d+)", raw)
            assert marker, "fixture marker missing from the upstream request"
            case, delay = marker.group(1).decode(), int(marker.group(2))
            entry = upstream_log[case] = {"delay_ms": delay, "answered": False}
            time.sleep(delay / 1000)
            result = {
                "id": "resp_" + case,
                "object": "response",
                "created_at": 1,
                "model": body["model"],
                "status": "completed",
                "output": [
                    {
                        "type": "function_call",
                        "id": "fc_" + case,
                        "call_id": "call_" + case,
                        "name": "choose_action",
                        "arguments": json.dumps({"candidate_id": "resupply"}),
                        "status": "completed",
                    }
                ],
                "usage": {
                    "input_tokens": INPUT_TOKENS,
                    "output_tokens": OUTPUT_TOKENS,
                    "total_tokens": INPUT_TOKENS + OUTPUT_TOKENS,
                },
            }
            encoded = json.dumps(result).encode()
            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
                entry["answered"] = True  # A real provider would bill this answer.
            except OSError as error:
                entry["write_error"] = type(error).__name__
            finally:
                entry["done"] = True

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    threading.Thread(target=upstream.serve_forever, daemon=True).start()
    with tempfile.TemporaryDirectory(prefix="deadline-qa-") as tmp:
        root = Path(tmp)
        port = free_port()
        config = {
            "model_list": [
                {
                    "model_name": "test-a",
                    "litellm_params": {
                        "model": "openai/model-a",
                        "api_base": f"http://127.0.0.1:{upstream.server_port}/v1",
                        "api_key": "local-fixture",
                        "num_retries": 0,
                    },
                    "model_info": {
                        "id": "deployment-a",
                        "supported_endpoints": ["/v1/responses"],
                    },
                }
            ],
            "router_settings": {
                "num_retries": 0,
                "max_fallbacks": 0,
                "fallbacks": [],
                "cache_responses": False,
            },
            "litellm_settings": {
                "num_retries": 0,
                "fallbacks": [],
                "cache": False,
                "drop_params": False,
                "turn_off_message_logging": True,
            },
            "general_settings": {
                "custom_auth": "gateway_policy.authenticate",
                "master_key": "os.environ/LITELLM_MASTER_KEY",
            },
        }
        (root / "gateway.yaml").write_bytes(
            json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
        )
        log = (root / "gateway.log").open("w")
        policy = Path(__file__).resolve().parents[1] / "src" / "canary_brain"
        environment = dict(
            os.environ,
            LITELLM_WORKER_KEY="sk-local-fixture",
            LITELLM_MASTER_KEY="sk-" + secrets.token_hex(32),
            CANARY_GATEWAY_CONFIG=str(root / "gateway.yaml"),
            LITELLM_LOCAL_MODEL_COST_MAP="true",
            PYTHONPATH=os.pathsep.join([str(policy), os.environ.get("PYTHONPATH", "")]),
        )
        litellm = Path(sys.executable).with_name("litellm")
        process = subprocess.Popen(
            [
                str(litellm) if litellm.exists() else "litellm",
                "--config",
                str(root / "gateway.yaml"),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            ready_by = time.monotonic() + 90
            while True:
                try:
                    urllib.request.urlopen(
                        f"http://127.0.0.1:{port}/health/readiness", timeout=1
                    ).close()
                    break
                except (OSError, urllib.error.URLError):
                    if process.poll() is not None or time.monotonic() > ready_by:
                        log.flush()
                        raise RuntimeError(
                            (root / "gateway.log").read_text()[-5000:]
                        ) from None
                    time.sleep(0.2)
            result = asyncio.run(exercise(root, port, config, upstream_log))
            print(json.dumps(result))
            if not all(result["checks"].values()):
                raise SystemExit("deadline qualification checks failed")
        finally:
            process.terminate()
            process.wait(timeout=20)
            log.close()
            upstream.shutdown()


async def exercise(
    root: Path, port: int, config: dict[str, Any], upstream_log: dict[str, Any]
) -> dict[str, Any]:
    gateway = GatewayConfiguration(
        base_url=f"http://127.0.0.1:{port}/v1",
        alias="test-a",
        effective_model="model-a",
        deployment_id="deployment-a",
        provider="fake-upstream",
        upstream_model="openai/model-a",
        version="1.108.0",
        configuration_sha256=digest(config),
        prices=PRICES,
    )
    manifest = Manifest(
        run_id="deadline:7",
        bot_id=7,
        lineage="deadline:7",
        provider="fake-upstream",
        model="model-a",
        synthetic=True,
    )
    recorder = Recorder(
        RecordingConfiguration(path=root / "replay.db", namespace="deadline"),
        [manifest],
    )
    ledger = Store(root / "budget.db")
    rows: list[dict[str, Any]] = []
    case = 0
    async with AsyncOpenAI(
        api_key="sk-local-fixture", base_url=gateway.base_url, max_retries=0, timeout=45
    ) as client:
        # Warm the gateway once so the first measured case is not a cold import.
        warm = GatewayProvider(ledger, client, 30, gateway=gateway, recorder=recorder)
        with attribution(7):
            await warm.decide(observation("deadline-case-0-0", "strategic"))
        for configured in CONFIGURED_S:
            for profile, catalog in PROFILES.items():
                for delay in DELAYS_MS:
                    case += 1

                    class Probe(GatewayProvider):
                        applied: list[float]

                        async def _request(
                            self,
                            endpoint: str,
                            body: dict[str, Any],
                            timeout: float,
                            *,
                            fast: bool = False,
                        ) -> dict[str, Any]:
                            self.applied.append(timeout)
                            return await super()._request(
                                endpoint, body, timeout, fast=fast
                            )

                    # A fresh adapter per case: backoff after a timeout is a
                    # separate behavior and must not mask the next scenario.
                    provider = Probe(
                        ledger,
                        client,
                        configured,
                        gateway=gateway,
                        recorder=recorder,
                        run_cap=10**9,
                    )
                    provider.applied = []
                    before = ledger.budget()
                    started = time.monotonic()
                    try:
                        with attribution(7):
                            choice = await provider.decide(
                                observation(f"deadline-case-{case}-{delay}", profile)
                            )
                        outcome = "selected:" + choice
                    except TimeoutError:
                        outcome = "TimeoutError"
                    waited = round((time.monotonic() - started) * 1000)
                    after = ledger.budget()
                    rows.append(
                        {
                            "case": str(case),
                            "configured_s": configured,
                            "profile": profile,
                            "min_ttl_ms": min(t for _, _, t in catalog),
                            "delay_ms": delay,
                            "applied_deadline_s": provider.applied[0],
                            "outcome": outcome,
                            "waited_ms": waited,
                            "spent_delta": after["spent"] - before["spent"],
                            "reserved_delta": after["reserved"] - before["reserved"],
                        }
                    )
        ledger_before_late = ledger.budget()
        # Let every late upstream answer finish, then prove nothing settled late.
        deadline = time.monotonic() + max(DELAYS_MS) / 1000 + 5
        while time.monotonic() < deadline and not all(
            upstream_log.get(r["case"], {}).get("done") for r in rows
        ):
            await asyncio.sleep(0.1)
        await asyncio.sleep(1)
        ledger_after_late = ledger.budget()
    recorder.close()
    events = list(ReplayReader(root / "replay.db").all_events(manifest.run_id))
    requests: dict[str, dict[str, Any]] = {}
    failed_events: list[dict[str, Any]] = []
    for event in events:
        if event["kind"] == "request":
            requests.setdefault(event["data"]["request_id"], {}).update(event["data"])
            if event["data"].get("phase") == "failed":
                failed_events.append(event["data"])
    metrics = summarize(events, manifest.model_dump())
    with sqlite3.connect(root / "budget.db") as db:
        ledger_rows = db.execute("SELECT reserved, spent FROM requests").fetchall()
    for row in rows:
        row["upstream_answered_late_or_on_time"] = upstream_log[row["case"]].get(
            "answered"
        )
    timeouts = [r for r in rows if r["outcome"] == "TimeoutError"]
    successes = [r for r in rows if r["outcome"].startswith("selected:")]
    failed = [r for r in requests.values() if r.get("phase") == "failed"]
    finished = [r for r in requests.values() if r.get("phase") == "finished"]
    unsettled_rows = [r for r in ledger_rows if r[1] is None]
    checks = {
        "one_ledger_row_per_transmission": len(ledger_rows) == len(rows) + 1,
        "applied_deadline_is_min_configured_ttl": all(
            r["applied_deadline_s"] == min(r["configured_s"], r["min_ttl_ms"] / 1000)
            for r in rows
        ),
        # A late answer must never become a success; host jitter may only turn a
        # near-deadline answer into a recorded timeout, never the reverse.
        "no_success_at_or_past_applied_deadline": all(
            r["delay_ms"] < r["applied_deadline_s"] * 1000
            and r["waited_ms"] <= r["applied_deadline_s"] * 1000 + 50
            for r in successes
        ),
        "every_delay_past_applied_deadline_timed_out": all(
            r["outcome"] == "TimeoutError"
            for r in rows
            if r["delay_ms"] >= r["applied_deadline_s"] * 1000
        ),
        "clearly_fast_cases_succeed": all(
            r["outcome"].startswith("selected:")
            for r in rows
            if r["delay_ms"] + 400 < r["applied_deadline_s"] * 1000
        ),
        "timeouts_never_spend_and_keep_full_reservation": all(
            r["spent_delta"] == 0 and r["reserved_delta"] > 0 for r in timeouts
        ),
        "successes_settle_exact_usage": all(
            r["spent_delta"] == SPEND and r["reserved_delta"] == 0 for r in successes
        ),
        "late_answers_reached_upstream": all(
            r["upstream_answered_late_or_on_time"] for r in timeouts
        ),
        "late_answers_never_settle": ledger_after_late == ledger_before_late,
        "ledger_reserved_equals_unsettled_rows": ledger_after_late["reserved"]
        == sum(r[0] for r in unsettled_rows)
        == sum(r["reserved_delta"] for r in timeouts),
        "replay_failures_equal_timeouts": metrics["provider_failures"] == len(timeouts)
        and len(failed) == len(timeouts),
        "replay_reserved_equals_ledger": metrics["reserved_nanousd"]
        == ledger_after_late["reserved"],
        "failed_events_classified_as_timeout": all(
            r.get("error") == "TimeoutError" for r in failed
        ),
        # Checked on each failed event alone, not merged with its reserved event.
        "failed_events_carry_applied_deadline": sorted(
            e.get("deadline_ms", -1) for e in failed_events
        )
        == sorted(round(r["applied_deadline_s"] * 1000) for r in timeouts),
    }
    return {
        "litellm": "1.108.0",
        "rows": rows,
        "failed_error_classes": sorted({str(r.get("error")) for r in failed}),
        # Gateway + adapter time on top of the injected upstream delay.
        "success_overhead_ms": sorted(
            r["waited_ms"] - r["delay_ms"] for r in successes
        ),
        # Event-loop lateness of the deadline itself on this host.
        "timeout_overshoot_ms": sorted(
            r["waited_ms"] - round(r["applied_deadline_s"] * 1000) for r in timeouts
        ),
        "finished_latency_ms": sorted(int(r["elapsed_ms"]) for r in finished),
        "replay_metrics": {
            k: metrics[k]
            for k in (
                "model_decisions",
                "provider_failures",
                "spent_nanousd",
                "reserved_nanousd",
                "latency_p50_ms",
                "latency_p95_ms",
            )
        },
        "ledger": ledger_after_late,
        "checks": checks,
    }


if __name__ == "__main__":
    main()
