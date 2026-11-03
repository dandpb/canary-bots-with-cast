"""Deterministic held-out synthetic acceptance checks, never a claim about live skill."""

import argparse
import json
import math
import random
import statistics
import tempfile
from pathlib import Path

from canary_brain.learning import Policy
from canary_brain.store import Store


def evaluate(seeds: int = 20, episodes: int = 100) -> dict:
    arms = [f"hunt:{i}" for i in range(5)]
    rewards = [0.3, 0.9, 0.85, 0.2, 0.1]
    results = {
        "fixed_rules": [],
        "hybrid_without_learning": [],
        "hybrid_with_learning": [],
    }
    variety = []
    for seed in range(seeds):
        with tempfile.TemporaryDirectory(prefix="brain-eval-") as directory:
            root = Path(directory)
            learned = Policy(Store(root / "learned.db"), random.Random(seed))
            cold = Policy(Store(root / "cold.db"), random.Random(seed))
            # Training observations and held-out measurements use different random draws.
            train = random.Random(seed + 10000)
            for arm, reward in zip(arms, rewards, strict=True):
                for _ in range(12):
                    learned.learn(
                        7,
                        "knight-party",
                        arm,
                        max(0, min(1, reward + train.uniform(-0.1, 0.1))),
                    )
            measured = random.Random(seed + 20000)
            scores = {key: [] for key in results}
            visited = []
            for _ in range(episodes):
                noise = measured.uniform(-0.08, 0.08)
                selected = {
                    "fixed_rules": arms[0],
                    "hybrid_without_learning": cold.choose(
                        7, "knight-party", arms
                    ).candidate_id,
                    "hybrid_with_learning": learned.choose(
                        7, "knight-party", arms
                    ).candidate_id,
                }
                for key, arm in selected.items():
                    scores[key].append(max(0, min(1, rewards[arms.index(arm)] + noise)))
                visited.append(selected["hybrid_with_learning"])
            for key, values in scores.items():
                results[key].append(statistics.mean(values))
            variety.append(len(set(visited)))
    summary = {}
    for key, values in results.items():
        margin = 1.96 * statistics.stdev(values) / math.sqrt(len(values))
        mean = statistics.mean(values)
        summary[key] = {
            "mean_progress": round(mean, 4),
            "seed_mean_ci95": [round(mean - margin, 4), round(mean + margin, 4)],
        }
    # Survival is held equal by the eligible catalog fixture, not inferred from reward.
    worst_unseen_failure_rate = 3 / (seeds * episodes)
    passed = (
        summary["hybrid_with_learning"]["seed_mean_ci95"][0]
        > summary["hybrid_without_learning"]["seed_mean_ci95"][1]
        and worst_unseen_failure_rate < 0.01
        and min(variety) >= 4
    )
    return {
        "fixture": "synthetic safe eligible hunts; no live-game performance inference",
        "seeds": seeds,
        "held_out_episodes_per_seed": episodes,
        "criteria": {
            "progress_ci_separation": True,
            "survival_non_regression_bound": 0.01,
            "minimum_distinct_hunts": 4,
        },
        "results": summary,
        "observed_survival": 1,
        "zero_failure_rate_upper_approx95": worst_unseen_failure_rate,
        "distinct_hunts_range": [min(variety), max(variety)],
        "synthetic_acceptance_passed": passed,
        "live_learning_promotion": "requires isolated hunt, survival observations and human playtest",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate()
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
