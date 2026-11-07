"""Live operator supervision over the same offers and outcomes used by the brain.

No game credentials, admin commands, invented rewards or movement destinations.
Human advice is labelled advice; native outcomes remain the source of truth.
"""

import asyncio
import time
import uuid
from collections import deque
from typing import TYPE_CHECKING, Any

from .protocol import Observation, Outcome
from .recording import attribution

if TYPE_CHECKING:
    from .controller import Controller


class Supervisor:
    def __init__(self, controller: "Controller") -> None:
        self.controller = controller
        self.store = controller.store
        self.received: dict[int, float] = {}
        self.progress: dict[int, dict[str, Any]] = {}
        self.samples: dict[int, deque[dict[str, Any]]] = {}
        self.settings: dict[int, dict[str, Any]] = {}
        self.revision: dict[int, int] = {}
        self.acknowledged: deque[tuple[str, str, str]] = deque(maxlen=512)

    def state(self, bot: int) -> dict[str, Any]:
        if bot not in self.settings:
            self.settings[bot] = self.store.get("supervision", str(bot)) or {
                "paused": False,
                "automatic": True,
                "phase": "idle",
            }
        return self.settings[bot]

    def save(self, bot: int) -> None:
        self.store.put("supervision", str(bot), self.state(bot))

    def event(self, bot: int, kind: str, text: str, **details: Any) -> None:
        self.controller.record(bot, "operator", {"kind": kind, "text": text, **details})
        self.store.put(
            "operator_event",
            uuid.uuid4().hex,
            {
                "bot": bot,
                "kind": kind,
                "text": text,
                "at": time.time(),
                **details,
            },
        )

    def advice(self, bot: int) -> list[dict[str, Any]]:
        return [
            {"kind": "operator_advice", "text": row["text"], "at": row["at"]}
            for _, row in self.store.records("guidance", 100)
            if row.get("bot") == bot
        ][:8]

    def blocked(self, bot: int) -> dict[str, dict[str, Any]]:
        state = self.state(bot)
        return {
            key: row
            for key, row in state.get("avoided", {}).items()
            if row["until"] > time.time()
        }

    def offers(self, snapshot: Observation) -> Observation:
        if not snapshot.autonomous or snapshot.party is not None:
            return snapshot
        avoided = self.blocked(snapshot.bot.id)
        return snapshot.model_copy(
            update={
                "actions": [
                    item for item in snapshot.actions if item.id not in avoided
                ],
            }
        )

    def managed(self, bot: int) -> bool:
        state = self.state(bot)
        return bool(state.get("paused") or state.get("phase", "idle") != "idle")

    def current_candidate(self, bot: int) -> str | None:
        snapshot = self.controller.latest.get(bot)
        for _, row in self.store.records("episode", 100):
            if (
                row.get("bot") == bot
                and not row.get("terminal")
                and snapshot
                and row.get("world") == snapshot.world
                and row.get("candidate", "").startswith("hunt:")
            ):
                return str(row["candidate"])
        return None

    def snapshot(self, bot: int) -> Observation:
        snapshot = self.controller.latest.get(bot)
        if snapshot is None or time.time() - self.received.get(bot, 0) > 3:
            raise ValueError("Observação indisponível ou antiga; aguarde o servidor.")
        if not snapshot.autonomous or snapshot.party is not None:
            raise ValueError(
                "O controle local exige um bot autônomo fora de party humana."
            )
        if (
            not snapshot.bot.alive
            or snapshot.mode != "active"
            or self.controller.mode != "active"
        ):
            raise ValueError("O personagem precisa estar vivo e a IA ativa.")
        return snapshot

    def interrupt(self, bot: int) -> None:
        self.revision[bot] = self.revision.get(bot, 0) + 1
        for (target, _), task in list(self.controller.pending.items()):
            if target == bot:
                task.cancel()
        self.store.delete("plan", str(bot))
        # Do not retransmit a superseded proposal after an operator intervention.
        for key, row in self.store.records("pending", 1000):
            if row["intent"]["bot_id"] == bot:
                row.update(status="querying", at=time.monotonic())
                self.store.put("pending", key, row)

    def send(self, snapshot: Observation, candidate: str, phase: str) -> str:
        if candidate not in {item.id for item in self.offers(snapshot).actions}:
            raise ValueError("Essa ação não está disponível neste momento.")
        action_id = self.controller._apply(
            snapshot,
            candidate,
            {"source": "operator"},
            operator=True,
        )
        if action_id is None:
            raise ValueError("O servidor não ofereceu uma ação executável.")
        state = self.state(snapshot.bot.id)
        state.update(
            phase=phase,
            action_id=action_id,
            sent_at=time.time(),
            generation=snapshot.objective_generation,
            world=snapshot.world,
        )
        self.save(snapshot.bot.id)
        self.event(
            snapshot.bot.id,
            "proposed",
            f"Ação enviada: {candidate}; aguardando confirmação.",
            action_id=action_id,
            candidate=candidate,
        )
        return action_id

    def command(
        self,
        bot: int,
        operation: str,
        data: dict[str, Any],
        *,
        automatic_recovery: bool = False,
    ) -> dict[str, Any]:
        result = self._command(
            bot, operation, data, automatic_recovery=automatic_recovery
        )
        self.controller.record(
            bot,
            "operator",
            {
                "operation": operation,
                "automatic": automatic_recovery,
            },
        )
        return result

    def _command(
        self,
        bot: int,
        operation: str,
        data: dict[str, Any],
        *,
        automatic_recovery: bool = False,
    ) -> dict[str, Any]:
        snapshot = self.snapshot(bot)
        state = self.state(bot)
        if operation == "automatic":
            if type(data.get("enabled")) is not bool:
                raise ValueError("Informe se a recuperação automática está habilitada.")
            state["automatic"] = data["enabled"]
            self.save(bot)
            return {"status": "saved"}
        if operation == "note":
            text = str(data.get("text", "")).strip()
            if not text or len(text) > 1000:
                raise ValueError("Escreva uma orientação de até 1.000 caracteres.")
            key = uuid.uuid4().hex
            self.store.put(
                "guidance",
                key,
                {
                    "bot": bot,
                    "text": text,
                    "kind": "operator_advice",
                    "at": time.time(),
                    "position": snapshot.bot.position,
                },
            )
            self.event(bot, "advice", "Orientação guardada para as próximas decisões.")
            return {"status": "saved", "id": key}
        if operation == "forget_note":
            key = str(data.get("id", ""))
            note = self.store.get("guidance", key)
            if note is None or note.get("bot") != bot:
                raise ValueError("Orientação não encontrada.")
            self.store.delete("guidance", key)
            return {"status": "removed"}
        if operation == "allow_route":
            candidate = str(data.get("candidate", ""))
            state.setdefault("avoided", {}).pop(candidate, None)
            self.save(bot)
            return {"status": "removed"}
        if operation == "avoid":
            active_candidate = self.current_candidate(bot)
            if active_candidate is None:
                raise ValueError("Não há uma caça ativa confirmada para evitar.")
            self.avoid(bot, active_candidate, 1800, "Orientação do operador")
            return {"status": "saved", "candidate": active_candidate}
        if operation not in {"pause", "resume", "recover", "retreat"}:
            raise ValueError("Operação desconhecida.")
        if (
            operation == "resume"
            and not self.managed(bot)
            and snapshot.bot.objective != "hold"
        ):
            return {"status": "already_running", "phase": "idle"}
        offered = {item.id for item in snapshot.actions}
        required = "retreat" if operation == "retreat" else "hold"
        if operation != "resume" and required not in offered:
            raise ValueError("Essa ação não foi oferecida pelo servidor.")
        self.interrupt(bot)
        state["paused"] = operation == "pause"
        if operation == "resume":
            state.update(phase="choose", world=snapshot.world)
            self.save(bot)
            self.event(
                bot, "resume", "Retomada solicitada; aguardando uma oferta atual."
            )
        elif operation == "retreat":
            self.send(snapshot, "retreat", "waiting_action")
        else:
            if operation == "recover":
                recovering_candidate = self.current_candidate(bot)
                if recovering_candidate:
                    self.avoid(bot, recovering_candidate, 1800, "Rota em recuperação")
                state["last_recovery"] = time.time()
                recent_recoveries = [
                    at for at in state.get("recoveries", []) if time.time() - at < 3600
                ]
                state["recoveries"] = (recent_recoveries + [time.time()])[-12:]
                if automatic_recovery:
                    automatic_times = [
                        at
                        for at in state.get("automatic_recoveries", [])
                        if time.time() - at < 3600
                    ]
                    state["automatic_recoveries"] = automatic_times + [time.time()]
                state["recovery_count"] = state.get("recovery_count", 0) + 1
                self.event(
                    bot,
                    "recovery",
                    "Recuperação iniciada: pausa, nova observação e outra ação elegível.",
                )
            self.send(snapshot, "hold", "waiting_hold")
        return {"status": "requested", "phase": state["phase"]}

    def avoid(self, bot: int, candidate: str, seconds: int, reason: str) -> None:
        state = self.state(bot)
        state["avoided"] = self.blocked(bot)
        state["avoided"][candidate] = {"until": time.time() + seconds, "reason": reason}
        self.save(bot)
        self.event(
            bot,
            "avoid",
            f"{candidate} será evitada por {seconds // 60} minutos.",
            candidate=candidate,
        )

    def outcome(self, outcome: Outcome) -> None:
        acknowledgement = (outcome.action_id, outcome.status, outcome.reason)
        if acknowledgement in self.acknowledged:
            return
        self.acknowledged.append(acknowledgement)
        episode = self.store.get("episode", outcome.action_id) or {}
        if (episode.get("selection") or {}).get("source") == "operator":
            self.event(
                outcome.bot_id,
                "outcome",
                f"Servidor: {outcome.status} ({outcome.reason}).",
                action_id=outcome.action_id,
                candidate=episode.get("candidate"),
            )
        state = self.state(outcome.bot_id)
        snapshot = self.controller.latest.get(outcome.bot_id)
        candidate = str(episode.get("candidate", ""))
        if (
            snapshot is not None
            and snapshot.autonomous
            and snapshot.party is None
            and state.get("automatic", True)
            and outcome.status == "failed"
            and candidate.startswith("hunt:")
            and outcome.reason in {"no_confirmed_combat_progress", "objective_timeout"}
            and outcome.metrics.get("elapsed_seconds", 0) >= 300
            and outcome.metrics.get("xp_delta", 0) <= 0
            and outcome.metrics.get("defeats_delta", 0) <= 0
        ):
            self.avoid(
                outcome.bot_id,
                candidate,
                1800,
                "Caça encerrada pelo servidor sem resultado após cinco minutos",
            )
        if (
            state.get("world") != outcome.world
            or state.get("action_id") != outcome.action_id
        ):
            return
        phase = state.get("phase")
        if phase not in {"waiting_hold", "waiting_action"}:
            return
        if outcome.status in {"accepted", "running", "completed"}:
            state["phase"] = (
                ("paused" if state.get("paused") else "choose")
                if phase == "waiting_hold"
                else "idle"
            )
            state["next_hold"] = time.time() + 20
        elif outcome.status in {"failed", "rejected", "expired", "cancelled"}:
            state.update(phase="failed", paused=True, error=outcome.reason)
        self.save(outcome.bot_id)

    def observe(self, snapshot: Observation) -> None:
        bot, now = snapshot.bot.id, time.time()
        previous_at = self.received.get(bot, 0)
        self.received[bot] = now
        progress = self.progress.get(bot)
        previous = progress.get("previous") if progress else None
        changed = (
            previous is None
            or previous.world != snapshot.world
            or previous.bot.position != snapshot.bot.position
            or previous.bot.xp != snapshot.bot.xp
            or snapshot.bot.objective_defeats > previous.bot.objective_defeats
        )
        if progress is None or changed or now - previous_at > 10:
            progress = {**(progress or {}), "since": now}
            self.progress[bot] = progress
        position = snapshot.bot.position
        origin = progress.get("navigation_origin")
        if (
            previous is None
            or previous.world != snapshot.world
            or (snapshot.bot.objective == "retreat"
                and previous.bot.objective != "retreat"
                and now - progress.get("last_retreat_seen", 0) > 60)
            or now - previous_at > 10
            or origin is None
            or position[2] != origin[2]
            or max(abs(position[0] - origin[0]), abs(position[1] - origin[1])) > 3
        ):
            progress["navigation_since"] = now
            progress["navigation_origin"] = position
        if snapshot.bot.objective == "retreat":
            progress["last_retreat_seen"] = now
        progress["previous"] = snapshot
        rows = self.samples.setdefault(bot, deque(maxlen=360))
        if not rows or now - rows[-1]["at"] >= 5:
            rows.append(
                {
                    "at": now,
                    "position": snapshot.bot.position,
                    "xp": snapshot.bot.xp,
                    "health": snapshot.bot.health,
                    "defeats": snapshot.bot.objective_defeats,
                    "objective": snapshot.bot.objective,
                }
            )
        if (
            not snapshot.autonomous
            or snapshot.party is not None
            or not snapshot.bot.alive
        ):
            return
        state = self.state(bot)
        if state.get("world") not in {None, snapshot.world}:
            if state.get("phase", "idle") != "idle":
                state.update(phase="failed", paused=True, error="world_changed")
            state["world"] = snapshot.world
            self.save(bot)
        phase = state.get("phase", "idle")
        if phase in {"waiting_hold", "waiting_action"}:
            if now - state.get("sent_at", now) > 12:
                state.update(phase="failed", paused=True, error="ack_timeout")
                self.save(bot)
                self.event(
                    bot,
                    "failure",
                    "Sem confirmação do servidor; recuperação interrompida.",
                )
            return
        if state.get("paused"):
            if (
                phase != "failed"
                and now >= state.get("next_hold", 0)
                and "hold" in {item.id for item in snapshot.actions}
            ):
                self.send(snapshot, "hold", "waiting_hold")
            return
        if phase == "choose":
            if (
                snapshot.objective_generation <= state.get("generation", -1)
                and snapshot.bot.objective == "hold"
            ):
                return
            offers = self.offers(snapshot).actions
            actions = {item.id: item for item in offers}
            candidate = None
            if snapshot.bot.health < 80 and "retreat" in actions:
                candidate = "retreat"
            elif "resupply" in actions and snapshot.bot.potions < 20:
                candidate = "resupply"
            else:
                hunts = [item.id for item in offers if item.action == "hunt"]
                if hunts:
                    candidate = self.controller.policy.choose(
                        bot, self.controller.context(snapshot), hunts
                    ).candidate_id
                elif "retreat" in actions:
                    candidate = "retreat"
            if candidate:
                self.send(snapshot, candidate, "waiting_action")
            elif snapshot.bot.objective != "hold" or not snapshot.bot.objective_running:
                state["phase"] = "idle"
                self.save(bot)
                self.event(
                    bot,
                    "waiting",
                    "Nenhuma rota alternativa disponível; autonomia retomada com as restrições atuais.",
                )
            return
        navigation_stalled = (
            snapshot.bot.objective_running
            and snapshot.bot.objective == "retreat"
            and now - progress["navigation_since"] >= 300
        )
        if navigation_stalled and now - state.get("last_navigation_alert", 0) >= 300:
            state["last_navigation_alert"] = now
            self.save(bot)
            self.event(bot, "retreat_stall", "Retirada sem avanço de posição por cinco minutos, mesmo que haja combate ou XP.")
            anchor = state.get("retreat_retry_anchor")
            if anchor is None and state.get("retreat_retries") and state.get("world") == snapshot.world:
                anchor = list(position)
                state["retreat_retry_anchor"] = anchor
                state["retreat_retry_world"] = snapshot.world
                self.save(bot)
            if (state.get("retreat_retry_world") != snapshot.world or anchor is None
                or position[2] != anchor[2]
                or max(abs(position[0] - anchor[0]), abs(position[1] - anchor[1])) > 3):
                state["retreat_retry_anchor"] = list(position)
                state["retreat_retry_world"] = snapshot.world
                state["retreat_retries"] = []
                self.save(bot)
            attempts = state.get("retreat_retries", [])
            if (
                state.get("automatic", True)
                and len(attempts) < 2
                and (not attempts or now - attempts[-1] >= 600)
                and "retreat" in {item.id for item in self.offers(snapshot).actions}
            ):
                try:
                    self.command(bot, "retreat", {}, automatic_recovery=True)
                except ValueError:
                    self.event(bot, "waiting", "A nova tentativa da retirada aguarda uma oferta atual.")
                else:
                    state["retreat_retries"] = attempts + [now]
                    self.save(bot)
                    self.event(bot, "retreat_retry", "Retirada solicitada novamente; aguardando confirmação do servidor.")
            return
        stagnant = now - progress["since"] >= 300
        working = snapshot.bot.objective_running and snapshot.bot.objective in {
            "hunt",
            "retreat",
            "resupply",
        }
        if stagnant and working and now - state.get("last_alert", 0) >= 300:
            state["last_alert"] = now
            self.save(bot)
            self.event(
                bot,
                "stall",
                "Cinco minutos sem movimento, XP ou novos abates; verificar a tarefa.",
            )
            # Do not interrupt an ongoing combat or a weakened character blindly.
            if (
                state.get("automatic", True)
                and not snapshot.nearby
                and snapshot.bot.health >= 80
                and now - state.get("last_recovery", 0) >= 600
                and len(
                    [
                        at
                        for at in state.get("automatic_recoveries", [])
                        if now - at < 3600
                    ]
                )
                < 2
            ):
                try:
                    self.command(bot, "recover", {}, automatic_recovery=True)
                except ValueError:
                    self.event(
                        bot,
                        "waiting",
                        "A recuperação aguarda uma ação segura oferecida pelo servidor.",
                    )

    def view(self) -> dict[str, Any]:
        now = time.time()
        bots = []
        for bot, snapshot in self.controller.latest.items():
            if not snapshot.autonomous:
                continue
            age = now - self.received.get(bot, 0)
            quiet = now - self.progress.get(bot, {}).get("since", now)
            diagnosis = (
                "stale"
                if age > 3
                else "retreat_stalled"
                if snapshot.bot.objective_running
                and snapshot.bot.objective == "retreat"
                and now - self.progress.get(bot, {}).get("navigation_since", now) >= 300
                else "combat"
                if snapshot.nearby
                else "stalled"
                if quiet >= 300
                and snapshot.bot.objective_running
                and snapshot.bot.objective != "hold"
                else "observing"
            )
            bots.append(
                {
                    **snapshot.bot.model_dump(),
                    "world": snapshot.world,
                    "observation_age": round(age, 2),
                    "no_progress_seconds": round(quiet),
                    "no_navigation_progress_seconds": round(now - self.progress.get(bot, {}).get("navigation_since", now)),
                    "diagnosis": diagnosis,
                    "candidate": self.current_candidate(bot),
                    "actions": [
                        item.model_dump() for item in self.offers(snapshot).actions
                    ],
                    "control": self.state(bot),
                    "avoided": self.blocked(bot),
                    "history": list(self.samples.get(bot, [])),
                    "chat": (self.store.get("operator_chat", str(bot)) or {}).get(
                        "entries", []
                    ),
                    "notes": [
                        {"id": key, **row}
                        for key, row in self.store.records("guidance", 100)
                        if row.get("bot") == bot
                    ],
                    "events": self.events(bot),
                    "episodes": [
                        {"id": key, **row}
                        for key, row in self.store.records("episode", 60)
                        if row.get("bot") == bot
                    ][:12],
                }
            )
        return {"at": now, "mode": self.controller.mode, "bots": bots}

    def events(self, bot: int) -> list[dict[str, Any]]:
        result = []
        seen = set()
        for _, row in self.store.records("operator_event", 200):
            if row.get("bot") != bot:
                continue
            if row.get("kind") == "outcome":
                key = (row.get("action_id"), row["text"])
                if key in seen:
                    continue
                seen.add(key)
            result.append(row)
            if len(result) >= 30:
                break
        return result

    async def chat(self, bot: int, text: str, act: bool) -> dict[str, Any]:
        c = self.controller
        c.require_model_admission()
        if bot in c.operator_tasks or len(c.operator_tasks) >= 3:
            raise ValueError("O bot já está respondendo; aguarde.")
        with attribution(bot):
            task = asyncio.current_task()
            assert task is not None
            c.operator_tasks[bot] = task
            try:
                # Track the actual request task, preserving its initial snapshot
                # before another operator command can run.
                result = await self._chat(bot, text, act)
                c.record(bot, "operator", {"operation": "chat_act" if act else "chat"})
                return result
            finally:
                if c.operator_tasks.get(bot) is task:
                    c.operator_tasks.pop(bot, None)

    async def _chat(self, bot: int, text: str, act: bool) -> dict[str, Any]:
        self.controller.require_model_admission()
        snapshot = self.snapshot(bot)
        observed_at = self.received[bot]
        if not text.strip() or len(text) > 1024:
            raise ValueError("Escreva uma mensagem de até 1.024 caracteres.")
        if act and self.managed(bot):
            raise ValueError(
                "Retome a autonomia antes de enviar uma ordem pela conversa."
            )
        revision = self.revision.get(bot, 0)
        conversation = self.store.get("operator_chat", str(bot)) or {"entries": []}
        history = conversation["entries"][-6:]
        facts = [
            {
                "kind": "observed_episode",
                "candidate": row["candidate"],
                "status": row["status"],
                "metrics": row.get("metrics", {}),
            }
            for _, row in self.store.records("episode", 60)
            if row.get("bot") == bot and row.get("terminal")
        ][:3]
        conversation["entries"] = (
            conversation["entries"]
            + [{"speaker": "human", "text": text, "at": time.time()}]
        )[-30:]
        self.store.put("operator_chat", str(bot), conversation)
        self.controller.require_model_admission()
        try:
            proposal = await self.controller.model.converse(
                self.offers(snapshot),
                text,
                act,
                history + self.advice(bot) + facts,
                False,
            )
        except Exception as error:  # noqa: BLE001 - provider errors can contain credentials; report category only
            self.event(
                bot,
                "failure",
                f"Conversa indisponível ({type(error).__name__}); nenhuma ordem aplicada.",
            )
            raise ValueError(
                "A IA não respondeu agora; tente novamente. Nenhuma ordem foi aplicada."
            ) from None
        self.controller.require_model_admission()
        latest = self.snapshot(bot)
        applied = None
        valid = (
            latest.world == snapshot.world
            and latest.objective_generation == snapshot.objective_generation
            and self.revision.get(bot, 0) == revision
            and not self.managed(bot)
        )
        if act and proposal.candidate_id != "continue" and valid:
            self.interrupt(bot)
            applied = self.send(latest, proposal.candidate_id, "waiting_action")
        conversation = self.store.get("operator_chat", str(bot)) or conversation
        conversation["entries"] = (
            conversation["entries"]
            + [
                {
                    "speaker": "bot",
                    "text": proposal.reply,
                    "at": time.time(),
                    "candidate": proposal.candidate_id,
                    "action_id": applied,
                    "execution": "requested" if applied else "not_applied",
                    "observed_at": observed_at,
                }
            ]
        )[-30:]
        self.store.put("operator_chat", str(bot), conversation)
        return {
            "reply": proposal.reply,
            "action_id": applied,
            "status": "requested"
            if applied
            else "conversation_only"
            if not act
            else "not_applied",
        }
