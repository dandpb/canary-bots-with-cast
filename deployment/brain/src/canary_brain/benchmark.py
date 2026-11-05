"""Predeclared, isolated runs. Recorded alternatives never invent live outcomes."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .gateway import GatewayConfiguration
from .recording import (
    Manifest,
    RecordingConfiguration,
    RecordingStore,
    ReplayReader,
    attribution,
    canonical,
    digest,
    public_data,
)
from .replay import campaign
from .runtime import Configuration, run
from .store import USD, Store


class Participant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,47}$")
    kind: Literal["native", "litellm"]
    gateway: GatewayConfiguration | None = None

    @model_validator(mode="after")
    def configured(self) -> Participant:
        if (self.kind == "litellm") != (self.gateway is not None):
            raise ValueError("only a LiteLLM participant has a gateway model mapping")
        return self


class Experiment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,39}$")
    output: Path
    fixture: Path
    world_map: Path
    budget_file: Path
    gateway_credential: Path | None = None
    game_image: str = "canary-bots-wsl-game:local"
    bot_id: int = Field(gt=0)
    participants: list[Participant] = Field(min_length=1, max_length=8)
    seconds: int = Field(default=1800, ge=10, le=86400)
    repetitions: int = Field(default=3, ge=1, le=50)
    memory_mode: Literal["frozen", "independent"] = "frozen"
    run_cap_nanousd: int = Field(default=100_000_000, ge=1, le=50 * USD)
    campaign_cap_nanousd: int = Field(default=1_000_000_000, ge=1, le=50 * USD)
    seed: int = 42
    source_revision: str = Field(min_length=1, max_length=128)
    decision_timeout: float = Field(default=10, ge=0.1, le=30)
    expected_initial_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def distinct(self) -> Experiment:
        names = [p.name for p in self.participants]
        if len(names) != len(set(names)):
            raise ValueError("participant names must be distinct")
        return self


def file_hash(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def fixture_hash(fixture: Path, world_map: Path) -> str:
    if (
        fixture.is_symlink()
        or not fixture.is_dir()
        or not world_map.is_file()
        or world_map.is_symlink()
    ):
        raise ValueError("a local isolated fixture and world map are required")
    entries = {}
    for path in sorted(fixture.rglob("*")):
        if path.is_symlink():
            raise ValueError("fixture symlinks are not supported")
        if path.is_file():
            name = path.relative_to(fixture).as_posix()
            if any(s in name.lower() for s in ("secret", "credential", ".env")):
                raise ValueError("fixture must not contain credential files")
            entries[name] = file_hash(path)
    if "database.sql" not in entries or "character.json" not in entries:
        raise ValueError("fixture requires database.sql and character.json")
    return digest({"fixture": entries, "world_map": file_hash(world_map)})


def preflight(experiment: Experiment) -> dict[str, Any]:
    for path in (
        experiment.output,
        experiment.fixture,
        experiment.world_map,
        experiment.budget_file,
    ):
        if not path.is_absolute() or path.is_symlink():
            raise ValueError("experiment paths must be absolute and nonsymlink")
    for participant in experiment.participants:
        address = (
            experiment.output
            / f"{participant.name}-{experiment.repetitions - 1}"
            / "socket"
            / "worker.sock"
        )
        if len(str(address).encode()) >= 108:
            raise ValueError(
                "experiment output path is too long for a private Unix socket"
            )
    if (
        experiment.output.resolve() == experiment.fixture.resolve()
        or experiment.fixture.resolve().is_relative_to(experiment.output.resolve())
    ):
        raise ValueError("output must be separate from immutable fixtures")
    if experiment.budget_file.resolve().is_relative_to(experiment.output.resolve()):
        raise ValueError(
            "use the existing shared monthly ledger outside run directories"
        )
    initial = fixture_hash(experiment.fixture, experiment.world_map)
    if initial != experiment.expected_initial_sha256:
        raise ValueError("initial fixture hash changed")
    character = json.loads((experiment.fixture / "character.json").read_text())
    if (
        set(character) != {"id", "level", "experience", "posx", "posy", "posz"}
        or character["id"] != experiment.bot_id
        or any(type(v) is not int or v < 0 for v in character.values())
    ):
        raise ValueError(
            "character fixture must declare the exact initial saved progression and position"
        )
    if any(p.kind == "litellm" for p in experiment.participants):
        credential = experiment.gateway_credential
        if (
            credential is None
            or not credential.is_absolute()
            or credential.resolve().is_relative_to(experiment.output.resolve())
        ):
            raise ValueError(
                "a private gateway credential outside the artifacts is required"
            )
        from .runtime import read_credential

        read_credential(credential, "LITELLM_API_KEY")
    planned = len(experiment.participants) * experiment.repetitions
    liability = (
        sum(p.kind == "litellm" for p in experiment.participants)
        * experiment.repetitions
        * experiment.run_cap_nanousd
    )
    if liability > experiment.campaign_cap_nanousd:
        raise ValueError(
            "planned worst-case run caps exceed the declared campaign budget"
        )
    budget = Store(experiment.budget_file).budget()
    if (
        any(p.kind == "litellm" for p in experiment.participants)
        and liability > budget["available"]
    ):
        raise ValueError("campaign does not fit the existing shared monthly budget")
    return {
        "initial_sha256": initial,
        "runs": planned,
        "worst_case_nanousd": liability,
        "budget": budget,
        "character": character,
        "limitations": [
            "Live world RNG and scheduling are not deterministic.",
            "Initial world and character identity do not make later encounters identical.",
        ],
    }


class DockerFixture:
    """Owns only one newly created experiment project; never targets production."""

    def __init__(self, experiment: Experiment, directory: Path, identity: str) -> None:
        self.experiment, self.directory = experiment, directory
        self.project = "canary-bench-" + identity[:20]
        self.compose = directory / "compose.json"
        self.env_file = directory / "database.env"
        self.started = False

    def command(self, *arguments: str, timeout: int = 900) -> str:
        result = subprocess.run(
            [
                "docker",
                "compose",
                "--project-name",
                self.project,
                "--env-file",
                str(self.env_file),
                "--file",
                str(self.compose),
                *arguments,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode:
            details = result.stdout + "\n" + result.stderr
            if self.env_file.exists():
                for line in self.env_file.read_text().splitlines():
                    _name, separator, value = line.partition("=")
                    if separator and value:
                        details = details.replace(value, "[redacted]")
            log = self.directory / "command-errors.log"
            with log.open("a", encoding="utf-8") as target:
                os.chmod(log, 0o600)
                target.write(str(public_data(details)) + "\n")
            raise RuntimeError(
                "isolated Docker operation failed; inspect the private experiment deployment logs"
            )
        return result.stdout

    def prepare(self, participant: Participant) -> None:
        self.directory.mkdir(parents=True, exist_ok=False, mode=0o700)
        config = self.directory / "config"
        config.mkdir(mode=0o700)
        socket_dir = self.directory / "socket"
        socket_dir.mkdir(mode=0o700)
        seed = self.directory / "initdb"
        seed.mkdir(mode=0o700)
        shutil.copyfile(
            self.experiment.fixture / "database.sql", seed / "01-fixture.sql"
        )
        os.chmod(seed / "01-fixture.sql", 0o600)
        data = self.directory / "database"
        data.mkdir(mode=0o700)
        server = {
            "mode": "shadow" if participant.kind == "native" else "active",
            "bots": [self.experiment.bot_id],
            "autonomous_bot": self.experiment.bot_id,
            "keep_awake": True,
            "socket_directory": str(socket_dir),
        }
        (config / "server.json").write_text(canonical(server))
        self.env_file.write_text(
            "MARIADB_PASSWORD="
            + secrets.token_hex(24)
            + "\nMARIADB_ROOT_PASSWORD="
            + secrets.token_hex(24)
            + "\n"
        )
        os.chmod(self.env_file, 0o600)
        game: dict[str, Any] = {
            "image": self.experiment.game_image,
            "environment": {
                "MARIADB_PASSWORD": "${MARIADB_PASSWORD}",
                "GAME_PUBLIC_IP": "127.0.0.1",
                "BOT_PLAYERS_ONLINE": "1",
                "CANARY_BRAIN_CONFIG": "/etc/canary-brain/server.json",
            },
            "depends_on": {"database": {"condition": "service_healthy"}},
            "volumes": [
                f"{config}:/etc/canary-brain:ro",
                f"{socket_dir}:{socket_dir}",
                f"{self.experiment.world_map}:/canary/data-otservbr-global/world/otservbr.otbm:ro",
            ],
            "healthcheck": {
                "test": [
                    "CMD",
                    "python3",
                    "-c",
                    "import socket;socket.create_connection(('127.0.0.1',7173),2).close()",
                ],
                "interval": "2s",
                "timeout": "3s",
                "retries": 180,
                "start_period": "10s",
            },
        }
        if (self.experiment.fixture / "authored").is_dir():
            authored = self.directory / "authored"
            shutil.copytree(self.experiment.fixture / "authored", authored)
            game["volumes"].append(f"{authored}:/canary/data/bot/authored")
        services = {
            "database": {
                "image": "mariadb:11.4",
                "environment": {
                    "MARIADB_DATABASE": "canary",
                    "MARIADB_USER": "canary",
                    "MARIADB_PASSWORD": "${MARIADB_PASSWORD}",
                    "MARIADB_ROOT_PASSWORD": "${MARIADB_ROOT_PASSWORD}",
                },
                "volumes": [
                    f"{data}:/var/lib/mysql",
                    f"{seed}:/docker-entrypoint-initdb.d:ro",
                ],
                "healthcheck": {
                    "test": [
                        "CMD",
                        "healthcheck.sh",
                        "--connect",
                        "--innodb_initialized",
                    ],
                    "interval": "2s",
                    "timeout": "5s",
                    "retries": 90,
                },
            },
            "game": game,
        }
        # No host game/database ports; a dedicated project network and bind directories.
        self.compose.write_text(canonical({"services": services}))

    def character(self) -> dict[str, int]:
        query = f"SELECT id,level,experience,posx,posy,posz FROM players WHERE id={self.experiment.bot_id};"
        result = self.command(
            "exec",
            "-T",
            "database",
            "sh",
            "-c",
            'MYSQL_PWD="$MARIADB_PASSWORD" mariadb -u canary canary -N -e "$1"',
            "sh",
            query,
            timeout=20,
        )
        values = result.strip().split("\t")
        if len(values) != 6:
            raise ValueError("isolated character is missing")
        return dict(
            zip(
                ("id", "level", "experience", "posx", "posy", "posz"),
                map(int, values),
                strict=True,
            )
        )

    def start_database(self) -> None:
        self.started = True
        self.command("up", "-d", "--wait", "database")

    def start_game(self) -> None:
        self.command("up", "-d", "--wait", "game")

    def stop_game(self) -> None:
        self.command("stop", "--timeout", "180", "game", timeout=210)

    def close(self) -> None:
        if self.started:
            # Only this newly generated project. Keep its bind data for evidence.
            self.command("down", "--timeout", "180", timeout=240)


async def run_campaign(experiment: Experiment, *, live: bool = False) -> dict[str, Any]:
    if not live:
        raise ValueError("live game/provider execution requires --live")
    check = preflight(experiment)
    experiment.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    plan_file = experiment.output / "experiment.json"
    public_plan = experiment.model_dump(
        mode="json", exclude={"gateway_credential", "budget_file"}
    )
    fingerprint = digest(experiment.model_dump(mode="json"))
    if (
        plan_file.exists()
        and json.loads(plan_file.read_text())["configuration_sha256"] != fingerprint
    ):
        raise ValueError("an existing campaign has a different configuration")
    plan_file.write_text(
        canonical(
            {
                "configuration_sha256": fingerprint,
                "plan": public_plan,
                "preflight": check,
            }
        )
    )
    recording = experiment.output / "recording.sqlite3"
    identities = []
    for repetition in range(experiment.repetitions):
        # Rotate execution order to avoid tying a provider to one wall-clock slot.
        participants = (
            experiment.participants[repetition % len(experiment.participants) :]
            + experiment.participants[: repetition % len(experiment.participants)]
        )
        for participant in participants:
            identity = f"{experiment.name}:{participant.name}:{repetition}"
            identities.append(identity)
            if recording.exists():
                try:
                    existing = ReplayReader(recording).run(identity)
                except ValueError:
                    existing = None
                if existing:
                    # Never restart a completed attempt, or silently turn an interrupted one into a new trial.
                    if existing["status"] == "running":
                        RecordingStore(recording).finish(identity, "interrupted")
                    continue
            manifest = Manifest(
                run_id=identity,
                bot_id=experiment.bot_id,
                lineage=f"{experiment.name}:{repetition}",
                experiment=experiment.name,
                scenario="autonomous-progression",
                participant=participant.name,
                model=participant.gateway.effective_model
                if participant.gateway
                else "none",
                provider=participant.gateway.provider
                if participant.gateway
                else "native",
                memory_mode=experiment.memory_mode,
                initial_sha256=check["initial_sha256"],
                configuration_sha256=fingerprint,
                source_revision=experiment.source_revision,
            )
            store = RecordingStore(recording)
            store.begin(
                manifest
            )  # Durable attempt exists before any game/provider action.
            directory = experiment.output / (participant.name + f"-{repetition}")
            harness = DockerFixture(
                experiment, directory, hashlib.sha256(identity.encode()).hexdigest()
            )
            worker: asyncio.Task[None] | None = None
            stopped = asyncio.Event()
            status = "failed"
            try:
                await asyncio.to_thread(harness.prepare, participant)
                await asyncio.to_thread(harness.start_database)
                initial = await asyncio.to_thread(harness.character)
                if initial != check["character"]:
                    raise ValueError(
                        "restored character differs from the declared initial fixture"
                    )
                state = directory / "worker.sqlite3"
                seed_file = experiment.fixture / "worker-state.json"
                if seed_file.exists():
                    seed = json.loads(seed_file.read_text())
                    seeded = Store(state)
                    for row in seed:
                        if row["kind"] not in {
                            "policy",
                            "recent",
                            "guidance",
                            "autonomous_strategy",
                        }:
                            raise ValueError(
                                "only declared learning records may seed an experiment"
                            )
                        seeded.put(row["kind"], row["key"], row["data"])
                configuration = Configuration(
                    provider=participant.kind,
                    mode="shadow" if participant.kind == "native" else "active",
                    socket_directory=directory / "socket",
                    state_file=state,
                    budget_file=experiment.budget_file,
                    credential_file=experiment.gateway_credential,
                    bots=[experiment.bot_id],
                    gateway=participant.gateway,
                    memory_mode=experiment.memory_mode,
                    policy_seed=experiment.seed + repetition,
                    run_cap_nanousd=experiment.run_cap_nanousd,
                    run_seconds=experiment.seconds,
                    decision_timeout=experiment.decision_timeout
                    if participant.kind == "litellm"
                    else 1.2,
                    recording=RecordingConfiguration(
                        path=recording, namespace=experiment.name, manifests=[manifest]
                    ),
                )
                worker = asyncio.create_task(run(configuration, stopped))
                ready_until = time.monotonic() + 10
                while not (directory / "socket" / "worker.sock").exists():
                    if worker.done():
                        await worker
                        raise RuntimeError(
                            "worker stopped before creating its private socket"
                        )
                    if time.monotonic() > ready_until:
                        raise TimeoutError("experiment worker did not become ready")
                    await asyncio.sleep(0.02)
                await asyncio.to_thread(harness.start_game)
                deadline = time.monotonic() + experiment.seconds
                started = time.monotonic()
                while time.monotonic() < deadline:
                    if worker.done():
                        await worker
                        clock = Store(state).get("run_clock", "start")
                        if (
                            clock
                            and time.monotonic() - clock["monotonic"]
                            >= experiment.seconds
                        ):
                            status = "completed"
                            break
                        raise RuntimeError(
                            "experiment worker ended before the run horizon"
                        )
                    await asyncio.sleep(min(1, max(0.01, deadline - time.monotonic())))
                    state_rows = Store(state).get("budget_stop", str(experiment.bot_id))
                    if state_rows:
                        status = "budget_stop"
                        break
                    observed = Store(state).get("status", str(experiment.bot_id)) or {}
                    if (
                        time.monotonic() - started > min(15, experiment.seconds / 2)
                        and time.time() - observed.get("last_observation", 0) > 5
                    ):
                        raise ValueError(
                            "experiment bot observations are missing or stale"
                        )
                    bridge = Store(state).get("bridge", "benchmark")
                    if bridge is not None and not bridge["ready"]:
                        raise ValueError(
                            "game image lacks benchmark lifecycle/awake capabilities"
                        )
                if status != "budget_stop":
                    status = "completed"
                stopped.set()
                await worker
                worker = None
                await asyncio.to_thread(harness.stop_game)
                saved = await asyncio.to_thread(harness.character)
                (directory / "saved-character.json").write_text(canonical(saved))
            except BaseException as error:
                status = (
                    "interrupted"
                    if isinstance(error, (KeyboardInterrupt, asyncio.CancelledError))
                    else "failed"
                )
                end = ReplayReader(recording).run(identity)["duration_ms"]
                store.append(
                    {
                        "run": identity,
                        "key": "orchestrator-failure",
                        "segment": "orchestrator",
                        "t_ms": end + 1,
                        "wall": time.time(),
                        "kind": "lifecycle",
                        "data": {
                            "phase": "run_failed",
                            "category": type(error).__name__,
                            "classification": "infrastructure_or_operator_interruption",
                        },
                    }
                )
                raise
            finally:
                stopped.set()
                try:
                    if worker:
                        await asyncio.gather(worker, return_exceptions=True)
                    store.finish(identity, status)
                finally:
                    await asyncio.to_thread(harness.close)
    result = campaign(ReplayReader(recording), identities)
    (experiment.output / "summary.json").write_text(canonical(result))
    return result


def demo(path: Path) -> list[str]:
    """Explicitly synthetic viewer fixture; no provider, no Docker, no game progress."""
    store = RecordingStore(path)
    runs = []
    for index, name in enumerate(("native-fixture", "model-fixture")):
        run_id = "demo:" + name
        runs.append(run_id)
        manifest = Manifest(
            run_id=run_id,
            bot_id=7,
            lineage="demo:7",
            provider="fake",
            model=name,
            participant=name,
            scenario="synthetic-viewer-fixture",
            memory_mode="frozen",
            initial_sha256="0" * 64,
            synthetic=True,
            sample_ms=10000,
        )
        store.begin(manifest)
        for step in range(61):
            t = step * 10000
            payload: dict[str, Any] = {
                "world": "synthetic",
                "bot": {
                    "id": 7,
                    "name": "Bot de demonstração",
                    "level": 8 + int(step >= 35 - index * 5),
                    "vocation": 4,
                    "state": "HUNTING",
                    "position": [
                        32340 + step // 2,
                        32220 + (step % 20),
                        7 + int(15 < step < 40),
                    ],
                    "health": 100 - step % 15,
                    "mana": 80,
                    "potions": 40 - step // 8,
                    "xp": 4200 + step * (70 + index * 20),
                    "objective": "hunt" if step < 45 else "resupply",
                    "alive": True,
                },
            }
            base = {
                "run": run_id,
                "key": f"sample:{step}",
                "segment": "demo",
                "t_ms": t,
                "wall": 1_800_000_000 + t / 1000,
            }
            store.append({**base, "kind": "sample", "data": payload})
            if step == 35 - index * 5:
                store.append(
                    {
                        **base,
                        "key": "level",
                        "kind": "level",
                        "data": {"from": 8, "to": 9, "xp": payload["bot"]["xp"]},
                    }
                )
            if step in (10, 45):
                store.append(
                    {
                        **base,
                        "key": f"decision:{step}",
                        "kind": "decision",
                        "data": {
                            "decision_id": f"d{step}",
                            "phase": "selected",
                            "proposed": "hunt:a",
                            "selected": "hunt:a",
                            "source": "synthetic-fixture",
                        },
                    }
                )
        store.append(
            {
                "run": run_id,
                "key": "native",
                "segment": "demo",
                "t_ms": 600000,
                "wall": 1_800_000_600,
                "kind": "lifecycle",
                "data": {"world": "synthetic", "deaths": 0, "phase": "alive"},
            }
        )
        store.finish(run_id, "completed")
    return runs


async def evaluate_decisions(
    provider: Any, fixtures: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    from .protocol import Observation

    rows = []
    for fixture in fixtures:
        snapshot = Observation.model_validate(fixture["observation"])
        started = time.monotonic()
        try:
            with attribution(snapshot.bot.id) as decision:
                recorder = getattr(provider, "recorder", None)
                if recorder:
                    recorder.emit(
                        snapshot.bot.id,
                        "decision",
                        {
                            "decision_id": decision,
                            "phase": "requested",
                            "observation": snapshot.model_dump(
                                exclude={"lease", "messages"}
                            ),
                            "memory": fixture.get("memory", {}),
                        },
                    )
                choice = await provider.decide(snapshot, fixture.get("memory", {}))
                if recorder:
                    recorder.emit(
                        snapshot.bot.id,
                        "decision",
                        {
                            "decision_id": decision,
                            "phase": "model_proposed",
                            "candidate": choice,
                        },
                    )
            valid = choice in {action.id for action in snapshot.actions}
            row = {
                "choice": choice,
                "valid": valid,
                "expected": fixture.get("expected"),
                "matches_expected": choice == fixture["expected"]
                if "expected" in fixture
                else None,
            }
        except Exception as error:  # noqa: BLE001 - provider exceptions may contain credentials
            row = {"valid": False, "error": type(error).__name__}
        rows.append(
            {
                **row,
                "bot_id": snapshot.bot.id,
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "scope": "decision_only_no_counterfactual_xp_or_survival",
            }
        )
    return rows
