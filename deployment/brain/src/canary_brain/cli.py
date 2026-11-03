"""Operator commands expose state and cost metadata, never credentials."""

import argparse
import asyncio
import json
from pathlib import Path

from .learning import VERSION, Policy
from .runtime import Configuration, run
from .store import Store


def main() -> None:
    parser = argparse.ArgumentParser(description="GPT-6 Luna party companion service")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--config", type=Path, required=True)
    status = commands.add_parser("status")
    status.add_argument("--state", type=Path, required=True)
    forget = commands.add_parser("forget")
    forget.add_argument("--state", type=Path, required=True)
    forget.add_argument(
        "--kind", choices=["policy", "memory", "profile", "recent"], required=True
    )
    forget.add_argument("--key", required=True)
    for command in ("checkpoint", "rollback", "inspect"):
        operation = commands.add_parser(command)
        operation.add_argument("--state", type=Path, required=True)
        operation.add_argument("--name", required=command != "inspect")
    seed = commands.add_parser("record-cost")
    seed.add_argument("--state", type=Path, required=True)
    seed.add_argument("--id", required=True)
    seed.add_argument("--month", required=True)
    seed.add_argument("--nanousd", type=int, required=True)
    args = parser.parse_args()
    if args.command == "serve":
        configuration = Configuration.model_validate_json(args.config.read_text())
        try:
            asyncio.run(run(configuration))
        except Exception as error:  # noqa: BLE001 - keep credential-bearing provider messages out of stderr
            # Exception messages can contain credential fragments; only report the category.
            parser.exit(1, f"Companion service stopped: {type(error).__name__}\n")
    elif args.command == "status":
        store = Store(args.state)
        print(
            json.dumps(
                {
                    "budget_nanousd": store.budget(),
                    "bots": store.records("status"),
                    "episodes": store.records("episode", 20),
                    "requests": store.records("request", 20),
                    "policy_version": VERSION,
                    "policy": store.records("policy", 30),
                    "recent": store.records("recent", 3),
                    "pending": store.records("pending", 12),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "forget":
        Store(args.state).forget(args.kind, args.key)
        print("Requested learning record removed; spending history retained.")
    elif args.command == "record-cost":
        store = Store(args.state)
        store.reserve(args.id, args.nanousd, args.month, "historical-evaluation")
        store.settle(args.id, args.nanousd)
        print("Historical evaluation cost recorded.")
    elif args.command == "inspect":
        store = Store(args.state)
        print(
            json.dumps(
                {
                    kind: store.records(kind, 100)
                    for kind in ("policy", "recent", "memory", "checkpoint")
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        policy = Policy(Store(args.state))
        if args.command == "checkpoint":
            policy.checkpoint(args.name)
        else:
            policy.rollback(args.name)
        print("Policy updated; character state and spending history retained.")


if __name__ == "__main__":
    main()
