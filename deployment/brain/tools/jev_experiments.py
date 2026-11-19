"""Evaluate four Jev experiments over synthetic, labelled Canary fixtures."""

import argparse
import json
import math
import os
import sqlite3
import sys
import time
from collections import defaultdict
from contextlib import closing
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import mean, median
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

FIXTURES = Path(__file__).with_name("jev_experiment_cases.json")
EXPERIMENTS = ("intent", "hunts", "outcomes", "replays")
MODEL = "jev-1.14.0"
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
USD = 1_000_000_000
# TypeSafe standard text context and input-only price for this pinned model.
MAX_INPUT_TOKENS = 65_536
NANOUSD_PER_TOKEN = 42
THRESHOLD = 0.7
BASELINES = {
    "intent": "Controller planning/sequence keywords and a simple lexical action matcher",
    "hunts": "Nearest offered route by distance_tiles",
    "outcomes": "Treat replies about completed outcomes as supported",
    "replays": "Order by number of milestones, then XP",
}

# Snapshot of the two keyword checks in Controller._dialogue.
PLAN_WORDS = ("estratég", "estrateg", "planej", "pense com calma", "effort max")
SEQUENCE_WORDS = ("depois", "antes", "planej", "em seguida")
ACTION_WORDS = {
    "follow": ("segue", "seguir", "acompanha"),
    "hold": ("espera", "parado", "fica"),
    "resupply": ("poção", "poções", "reabastece", "pots"),
    "hunt_wolves": ("lobos",),
    "hunt_trolls": ("trolls",),
    "retreat": ("recua", "templo"),
}


@dataclass(frozen=True)
class Case:
    experiment: str
    id: str
    state: dict[str, Any]
    questions: dict[str, Any]
    expected: dict[str, Any]
    baseline: dict[str, Any]
    group: str = "all"

    def payload(self) -> dict[str, Any]:
        return {"model": MODEL, "state": self.state, "questions": self.questions}


def noul(instructions: str, yes: str, no: str) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {"true": yes, "false": no},
    }


def score(instructions: str, levels: list[str]) -> dict[str, Any]:
    return {"type": "score", "instructions": instructions, "criteria": levels}


def intent_cases(data: dict[str, Any], split: str) -> list[Case]:
    cases = []
    for group, examples in data["intent"].items():
        if split not in ("all", group):
            continue
        for index, (profile, message, plan, sequence, action) in enumerate(examples, 1):
            offered = data["action_sets"][profile]
            if action is not None and action not in offered:
                raise ValueError(f"{group}-{index} expects an unavailable action")
            text = message.casefold()
            matches = [
                name
                for name in offered
                if any(word in text for word in ACTION_WORDS[name])
            ]
            cases.append(
                Case(
                    "intent",
                    f"{group}-{index:02}",
                    {"message": message, "offered": offered},
                    {
                        "plan": noul(
                            "A mensagem pede que o companheiro elabore ou recomende um plano agora?",
                            "O jogador quer que o companheiro monte ou recomende uma estratégia.",
                            "O jogador dá sua própria ordem, conversa, adia o plano ou veta o planejamento.",
                        ),
                        "sequence": noul(
                            "A mensagem dá uma ordem com duas ou mais ações numa sequência explícita?",
                            "O jogador manda começar uma ação agora e realizar outra após a primeira.",
                            "Há uma ação só, um pedido de ideias ou uma ação depende de condição futura incerta.",
                        ),
                        "actionable": noul(
                            "Alguma ação em `offered` corresponde à primeira ação que `message` pede para iniciar agora?",
                            "O jogador solicita uma ação disponível que pode começar agora.",
                            "A mensagem é pergunta, negação, pedido de plano, ordem ambígua, ação adiada ou indisponível.",
                        ),
                        "first_action": {
                            "type": "choice",
                            "instructions": "Qual opção em `offered` melhor corresponde à primeira ação imediata pedida na mensagem?",
                            "criteria": offered,
                        },
                    },
                    {"plan": plan, "sequence": sequence, "action": action},
                    {
                        "plan": any(word in text for word in PLAN_WORDS),
                        "sequence": any(word in text for word in SEQUENCE_WORDS),
                        "action": matches[0] if len(matches) == 1 else None,
                    },
                    group,
                )
            )
    return cases


