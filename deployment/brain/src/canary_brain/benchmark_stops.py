"""Monotonic stop policy for timed, recorded single-bot benchmark runs."""

from dataclasses import dataclass, field
from typing import Any

from .protocol import Observation, TelemetryStatus


@dataclass
class TelemetryTail:
    """Freeze the real horizon observation, then one producer delivery watermark."""

    observation: Observation
    deadline: float
    required_sequence: int | None = None
    cutoff: TelemetryStatus | None = None

    def confirm(
        self,
        status: TelemetryStatus | None,
        received: tuple[str, int] | None,
        *,
        invalid: bool = False,
    ) -> bool:
        if (
            invalid
            or status is None
            or status.world != self.observation.world
            or status.bot_id != self.observation.bot.id
            or status.overflow_frames
            or status.discarded_frames
        ):
            return False
        if self.required_sequence is None:
            if (
                status.captured_ms < self.observation.captured_ms
                or status.pending_frames
                or status.pending_bytes
                or status.issued_sequence < 1
                or status.issued_sequence != status.accepted_sequence
            ):
                return False
            self.required_sequence = status.issued_sequence
            self.cutoff = status
        return (
            received is not None
            and received[0] == self.observation.world
            and received[1] >= self.required_sequence
        )


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
    sequences: dict[str, int] = field(default_factory=dict)

    def observe(self, packet: dict[str, Any], now: float) -> None:
        if self.world is not None and packet["world"] != self.world:
            self.reason = "world_changed"
        self.world = packet["world"]
        kind = packet["type"]
        if "sequence" in packet:
            sequence = packet["sequence"]
            if sequence <= self.sequences.get(kind, -1):
                return
            self.sequences[kind] = sequence
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
        if self.last is not None and self.last - self.start >= self.horizon:
            return "completed"
        return None
