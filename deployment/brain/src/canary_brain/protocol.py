"""Versioned wire contracts; model output never becomes an operator command."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator


class Packet(BaseModel):
    model_config = ConfigDict(
        extra="forbid", strict=True, frozen=True, allow_inf_nan=False
    )


class Candidate(Packet):
    id: str = Field(min_length=1, max_length=80)
    action: Literal[
        "continue", "follow", "hold", "hunt", "resupply", "target", "retreat", "release"
    ]
    description: str = Field(max_length=400)
    ttl_ms: int = Field(ge=100, le=30000)


class Bot(Packet):
    id: int = Field(gt=0)
    name: str = Field(max_length=64)
    level: int = Field(ge=1)
    vocation: int = Field(ge=0)
    state: str = Field(max_length=32)
    position: list[int] = Field(min_length=3, max_length=3)
    health: int = Field(ge=0, le=100)
    mana: int = Field(ge=0, le=100)
    potions: int = Field(ge=0)
    xp: int = Field(ge=0)
    alive: bool
    objective: str = "follow"
    objective_running: bool = False
    objective_defeats: int = Field(default=0, ge=0)


class MemberState(Packet):
    id: int = Field(gt=0)
    position: list[int] = Field(min_length=3, max_length=3)
    health: int = Field(ge=0, le=100)
    online: bool


class Party(Packet):
    leader_id: int = Field(gt=0)
    members: list[int] = Field(max_length=20)
    status: list[MemberState] = Field(default_factory=list, max_length=20)


class Message(Packet):
    id: str = Field(min_length=1, max_length=80)
    player_id: int = Field(gt=0)
    text: str = Field(max_length=1024)
    channel: Literal["pm", "party", "local"] = "pm"


class Observation(Packet):
    version: Literal[1] = 1
    type: Literal["observation"] = "observation"
    world: str = Field(min_length=1, max_length=80)
    sequence: int = Field(ge=0)
    captured_ms: int = Field(ge=0)
    lease: str = Field(min_length=1, max_length=80)
    objective_generation: int = Field(ge=0)
    mode: Literal["shadow", "active"] = "shadow"
    bot: Bot
    party: Party | None = None
    autonomous: bool = False
    actions: list[Candidate] = Field(min_length=1, max_length=32)
    nearby: list[dict[str, JsonValue]] = Field(default_factory=list, max_length=24)
    messages: list[Message] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def unique_candidates(self) -> "Observation":
        if len({item.id for item in self.actions}) != len(self.actions):
            raise ValueError("duplicate candidate")
        return self


class Intent(Packet):
    version: Literal[1] = 1
    type: Literal["intent"] = "intent"
    world: str
    action_id: str = Field(min_length=1, max_length=80)
    bot_id: int
    lease: str
    objective_generation: int
    observation_sequence: int
    candidate_id: str
    expires_ms: int


class Telemetry(Packet):
    """Cumulative native lifecycle counters survive a lost datagram in one world."""

    version: Literal[1] = 1
    type: Literal["telemetry"] = "telemetry"
    world: str = Field(min_length=1, max_length=80)
    bot_id: int = Field(gt=0)
    sequence: int = Field(ge=0)
    captured_ms: int = Field(ge=0)
    deaths: int = Field(ge=0)
    phase: Literal["alive", "dead", "hibernated", "unavailable"]
    model_owned: bool = False


class Outcome(Packet):
    version: Literal[1] = 1
    type: Literal["outcome"] = "outcome"
    world: str
    action_id: str
    bot_id: int
    status: Literal[
        "accepted", "running", "completed", "failed", "rejected", "expired", "cancelled"
    ]
    reason: str = ""
    metrics: dict[str, float] = Field(default_factory=dict)


def intent_for(observation: Observation, candidate_id: str, action_id: str) -> Intent:
    candidate = next(
        (item for item in observation.actions if item.id == candidate_id), None
    )
    if candidate is None:
        raise ValueError("unknown candidate")
    return Intent(
        world=observation.world,
        action_id=action_id,
        bot_id=observation.bot.id,
        lease=observation.lease,
        objective_generation=observation.objective_generation,
        observation_sequence=observation.sequence,
        candidate_id=candidate.id,
        expires_ms=observation.captured_ms + candidate.ttl_ms,
    )