def hunt_cases(data: dict[str, Any]) -> list[Case]:
    cases = []
    for row in data["hunts"]:
        routes = {name: data["routes"][name] for name in row["offered"]}
        if row["expected"] is not None and row["expected"] not in routes:
            raise ValueError(f"{row['id']} expects an unavailable route")
        closest = sorted(
            routes, key=lambda name: (routes[name]["distance_tiles"], name)
        )
        questions = {
            "match": noul(
                "Há uma rota em `routes` compatível com as restrições explícitas em `request`?",
                "Pelo menos uma rota satisfaz os requisitos expressos pelo jogador.",
                "Todas as rotas conflitam com algum requisito expresso pelo jogador.",
            ),
            **{
                name: score(
                    f"Quanto `routes.{name}` atende à hunt que o jogador pediu em `request`?",
                    [
                        "Viola um requisito",
                        "Cumpre os requisitos e parte das preferências",
                        "Cumpre requisitos e preferências",
                    ],
                )
                for name in routes
            },
        }
        cases.append(
            Case(
                "hunts",
                row["id"],
                {"request": row["request"], "routes": routes},
                questions,
                {"route": row["expected"]},
                {"route": closest[0], "ranking": closest},
            )
        )
    return cases


def outcome_cases(data: dict[str, Any]) -> list[Case]:
    cases = []
    for row in data["outcomes"]:
        outcome = row["outcome"]
        cases.append(
            Case(
                "outcomes",
                row["id"],
                {
                    "action": row["action"],
                    "outcome": outcome,
                    "reply": row["reply"],
                    "status_guide": {
                        "accepted": "O servidor aceitou o objetivo. Nenhuma etapa foi confirmada.",
                        "running": "O objetivo está em andamento.",
                        "completed": "O objetivo terminou. O motivo especifica o que foi concluído.",
                        "failed": "O objetivo falhou. O motivo ou as métricas podem confirmar progresso parcial.",
                        "cancelled": "O objetivo foi interrompido. Métricas ainda podem confirmar progresso parcial.",
                    },
                    "evidence_guide": {
                        "supplies_bought": "Compra concluída em modo solo, sem registro de retorno.",
                        "supplies_bought_and_party_rejoined": "Compra concluída com retorno à party.",
                        "return_route_unavailable": "O retorno planejado não pôde ser concluído.",
                        "supply_delta": "Variação líquida do estoque de poções.",
                        "defeats_delta": "Quantidade de monstros derrotados durante o objetivo.",
                    },
                },
                {
                    "supported": noul(
                        "Todos os fatos que `reply` afirma sobre a ação são sustentados por `outcome`?",
                        "Estado, resultados parciais, números e motivos na resposta correspondem às evidências.",
                        "A resposta tem algum detalhe sem evidência, quantia incorreta ou conclusão prematura.",
                    ),
                },
                {"supported": row["supported"]},
                {"supported": outcome["status"] == "completed"},
            )
        )
    return cases


def replay_cases(data: dict[str, Any]) -> list[Case]:
    cases = []
    for row in data["replays"]:
        clips = {clip["id"]: clip for clip in row["clips"]}
        baseline = sorted(
            clips,
            key=lambda name: (-clips[name]["milestones"], -clips[name]["xp"], name),
        )
        cases.append(
            Case(
                "replays",
                row["id"],
                {
                    "clips": {
                        name: {
                            key: clip[key]
                            for key in (
                                "start_ms",
                                "end_ms",
                                "events",
                                "xp",
                                "milestones",
                            )
                        }
                        for name, clip in clips.items()
                    }
                },
                {
                    name: score(
                        f"Por si só, quão interessante seria `clips.{name}` num vídeo curto sobre a vida do bot?",
                        [
                            "Rotina ou espera sem acontecimento",
                            "Atividade útil com interesse moderado",
                            "Momento decisivo com consequência clara para a história",
                        ],
                    )
                    for name in clips
                },
                {
                    "relevance": {
                        name: clip["relevance"] for name, clip in clips.items()
                    }
                },
                {"ranking": baseline},
            )
        )
    return cases


def number(value: Any, lower: float, upper: float) -> float:
    if type(value) not in (float, int) or not lower <= value <= upper:
        raise ValueError("invalid Jev numeric answer")
    return float(value)


def flag(value: Any) -> bool | None:
    probability = number(value, 0, 1)
    if probability >= THRESHOLD:
        return True
    if probability <= 0.3:
        return False
    return None


def interpret(case: Case, answers: dict[str, Any]) -> dict[str, Any]:
    if set(answers) != set(case.questions) or any(
        answers[name]["type"] != question["type"]
        for name, question in case.questions.items()
    ):
        raise ValueError("Jev answer types or IDs do not match the request")
    if case.experiment == "intent":
        choice = answers["first_action"]["choice"]
        if choice not in case.state["offered"]:
            raise ValueError("Jev selected an unavailable action")
        actionable = flag(answers["actionable"]["noul"])
        probability = number(answers["first_action"]["probabilities"][choice], 0, 1)
        return {
            "plan": flag(answers["plan"]["noul"]),
            "sequence": flag(answers["sequence"]["noul"]),
            "action": choice if actionable and probability >= THRESHOLD else None,
        }
    if case.experiment == "outcomes":
        return {"supported": flag(answers["supported"]["noul"])}

    scores = {
        name: number(answers[name]["score"], 0, len(question["criteria"]) - 1)
        for name, question in case.questions.items()
        if question["type"] == "score"
    }
    ranking = sorted(scores, key=lambda name: (-scores[name], name))
    if case.experiment == "hunts":
        return {
            "ranking": ranking,
            "route": ranking[0] if flag(answers["match"]["noul"]) else None,
        }
    return {"ranking": ranking}


