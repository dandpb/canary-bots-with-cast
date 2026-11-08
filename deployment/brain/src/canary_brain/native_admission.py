"""Prospective native qualification contract; runtime activation is a later gate.

Call only with packets from the pinned private peer. Completion here proves an
in-memory interval, not committed recorder coverage or successful shutdown.
"""

import json
from hashlib import sha256
from typing import Any, Literal

from pydantic import Field, model_validator

from .protocol import Observation, Packet, Telemetry, TelemetryStatus


class Admission(Packet):
    version: Literal[1] = 1
    type: Literal["telemetry_admitted"] = "telemetry_admitted"
    world: str = Field(min_length=1, max_length=80)
    bot_id: int = Field(gt=0)
    nonce: str = Field(min_length=1, max_length=80)
    begin_sequence: int = Field(gt=0)
    captured_ms: int = Field(ge=0)
    deaths: int = Field(ge=0)
    observation: Observation
    source: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_dirty: bool
    fault: str = Field(max_length=80)

    @model_validator(mode="after")
    def baseline(self) -> "Admission":
        initial = self.observation
        if (
            initial.world != self.world
            or initial.bot.id != self.bot_id
            or initial.captured_ms != self.captured_ms
            or not initial.bot.alive
        ):
            raise ValueError("inconsistent admission baseline")
        return self


class Qualification:
    """Fail-closed contiguous interval from admitted B, never first receipt.

    Single attempt, no restoration after process loss. Keep a bounded duplicate
    cache; exceeding it fails rather than silently forgetting sequence evidence.
    """

    def __init__(
        self,
        admission: Admission,
        *,
        nonce: str,
        world: str,
        bot_id: int,
        source: str,
        horizon_ms: int = 1_800_000,
    ) -> None:
        if (
            admission.nonce != nonce
            or admission.world != world
            or admission.bot_id != bot_id
            or admission.source != source
            or admission.source_dirty
            or admission.fault
        ):
            raise ValueError("admission identity or native fault")
        # Pydantic frozen models contain mutable nested lists; retain a private copy.
        self._admission = admission.model_copy(deep=True)
        self.horizon_ms = max(1_800_000, horizon_ms)
        self.failure: str | None = None
        self.deaths = 0
        self._next = admission.begin_sequence
        self._frames: dict[int, Telemetry] = {}
        self._captured = admission.captured_ms
        self._observation = admission.observation.model_copy(deep=True)
        self._observations = {
            admission.observation.sequence: self._observation_digest(self._observation)
        }
        self._horizon: Observation | None = None

    @staticmethod
    def _observation_digest(observation: Observation) -> str:
        # Comparable full-payload evidence, bounded independently of packet size.
        encoded = json.dumps(
            observation.model_dump(), sort_keys=True, separators=(",", ":")
        )
        return sha256(encoded.encode()).hexdigest()

    def abort(self, reason: str) -> None:
        if self.failure is None:
            self.failure = reason

    def retry(self, admission: Admission) -> None:
        if admission != self._admission:
            self.abort("admission_changed")

    def telemetry(self, packet: dict[str, Any]) -> None:
        if self.failure:
            return
        try:
            event = Telemetry.model_validate(packet)
        except ValueError:
            self.abort("invalid_telemetry")
            return
        a = self._admission
        if event.world != a.world or event.bot_id != a.bot_id:
            self.abort("identity_changed")
            return
        if event.sequence < a.begin_sequence:
            return  # pre-admission traffic is outside the certified interval
        if event.sequence in self._frames:
            if self._frames[event.sequence] != event:
                self.abort("telemetry_changed")
            return
        if event.sequence != self._next:
            self.abort("telemetry_gap")
            return
        if event.sequence == a.begin_sequence and (
            event.run_nonce != a.nonce
            or event.captured_ms != a.captured_ms
            or event.deaths != a.deaths
            or event.phase != "alive"
        ):
            self.abort("invalid_boundary")
            return
        if event.sequence != a.begin_sequence and event.run_nonce:
            self.abort("unexpected_boundary")
            return
        if event.captured_ms < self._captured or event.deaths < a.deaths + self.deaths:
            self.abort("native_regression")
            return
        if event.phase in {"unavailable", "hibernated"}:
            self.abort("bot_unavailable")
            return
        if len(self._frames) >= 8192:
            self.abort("coverage_limit")
            return
        self._frames[event.sequence] = event
        self._next += 1
        self._captured = event.captured_ms
        self.deaths = event.deaths - a.deaths

    def observe(self, packet: dict[str, Any]) -> None:
        if self.failure:
            return
        try:
            initial = Observation.model_validate(packet)
        except ValueError:
            self.abort("invalid_observation")
            return
        a = self._admission
        if initial.world != a.world or initial.bot.id != a.bot_id:
            self.abort("identity_changed")
            return
        fingerprint = self._observation_digest(initial)
        if initial.sequence in self._observations:
            if self._observations[initial.sequence] != fingerprint:
                self.abort("observation_changed")
            return
        if initial.sequence < a.observation.sequence:
            return  # Observations from before O0 are outside the admission interval.
        if initial.sequence <= self._observation.sequence:
            self.abort("observation_regression")
            return
        if initial.captured_ms < self._observation.captured_ms:
            self.abort("native_regression")
            return
        if len(self._observations) >= 8192:
            self.abort("observation_coverage_limit")
            return
        self._observations[initial.sequence] = fingerprint
        self._observation = initial
        if (
            self._horizon is None
            and initial.captured_ms - a.captured_ms >= self.horizon_ms
        ):
            self._horizon = initial

    def frame(self, sequence: int) -> Telemetry | None:
        return self._frames.get(sequence)

    @property
    def horizon(self) -> Observation | None:
        return self._horizon

    def complete(self, packet: dict[str, Any] | None) -> bool:
        if self.failure or packet is None:
            return False
        try:
            status = TelemetryStatus.model_validate(packet)
        except ValueError:
            self.abort("invalid_watermark")
            return False
        a = self._admission
        if (
            status.world != a.world
            or status.bot_id != a.bot_id
            or status.overflow_frames
            or status.discarded_frames
            or status.fault
        ):
            self.abort("terminal_fault")
            return False
        if self._horizon is None:
            return False
        return (
            not status.pending_frames
            and not status.pending_bytes
            and status.issued_sequence == status.accepted_sequence == self._next - 1
            and self._next > a.begin_sequence
            and status.captured_ms >= max(self._horizon.captured_ms, self._captured)
        )
