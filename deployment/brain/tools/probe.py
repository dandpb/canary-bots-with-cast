"""Opt-in real-model contract probes; account for every call in the shared ledger."""

import argparse
import asyncio
import json
import time
from pathlib import Path

from openai import AsyncOpenAI

from canary_brain.protocol import Observation
from canary_brain.provider import Provider
from canary_brain.runtime import read_credential
from canary_brain.store import Store


async def probe(args: argparse.Namespace) -> None:
    store = Store(args.state)
    snapshot = Observation.model_validate(
        {
            "version": 1,
            "type": "observation",
            "world": "contract-probe",
            "sequence": 1,
            "captured_ms": int(time.monotonic() * 1000),
            "lease": "probe",
            "objective_generation": 1,
            "bot": {
                "id": 1,
                "name": "Probe Companion",
                "level": 80,
                "vocation": 4,
                "state": "PARTY",
                "position": [100, 100, 7],
                "health": 95,
                "mana": 80,
                "potions": 3,
                "xp": 1000,
                "alive": True,
            },
            "party": {"leader_id": 2, "members": [1, 2]},
            "actions": [
                {
                    "id": "continue",
                    "action": "continue",
                    "description": "Keep following the party",
                    "ttl_ms": 1500,
                },
                {
                    "id": "resupply",
                    "action": "resupply",
                    "description": "Replenish the low potion supply at a reachable shop",
                    "ttl_ms": 5000,
                },
            ],
        }
    )
    reports = []
    async with AsyncOpenAI(
        api_key=read_credential(args.credential),
        max_retries=0,
        base_url="https://api.openai.com/v1",
    ) as client:
        provider = Provider(store, client, decision_timeout=10)
        for _ in range(args.samples):
            started = time.monotonic()
            result = await provider.decide(snapshot)
            reports.append(
                {
                    "endpoint": "decisions",
                    "choice": result,
                    "elapsed_ms": round((time.monotonic() - started) * 1000),
                }
            )
        for deep in [False, True] if args.max_effort else [False]:
            started = time.monotonic()
            result = await provider.converse(
                snapshot,
                "Vamos comprar poções antes da hunt. Planeje como fazer isso com prudência.",
                authorized=True,
                deep=deep,
            )
            reports.append(
                {
                    "endpoint": "responses",
                    "choice": result.candidate_id,
                    "effort": result.effort,
                    "elapsed_ms": round((time.monotonic() - started) * 1000),
                }
            )
            if args.tool_result:
                reflection = await provider.reflect(
                    result.tool_call,
                    {
                        "status": "failed",
                        "reason": "insufficient_funds",
                        "metrics": {"progress": 0},
                    },
                )
                reports.append(
                    {
                        "endpoint": "responses_tool_result",
                        "bytes": len(reflection.encode()),
                        "failure_summary": reflection,
                    }
                )
    report = {
        "model": "gpt-6-luna",
        "synthetic_contract_probes": reports,
        "budget_nanousd": store.budget(),
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    args.output.chmod(0o600)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", required=True)
    parser.add_argument("--credential", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, choices=range(1, 21), default=5)
    parser.add_argument("--max-effort", action="store_true")
    parser.add_argument("--tool-result", action="store_true")
    try:
        asyncio.run(probe(parser.parse_args()))
    except Exception as error:  # noqa: BLE001 - avoid exposing credential fragments in provider errors
        parser.exit(1, f"Live probe failed: {type(error).__name__}\n")