def grade(case: Case, prediction: dict[str, Any]) -> dict[str, float | bool]:
    expected = case.expected
    if case.experiment == "intent":
        metrics = {
            f"{key}_correct": prediction[key] == value
            for key, value in expected.items()
        }
        metrics["action_abstained"] = prediction["action"] is None
        if expected["action"] is None:
            metrics["false_action"] = prediction["action"] is not None
        else:
            metrics["missed_action"] = prediction["action"] is None
        return metrics
    if case.experiment == "outcomes":
        return {
            "correct": prediction["supported"] == expected["supported"],
            "review": prediction["supported"] is None,
            **(
                {"false_flag": prediction["supported"] is not True}
                if expected["supported"]
                else {"false_pass": prediction["supported"] is True}
            ),
        }
    if case.experiment == "hunts":
        route = expected["route"]
        return {
            "top_correct": prediction["route"] == route,
            **(
                {"false_match": prediction["route"] is not None}
                if route is None
                else {
                    "reciprocal_rank": 1 / (prediction["ranking"].index(route) + 1),
                }
            ),
        }

    relevance = expected["relevance"]
    chosen = prediction["ranking"][:5]
    ideal = sorted(relevance.values(), reverse=True)[:5]
    gain = sum(
        (2 ** relevance[name] - 1) / math.log2(index + 2)
        for index, name in enumerate(chosen)
    )
    best_gain = sum(
        (2**label - 1) / math.log2(index + 2) for index, label in enumerate(ideal)
    )
    return {
        "ndcg_at_5": gain / best_gain,
        "relevant_at_5": sum(relevance[name] > 0 for name in chosen) / len(chosen),
    }


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LiveJev:
    def __init__(self, budget_file: Path, cap: int) -> None:
        # Import the repo's existing accounting code only for real requests.
        from canary_brain.store import Store, month_now

        if not budget_file.is_file() or budget_file.is_symlink():
            raise ValueError("--budget-file must point to the existing shared ledger")
        with closing(
            sqlite3.connect(f"{budget_file.resolve().as_uri()}?mode=ro", uri=True)
        ) as db:
            columns = {row[1] for row in db.execute("PRAGMA table_info(requests)")}
        if not {"id", "month", "reserved", "spent", "endpoint", "run_id"} <= columns:
            raise ValueError("--budget-file is not an existing canary_brain ledger")

        self.key = os.environ.get("TYPESAFE_API_KEY", "").strip()
        if not self.key:
            raise ValueError(
                "set TYPESAFE_API_KEY in the environment for live requests"
            )
        self.store = Store(budget_file)
        self.month_now = month_now
        self.cap = cap
        self.run_id = f"jev-experiments:{uuid4().hex}"
        self.opener = build_opener(NoRedirects())

    def query(self, case: Case, request_id: str) -> dict[str, Any]:
        body = json.dumps(case.payload(), ensure_ascii=False, allow_nan=False).encode(
            "utf-8"
        )
        request = Request(
            ENDPOINT,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
            },
        )
        self.store.reserve(
            request_id,
            MAX_INPUT_TOKENS * NANOUSD_PER_TOKEN,
            self.month_now(),
            endpoint="typesafe:systemone",
            run_id=self.run_id,
            run_cap=self.cap,
        )
        started = time.monotonic()
        with self.opener.open(request, timeout=20) as response:
            result = json.load(response)
        elapsed_ms = round((time.monotonic() - started) * 1000, 2)
        tokens = result["usage"]["input_tokens"]
        if result["model"] != MODEL or type(tokens) is not int or tokens < 0:
            raise ValueError("unexpected model or input usage")
        cost = tokens * NANOUSD_PER_TOKEN
        self.store.settle(request_id, cost)
        if tokens > MAX_INPUT_TOKENS:
            raise ValueError("returned usage exceeded the reserved text context")
        return {
            "elapsed_ms": elapsed_ms,
            "cost_nanousd": cost,
            "response": {name: result[name] for name in ("model", "answers", "usage")},
        }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        group = f"{row['experiment']}/{row['group']}"
        groups[group].append(row)

    report = {}
    for group, entries in groups.items():
        stats: dict[str, Any] = {
            "cases": len(entries),
            "baseline_method": BASELINES[entries[0]["experiment"]],
        }
        for mode in ("baseline", "jev"):
            metrics: dict[str, list[float]] = defaultdict(list)
            for row in entries:
                for key, value in row.get(mode, {}).get("metrics", {}).items():
                    metrics[key].append(value)
            if metrics:
                stats[mode] = {
                    key: {"mean": round(mean(values), 4), "n": len(values)}
                    for key, values in metrics.items()
                }
        latencies = sorted(row["elapsed_ms"] for row in entries if "elapsed_ms" in row)
        if latencies:
            stats["live_requests"] = len(latencies)
            stats["p50_ms"] = median(latencies)
            stats["p95_ms"] = latencies[math.ceil(0.95 * len(latencies)) - 1]
            stats["cost_nanousd"] = sum(row.get("cost_nanousd", 0) for row in entries)
        report[group] = stats
    return report


