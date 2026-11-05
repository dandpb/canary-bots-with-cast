"""Monotonic stop policy for timed, recorded single-bot benchmark runs."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Stops:
    horizon: float = 1800
    proposal_seconds: float = 30
    stall_seconds: float = 600
    stale_seconds: float = 5
    deaths_limit: int = 3
    model: bool = True
    start: float | None = None
    last: float | None = None
    progress_at: float | None = None
    signature: tuple[Any, ...] | None = None
    opportunity: float | None = None
    world: str | None = None
    deaths_base: int | None = None
    deaths: int = 0
    reason: str | None = None

    def observe(self, packet: dict[str, Any], now: float) -> None:
        if self.world is not None and packet["world"] != self.world:
            self.reason = "world_changed"
        self.world = packet["world"]
        if packet["type"] == "telemetry":
            value = packet["deaths"]
            if self.deaths_base is None:
                self.deaths_base = value
            self.deaths = max(self.deaths, value - self.deaths_base)
            return
        if packet["type"] != "observation":
            return
        bot = packet["bot"]
        if self.start is None:
            self.start = now
        self.last = now
        signature = (
            tuple(bot["position"]),
            bot["xp"],
            bot["potions"],
            bot.get("objective_defeats", 0),
        )
        if signature != self.signature:
            self.signature, self.progress_at = signature, now
        # No-op planning is not a missing-proposal opportunity while native work runs.
        if (
            bot.get("objective_running")
            or not bot["alive"]
            or not packet.get("autonomous")
            or len([a for a in packet.get("actions", []) if a["action"] != "hold"]) < 2
        ):
            self.opportunity = None

    def decision(self, data: dict[str, Any], now: float) -> None:
        if not self.model:
            return
        if data["phase"] == "requested":
            if len(data["observation"]["actions"]) > 1:
                if self.opportunity is None:
                    self.opportunity = now
            else:
                self.opportunity = None
        if data["phase"] == "selected":
            self.opportunity = None

    def check(self, now: float) -> str | None:
        if self.reason:
            return self.reason
        if self.start is None:
            return None
        if self.last is not None and now - self.last > self.stale_seconds:
            return "observation_stale"
        if self.deaths >= self.deaths_limit:
            return "deaths_limit"
        if (
            self.progress_at is not None
            and now - self.progress_at >= self.stall_seconds
        ):
            return "stalled"
        if (
            self.opportunity is not None
            and now - self.opportunity > self.proposal_seconds
        ):
            return "proposal_timeout"
        if now - self.start >= self.horizon:
            return "completed"
        return None
