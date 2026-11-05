"""One arbiter per companion; slow dialogue cannot block fresh tactical choices."""

import asyncio
import json
import time
import uuid
from collections import deque
from collections.abc import Callable
from functools import partial
from typing import Any, Protocol

from .benchmark_stops import Stops
from .learning import Policy, episode_reward
from .protocol import Message, Observation, Outcome, Telemetry, intent_for
from .provider import Proposal
from .recording import Recorder, attribution, request_context
from .store import BudgetExceeded, Store
from .supervision import Supervisor


class Model(Protocol):
    async def decide(
        self, observation: Observation, memory: dict[str, Any] | None = None
    ) -> str: ...
    async def converse(
        self,
        observation: Observation,
        text: str,
        authorized: bool,
        memory: list[dict[str, Any]] | None = None,
        deep: bool = False,
    ) -> Proposal: ...


class Controller:
    def __init__(
        self,
        store: Store,
        model: Model,
        send: Callable[[dict[str, Any]], None],
        mode: str = "shadow",
        roster: set[int] | None = None,
        learning: bool = False,
        exploration: float = 0.15,
        recorder: Recorder | None = None,
        memory_mode: str = "existing",
        observe_only: bool = False,
        require_benchmark_bridge: bool = False,
        benchmark_stops: Stops | None = None,
    ) -> None:
        if mode not in {"shadow", "active"}:
            raise ValueError("controller mode must be shadow or active")
        self.store, self.model, self.send, self.mode = store, model, send, mode
        self.roster = roster
        self.policy = Policy(store, epsilon=exploration)
        self.learning = learning
        self.recorder, self.memory_mode, self.observe_only = (
            recorder,
            memory_mode,
            observe_only,
        )
        self.require_benchmark_bridge = require_benchmark_bridge
        self.bridge_ready = not require_benchmark_bridge
        self.benchmark_stops = benchmark_stops
        self.latest: dict[int, Observation] = {}
        self.pending: dict[tuple[int, str], asyncio.Task[None]] = {}
        self.seen: deque[str] = deque(maxlen=512)
        self.last_decision: dict[int, tuple[float, str]] = {}
        self.leader_message: dict[int, str] = {}
        self.world = ""
        self.supervisor = Supervisor(self)

    def record(
        self, bot: int, kind: str, data: dict[str, Any], key: str | None = None
    ) -> None:
        if self.recorder:
            self.recorder.emit(bot, kind, data, key)
        if self.benchmark_stops and kind == "decision":
            self.benchmark_stops.decision(data, time.monotonic())

    @staticmethod
    def authority(snapshot: Observation) -> int:
        return snapshot.party.leader_id if snapshot.party else 0

    @staticmethod
    def authorized(snapshot: Observation, player: int) -> bool:
        return (
            snapshot.party.leader_id == player
            if snapshot.party
            else snapshot.autonomous
        )

    def _spawn(self, bot: int, kind: str, work: Callable[[], Any]) -> None:
        key = (bot, kind)
        if key in self.pending:
            return

        async def guarded() -> None:
            try:
                with attribution(bot):
                    await work()
            except Exception as error:  # noqa: BLE001 - isolate provider faults and redact their messages
                self.record(
                    bot,
                    "lifecycle",
                    {"phase": "native_fallback", "reason": type(error).__name__},
                )
                if isinstance(error, BudgetExceeded):
                    self.store.put("budget_stop", str(bot), {"at": time.time()})
                self.store.put(
                    "status",
                    str(bot),
                    {"fallback": type(error).__name__, "at": time.time()},
                )
            finally:
                if self.pending.get(key) is asyncio.current_task():
                    self.pending.pop(key, None)

        self.pending[key] = asyncio.create_task(guarded())

    async def handle(self, packet: dict[str, Any]) -> None:
        if packet.get("type") == "telemetry":
            telemetry = Telemetry.model_validate(packet)
            if self.benchmark_stops and (
                self.roster is None or telemetry.bot_id in self.roster
            ):
                self.benchmark_stops.observe(telemetry.model_dump(), time.monotonic())
            if self.recorder and (
                self.roster is None or telemetry.bot_id in self.roster
            ):
                self.recorder.native_event(
                    telemetry.bot_id,
                    telemetry.world,
                    telemetry.sequence,
                    telemetry.model_dump(
                        exclude={"version", "type", "world", "sequence", "bot_id"}
                    ),
                )
            return
        if packet.get("type") == "hello":
            world = packet.get("world")
            if (
                packet.get("version") == 1
                and isinstance(world, str)
                and 0 < len(world) <= 80
            ):
                if self.require_benchmark_bridge:
                    capabilities = packet.get("capabilities", {})
                    self.bridge_ready = (
                        capabilities.get("lifecycle_telemetry") == 1
                        and capabilities.get("keep_awake") is True
                    )
                    self.store.put("bridge", "benchmark", {"ready": self.bridge_ready})
                self._world(world)
            return
        if packet.get("type") == "outcome":
            outcome = Outcome.model_validate(packet)
            self.record(
                outcome.bot_id,
                "outcome",
                outcome.model_dump(),
                f"outcome:{outcome.world}:{outcome.action_id}:{outcome.status}",
            )
            self._outcome(outcome)
            return
        snapshot = Observation.model_validate(packet)
        if not self.bridge_ready:
            return
        bot = snapshot.bot.id
        if self.roster is not None and bot not in self.roster:
            return
        self._world(snapshot.world)
        previous_observation = self.latest.get(bot)
        if (
            self.benchmark_stops
            and previous_observation
            and previous_observation.world == snapshot.world
            and snapshot.sequence <= previous_observation.sequence
        ):
            return
        if len(self.latest) >= 3 and bot not in self.latest:
            return
        self.latest[bot] = snapshot
        if self.benchmark_stops:
            self.benchmark_stops.observe(snapshot.model_dump(), time.monotonic())
        if self.store.get("run_clock", "start") is None:
            self.store.put(
                "run_clock",
                "start",
                {"monotonic": time.monotonic(), "wall": time.time()},
            )
        if self.recorder:
            self.recorder.observe(snapshot)
        self.store.put(
            "status",
            str(bot),
            {
                "mode": self.mode,
                "name": snapshot.bot.name,
                "level": snapshot.bot.level,
                "state": snapshot.bot.state,
                "objective": snapshot.bot.objective,
                "last_observation": time.time(),
                "sequence": snapshot.sequence,
                "position": snapshot.bot.position,
                "potions": snapshot.bot.potions,
                "xp": snapshot.bot.xp,
                "objective_defeats": snapshot.bot.objective_defeats,
                "nearby": snapshot.nearby,
                "health": snapshot.bot.health,
                "leader": self.authority(snapshot) if snapshot.party else None,
                "party": snapshot.party.model_dump() if snapshot.party else None,
                "autonomous": snapshot.autonomous,
                "learning": self.learning or snapshot.autonomous,
                "eligible": [item.id for item in snapshot.actions],
            },
        )
        if self.observe_only:
            return
        self.supervisor.observe(snapshot)
        if (
            self.supervisor.managed(bot)
            and snapshot.autonomous
            and snapshot.party is None
        ):
            return
        for message in snapshot.messages:
            if self.authorized(snapshot, message.player_id):
                self.leader_message[bot] = message.id
            if message.id in self.seen or (bot, "dialogue") in self.pending:
                continue
            self.seen.append(message.id)
            self._spawn(bot, "dialogue", partial(self._dialogue, snapshot, message))
        if (
            snapshot.party is None and not snapshot.autonomous
        ) or not snapshot.bot.alive:
            return
        if (
            snapshot.autonomous
            and snapshot.party is None
            and not snapshot.bot.objective_running
            and len(snapshot.actions) > 1
            and self.memory_mode != "frozen"
        ):
            profile = self.store.get("profile", str(bot)) or {}
            if time.time() - profile.get("last_autonomous_plan", 0) >= 600:
                profile["last_autonomous_plan"] = time.time()
                self.store.put("profile", str(bot), profile)
                self._spawn(
                    bot, "strategy", partial(self._autonomous_strategy, snapshot)
                )
        plan = self.store.get("plan", str(bot))
        if (
            plan
            and plan.get("phase") == "ready"
            and (bot, "dialogue") not in self.pending
        ):
            if (
                plan["world"] != snapshot.world
                or plan["leader"] != self.authority(snapshot)
                or time.time() - plan["started"] > 7200
            ):
                self.store.delete("plan", str(bot))
            else:
                self._spawn(bot, "replan", partial(self._replan, snapshot, plan))
        fingerprint = json.dumps(
            [
                snapshot.world,
                self.authority(snapshot),
                snapshot.objective_generation,
                snapshot.bot.health // 25,
                snapshot.bot.potions < 10,
                [entity.get("id") for entity in snapshot.nearby],
                [item.id for item in snapshot.actions],
                snapshot.bot.objective_running,
            ]
        )
        previous_time, previous = self.last_decision.get(bot, (0, ""))
        interval = 0.5 if fingerprint != previous else 60.0
        if (
            time.monotonic() - previous_time >= interval
            and (bot, "decision") not in self.pending
        ):
            self.last_decision[bot] = (time.monotonic(), fingerprint)
            self._spawn(bot, "decision", lambda: self._decide(snapshot))

    @staticmethod
    def context(snapshot: Observation) -> str:
        size = len(snapshot.party.members) if snapshot.party else 1
        x, y, floor = snapshot.bot.position
        return f"v1:{snapshot.bot.level // 50}:{snapshot.bot.vocation}:{size}:{floor}:{x // 128}:{y // 128}"

    def _world(self, world: str) -> None:
        if world == self.world:
            return
        for task in self.pending.values():
            task.cancel()
        self.pending.clear()
        self.latest.clear()
        self.seen.clear()
        self.last_decision.clear()
        self.leader_message.clear()
        self.world = world
        self.send({"version": 1, "type": "heartbeat", "world": world})
        for action_id, pending in self.store.records("pending", 1000):
            intent = pending["intent"]
            if intent["world"] != world:
                self._outcome(
                    Outcome(
                        version=1,
                        type="outcome",
                        world=intent["world"],
                        action_id=action_id,
                        bot_id=intent["bot_id"],
                        status="cancelled",
                        reason="engine_changed",
                        metrics={},
                    )
                )

    def _apply(
        self,
        snapshot: Observation,
        candidate: str,
        selection: dict[str, Any] | None = None,
        tool_call: dict[str, Any] | None = None,
        *,
        operator: bool = False,
    ) -> str | None:
        self.record(
            snapshot.bot.id,
            "proposal",
            {
                "decision_id": request_context.get()[1],
                "candidate": candidate,
                "source": "operator" if operator else "controller",
                "selection": selection,
                "observation_sequence": snapshot.sequence,
                "world": snapshot.world,
            },
        )
        if candidate == "continue":
            return None
        if snapshot.autonomous and snapshot.party is None:
            if candidate in self.supervisor.blocked(snapshot.bot.id):
                return None
            if not operator and self.supervisor.managed(snapshot.bot.id):
                return None
        if len(self.store.records("pending", 25)) >= 24:
            return None
        intent = intent_for(snapshot, candidate, uuid.uuid4().hex)
        self.record(
            snapshot.bot.id,
            "intent",
            {
                **intent.model_dump(),
                "decision_id": request_context.get()[1],
                "mode": self.mode,
                "operator": operator,
            },
            "intent:" + intent.action_id,
        )
        episode = {
            "bot": snapshot.bot.id,
            "world": snapshot.world,
            "context": self.context(snapshot),
            "candidate": candidate,
            "selection": selection,
            "started": time.time(),
            "status": "proposed",
            "terminal": self.mode != "active" or snapshot.mode != "active",
            "tool_call": tool_call,
        }
        self.store.put("episode", intent.action_id, episode)
        if self.mode == "active" and snapshot.mode == "active":
            packet = intent.model_dump()
            self.store.put(
                "pending",
                intent.action_id,
                {
                    "intent": packet,
                    "attempts": 1,
                    "status": "proposed",
                    "at": time.monotonic(),
                },
            )
            self.send(packet)

        return intent.action_id

    def reconcile(self) -> None:
        """Recover lost datagrams using one stable identity, including after worker restart."""
        now = time.monotonic()
        for action_id, pending in self.store.records("pending", 1000):
            intent = pending["intent"]
            if intent["world"] != self.world:
                continue
            interval = 0.5 if pending["status"] == "proposed" else 5.0
            if 0 <= now - pending["at"] < interval:
                continue
            if (
                pending["status"] == "proposed"
                and pending["attempts"] < 3
                and now * 1000 < intent["expires_ms"]
            ):
                self.send(intent)
                pending["attempts"] += 1
            else:
                self.send(
                    {
                        "version": 1,
                        "type": "query",
                        "world": self.world,
                        "action_id": action_id,
                        "bot_id": intent["bot_id"],
                    }
                )
                pending["status"] = "querying"
            pending["at"] = now
            self.store.put("pending", action_id, pending)

    async def _decide(self, snapshot: Observation) -> None:
        snapshot = self.supervisor.offers(snapshot)
        # A repeated retreat resets the native floor planner. Let it finish;
        # explicit human requests can still supersede it through dialogue.
        if snapshot.bot.objective_running and snapshot.bot.objective == "retreat":
            return
        # Holding is useful only when requested; autonomous idle loops earn no work.
        snapshot = snapshot.model_copy(
            update={
                "actions": [item for item in snapshot.actions if item.action != "hold"]
            }
        )
        has_work = any(item.action in {"hunt", "resupply"} for item in snapshot.actions)
        if (
            snapshot.autonomous
            and snapshot.party is None
            and not snapshot.bot.objective_running
            and (has_work or any(item.action == "retreat" for item in snapshot.actions))
        ):
            snapshot = snapshot.model_copy(
                update={
                    "actions": [
                        item
                        for item in snapshot.actions
                        if item.action != "continue"
                        and not (
                            item.action == "retreat"
                            and has_work
                            and snapshot.bot.health >= 80
                            and not snapshot.nearby
                        )
                    ]
                }
            )
        context = self.context(snapshot)
        statistics = self.policy.statistics(snapshot.bot.id, context)
        eligible = {item.id for item in snapshot.actions}
        memory = {
            "operator_advice": self.supervisor.advice(snapshot.bot.id),
            "actions": {
                key: value for key, value in statistics.items() if key in eligible
            },
            "strategy_hypothesis": self.store.get(
                "autonomous_strategy", str(snapshot.bot.id)
            )
            if snapshot.autonomous
            else None,
        }
        if snapshot.bot.objective_running:
            actions = [
                item
                for item in snapshot.actions
                if item.action in {"continue", "target", "retreat"}
            ]
            snapshot = snapshot.model_copy(update={"actions": actions})
            if not snapshot.nearby and snapshot.bot.health >= 50:
                return
        guides = [
            item.bot.id
            for item in self.latest.values()
            if item.party
            and snapshot.party
            and item.party.leader_id == self.authority(snapshot)
        ]
        if guides and snapshot.bot.id != min(guides):
            snapshot = snapshot.model_copy(
                update={
                    "actions": [
                        item for item in snapshot.actions if item.action != "hunt"
                    ]
                }
            )
        self.record(
            snapshot.bot.id,
            "decision",
            {
                "decision_id": request_context.get()[1],
                "phase": "requested",
                "observation": snapshot.model_dump(exclude={"lease", "messages"}),
                "memory": memory,
            },
        )
        selected = await self.model.decide(snapshot, memory)
        proposed = selected
        self.record(
            snapshot.bot.id,
            "decision",
            {
                "decision_id": request_context.get()[1],
                "phase": "model_proposed",
                "candidate": proposed,
                "source": "single_candidate_rule"
                if len(snapshot.actions) == 1
                else "model",
            },
        )
        # Raw observations may still contain options removed from this request.
        if selected not in {item.id for item in snapshot.actions}:
            return
        latest = self.latest.get(snapshot.bot.id)
        if (
            latest is None
            or (latest.world, latest.lease, latest.objective_generation)
            != (snapshot.world, snapshot.lease, snapshot.objective_generation)
            or latest.bot.position[2] != snapshot.bot.position[2]
        ):
            return
        if selected not in {item.id for item in latest.actions}:
            return
        activity = self.store.get("activity_recent", str(snapshot.bot.id)) or {}
        if (
            selected in {"follow", "resupply"}
            and activity.get("candidate") == selected
            and time.time() - activity.get("at", 0) < 120
        ):
            return
        if any(
            (snapshot.bot.id, kind) in self.pending for kind in ("dialogue", "replan")
        ) and selected not in {
            item.id
            for item in snapshot.actions
            if item.action in {"target", "retreat", "continue"}
        }:
            return
        selection = None
        if (
            self.memory_mode != "frozen"
            and (self.learning or snapshot.autonomous)
            and selected.startswith("hunt:")
        ):
            alternatives = [
                item.id for item in snapshot.actions if item.action == "hunt"
            ]
            chosen = self.policy.choose(
                snapshot.bot.id, context, alternatives, selected
            )
            selected = chosen.candidate_id
            selection = {
                "probability": chosen.probability,
                "exploring": chosen.exploring,
                "version": chosen.policy_version,
                "offered": alternatives,
            }
        self.record(
            snapshot.bot.id,
            "decision",
            {
                "decision_id": request_context.get()[1],
                "phase": "selected",
                "proposed": proposed,
                "selected": selected,
                "selection": selection,
                "source": "policy"
                if proposed != selected
                else "single_candidate_rule"
                if len(snapshot.actions) == 1
                else "model",
            },
        )
        # The original tactical deadline remains authoritative despite newer observations.
        action_id = self._apply(snapshot, selected, selection)
        if action_id is not None:
            self.store.put(
                "activity_recent",
                str(snapshot.bot.id),
                {"candidate": selected, "at": time.time(), "action_id": action_id},
            )

    async def _autonomous_strategy(self, snapshot: Observation) -> None:
        snapshot = self.supervisor.offers(snapshot)
        facts = [
            {
                "candidate": value["candidate"],
                "status": value["status"],
                "metrics": value.get("metrics", {}),
            }
            for _, value in self.store.records("episode", 40)
            if value.get("bot") == snapshot.bot.id and value.get("terminal")
        ][:6]
        proposal = await self.model.converse(
            snapshot,
            "You are exploring alone. Propose a prudent varied objective from the offered candidates. "
            "Learn from observed outcomes; avoid repeating failed or monotonous activities. "
            "Restock when necessary, preserve your life and respect level limits. This is a strategy hypothesis, not execution.",
            True,
            facts + self.supervisor.advice(snapshot.bot.id),
            False,
        )
        latest = self.latest.get(snapshot.bot.id)
        if (
            latest is not None
            and latest.world == snapshot.world
            and latest.autonomous
            and latest.party is None
        ):
            self.store.put(
                "autonomous_strategy",
                str(snapshot.bot.id),
                {
                    "kind": "model_hypothesis",
                    "candidate": proposal.candidate_id,
                    "text": proposal.reply[:600],
                    "at": time.time(),
                },
            )

    async def _dialogue(self, snapshot: Observation, message: Message) -> None:
        snapshot = self.supervisor.offers(snapshot)
        bot = snapshot.bot.id
        authorized = self.authorized(snapshot, message.player_id)
        memory_key = f"{bot}:{message.player_id}"
        memory = self.store.get("memory", memory_key) or {}
        history = (
            memory.get("entries", [])[-6:]
            if time.time() - memory.get("at", 0) < 86400
            else []
        )
        profile = self.store.get("profile", str(bot)) or {}
        deep = authorized and any(
            word in message.text.lower()
            for word in (
                "estratég",
                "estrateg",
                "planej",
                "pense com calma",
                "effort max",
            )
        )
        deep = deep and time.time() - profile.get("last_max", 0) > 600
        if deep:
            profile["last_max"] = time.time()
            self.store.put("profile", str(bot), profile)
        facts = [
            {
                "kind": "observed_episode",
                "source": key,
                "candidate": data["candidate"],
                "status": data["status"],
                "metrics": data.get("metrics", {}),
            }
            for key, data in self.store.records("episode", 50)
            if data.get("bot") == bot and data.get("terminal")
        ][:3]
        hypotheses = [
            {"kind": "model_hypothesis", "source": key, "text": data["text"][:600]}
            for key, data in self.store.records("reflection", 20)
            if data.get("bot") == bot
        ][:2]
        try:
            proposal = await self.model.converse(
                snapshot,
                message.text,
                authorized,
                history + facts + hypotheses + self.supervisor.advice(bot),
                deep,
            )
        except Exception:
            if self.mode == "active" and snapshot.mode == "active":
                self.send(
                    {
                        "version": 1,
                        "type": "reply",
                        "world": snapshot.world,
                        "bot_id": bot,
                        "message_id": message.id,
                        "text": "Minha conversa está indisponível agora. Continuo com o comportamento nativo.",
                    }
                )
            raise
        latest = self.latest.get(bot)
        if latest is None or latest.world != snapshot.world:
            return
        if self.mode == "active" and latest.mode == "active":
            self.send(
                {
                    "version": 1,
                    "type": "reply",
                    "world": latest.world,
                    "bot_id": bot,
                    "message_id": message.id,
                    "text": proposal.reply,
                }
            )
        self.store.put(
            "memory",
            memory_key,
            {
                "at": time.time(),
                "entries": (
                    history
                    + [
                        {"speaker": "human", "text": message.text},
                        {"speaker": "bot", "text": proposal.reply},
                    ]
                )[-8:],
            },
        )
        if not authorized or not self.authorized(latest, message.player_id):
            return
        if latest.objective_generation != snapshot.objective_generation:
            return
        if self.leader_message.get(bot) != message.id:
            return
        if proposal.candidate_id in {item.id for item in latest.actions}:
            action_id = self._apply(
                latest, proposal.candidate_id, tool_call=proposal.tool_call
            )
            self.store.delete("plan", str(bot))
            if action_id and any(
                word in message.text.lower()
                for word in ("depois", "antes", "planej", "em seguida")
            ):
                self.store.put(
                    "plan",
                    str(bot),
                    {
                        "id": message.id,
                        "world": snapshot.world,
                        "leader": self.authority(snapshot),
                        "text": message.text,
                        "started": time.time(),
                        "remaining": 2,
                        "failures": 0,
                        "phase": "waiting",
                        "action_id": action_id,
                        "outcomes": [],
                    },
                )

    def _outcome(self, outcome: Outcome) -> None:
        with self.store.atomic():
            self._record_outcome(outcome)

    def _record_outcome(self, outcome: Outcome) -> None:
        episode = self.store.get("episode", outcome.action_id)
        if (
            episode is None
            or episode.get("world") != outcome.world
            or episode.get("bot") != outcome.bot_id
            or episode.get("terminal")
        ):
            return
        terminal = outcome.status not in {"accepted", "running"}
        episode.update(
            status=outcome.status,
            terminal=terminal,
            reason=outcome.reason,
            metrics=outcome.metrics,
        )
        reward = episode_reward(outcome.status, outcome.metrics, episode["candidate"])
        if (
            terminal
            and reward is not None
            and self.memory_mode != "frozen"
            and (
                str(episode["candidate"]).startswith("hunt:")
                or episode["candidate"] == "resupply"
            )
        ):
            self.policy.learn(
                outcome.bot_id, episode["context"], episode["candidate"], reward
            )
            episode["reward"] = reward
        self.store.put("episode", outcome.action_id, episode)
        self.supervisor.outcome(outcome)
        if terminal:
            if outcome.status in {"cancelled", "expired", "rejected"}:
                recent = self.store.get("activity_recent", str(outcome.bot_id)) or {}
                if recent.get("action_id") == outcome.action_id:
                    self.store.delete("activity_recent", str(outcome.bot_id))
            self.store.delete("pending", outcome.action_id)
            plan = self.store.get("plan", str(outcome.bot_id))
            if plan and plan["action_id"] == outcome.action_id:
                if (
                    outcome.status in {"cancelled", "expired", "rejected"}
                    or plan["remaining"] <= 0
                ):
                    self.store.put(
                        "plan_history",
                        plan["id"],
                        {**plan, "terminal": outcome.model_dump()},
                    )
                    self.store.delete("plan", str(outcome.bot_id))
                else:
                    plan["failures"] += int(outcome.status == "failed")
                    plan["outcomes"].append(outcome.model_dump())
                    plan["phase"] = "ready" if plan["failures"] < 2 else "stopped"
                    self.store.put("plan", str(outcome.bot_id), plan)
            if (
                self.memory_mode != "frozen"
                and episode.get("tool_call")
                and hasattr(self.model, "reflect")
            ):
                self._spawn(
                    outcome.bot_id,
                    "reflection",
                    partial(self._reflect, outcome, episode),
                )
        else:
            pending = self.store.get("pending", outcome.action_id)
            if pending:
                pending.update(status=outcome.status, at=time.monotonic())
                self.store.put("pending", outcome.action_id, pending)

    async def _reflect(self, outcome: Outcome, episode: dict[str, Any]) -> None:
        reflect = getattr(self.model, "reflect", None)
        if reflect is None:
            return
        text = await reflect(episode["tool_call"], outcome.model_dump())
        self.store.put(
            "reflection",
            outcome.action_id,
            {
                "kind": "model_hypothesis",
                "bot": outcome.bot_id,
                "source": outcome.action_id,
                "text": text,
                "at": time.time(),
            },
        )

    async def _replan(self, snapshot: Observation, plan: dict[str, Any]) -> None:
        snapshot = self.supervisor.offers(snapshot)
        # Reserve this plan round durably before a billable call. A stale answer or
        # provider failure must not leave a ready plan that is retried every tick.
        plan["phase"] = "planning"
        plan["attempts"] = plan.get("attempts", 0) + 1
        self.store.put("plan", str(snapshot.bot.id), plan)
        if plan["attempts"] > 3:
            plan["phase"] = "stopped"
            self.store.put("plan", str(snapshot.bot.id), plan)
            return
        proposal = await self.model.converse(
            snapshot,
            "Continue this bounded leader plan only if its next step is currently offered. "
            "Choose continue if finished or clarification/resources are needed. Never repeat a failed purchase without changed resources. "
            + json.dumps(
                {
                    "leader_request": plan["text"],
                    "authoritative_outcomes": plan["outcomes"],
                },
                ensure_ascii=False,
            ),
            True,
            [],
            False,
        )
        latest = self.latest.get(snapshot.bot.id)
        current = self.store.get("plan", str(snapshot.bot.id))
        if (
            latest is None
            or current is None
            or current["id"] != plan["id"]
            or self.leader_message.get(snapshot.bot.id) not in {None, plan["id"]}
            or latest.world != plan["world"]
            or self.authority(latest) != plan["leader"]
            or latest.objective_generation != snapshot.objective_generation
        ):
            return
        action_id = self._apply(
            latest, proposal.candidate_id, tool_call=proposal.tool_call
        )
        if action_id is None:
            self.store.put("plan_history", plan["id"], {**plan, "phase": "completed"})
            self.store.delete("plan", str(snapshot.bot.id))
        else:
            plan.update(
                action_id=action_id, remaining=plan["remaining"] - 1, phase="waiting"
            )
            self.store.put("plan", str(snapshot.bot.id), plan)

    async def drain(self) -> None:
        while self.pending:
            await asyncio.gather(*list(self.pending.values()), return_exceptions=True)

    async def close(self) -> None:
        for task in self.pending.values():
            task.cancel()
        await self.drain()
