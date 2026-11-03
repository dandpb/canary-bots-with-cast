"""Explicit offline fixture; never an automatic provider fallback."""

from typing import Any

from .protocol import Observation
from .provider import Proposal


class FakeProvider:
    async def decide(
        self, observation: Observation, memory: dict[str, Any] | None = None
    ) -> str:
        return "continue"

    async def converse(
        self,
        observation: Observation,
        text: str,
        authorized: bool,
        memory: list[dict[str, Any]] | None = None,
        deep: bool = False,
    ) -> Proposal:
        candidates = {item.id for item in observation.actions}
        requested = "continue"
        for word, candidate in (
            ("aguard", "hold"),
            ("fique", "hold"),
            ("siga", "follow"),
            ("reabaste", "resupply"),
            ("poc", "resupply"),
            ("recue", "retreat"),
        ):
            if word in text.lower() and candidate in candidates and authorized:
                requested = candidate
                break
        return Proposal(
            requested,
            f"Teste: proposta {requested}; aguardando confirmação do jogo.",
            "low",
        )
