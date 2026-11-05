"""Local replay and isolated benchmark commands; live inference is explicit."""

import argparse
import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from .benchmark import (
    Experiment,
    demo,
    evaluate_decisions,
    fixture_hash,
    preflight,
    run_campaign,
)
from .gateway import GatewayProvider
from .operator_http import OperatorServer
from .recording import (
    Manifest,
    Recorder,
    RecordingConfiguration,
    RecordingStore,
    ReplayReader,
    digest,
)
from .replay import campaign, export_archive, export_report, import_archive, summary
from .runtime import Configuration, read_credential
from .store import USD, Store
from .testing import FakeProvider


def configure(commands: Any) -> None:
    replay = commands.add_parser(
        "replay", help="read-only historical playback and archives"
    )
    operations = replay.add_subparsers(dest="operation", required=True)
    for name in ("list", "summary", "serve", "export", "import", "report", "demo"):
        operation = operations.add_parser(name)
        operation.add_argument("--recording", type=Path, required=True)
        if name in {"summary", "export"}:
            operation.add_argument("--run", required=True)
        if name == "report":
            operation.add_argument("--run", action="append", required=True)
        if name in {"export", "report"}:
            operation.add_argument("--output", type=Path, required=True)
        if name == "import":
            operation.add_argument("--archive", type=Path, required=True)
        if name == "serve":
            operation.add_argument("--port", type=int, default=8092)
    benchmark = commands.add_parser(
        "benchmark", help="predeclare and run isolated model comparisons"
    )
    operations = benchmark.add_subparsers(dest="operation", required=True)
    decisions = operations.add_parser(
        "decisions", help="evaluate recorded decisions without game actions"
    )
    decisions.add_argument("--fixtures", type=Path, required=True)
    decisions.add_argument("--worker-config", type=Path)
    decisions.add_argument("--live", action="store_true")
    for name in ("hash", "preflight", "run", "summary"):
        operation = operations.add_parser(name)
        if name in {"preflight", "run"}:
            operation.add_argument("--config", type=Path, required=True)
        elif name == "hash":
            operation.add_argument("--fixture", type=Path, required=True)
            operation.add_argument("--world-map", type=Path, required=True)
        else:
            operation.add_argument("--recording", type=Path, required=True)
            operation.add_argument("--run", action="append", required=True)
        if name == "run":
            operation.add_argument("--live", action="store_true")


async def serve(reader: ReplayReader, port: int) -> None:
    if not 1024 <= port <= 65535:
        raise ValueError("choose a local port from 1024 to 65535")
    server = OperatorServer(None, port, reader)
    await server.start("127.0.0.1")
    try:
        assert server.server is not None
        print(f"Read-only replay: http://127.0.0.1:{server.port}/replay", flush=True)
        async with server.server:
            await server.server.serve_forever()
    finally:
        await server.close()


async def decision_fixtures(args: argparse.Namespace) -> Any:
    if args.fixtures.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("decision fixture file exceeds 4 MiB")
    fixtures = json.loads(args.fixtures.read_text())
    if not isinstance(fixtures, list) or not 1 <= len(fixtures) <= 100:
        raise ValueError("provide one to 100 recorded decision fixtures")
    if not args.live:
        return {
            "mode": "offline-fake",
            "decisions": await evaluate_decisions(FakeProvider(), fixtures),
        }
    if args.worker_config is None:
        raise ValueError("live decision evaluation requires --worker-config")
    config = Configuration.model_validate_json(args.worker_config.read_text())
    if (
        config.provider != "litellm"
        or config.gateway is None
        or config.recording is None
        or config.credential_file is None
        or config.run_cap_nanousd is None
        or config.budget_file is None
    ):
        raise ValueError(
            "live fixtures require LiteLLM, recording, a shared ledger and an explicit run cap"
        )
    from .protocol import Observation

    bots = {Observation.model_validate(f["observation"]).bot.id for f in fixtures}
    if len(bots) > 3:
        raise ValueError("at most three recorded bots per fixture evaluation")
    identity = uuid.uuid4().hex
    manifests = [
        Manifest(
            run_id=f"decisions:{identity}:{bot}",
            bot_id=bot,
            lineage=f"decision-fixture:{bot}",
            experiment=f"decision-fixtures:{identity}",
            scenario="recorded-decisions-real-inference",
            participant=config.gateway.alias,
            model=config.gateway.effective_model,
            provider=config.gateway.provider,
            memory_mode="frozen",
            synthetic=True,
            initial_sha256=digest(fixtures),
        )
        for bot in sorted(bots)
    ]
    recorder = Recorder(
        RecordingConfiguration(
            path=config.recording.path, namespace=config.recording.namespace
        ),
        manifests,
    )
    rows: list[dict[str, Any]] = []
    try:
        async with AsyncOpenAI(
            base_url=config.gateway.base_url,
            api_key=read_credential(config.credential_file, "LITELLM_API_KEY"),
            max_retries=0,
            timeout=45,
        ) as client:
            provider = GatewayProvider(
                Store(config.budget_file, cap=config.monthly_usd * USD),
                client,
                config.decision_timeout,
                gateway=config.gateway,
                recorder=recorder,
                run_cap=config.run_cap_nanousd,
            )
            rows = await evaluate_decisions(provider, fixtures)
    finally:
        recorder.close()
        for manifest in manifests:
            relevant = [row for row in rows if row["bot_id"] == manifest.bot_id]
            RecordingStore(config.recording.path).finish(
                manifest.run_id,
                "completed"
                if relevant and all(row["valid"] for row in relevant)
                else "failed",
            )
    return {
        "mode": "real-inference-on-recorded-inputs-no-game-actions",
        "runs": [m.run_id for m in manifests],
        "decisions": rows,
    }


def execute(args: argparse.Namespace) -> None:
    result: Any = None
    if args.command == "benchmark":
        if args.operation == "decisions":
            result = asyncio.run(decision_fixtures(args))
        elif args.operation == "hash":
            result = {"initial_sha256": fixture_hash(args.fixture, args.world_map)}
        elif args.operation == "summary":
            result = campaign(ReplayReader(args.recording), args.run)
        else:
            experiment = Experiment.model_validate_json(args.config.read_text())
            result = (
                preflight(experiment)
                if args.operation == "preflight"
                else asyncio.run(run_campaign(experiment, live=args.live))
            )
    elif args.operation == "demo":
        result = {"synthetic_runs": demo(args.recording)}
    elif args.operation == "import":
        result = {"run": import_archive(args.archive, args.recording)}
    else:
        reader = ReplayReader(args.recording)
        if args.operation == "serve":
            asyncio.run(serve(reader, args.port))
        elif args.operation == "list":
            result = reader.runs()
        elif args.operation == "summary":
            result = summary(reader, args.run)
        elif args.operation == "export":
            export_archive(reader, args.run, args.output)
            result = {"archive": str(args.output)}
        elif args.operation == "report":
            export_report(reader, args.run, args.output)
            result = {"report": str(args.output)}
    if result is not None:
        print(json.dumps(result, ensure_ascii=False, indent=2))
