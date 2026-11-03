"""An auditable contextual bandit over server-approved objectives."""

import random
import time
from dataclasses import dataclass
from typing import Any

from .store import Store

VERSION = "bandit-v1"


@dataclass(frozen=True)
class Selection:
    candidate_id: str
    probability: float
    exploring: bool
    policy_version: str = VERSION


class Policy:
    def __init__(
        self, store: Store, rng: random.Random | None = None, epsilon: float = 0.15
    ) -> None:
        if not 0 <= epsilon <= 0.5:
            raise ValueError("exploration must be between zero and 0.5")
        self.store, self.rng, self.epsilon = store, rng or random.Random(), epsilon

    def checkpoint(self, name: str) -> None:
        if not name or len(name) > 64:
            raise ValueError("checkpoint name must contain one to 64 characters")
        with self.store.atomic():
            self.store.put(
                "checkpoint",
                name,
                {
                    "version": VERSION,
                    "at": time.time(),
                    "policy": self.store.records("policy", 1000),
                    "recent": self.store.records("recent", 1000),
                },
            )

    def rollback(self, name: str) -> None:
        with self.store.atomic():
            saved = self.store.get("checkpoint", name)
            if saved is None or saved.get("version") != VERSION:
                raise ValueError("compatible checkpoint not found")
            for kind in ("policy", "recent"):
                for key, _ in self.store.records(kind, 1000):
                    self.store.delete(kind, key)
                for key, data in saved[kind]:
                    self.store.put(kind, key, data)

    def statistics(self, bot: int, context: str) -> dict[str, Any]:
        actions = (self.store.get("policy", f"{bot}:{context}") or {}).get(
            "actions", {}
        )
        if not isinstance(actions, dict):
            raise TypeError("invalid stored policy")
        return actions

    def learn(self, bot: int, context: str, action: str, reward: float) -> None:
        if not 0 <= reward <= 1:
            raise ValueError("reward must be between zero and one")
        actions = self.statistics(bot, context)
        previous = actions.get(action, {"count": 0, "mean": 0.5})
        count = int(previous["count"]) + 1
        # A finite effective window adapts after equipment, level, or world changes.
        mean = float(previous["mean"]) + (reward - float(previous["mean"])) / min(
            count, 30
        )
        actions[action] = {"count": count, "mean": mean, "updated": time.time()}
        self.store.put(
            "policy", f"{bot}:{context}", {"version": VERSION, "actions": actions}
        )

    def choose(
        self,
        bot: int,
        context: str,
        candidates: list[str],
        preferred: str | None = None,
    ) -> Selection:
        if not candidates or len(set(candidates)) != len(candidates):
            raise ValueError("unique eligible candidates are required")
        actions = self.statistics(bot, context)
        recent = (self.store.get("recent", str(bot)) or {}).get("actions", [])[-12:]
        eligible = list(candidates)
        last = (self.store.get("recent", str(bot)) or {}).get("last", {})
        cooled = [item for item in eligible if time.time() - last.get(item, 0) >= 120]
        if cooled:
            eligible = cooled
        if len(eligible) > 1 and len(recent) >= 3 and len(set(recent[-3:])) == 1:
            eligible = [item for item in eligible if item != recent[-1]]

        def quality(action: str) -> tuple[float, int, int]:
            learned = actions.get(action, {})
            value = (
                float(learned.get("mean", 0.5)) if learned.get("count", 0) >= 3 else 0.5
            )
            return (
                value - 0.06 * recent.count(action),
                int(action == preferred),
                -recent.count(action),
            )

        best_quality = max(quality(action) for action in eligible)
        best = [action for action in eligible if quality(action) == best_quality]
        weights = [1.0 / (1 + recent.count(action)) for action in eligible]
        exploring = len(eligible) > 1 and self.rng.random() < self.epsilon
        selected = (
            self.rng.choices(eligible, weights=weights)[0]
            if exploring
            else self.rng.choice(best)
        )
        probability = self.epsilon * weights[eligible.index(selected)] / sum(weights)
        probability += (1 - self.epsilon) / len(best) if selected in best else 0
        if len(eligible) == 1:
            probability = 1.0
        last[selected] = time.time()
        self.store.put(
            "recent",
            str(bot),
            {
                "actions": (recent + [selected])[-12:],
                "last": {
                    key: value
                    for key, value in last.items()
                    if time.time() - value < 86400
                },
            },
        )
        return Selection(selected, probability, exploring)


def episode_reward(
    status: str, metrics: dict[str, float], objective: str = ""
) -> float | None:
    """Only authoritative, completed useful episodes can earn positive reward."""
    if status in {"cancelled", "expired", "rejected"}:
        return None
    if metrics.get("deaths", 0) > 0:
        return 0.0
    if status != "completed":
        return 0.1 if status == "failed" else None
    progress = min(1.0, max(0.0, metrics.get("progress", 0)))
    if progress == 0 or metrics.get("elapsed_seconds", 0) < 5:
        return None
    danger = min(1.0, max(0.0, metrics.get("danger", 0)))
    elapsed = metrics["elapsed_seconds"]
    if objective.startswith("hunt:"):
        level = max(1, metrics.get("level", 1))
        party = max(1, metrics.get("party_size", 1))
        # Conservative per-level/party normalization; yield remains subordinate to survival.
        yield_score = min(
            1, metrics.get("xp_delta", 0) / max(1, level * level * elapsed / 60 * party)
        )
        supplies = max(0, -metrics.get("supply_delta", 0))
        efficiency = yield_score / (1 + supplies / max(1, level))
    else:
        efficiency = 1 / (1 + elapsed / 300)
    efficiency = min(1.0, max(0.0, metrics.get("efficiency", efficiency)))
    cohesion = 1 / (1 + max(0, metrics.get("party_distance", 0)) / 12)
    novelty = min(1.0, max(0.0, metrics.get("novelty", 0)))
    return min(
        1.0,
        max(
            0.0,
            0.5 * progress
            + 0.3 * (1 - danger)
            + 0.1 * cohesion
            + 0.05 * efficiency
            + 0.05 * novelty,
        ),
    )