def evaluate(cases: list[Case], live: LiveJev | None) -> dict[str, Any]:
    rows = []
    error = None
    for case in cases:
        row = {
            "experiment": case.experiment,
            "id": case.id,
            "group": case.group,
            "expected": case.expected,
            "request": case.payload(),
            "baseline": {
                "prediction": case.baseline,
                "metrics": grade(case, case.baseline),
            },
        }
        rows.append(row)
        if live is None:
            continue
        request_id = f"{live.run_id}:{case.experiment}:{case.id}"
        row["request_id"] = request_id
        try:
            row.update(live.query(case, request_id))
            prediction = interpret(case, row["response"]["answers"])
            row["jev"] = {"prediction": prediction, "metrics": grade(case, prediction)}
        except Exception as exc:  # noqa: BLE001 - Preserve partial results and ledger evidence.
            error = type(exc).__name__
            if isinstance(exc, HTTPError):
                error = f"HTTP {exc.code}"
            elif isinstance(exc, URLError):
                error = f"network: {type(exc.reason).__name__}"
            row["error"] = error
            break
    return {
        "mode": "live" if live else "offline_baseline",
        "model": MODEL,
        "run_id": live.run_id if live else None,
        "status": "stopped" if error else "complete",
        "selected_cases": len(cases),
        "summary": summarize(rows),
        "cases": rows,
    }


def usd_cap(value: str) -> int:
    try:
        amount = Decimal(value) * USD
        if 0 < amount <= 50 * USD and amount == amount.to_integral_value():
            return int(amount)
    except InvalidOperation:
        pass
    raise argparse.ArgumentTypeError(
        "expected a positive USD amount up to 50 with at most nine decimal places"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", choices=("all", *EXPERIMENTS))
    parser.add_argument(
        "--split",
        choices=("all", "pilot", "holdout"),
        default="all",
        help="intent cases only",
    )
    parser.add_argument("--output", type=Path, help="new JSON file (default: stdout)")
    parser.add_argument(
        "--live", action="store_true", help="send the synthetic fixtures to TypeSafe"
    )
    parser.add_argument(
        "--budget-file", type=Path, help="existing shared Canary Brain ledger"
    )
    parser.add_argument(
        "--max-usd", type=usd_cap, help="total USD cap for this live run"
    )
    args = parser.parse_args()
    if args.live and (args.budget_file is None or args.max_usd is None):
        parser.error("--live requires --budget-file and --max-usd")
    if args.live and args.max_usd < MAX_INPUT_TOKENS * NANOUSD_PER_TOKEN:
        parser.error(
            "--max-usd must cover at least one full-context reservation ($0.002752512)"
        )
    if not args.live and (args.budget_file is not None or args.max_usd is not None):
        parser.error("budget options apply only with --live")

    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    cases = []
    selected = EXPERIMENTS if args.experiment == "all" else (args.experiment,)
    if "intent" in selected:
        cases.extend(intent_cases(data, args.split))
    for name, build in (
        ("hunts", hunt_cases),
        ("outcomes", outcome_cases),
        ("replays", replay_cases),
    ):
        if name in selected:
            cases.extend(build(data))

    try:
        live = LiveJev(args.budget_file, args.max_usd) if args.live else None
    except (ValueError, ImportError) as exc:
        parser.error(str(exc))
    if args.output is not None:
        try:
            output = args.output.open("x", encoding="utf-8")
        except OSError as exc:
            parser.error(str(exc))
        with output:
            report = evaluate(cases, live)
            print(json.dumps(report, indent=2, ensure_ascii=False), file=output)
    else:
        report = evaluate(cases, live)
        print(json.dumps(report, indent=2))
    if report["status"] == "stopped":
        print(f"Live run stopped: {report['cases'][-1]['error']}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
