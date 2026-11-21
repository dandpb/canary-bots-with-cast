"""Predeclared, isolated runs. Recorded alternatives never invent live outcomes."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import sqlite3
import stat
import subprocess
import tempfile
import time
from collections.abc import Callable, Coroutine, Iterator
from contextlib import contextmanager
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
from .sqlite_files import failure_metadata
from .store import USD, Store


class Participant(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,47}$")
    kind: Literal["native", "fake", "litellm"]
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
    database_image: str = "mariadb:11.4"
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
        for image in (experiment.game_image, experiment.database_image):
            if re.fullmatch(r"(?:sha256:|[^@\s]+@sha256:)[a-f0-9]{64}", image) is None:
                raise ValueError(
                    "scored provider campaigns require immutable image IDs for game and database"
                )
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
    remaining = liability
    recording = experiment.output / "recording.sqlite3"
    if recording.exists():
        fingerprint = digest(experiment.model_dump(mode="json"))
        with ReplayReader(recording).snapshot() as reader:
            for repetition in range(experiment.repetitions):
                for participant in experiment.participants:
                    identity = f"{experiment.name}:{participant.name}:{repetition}"
                    try:
                        prior = reader.run(identity)
                    except ValueError:
                        continue
                    if prior["manifest"]["configuration_sha256"] != fingerprint:
                        raise ValueError(
                            "recorded attempt has a different experiment configuration"
                        )
                    if participant.kind == "litellm":
                        remaining -= experiment.run_cap_nanousd
    if (
        any(p.kind == "litellm" for p in experiment.participants)
        and remaining > budget["available"]
    ):
        raise ValueError("campaign does not fit the existing shared monthly budget")
    return {
        "initial_sha256": initial,
        "runs": planned,
        "worst_case_nanousd": liability,
        "remaining_nanousd": remaining,
        "budget": budget,
        "character": character,
        "limitations": [
            "Live world RNG and scheduling are not deterministic.",
            "Initial world and character identity do not make later encounters identical.",
        ],
    }


class ComposeOwnershipInvalid(ValueError):
    code = "compose_ownership_invalid"

    def __init__(self) -> None:
        super().__init__(self.code)


class LegacyCleanupRequired(ValueError):
    code = "legacy_cleanup_required"

    def __init__(self) -> None:
        super().__init__(self.code)


COMPOSE_PROJECT_LABEL = "com.docker.compose.project"
BENCHMARK_OWNER_LABEL = "org.canary.benchmark.owner"


def _sync_directory(directory: Path) -> None:
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _publish_text(path: Path, value: str) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
            temporary.replace(path)
            _sync_directory(path.parent)
        finally:
            temporary.unlink(missing_ok=True)


class DockerFixture:
    """Owns only one newly created experiment project; never targets production."""

    def __init__(self, experiment: Experiment, directory: Path, identity: str) -> None:
        self.experiment, self.directory = experiment, directory
        self.run_id = identity
        self.owner_file = directory / "compose-ownership.json"
        self.project = ""
        self.compose = directory / "compose.json"
        self.env_file = directory / "database.env"
        self.started = False
        self.stop_requested = False

    def ownership_record(self, owner_id: str) -> dict[str, Any]:
        return {
            "version": 1,
            "run_id": self.run_id,
            "project_name": "canary-bench-" + owner_id,
            "owner_id": owner_id,
            "output_path_sha256": hashlib.sha256(
                os.fsencode(self.experiment.output.resolve())
            ).hexdigest(),
        }

    def create_ownership(self) -> dict[str, Any]:
        record = self.ownership_record(secrets.token_hex(16))
        temporary = self.owner_file.with_suffix(".tmp")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(canonical(record))
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(self.owner_file)
        _sync_directory(self.directory)
        self.project = record["project_name"]
        return record

    def read_ownership(self) -> dict[str, Any]:
        try:
            if self.directory.is_symlink():
                raise ComposeOwnershipInvalid()
            fd = os.open(self.owner_file, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, "r", encoding="utf-8") as stream:
                decoded: object = json.loads(stream.read(4097))
                if not isinstance(decoded, dict):
                    raise ComposeOwnershipInvalid()
                record: dict[str, Any] = decoded
                mode = os.fstat(stream.fileno()).st_mode
                if not stat.S_ISREG(mode) or mode & 0o077:
                    raise ComposeOwnershipInvalid()
            owner_id = record["owner_id"]
            if (
                type(record["version"]) is not int
                or not re.fullmatch(r"[a-f0-9]{32}", owner_id)
                or record != self.ownership_record(owner_id)
            ):
                raise ComposeOwnershipInvalid()
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            raise ComposeOwnershipInvalid() from error
        if self.project and self.project != record["project_name"]:
            raise ComposeOwnershipInvalid()
        self.project = record["project_name"]
        return record

    @staticmethod
    def docker_metadata(*arguments: str) -> str:
        try:
            result = subprocess.run(
                ("docker", *arguments),
                cwd="/",
                capture_output=True,
                text=True,
                timeout=20,
                check=True,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise ComposeOwnershipInvalid() from error
        return result.stdout.strip()

    def _docker_resources(self, owner: str) -> Iterator[tuple[str, str]]:
        for resource in ("container", "network", "volume"):
            listing = [resource, "ls", "-q"]
            if resource == "container":
                listing.append("-a")
            ids = set()
            for label, value in (
                (COMPOSE_PROJECT_LABEL, self.project),
                (BENCHMARK_OWNER_LABEL, owner),
            ):
                ids.update(
                    self.docker_metadata(
                        *listing, "--filter", f"label={label}={value}"
                    ).split()
                )
            if resource == "network":
                ids.update(
                    self.docker_metadata(
                        *listing, "--filter", "name=" + self.project + "_default"
                    ).split()
                )
            for resource_id in sorted(ids):
                yield resource, resource_id

    def validate_docker_ownership(self) -> None:
        owner = self.read_ownership()["owner_id"]
        if self.compose.is_symlink() or self.env_file.is_symlink():
            raise ComposeOwnershipInvalid()
        required = {COMPOSE_PROJECT_LABEL: self.project, BENCHMARK_OWNER_LABEL: owner}
        if self.compose.is_file():
            try:
                compose = json.loads(self.compose.read_text())
                services = compose["services"]
                networks = compose["networks"]
                if (
                    set(services) != {"database", "game"}
                    or set(networks) != {"default"}
                    or compose.get("name", self.project) != self.project
                    or compose.get("volumes")
                    or networks["default"].get("external")
                    or networks["default"].get("name", self.project + "_default")
                    != self.project + "_default"
                    or any(
                        spec["labels"].get(BENCHMARK_OWNER_LABEL) != owner
                        for spec in [*services.values(), networks["default"]]
                    )
                ):
                    raise ComposeOwnershipInvalid()
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
                raise ComposeOwnershipInvalid() from error
        for resource, resource_id in self._docker_resources(owner):
            label_field = ".Config.Labels" if resource == "container" else ".Labels"
            try:
                labels = json.loads(
                    self.docker_metadata(
                        resource,
                        "inspect",
                        "--format",
                        "{{json " + label_field + "}}",
                        resource_id,
                    )
                )
            except ValueError as error:
                raise ComposeOwnershipInvalid() from error
            if not isinstance(labels, dict) or any(
                labels.get(k) != v for k, v in required.items()
            ):
                raise ComposeOwnershipInvalid()

    def command(self, *arguments: str, timeout: int = 900) -> str:
        if arguments[0] in {
            "up",
            "create",
            "start",
            "down",
            "stop",
            "kill",
            "exec",
            "logs",
            "wait",
        }:
            self.validate_docker_ownership()
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
            # A long-lived checkout cwd can outlive a detached WSL/DrvFS mount.
            cwd="/",
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode:
            self.diagnostics("command-errors.log", result.stdout + "\n" + result.stderr)
            raise RuntimeError(
                "isolated Docker operation failed; inspect the private experiment deployment logs"
            )
        return result.stdout

    def diagnostics(self, name: str, details: str) -> None:
        if self.env_file.exists():
            for line in self.env_file.read_text().splitlines():
                _name, separator, value = line.partition("=")
                if separator and value:
                    details = details.replace(value, "[redacted]")
        log = self.directory / name
        with log.open("a", encoding="utf-8") as target:
            os.chmod(log, 0o600)
            target.write(str(public_data(details)) + "\n")

    def prepare(self, participant: Participant) -> None:
        self.directory.mkdir(parents=True, exist_ok=False, mode=0o700)
        owner = self.create_ownership()["owner_id"]
        config = self.directory / "config"
        config.mkdir(mode=0o700)
        socket_dir = self.directory / "socket"
        socket_dir.mkdir(mode=0o700)
        seed = self.directory / "initdb"
        seed.mkdir(mode=0o755)
        os.chmod(seed, 0o755)
        shutil.copyfile(
            self.experiment.fixture / "database.sql", seed / "01-fixture.sql"
        )
        # The host attempt directory stays 0700. Only its read-only seed subtree
        # is mounted into MariaDB, whose mysql UID differs from the host worker.
        os.chmod(seed / "01-fixture.sql", 0o644)
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
        _publish_text(
            self.env_file,
            "MARIADB_PASSWORD="
            + secrets.token_hex(24)
            + "\nMARIADB_ROOT_PASSWORD="
            + secrets.token_hex(24)
            + "\n",
        )
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
                "image": self.experiment.database_image,
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
        labels = {BENCHMARK_OWNER_LABEL: owner}
        for service in services.values():
            service["labels"] = labels
        self.write_compose(
            {
                "services": services,
                "networks": {"default": {"labels": labels}},
            }
        )

    def write_compose(self, definition: dict[str, Any]) -> None:
        _publish_text(self.compose, canonical(definition))

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
        self.stop_requested = True
        if self.game_running():
            # Compose stop escalates to SIGKILL. A wait timeout only ends this
            # client and leaves the closed server available for explicit retry.
            self.command("kill", "-s", "SIGTERM", "game", timeout=20)
        self.command("wait", "game", timeout=210)

    def game_running(self) -> bool:
        return bool(
            self.command(
                "ps", "--status", "running", "--quiet", "game", timeout=20
            ).strip()
        )

    def close(self) -> None:
        if self.started:
            # Only this newly generated project. Keep its bind data for evidence.
            try:
                try:
                    logs = self.command(
                        "logs",
                        "--no-color",
                        "--timestamps",
                        "--tail",
                        "2000",
                        timeout=30,
                    )
                    self.diagnostics("services.log", logs)
                except (RuntimeError, subprocess.TimeoutExpired, OSError) as error:
                    try:
                        self.diagnostics(
                            "services.log",
                            "Service log capture unavailable: " + type(error).__name__,
                        )
                    except OSError:
                        pass  # Cleanup still runs if the evidence disk cannot accept writes.
            finally:
                if self.game_running():
                    if self.stop_requested:
                        raise RuntimeError(
                            "final save pending; the game and database are still available"
                        )
                    self.stop_game()
                self.command(
                    "down", "--remove-orphans", "--timeout", "180", timeout=240
                )

    def recover(
        self, *, ownership_expected: bool = False, allow_unprepared: bool = False
    ) -> None:
        if not self.owner_file.exists() and not self.owner_file.is_symlink():
            if ownership_expected:
                # Preparation creates only the directory and receipt temp file before ownership.
                if allow_unprepared and not self.directory.is_symlink():
                    try:
                        entries = {entry.name for entry in self.directory.iterdir()}
                    except FileNotFoundError:
                        entries = set()
                    except OSError as error:
                        raise ComposeOwnershipInvalid() from error
                    if entries <= {self.owner_file.with_suffix(".tmp").name}:
                        return
                raise ComposeOwnershipInvalid()
            if self.compose.is_file() and self.env_file.is_file():
                try:
                    compose = json.loads(self.compose.read_text())
                    labels = (
                        compose.get("networks", {}).get("default", {}).get("labels", {})
                    )
                except (OSError, ValueError, AttributeError) as error:
                    raise ComposeOwnershipInvalid() from error
                if BENCHMARK_OWNER_LABEL in labels:
                    raise ComposeOwnershipInvalid()
                raise LegacyCleanupRequired()
            return
        owner = self.read_ownership()["owner_id"]
        if self.compose.is_symlink() or self.env_file.is_symlink():
            raise ComposeOwnershipInvalid()
        inputs_complete = self.compose.is_file() and self.env_file.is_file()
        if inputs_complete and allow_unprepared:
            try:
                json.loads(self.compose.read_text())
            except (json.JSONDecodeError, UnicodeDecodeError):
                inputs_complete = False
            except OSError as error:
                raise ComposeOwnershipInvalid() from error
        if inputs_complete:
            self.started = True
            self.close()
        elif (
            not allow_unprepared
            or next(self._docker_resources(owner), None) is not None
        ):
            raise ComposeOwnershipInvalid()


async def settle_teardown(
    future: asyncio.Future[Any],
) -> tuple[BaseException | None, asyncio.CancelledError | None]:
    """Wait for owned cleanup to finish even if its caller is cancelled."""
    cancellation: asyncio.CancelledError | None = None
    while not future.done():
        try:
            await asyncio.shield(future)
        except asyncio.CancelledError as error:
            current = asyncio.current_task()
            if not future.done() or (current is not None and current.cancelling()):
                cancellation = cancellation or error
        except BaseException:  # noqa: BLE001
            break  # Read the completed future's own error below.
    try:
        future.result()
    except BaseException as error:  # noqa: BLE001
        return error, cancellation
    return None, cancellation


FixtureFactory = Callable[[Experiment, Path, str], DockerFixture]
WorkerRunner = Callable[[Configuration, asyncio.Event], Coroutine[Any, Any, None]]


async def run_campaign(
    experiment: Experiment,
    *,
    live: bool = False,
    fixture_factory: FixtureFactory | None = None,
    worker_runner: WorkerRunner | None = None,
) -> dict[str, Any]:
    if not live:
        raise ValueError("live game/provider execution requires --live")
    with campaign_lease(experiment.output), campaign_signals() as operator_stop:
        return await _run_campaign(
            experiment,
            operator_stop,
            fixture_factory=DockerFixture
            if fixture_factory is None
            else fixture_factory,
            worker_runner=run if worker_runner is None else worker_runner,
        )


@contextmanager
def campaign_signals() -> Iterator[asyncio.Event]:
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}

    def interrupt(_signum: int, _frame: Any) -> None:
        # Mark synchronously before a provisioning await can resume and create
        # a provider worker. Wake the selector even if no timer is pending.
        stopped.set()
        loop.call_soon_threadsafe(stopped.set)

    installed: list[signal.Signals] = []
    loop_handlers = getattr(loop, "_signal_handlers", {})
    try:
        for sig in previous:
            # An existing loop handler already keeps the wakeup FD active.
            # Preserve it; only remove handlers this context installs.
            if sig not in loop_handlers:
                loop.add_signal_handler(sig, stopped.set)
                installed.append(sig)
            signal.signal(sig, interrupt)
        yield stopped
    finally:
        for sig in installed:
            loop.remove_signal_handler(sig)
        for sig, handler in previous.items():
            signal.signal(sig, handler)


@contextmanager
def campaign_lease(output: Path) -> Iterator[None]:
    # A live worker uses Unix sockets. The kernel releases this lease on a crash;
    # another orchestrator must never mistake a live attempt for an orphan.
    if os.name != "posix":
        raise ValueError("live campaigns require Linux/WSL")
    import fcntl

    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(
        output / "runner.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
    )
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("another campaign orchestrator is running") from error
        yield
    finally:
        os.close(descriptor)


async def _run_campaign(
    experiment: Experiment,
    operator_stop: asyncio.Event,
    *,
    fixture_factory: FixtureFactory,
    worker_runner: WorkerRunner,
) -> dict[str, Any]:
    check = preflight(experiment)
    experiment.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    plan_file = experiment.output / "experiment.json"
    public_plan = experiment.model_dump(
        mode="json", exclude={"gateway_credential", "budget_file"}
    )
    fingerprint = digest(experiment.model_dump(mode="json"))
    if plan_file.exists():
        previous_plan = json.loads(plan_file.read_text())
        if previous_plan["configuration_sha256"] != fingerprint:
            raise ValueError("an existing campaign has a different configuration")
        ownership_expected = previous_plan.get("compose_ownership_version") == 1
    else:
        ownership_expected = not (experiment.output / "recording.sqlite3").exists()
    _publish_text(
        plan_file,
        canonical(
            {
                "configuration_sha256": fingerprint,
                "plan": public_plan,
                "preflight": check,
                **({"compose_ownership_version": 1} if ownership_expected else {}),
            }
        ),
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
            if operator_stop.is_set():
                raise asyncio.CancelledError("campaign stopped by operator")
            identity = await _run_attempt(
                experiment,
                participant,
                repetition,
                operator_stop,
                fixture_check=check,
                configuration_sha256=fingerprint,
                ownership_expected=ownership_expected,
                fixture_factory=fixture_factory,
                worker_runner=worker_runner,
            )
            identities.append(identity)
    result = campaign(ReplayReader(recording), identities)
    (experiment.output / "summary.json").write_text(canonical(result))
    return result


async def _run_attempt(
    experiment: Experiment,
    participant: Participant,
    repetition: int,
    operator_stop: asyncio.Event,
    *,
    fixture_check: dict[str, Any],
    configuration_sha256: str,
    ownership_expected: bool,
    fixture_factory: FixtureFactory,
    worker_runner: WorkerRunner,
) -> str:
    """Run a new attempt or reconcile an existing one before advancing the campaign."""
    identity = f"{experiment.name}:{participant.name}:{repetition}"
    directory = experiment.output / f"{participant.name}-{repetition}"
    recording = experiment.output / "recording.sqlite3"
    existing = None
    if recording.exists():
        try:
            existing = ReplayReader(recording).run(identity)
        except ValueError:
            pass
    if existing:
        harness = fixture_factory(experiment, directory, identity)
        # An unfinished cleanup blocks subsequent trials, including on resume.
        await asyncio.to_thread(
            harness.recover,
            ownership_expected=ownership_expected,
            allow_unprepared=existing["status"] in {"running", "interrupted", "failed"},
        )
        if existing["status"] == "running":
            RecordingStore(recording).finish(identity, "interrupted")
        return identity

    manifest = Manifest(
        run_id=identity,
        bot_id=experiment.bot_id,
        lineage=f"{experiment.name}:{repetition}",
        experiment=experiment.name,
        scenario="autonomous-progression",
        participant=participant.name,
        model=participant.gateway.effective_model if participant.gateway else "none",
        provider=participant.gateway.provider
        if participant.gateway
        else participant.kind,
        memory_mode=experiment.memory_mode,
        initial_sha256=fixture_check["initial_sha256"],
        configuration_sha256=configuration_sha256,
        source_revision=experiment.source_revision,
    )
    store = RecordingStore(recording)
    # Durable attempt exists before any game/provider action.
    store.begin(manifest)
    harness = fixture_factory(experiment, directory, identity)
    worker: asyncio.Task[None] | None = None
    stopped = asyncio.Event()

    async def forward_operator_stop(
        stop_event: asyncio.Event = stopped,
    ) -> None:
        await operator_stop.wait()
        stop_event.set()

    stop_relay = asyncio.create_task(forward_operator_stop())
    status = "failed"
    failure: BaseException | None = None
    try:
        await asyncio.to_thread(harness.prepare, participant)
        if operator_stop.is_set():
            raise asyncio.CancelledError("campaign stopped by operator")
        await asyncio.to_thread(harness.start_database)
        if operator_stop.is_set():
            raise asyncio.CancelledError("campaign stopped by operator")
        initial = await asyncio.to_thread(harness.character)
        if operator_stop.is_set():
            raise asyncio.CancelledError("campaign stopped by operator")
        if initial != fixture_check["character"]:
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
            benchmark_supervision=True,
            native_source_revision=experiment.source_revision,
            decision_timeout=experiment.decision_timeout
            if participant.kind == "litellm"
            else 1.2,
            recording=RecordingConfiguration(
                path=recording, namespace=experiment.name, manifests=[manifest]
            ),
        )
        worker = asyncio.create_task(worker_runner(configuration, stopped))
        ready_until = time.monotonic() + 10
        while not (directory / "socket" / "worker.sock").exists():
            if operator_stop.is_set():
                raise asyncio.CancelledError("campaign stopped by operator")
            if worker.done():
                await worker
                raise RuntimeError("worker stopped before creating its private socket")
            if time.monotonic() > ready_until:
                raise TimeoutError("experiment worker did not become ready")
            await asyncio.sleep(0.02)
        if operator_stop.is_set():
            raise asyncio.CancelledError("campaign stopped by operator")
        await asyncio.to_thread(harness.start_game)
        started = time.monotonic()
        while True:
            if operator_stop.is_set():
                raise asyncio.CancelledError("campaign stopped by operator")
            if worker.done():
                await worker
                break
            await asyncio.sleep(1)
            state_rows = Store(state).get("budget_stop", str(experiment.bot_id))
            if state_rows:
                status = "budget_stop"
                break
            clock = Store(state).get("run_clock", "start")
            if time.monotonic() - started > 240 and clock is None:
                raise ValueError("experiment bot observations are missing or stale")
            if (
                clock
                and time.monotonic() - clock["monotonic"] > experiment.seconds + 30
            ):
                raise TimeoutError("worker did not stop at its observed horizon")
            bridge = Store(state).get("bridge", "benchmark")
            if bridge is not None and not bridge["ready"]:
                raise ValueError(
                    "game image lacks benchmark lifecycle/awake capabilities"
                )
        stopped.set()
        await worker
        worker = None
        if operator_stop.is_set():
            raise asyncio.CancelledError("campaign stopped by operator")
        # The worker has drained its recorder and provider tasks. Only now
        # classify the final durable evidence and financial marker.
        if ReplayReader(recording).run(identity)["incomplete"]:
            raise RuntimeError("campaign stopped: recording_gap")
        ending = Store(state).get("run_stop", "end")
        if ending is None:
            raise RuntimeError("experiment worker ended without a supervised stop")
        reason = ending["reason"]
        if reason == "operator_stop" and not Store(state).get(
            "budget_stop", str(experiment.bot_id)
        ):
            raise asyncio.CancelledError("campaign stopped by operator")
        if reason not in {
            "completed",
            "deaths_limit",
            "stalled",
            "proposal_timeout",
            "budget_stop",
            "operator_stop",
        }:
            raise RuntimeError("campaign stopped: " + reason)
        if (
            Store(state).get("budget_stop", str(experiment.bot_id))
            or reason == "budget_stop"
        ):
            status = "budget_stop"
        elif reason == "completed":
            clock = Store(state).get("run_clock", "start")
            samples = [
                e["t_ms"]
                for e in ReplayReader(recording).all_events(identity)
                if e["kind"] == "sample"
            ]
            if (
                not clock
                or time.monotonic() - clock["monotonic"] < experiment.seconds
                or ending.get("elapsed_seconds", 0) < experiment.seconds
                or ending.get("observed_seconds", 0) < experiment.seconds
                or len(samples) < 2
                or max(samples) - min(samples) < experiment.seconds * 1000
            ):
                raise RuntimeError("worker completed before the observed horizon")
            status = "completed"
        else:
            status = "failed"
        await asyncio.to_thread(harness.stop_game)
        saved = await asyncio.to_thread(harness.character)
        (directory / "saved-character.json").write_text(canonical(saved))
    except BaseException as error:
        failure = error
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
        stop_relay.cancel()
        tasks = [stop_relay]
        if worker:
            tasks.append(worker)
        drain = asyncio.gather(*tasks, return_exceptions=True)
        teardown_failure, cancellation = await settle_teardown(drain)
        if teardown_failure is not None:
            if failure is None:
                failure = teardown_failure
                status = (
                    "interrupted"
                    if isinstance(
                        teardown_failure,
                        (KeyboardInterrupt, asyncio.CancelledError),
                    )
                    else "failed"
                )
            else:
                failure.add_note(
                    "Worker teardown also failed: " + type(teardown_failure).__name__
                )
        close_task = asyncio.create_task(asyncio.to_thread(harness.close))
        cleanup_error, close_cancellation = await settle_teardown(close_task)
        cancellation = cancellation or close_cancellation
        current = asyncio.current_task()
        if (
            cancellation is None
            and not isinstance(failure, asyncio.CancelledError)
            and current is not None
            and current.cancelling()
        ):
            cancellation = asyncio.CancelledError("campaign cancelled during teardown")
        if cancellation is not None:
            status = "interrupted"
        if cleanup_error is not None:
            if failure is None and cancellation is None:
                status = "failed"
            else:
                target = failure or cancellation
                assert target is not None
                target.add_note(
                    "Isolated Docker cleanup also failed: "
                    + type(cleanup_error).__name__
                )
            try:
                end = ReplayReader(recording).run(identity)["duration_ms"]
                store.append(
                    {
                        "run": identity,
                        "key": "cleanup-unverified",
                        "segment": "orchestrator",
                        "t_ms": end + 1,
                        "wall": time.time(),
                        "kind": "gap",
                        "data": {
                            "reason": "cleanup_unverified",
                            "category": type(cleanup_error).__name__,
                        },
                    }
                )
            except Exception as recording_error:  # noqa: BLE001
                # Evidence IO must not replace the original failure.
                target = failure or cancellation or cleanup_error
                target.add_note(
                    "Could not record cleanup failure: "
                    + type(recording_error).__name__
                )
        store.finish(identity, status)
        if cancellation is not None:
            if failure is not None:
                raise cancellation from failure
            raise cancellation
        if teardown_failure is not None and failure is teardown_failure:
            raise teardown_failure
        if cleanup_error is not None and failure is None:
            raise cleanup_error
    return identity


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
            if isinstance(error, sqlite3.Error):
                row["sqlite_failure"] = failure_metadata(error, "decision_fixture")
        rows.append(
            {
                **row,
                "bot_id": snapshot.bot.id,
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "scope": "decision_only_no_counterfactual_xp_or_survival",
            }
        )
    return rows
