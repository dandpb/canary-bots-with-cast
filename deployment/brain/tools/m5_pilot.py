"""Admitted M5 execution through the canonical decision/campaign runners.

Preflight performs only file reads, SQL reads and inspection of this container.
The executor never copies the monthly ledger or retries an attempt.
"""

from __future__ import annotations

import argparse
import asyncio
import fcntl
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import socket
import sqlite3
import subprocess
import tempfile
import threading
import time
from _thread import LockType
from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field

from canary_brain import benchmark, runtime
from canary_brain.protocol import Observation
from canary_brain.recording import ReplayReader, digest, public_data
from canary_brain.replay_cli import decision_fixtures
from canary_brain.sqlite_files import failure_metadata, sqlite_operation
from canary_brain.store import USD, Store, month_now

GATES = {
    "fixture_30m_native_fake_current_runner",
    "same_candidate_schema_and_application_validation",
    "routing_immutable_before_upstream",
    "current_gateway_ids_hash_and_prices_revalidated",
    "conformance_input_provenance_frozen",
    "same_canonical_ledger_available_at_least_12usd",
}
CANONICAL_VOLUME = "canary-bots-wsl_brain-state"
CANONICAL_LEDGER_FILE = Path("/var/lib/canary-brain/state.sqlite3")
SHORT_DEADLINE_POLICY = "short_deadline_performance_v1"
SHORT_DEADLINE_TOTAL_CAP = 6_980_214_600
RECOVERY_POLICY = "short_deadline_performance_recovery_v2"
PERFORMANCE_POLICIES = frozenset({SHORT_DEADLINE_POLICY, RECOVERY_POLICY})
RECOVERY_PREVIOUS_NAMESPACE = "m5-og-20261106-dae4b84b"
RECOVERY_PRIOR_RUNS = frozenset(
    {
        "decisions:e9b235a5fcd24566b020fc332cd44e0d:65001",
        "decisions:3f5394354a1a43ef8072c99256c4cbb3:65001",
    }
)
RECOVERY_HISTORICAL = {
    "8e32e915ca5e4407a3ec55ab501bd99a": 52_800,
    "57f0becd17ab47a2ad3638987ca2f6ef": 161_800,
}
RECOVERY_CLAIM_KIND = "m5_recovery_v2"
RECOVERY_CLAIM_KEY = "single_use"


class ProbeTimingError(ValueError):
    """A purported positive response lacks timing evidence within its deadline."""


# Request only these fields. Full inspect and Config.Env can contain credentials.
CONTAINER_METADATA = (
    '{"id":{{json .Id}},"image":{{json .Image}},'
    '"project":{{json (index .Config.Labels "com.docker.compose.project")}},'
    '"service":{{json (index .Config.Labels "com.docker.compose.service")}},'
    '"oneoff":{{json (index .Config.Labels "com.docker.compose.oneoff")}},'
    '"state":{{json .State.Status}},'
    '"port_bindings":{{json .HostConfig.PortBindings}},'
    '"ports":{{json .NetworkSettings.Ports}},'
    '"network_mode":{{json .HostConfig.NetworkMode}},'
    '"networks":{{json .NetworkSettings.Networks}},"mounts":{{json .Mounts}}}'
)
NETWORK_METADATA = (
    '{"id":{{json .Id}},"name":{{json .Name}},"internal":{{json .Internal}},'
    '"scope":{{json .Scope}},"driver":{{json .Driver}},'
    '"project":{{json (index .Labels "com.docker.compose.project")}},'
    '"containers":{{json .Containers}}}'
)


def docker_metadata(*arguments: str) -> str:
    return subprocess.check_output(
        ["docker", *arguments], text=True, cwd="/", timeout=20
    )


def project_ids(project: str, kind: str) -> list[str]:
    if re.fullmatch(r"canary-bench-[a-f0-9]{20}", project) is None:
        raise ValueError("attestation requires an exact owned trial project")
    arguments = (
        ["container", "ls", "--all", "--quiet", "--no-trunc"]
        if kind == "container"
        else ["network", "ls", "--quiet", "--no-trunc"]
    )
    values = docker_metadata(
        *arguments, "--filter", "label=com.docker.compose.project=" + project
    ).split()
    if any(re.fullmatch(r"[a-f0-9]{64}", value) is None for value in values):
        raise ValueError("Docker returned an invalid resource identity")
    return values


def resource_metadata(identity: str, kind: str) -> dict[str, Any]:
    raw = json.loads(
        docker_metadata(
            kind,
            "inspect",
            "--format",
            CONTAINER_METADATA if kind == "container" else NETWORK_METADATA,
            identity,
        )
    )
    if raw.get("id") != identity:
        raise ValueError("Docker inspect returned a different resource identity")
    # Rebuild the public record as well: unexpected mock/runtime fields cannot
    # enter evidence through a nested object or a future Docker field addition.
    common = {key: raw.get(key) for key in ("id", "project")}
    if kind == "network":
        return {
            **common,
            **{key: raw.get(key) for key in ("name", "internal", "scope", "driver")},
            "container_ids": sorted((raw.get("containers") or {}).keys()),
        }
    return {
        **common,
        **{
            key: raw.get(key)
            for key in ("image", "service", "oneoff", "state", "network_mode")
        },
        "host_ports": any((raw.get("port_bindings") or {}).values())
        or any((raw.get("ports") or {}).values()),
        "networks": {
            name: value.get("NetworkID")
            for name, value in (raw.get("networks") or {}).items()
        },
        "mounts": [
            {key: mount.get(key) for key in ("Type", "Source", "Destination", "RW")}
            for mount in raw.get("mounts", [])
        ],
    }


def image_content_id(reference: str) -> str:
    """Resolve a pinned manifest to the local config ID used by containers."""
    if re.fullmatch(r"sha256:[a-f0-9]{64}", reference):
        return reference
    if re.fullmatch(r"[^@\s]+@sha256:[a-f0-9]{64}", reference) is None:
        raise ValueError("trial image reference is not immutable")
    identity = docker_metadata(
        "image", "inspect", "--format", "{{.Id}}", reference
    ).strip()
    if re.fullmatch(r"sha256:[a-f0-9]{64}", identity) is None:
        raise ValueError("Docker returned an invalid image content identity")
    return identity


def replace_evidence(path: Path, data: Any) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as target:
            os.fchmod(target.fileno(), 0o600)
            json.dump(data, target, indent=2)
            target.write("\n")
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


class TrialAttestation:
    """Observed image/scope/cleanup evidence for one canonical trial only."""

    def __init__(self, fixture: Any, aggregate: dict[str, Any], lock: LockType) -> None:
        self.fixture, self.aggregate, self.lock = fixture, aggregate, lock
        experiment = fixture.experiment
        runs = {
            experiment.output / f"{participant.name}-{repetition}": (
                f"{experiment.name}:{participant.name}:{repetition}"
            )
            for participant in experiment.participants
            for repetition in range(experiment.repetitions)
        }
        self.run_id = runs[fixture.directory]
        expected = (
            "canary-bench-" + hashlib.sha256(self.run_id.encode()).hexdigest()[:20]
        )
        if fixture.project != expected:
            raise ValueError("trial project does not match its run identity")
        self.data: dict[str, Any] = {
            "run_id": self.run_id,
            "project": fixture.project,
            "images_verified": False,
            "resources_cleaned": False,
            "failures": [],
        }

    def persist(self) -> None:
        with self.lock:
            self.aggregate[self.run_id] = self.data
            # prepare can fail before creating the attempt directory. The
            # aggregate still records its failure and cleanup result.
            if self.fixture.directory.is_dir():
                replace_evidence(
                    self.fixture.directory / "trial-attestation.json", self.data
                )
            replace_evidence(
                self.fixture.experiment.output / "trial-attestations.json",
                {"trials": self.aggregate},
            )

    def failure(self, phase: str, error: BaseException) -> None:
        self.data["failures"].append(
            {"phase": phase, "error_type": type(error).__name__}
        )
        self.persist()

    def resources(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        return (
            [
                resource_metadata(identity, "container")
                for identity in project_ids(self.fixture.project, "container")
            ],
            [
                resource_metadata(identity, "network")
                for identity in project_ids(self.fixture.project, "network")
            ],
        )

    def verify_images(self, *, running: bool) -> None:
        try:
            before = self.data.get("containers")
            containers, networks = self.resources()
            self.data.update({"containers": containers, "networks": networks})
            project = self.fixture.project
            if len(containers) != 2 or {row["service"] for row in containers} != {
                "game",
                "database",
            }:
                raise ValueError("trial must contain exactly its game and database")
            if len(networks) != 1:
                raise ValueError("trial must have exactly one isolated network")
            network = networks[0]
            if (
                network["project"] != project
                or network["name"] != project + "_default"
                or network["internal"] is not True
                or network["scope"] != "local"
                or network["driver"] != "bridge"
                or not set(network["container_ids"])
                <= {row["id"] for row in containers}
                or not {row["id"] for row in containers if row["state"] == "running"}
                <= set(network["container_ids"])
            ):
                raise ValueError("trial network is not exclusively owned and internal")
            for row in containers:
                service = row["service"]
                if (
                    row["project"] != project
                    or row["oneoff"] != "False"
                    or row["host_ports"]
                ):
                    raise ValueError("trial container scope or host ports differ")
                reference = getattr(self.fixture.experiment, service + "_image")
                if row["image"] != image_content_id(reference):
                    raise ValueError("trial image differs from the admitted image")
                if row["state"] != (
                    "running" if running or service == "database" else "created"
                ):
                    raise ValueError("trial container has an unexpected state")
                if row["network_mode"] != network["name"] or set(row["networks"]) != {
                    network["name"]
                }:
                    raise ValueError("trial container network scope differs")
                joined = row["networks"][network["name"]]
                if (
                    row["state"] == "running" and joined != network["id"]
                ) or joined not in {None, "", network["id"]}:
                    raise ValueError("trial container joined a different network")
                directory = self.fixture.directory
                bindings = (
                    [
                        (directory / "database", "/var/lib/mysql", True),
                        (directory / "initdb", "/docker-entrypoint-initdb.d", False),
                    ]
                    if service == "database"
                    else [
                        (directory / "config", "/etc/canary-brain", False),
                        (directory / "socket", str(directory / "socket"), True),
                        (
                            self.fixture.experiment.world_map,
                            "/canary/data-otservbr-global/world/otservbr.otbm",
                            False,
                        ),
                        (directory, "/m5", True),
                    ]
                )
                if service == "game" and (directory / "authored").is_dir():
                    bindings.append(
                        (directory / "authored", "/canary/data/bot/authored", True)
                    )
                expected = [
                    {
                        "Type": "bind",
                        "Source": str(source),
                        "Destination": destination,
                        "RW": writable,
                    }
                    for source, destination, writable in bindings
                ]
                if sorted(
                    row["mounts"], key=lambda item: str(item["Destination"])
                ) != sorted(expected, key=lambda item: str(item["Destination"])):
                    raise ValueError(
                        "trial essential mounts differ from the owned fixture"
                    )
            if before and {row["id"] for row in before} != {
                row["id"] for row in containers
            }:
                raise ValueError(
                    "trial containers changed after the pre-start attestation"
                )
            self.data.update(
                {
                    "containers": containers,
                    "networks": networks,
                    "images_verified": True,
                    "verified_before_game_start": True,
                    # The reporter compares the admitted immutable references;
                    # containers above retain the observed config IDs.
                    "game_image": self.fixture.experiment.game_image,
                    "database_image": self.fixture.experiment.database_image,
                }
            )
            self.persist()
        except BaseException as error:
            self.data["images_verified"] = False
            self.failure("running_images" if running else "pre_start_images", error)
            raise

    def cleanup(self, close_error: BaseException | None) -> None:
        self.data["resources_cleaned"] = False
        if close_error:
            self.data["failures"].append(
                {"phase": "canonical_close", "error_type": type(close_error).__name__}
            )
        try:
            containers, networks = self.resources()
            self.data["remaining_containers"], self.data["remaining_networks"] = (
                containers,
                networks,
            )
            self.data["resources_cleaned"] = (
                close_error is None and not containers and not networks
            )
            self.persist()
            if not self.data["resources_cleaned"]:
                raise RuntimeError("trial cleanup could not be verified")
        except BaseException as error:
            self.failure("cleanup_verification", error)
            raise


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    output: Path
    campaign: Path
    admission: Path
    authorization: Path
    source_manifest: Path
    decision_fixtures: Path
    probe_workers: dict[str, Path]
    worker_image: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    canonical_ledger_file: Path = CANONICAL_LEDGER_FILE
    canonical_volume: str = CANONICAL_VOLUME


def input_paths(plan: Plan) -> dict[str, Path]:
    return {
        "campaign": plan.campaign,
        "admission": plan.admission,
        "authorization": plan.authorization,
        "source_manifest": plan.source_manifest,
        "decision_fixtures": plan.decision_fixtures,
        **plan.probe_workers,
    }


def read_json(path: Path) -> Any:
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError("inputs must be existing absolute nonsymlink files")
    return json.loads(path.read_text())


def capture_inputs(plan: Plan) -> dict[str, bytes]:
    captured = {}
    for name, path in input_paths(plan).items():
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            raise ValueError("inputs must be existing absolute nonsymlink files")
        captured[name] = path.read_bytes()
    return captured


def input_hashes(captured: dict[str, bytes]) -> dict[str, str]:
    return {name: hashlib.sha256(value).hexdigest() for name, value in captured.items()}


@dataclass(frozen=True)
class ImmutableJSON:
    """Canonical CLI reads these admitted bytes instead of reopening paths."""

    payload: bytes

    def read_text(self) -> str:
        return self.payload.decode("utf-8")

    def stat(self) -> SimpleNamespace:
        return SimpleNamespace(st_size=len(self.payload))


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def owned_output(path: Path, root: Path) -> bool:
    return (
        path.is_absolute()
        and not path.is_symlink()
        and path.resolve().is_relative_to(root.resolve())
        and path.resolve() != root.resolve()
    )


def source_files(manifest: dict[str, Any]) -> dict[str, str]:
    source = Path(manifest["source_path"])
    if not source.is_absolute() or source.is_symlink():
        raise ValueError("source export must be an absolute nonsymlink directory")
    files: dict[str, str] = manifest["files"]
    required = {
        "benchmark.py",
        "runtime.py",
        "provider.py",
        "gateway.py",
        "store.py",
        "recording.py",
        "replay_cli.py",
    }
    if (
        not required <= {Path(name).name for name in files}
        or "deployment/brain/tools/m5_pilot.py" not in files
    ):
        raise ValueError("source manifest omits executable pilot sources")
    if not {
        path.relative_to(source).as_posix()
        for path in (source / "deployment/brain/src").rglob("*.py")
    } <= set(files):
        raise ValueError("source manifest omits Python modules present in the export")
    for name, expected in files.items():
        relative = Path(name)
        path = source / relative
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or path.is_symlink()
            or not path.is_file()
            or file_hash(path) != expected
        ):
            raise ValueError("frozen source bytes do not match their manifest")
    return files


def assert_frozen_imports(manifest: dict[str, Any]) -> None:
    source = Path(manifest["source_path"]).resolve()
    if Path(__file__).resolve() != source / "deployment/brain/tools/m5_pilot.py":
        raise ValueError("execute the wrapper from the frozen source export")
    for module in (benchmark, runtime):
        if module.__file__ is None:
            raise ValueError("canonical runner module has no source file")
        if (
            not Path(module.__file__)
            .resolve()
            .is_relative_to(source / "deployment/brain/src")
        ):
            raise ValueError(
                "canonical runner imports must use the frozen source export"
            )


def container_identity() -> tuple[str, list[dict[str, Any]]]:
    name = socket.gethostname()
    mounts = json.loads(
        subprocess.check_output(
            ["docker", "inspect", "--format", "{{json .Mounts}}", name],
            cwd="/",
            text=True,
            timeout=20,
        )
    )
    image = subprocess.check_output(
        ["docker", "inspect", "--format", "{{.Image}}", name],
        cwd="/",
        text=True,
        timeout=20,
    ).strip()
    return image, mounts


def ledger_snapshot(
    path: Path,
    historical: list[dict[str, Any]],
    additional_runs: list[str],
    namespace: str,
    *,
    require_additional_runs: bool = False,
) -> dict[str, int]:
    if not path.is_file() or path.is_symlink():
        raise ValueError("the canonical ledger must already exist")
    with (
        sqlite_operation("m5.ledger_snapshot"),
        closing(
            sqlite3.connect("file:" + quote(str(path), safe="/") + "?mode=ro", uri=True)
        ) as db,
        db,
    ):
        db.execute("BEGIN")
        return _ledger_snapshot_in_transaction(
            db, historical, additional_runs, namespace, require_additional_runs
        )


def _ledger_snapshot_in_transaction(
    db: sqlite3.Connection,
    historical: list[dict[str, Any]],
    additional_runs: list[str],
    namespace: str,
    require_additional_runs: bool,
) -> dict[str, int]:
    """Check the complete envelope against one established SQL transaction."""
    if (
        require_additional_runs
        and db.execute(
            "SELECT 1 FROM records WHERE kind=? AND key=?",
            (RECOVERY_CLAIM_KIND, RECOVERY_CLAIM_KEY),
        ).fetchone()
        is not None
    ):
        raise ValueError("recovery has already been claimed")
    spent, reserved = db.execute(
        "SELECT COALESCE(SUM(CASE WHEN month=? THEN spent ELSE 0 END),0),COALESCE(SUM(CASE WHEN spent IS NULL THEN reserved ELSE 0 END),0) FROM requests",
        (month_now(),),
    ).fetchone()
    if db.execute(
        "SELECT COUNT(*) FROM requests WHERE run_id LIKE ?", (namespace + ":%",)
    ).fetchone()[0]:
        raise ValueError("campaign identity already has charged or reserved attempts")
    for request in historical:
        row = db.execute(
            "SELECT spent FROM requests WHERE id=?", (request["id"],)
        ).fetchone()
        if row is None or row[0] != request["spent_nanousd"]:
            raise ValueError(
                "historical envelope charges do not match the canonical ledger"
            )
    extra_liability = 0
    if require_additional_runs and not additional_runs:
        raise ValueError("required prior runs are missing")
    if additional_runs:
        clause = (
            " FROM requests WHERE run_id IN ("
            + ",".join("?" for _ in additional_runs)
            + ")"
        )
        parameters = list(additional_runs)
        if historical:
            clause += " AND id NOT IN (" + ",".join("?" for _ in historical) + ")"
            parameters.extend(row["id"] for row in historical)
        if require_additional_runs:
            rows = db.execute(
                "SELECT run_id,reserved,spent" + clause, parameters
            ).fetchall()
            if {row[0] for row in rows} != set(additional_runs):
                raise ValueError(
                    "required prior run is missing from the canonical ledger"
                )
            if any(
                type(reserved) is not int
                or reserved <= 0
                or (spent is not None and (type(spent) is not int or spent < 0))
                for _, reserved, spent in rows
            ):
                raise ValueError("invalid prior money amount in the canonical ledger")
        query = "SELECT COALESCE(SUM(COALESCE(spent,reserved)),0)" + clause
        extra_liability = db.execute(query, parameters).fetchone()[0]
    return {
        "cap": 50 * USD,
        "spent": spent,
        "reserved": reserved,
        "available": max(0, 50 * USD - spent - reserved),
        "prior_extra_liability": extra_liability,
    }


def ledger_export(
    plan: Plan,
    additional_runs: list[str] | None = None,
    captured: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    """Export only pilot rows, with a global balance from one SQL snapshot."""
    data = {
        name: json.loads(value)
        for name, value in (
            captured if captured is not None else capture_inputs(plan)
        ).items()
    }
    experiment = benchmark.Experiment.model_validate(data["campaign"])
    envelope = data["authorization"]
    ids = [row["id"] for row in envelope.get("historical_requests", [])]
    runs = {str(value) for value in envelope.get("additional_cost_run_ids", [])}
    runs.update(additional_runs or [])
    for name in plan.probe_workers:
        config = runtime.Configuration.model_validate(data[name])
        if config.recording is not None and config.recording.path.is_file():
            with sqlite_operation("m5.ledger_export.probe_recording"):
                runs.update(
                    row["id"] for row in ReplayReader(config.recording.path).runs()
                )
    game_recording = experiment.output / "recording.sqlite3"
    if game_recording.is_file():
        with sqlite_operation("m5.ledger_export.game_recording"):
            runs.update(row["id"] for row in ReplayReader(game_recording).runs())
    month = month_now()
    query = "SELECT id,month,run_id,reserved,spent,created FROM requests WHERE run_id LIKE ?"
    parameters: list[Any] = [experiment.name + ":%"]
    for column, values in (("id", ids), ("run_id", sorted(runs))):
        if values:
            query += f" OR {column} IN ({','.join('?' for _ in values)})"
            parameters.extend(values)
    with (
        sqlite_operation("m5.ledger_export.canonical"),
        closing(
            sqlite3.connect(
                "file:" + quote(str(plan.canonical_ledger_file), safe="/") + "?mode=ro",
                uri=True,
            )
        ) as db,
        db,
    ):
        db.execute("BEGIN")
        spent, reserved = db.execute(
            "SELECT COALESCE(SUM(CASE WHEN month=? THEN spent ELSE 0 END),0),COALESCE(SUM(CASE WHEN spent IS NULL THEN reserved ELSE 0 END),0) FROM requests",
            (month,),
        ).fetchone()
        rows = db.execute(query, parameters).fetchall()
        snapshot_utc = datetime.now(UTC).isoformat()
    return {
        "authority": f"{plan.canonical_volume}:{plan.canonical_ledger_file}",
        "month": month,
        "snapshot_utc": snapshot_utc,
        "budget": {
            "cap": 50 * USD,
            "spent": spent,
            "reserved": reserved,
            "available": max(0, 50 * USD - spent - reserved),
        },
        "requests": [
            dict(
                zip(
                    ("id", "month", "run_id", "reserved", "spent", "created"),
                    row,
                    strict=True,
                )
            )
            for row in rows
        ],
    }


def validate_recovery_envelope(envelope: dict[str, Any], namespace: str) -> None:
    """This version carries the closed attempt into one fresh USD7 invocation."""
    if (
        type(envelope.get("max_total_nanousd")) is not int
        or envelope["max_total_nanousd"] != 7 * USD
        or type(envelope.get("canonical_monthly_cap_nanousd")) is not int
        or envelope["canonical_monthly_cap_nanousd"] != 50 * USD
    ):
        raise ValueError("recovery requires exact integer USD7/USD50 caps")
    historical = envelope.get("historical_requests")
    if (
        not isinstance(historical, list)
        or len(historical) != 2
        or any(
            not isinstance(row, dict)
            or not isinstance(row.get("id"), str)
            or type(row.get("spent_nanousd")) is not int
            for row in historical
        )
        or {row["id"]: row["spent_nanousd"] for row in historical}
        != RECOVERY_HISTORICAL
    ):
        raise ValueError("recovery requires the two exact historical request amounts")
    additional = envelope.get("additional_cost_run_ids")
    if (
        not isinstance(additional, list)
        or len(additional) != 2
        or any(not isinstance(value, str) for value in additional)
        or set(additional) != RECOVERY_PRIOR_RUNS
    ):
        raise ValueError("recovery requires both prior probe runs exactly once")
    if namespace.casefold() == RECOVERY_PREVIOUS_NAMESPACE.casefold():
        raise ValueError("recovery requires a fresh campaign namespace")


def claim_recovery(
    plan: Plan, captured: dict[str, bytes], admitted: dict[str, Any]
) -> dict[str, Any]:
    """Spend the recovery's one use before inference, with current accounting."""
    data = {name: json.loads(value) for name, value in captured.items()}
    envelope = data["authorization"]
    namespace = benchmark.Experiment.model_validate(data["campaign"]).name
    validate_recovery_envelope(envelope, namespace)
    hashes = input_hashes(captured)
    if hashes != admitted["input_sha256"]:
        raise ValueError("recovery inputs changed after admission")
    historical = envelope["historical_requests"]
    additional = envelope["additional_cost_run_ids"]
    if (
        not plan.canonical_ledger_file.is_file()
        or plan.canonical_ledger_file.is_symlink()
    ):
        raise ValueError("the canonical ledger must already exist")
    with (
        sqlite_operation("m5.claim_recovery"),
        closing(
            sqlite3.connect(
                "file:" + quote(str(plan.canonical_ledger_file), safe="/") + "?mode=rw",
                uri=True,
            )
        ) as db,
        db,
    ):
        db.execute("BEGIN IMMEDIATE")
        budget = _ledger_snapshot_in_transaction(
            db, historical, additional, namespace, True
        )
        historical_total = sum(row["spent_nanousd"] for row in historical)
        historical_total += budget.pop("prior_extra_liability")
        if historical_total + 6_980_000_000 > 7 * USD:
            raise ValueError("prior pilot charges leave insufficient room inside USD7")
        if budget["available"] < 12 * USD:
            raise ValueError("monthly ledger lacks the admitted USD12 headroom")
        db.execute(
            "INSERT INTO records(kind,key,data) VALUES(?,?,?)",
            (
                RECOVERY_CLAIM_KIND,
                RECOVERY_CLAIM_KEY,
                json.dumps(
                    {
                        "policy": RECOVERY_POLICY,
                        "namespace": namespace,
                        "input_sha256": hashes,
                        "historical_nanousd": historical_total,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ),
        )
    return {"budget": budget, "historical_nanousd": historical_total}


def preflight(plan: Plan, captured: dict[str, bytes] | None = None) -> dict[str, Any]:
    if (
        not plan.output.is_absolute()
        or plan.output.is_symlink()
        or (
            plan.output.exists()
            and (not plan.output.is_dir() or any(plan.output.iterdir()))
        )
    ):
        raise ValueError(
            "pilot output must be new or empty; attempts cannot be replaced"
        )
    captured = capture_inputs(plan) if captured is None else captured
    hashes = input_hashes(captured)
    data = {name: json.loads(value) for name, value in captured.items()}
    admission = data["admission"]
    policy = admission.get("probe_outcome_policy")
    if policy not in (None, SHORT_DEADLINE_POLICY, RECOVERY_POLICY):
        raise ValueError("unknown prospectively admitted probe outcome policy")
    if (
        admission.get("approved") is not True
        or admission.get("read_only_preparation") is not False
        or set(admission.get("required_gates", {})) != GATES
        or not all(value is True for value in admission["required_gates"].values())
        or admission.get("native_decoding_guarantees_equal") is not False
        or admission.get("comparison_scope") != "configured_controller_stacks"
    ):
        raise ValueError("root admission has not accepted every free/gateway gate")
    if admission.get("approved_inputs_sha256") != {
        name: value for name, value in hashes.items() if name != "admission"
    }:
        raise ValueError("root admission is not bound to these exact inputs")
    envelope = data["authorization"]
    source = data["source_manifest"]
    files = source_files(source)
    experiment = benchmark.Experiment.model_validate(data["campaign"])
    if policy == RECOVERY_POLICY:
        validate_recovery_envelope(envelope, experiment.name)
    if admission.get("source_revision") != source["revision"]:
        raise ValueError("root admission source revision differs")
    credential = experiment.gateway_credential
    if (
        credential is None
        or not credential.is_absolute()
        or credential.is_symlink()
        or not credential.is_file()
        or credential.stat().st_mode & 0o077
    ):
        raise ValueError("the private client credential must already exist")
    if experiment.bot_id != 65001:
        raise ValueError("this status observer is qualified for fixture G bot65001")
    if (
        not re.fullmatch(r"[a-f0-9]{40}", source["revision"])
        or experiment.source_revision != source["revision"]
    ):
        raise ValueError("campaign and frozen source revisions differ")
    if (
        plan.canonical_ledger_file != CANONICAL_LEDGER_FILE
        or experiment.budget_file != plan.canonical_ledger_file
        or plan.canonical_volume != CANONICAL_VOLUME
    ):
        raise ValueError("one existing canonical monthly ledger is required")
    if not owned_output(experiment.output, plan.output) or experiment.output.exists():
        raise ValueError("game campaign output must be a new child of the pilot output")
    if (
        experiment.seconds != 1800
        or experiment.repetitions != 3
        or experiment.memory_mode != "frozen"
        or experiment.run_cap_nanousd != USD
        or experiment.campaign_cap_nanousd != 6 * USD
    ):
        raise ValueError(
            "M5 requires three frozen 1800-second blocks with six USD1 model caps"
        )
    participants = {p.name: p for p in experiment.participants}
    if (
        len(experiment.participants) != 3
        or set(participants) != {"native", "openai", "gemini"}
        or participants["native"].kind != "native"
    ):
        raise ValueError("participants must be native, OpenAI and Gemini exactly once")
    for name in ("openai", "gemini"):
        mapping = participants[name].gateway
        if (
            participants[name].kind != "litellm"
            or mapping is None
            or mapping.provider != name
        ):
            raise ValueError("model participant and provider names must match")
    for image in (experiment.game_image, experiment.database_image):
        if re.fullmatch(r"(?:sha256:|[^@\s]+@sha256:)[a-f0-9]{64}", image) is None:
            raise ValueError("this pilot requires immutable image references")
    if (
        benchmark.fixture_hash(experiment.fixture, experiment.world_map)
        != experiment.expected_initial_sha256
    ):
        raise ValueError("initial fixture bytes changed")
    for participant in experiment.participants:
        if (
            len(
                str(
                    experiment.output / f"{participant.name}-2/socket/worker.sock"
                ).encode()
            )
            >= 108
        ):
            raise ValueError("pilot socket paths exceed Unix limits")
    historical = envelope.get("historical_requests", [])
    historical_total = sum(row["spent_nanousd"] for row in historical)
    if (
        envelope.get("max_total_nanousd")
        != (SHORT_DEADLINE_TOTAL_CAP if policy == SHORT_DEADLINE_POLICY else 7 * USD)
        or envelope.get("canonical_monthly_cap_nanousd") != 50 * USD
        or envelope.get("canonical_authority")
        != f"{CANONICAL_VOLUME}:{plan.canonical_ledger_file}"
        or historical_total + 6 * USD + 980_000_000 > 7 * USD
    ):
        raise ValueError(
            "the complete envelope must fit USD7 inside the shared USD50 cap"
        )
    fixtures = data["decision_fixtures"]
    if not isinstance(fixtures, list) or not 1 <= len(fixtures) <= 6:
        raise ValueError("conformance requires at most six predeclared observations")
    observations = [Observation.model_validate(row["observation"]) for row in fixtures]
    if not any(len(row.actions) > 1 for row in observations):
        raise ValueError("conformance needs at least one real model-choice opportunity")
    if len({row.bot.id for row in observations}) != 1:
        raise ValueError("probe cap must be shared by one recorded bot per model")
    if set(plan.probe_workers) != {"openai", "gemini"}:
        raise ValueError("one conformance configuration per model is required")
    for name in plan.probe_workers:
        config = runtime.Configuration.model_validate(data[name])
        if policy in PERFORMANCE_POLICIES:
            probe_deadlines(config, fixtures)
        if (
            config.provider != "litellm"
            or config.gateway != participants[name].gateway
            or config.budget_file != plan.canonical_ledger_file
            or config.monthly_usd != 50
            or config.run_cap_nanousd != 490_000_000
            or config.recording is None
            or config.credential_file != experiment.gateway_credential
            or set(config.bots) != {observations[0].bot.id}
        ):
            raise ValueError(
                "probe identity, ledger, credential or USD0.49 cap differs"
            )
        if (
            not owned_output(config.recording.path, plan.output)
            or config.recording.path.exists()
        ):
            raise ValueError("probe recording must have a new pilot-owned path")
    image, mounts = container_identity()
    if image != plan.worker_image or admission.get("common_worker_image") != image:
        raise ValueError("worker image differs from root admission")
    for target in (
        plan.canonical_ledger_file,
        plan.canonical_ledger_file.with_name("m5-pilot.lock"),
    ):
        ancestors = [
            mount
            for mount in mounts
            if target.is_relative_to(Path(mount["Destination"]))
        ]
        effective = max(
            ancestors,
            key=lambda mount: len(Path(mount["Destination"]).parts),
            default={},
        )
        if (
            effective.get("Type") != "volume"
            or effective.get("Name") != CANONICAL_VOLUME
            or effective.get("Destination") != str(plan.canonical_ledger_file.parent)
            or effective.get("RW") is not True
        ):
            raise ValueError(
                "canonical Docker volume is missing or shadowed by another mount"
            )
    for key, actual in (
        ("common_worker_python", platform.python_version()),
        ("openai_sdk", importlib.metadata.version("openai")),
        ("pydantic", importlib.metadata.version("pydantic")),
    ):
        if admission.get(key) != actual:
            raise ValueError("worker dependency versions differ from root admission")
    budget = ledger_snapshot(
        plan.canonical_ledger_file,
        historical,
        envelope.get("additional_cost_run_ids", []),
        experiment.name,
        require_additional_runs=policy == RECOVERY_POLICY,
    )
    historical_total += budget.pop("prior_extra_liability")
    if (
        policy == SHORT_DEADLINE_POLICY
        and historical_total + 6_980_000_000 > SHORT_DEADLINE_TOTAL_CAP
    ):
        raise ValueError(
            "prior charges exceed the prospective complete liability envelope"
        )
    if historical_total + 6_980_000_000 > 7 * USD:
        raise ValueError("prior pilot charges leave insufficient room inside USD7")
    if budget["available"] < 12 * USD:
        raise ValueError("monthly ledger lacks the admitted USD12 headroom")
    order = [
        [p.name for p in experiment.participants[i:] + experiment.participants[:i]]
        for i in range(3)
    ]
    if envelope.get("scored", {}).get("order") != order:
        raise ValueError("declared execution order differs from canonical rotation")
    if any(file_hash(path) != hashes[name] for name, path in input_paths(plan).items()):
        raise ValueError("inputs changed during read-only preflight")
    return {
        "accepted": True,
        "budget": budget,
        "order": order,
        "source_files": files,
        "source_revision": source["revision"],
        "input_sha256": hashes,
        "fixture_sha256": experiment.expected_initial_sha256,
        "new_worst_case_nanousd": 6_980_000_000,
        "historical_nanousd": historical_total,
    }


async def observe_status(
    configuration: runtime.Configuration, stopped: asyncio.Event, active: Any
) -> None:
    last = -100.0
    while not stopped.is_set():
        clock = Store(configuration.state_file).get("run_clock", "start")
        elapsed = time.monotonic() - clock["monotonic"] if clock else None
        fixture = active()
        if elapsed is not None and elapsed >= 540 and elapsed - last >= 10 and fixture:
            last = elapsed

            def query(sql: str, target: Any = fixture) -> str:
                value = target.command(
                    "exec",
                    "-T",
                    "database",
                    "sh",
                    "-c",
                    'MYSQL_PWD="$MARIADB_PASSWORD" mariadb -u canary canary -N -e "$1"',
                    "sh",
                    sql,
                    timeout=10,
                )
                if not isinstance(value, str):
                    raise TypeError("status query did not return text")
                return value

            async def query_async(sql: str) -> str:
                pending = asyncio.create_task(asyncio.to_thread(query, sql))
                try:
                    return await asyncio.shield(pending)
                except asyncio.CancelledError:
                    await pending
                    raise

            identity = int(
                await query_async(
                    "INSERT INTO bot_commands(bot_name,command) VALUES('Grizzle Alyronia','status');SELECT LAST_INSERT_ID();",
                )
            )
            status = ""
            for _ in range(20):
                status = await query_async(
                    f"SELECT result FROM bot_commands WHERE id={identity} AND processed=1;",
                )
                if status:
                    break
                await asyncio.sleep(0.2)
            with (configuration.state_file.parent / "phase-status.jsonl").open(
                "a"
            ) as stream:
                stream.write(
                    json.dumps(
                        {"elapsed": elapsed, "command_id": identity, "status": status}
                    )
                    + "\n"
                )
        await asyncio.sleep(1)


async def run_attested_campaign(experiment: benchmark.Experiment) -> Any:
    original_run = runtime.run
    active = None
    attestations: dict[str, Any] = {}
    attestation_lock = threading.Lock()

    class AttestedFixture(benchmark.DockerFixture):
        def __init__(self, experiment: Any, directory: Path, identity: str) -> None:
            super().__init__(experiment, directory, identity)
            self.attestation = TrialAttestation(self, attestations, attestation_lock)

        def prepare(self, participant: Any) -> None:
            nonlocal active
            active = self
            super().prepare(participant)
            compose = json.loads(self.compose.read_text())
            compose["networks"] = {"default": {"internal": True}}
            compose["services"]["game"]["volumes"].append(f"{self.directory}:/m5")
            self.compose.write_text(json.dumps(compose))
            self.attestation.persist()

        def start_game(self) -> None:
            # No game observation (and thus no model request) can precede this
            # inspection. `start` preserves the exact container created here.
            try:
                self.command("create", "--no-build", "game", timeout=120)
                self.attestation.verify_images(running=False)
                self.command("start", "--wait", "game")
                self.attestation.verify_images(running=True)
            except BaseException as error:
                self.attestation.failure("game_start", error)
                raise

        def close(self) -> None:
            close_error = None
            try:
                super().close()
            except BaseException as error:  # noqa: BLE001 - verify cleanup even on cancellation, then re-raise
                close_error = error
            try:
                self.attestation.cleanup(close_error)
            except BaseException as error:
                if close_error is not None:
                    raise close_error from error
                raise

    async def observed_worker(
        configuration: runtime.Configuration, stopped: asyncio.Event
    ) -> None:
        observer = asyncio.create_task(
            observe_status(configuration, stopped, lambda: active)
        )
        worker = asyncio.create_task(original_run(configuration, stopped))
        try:
            await asyncio.wait((observer, worker), return_when=asyncio.FIRST_COMPLETED)
            if observer.done():
                await observer
                if not stopped.is_set():
                    raise RuntimeError(
                        "status observer ended before the supervised worker"
                    )
            await worker
        finally:
            stopped.set()
            observer.cancel()
            endings = await asyncio.gather(observer, worker, return_exceptions=True)
            if isinstance(endings[0], Exception):
                write_new(
                    configuration.state_file.parent / "status-observer-error.json",
                    {"error_type": type(endings[0]).__name__},
                )
                if active is not None:
                    active.attestation.failure("observer", endings[0])
                raise RuntimeError(  # noqa: TRY004 - propagate an asynchronous task failure
                    "passive status observer failed; run evidence is incomplete"
                )

    with (
        patch.object(benchmark, "DockerFixture", AttestedFixture),
        patch.object(benchmark, "run", observed_worker),
    ):
        return await benchmark.run_campaign(experiment, live=True)


def probe_deadlines(config: runtime.Configuration, fixtures: list[Any]) -> list[int]:
    observations = [Observation.model_validate(row["observation"]) for row in fixtures]
    deadlines = [
        round(min(config.decision_timeout * 1000, min(a.ttl_ms for a in row.actions)))
        for row in observations
    ]
    if (
        config.gateway is None
        or config.gateway.decision_api != "responses"
        or len(observations) != 6
        or sorted(
            deadline
            for row, deadline in zip(observations, deadlines, strict=True)
            if len(row.actions) > 1
        )
        != [1000, 1000, 1500, 5000, 5000]
    ):
        raise ValueError(
            "short-deadline policy requires two 5s and three 1s/1.5s choices"
        )
    return deadlines


def qualify_short_deadlines(
    probe: dict[str, Any],
    config: runtime.Configuration,
    fixtures: list[Any],
    ledger: Path,
) -> dict[str, Any]:
    """Reconcile one completed probe block; never release an unknown charge."""
    deadlines = probe_deadlines(config, fixtures)
    assert config.recording is not None and config.gateway is not None
    rows, runs = probe["decisions"], probe["runs"]
    if len(rows) != len(fixtures) or len(runs) != 1:
        raise ValueError("probe decision/run count differs from the frozen fixtures")
    reader = ReplayReader(config.recording.path)
    run = reader.run(runs[0])
    manifest = run["manifest"]
    if (
        run["incomplete"]
        or run["status"] not in {"completed", "failed"}
        or manifest["initial_sha256"] != digest(fixtures)
        or manifest["provider"] != config.gateway.provider
        or manifest["model"] != config.gateway.effective_model
        or manifest["participant"] != config.gateway.alias
        or manifest["bot_id"]
        != Observation.model_validate(fixtures[0]["observation"]).bot.id
    ):
        raise ValueError("probe recording identity or completeness differs")
    events = list(reader.all_events(runs[0]))
    decisions = [
        e["data"]
        for e in events
        if e["kind"] == "decision" and e["data"].get("phase") == "requested"
    ]
    if len(decisions) != len(fixtures) or any(e["kind"] == "gap" for e in events):
        raise ValueError("probe recording lost decisions")
    ids = [d["decision_id"] for d in decisions]
    if len(set(ids)) != len(ids):
        raise ValueError("probe repeats a decision identity")
    requests: dict[str, list[dict[str, Any]]] = {identity: [] for identity in ids}
    proposals: dict[str, list[str]] = {identity: [] for identity in ids}
    for event in events:
        if (
            event["kind"] == "decision"
            and event["data"].get("phase") == "model_proposed"
        ):
            proposed = event["data"]
            if proposed["decision_id"] not in proposals:
                raise ValueError("unattributed probe proposal")
            proposals[proposed["decision_id"]].append(proposed["candidate"])
        if event["kind"] == "request":
            data = event["data"]
            if data["decision_id"] not in requests:
                raise ValueError("unattributed probe request")
            requests[data["decision_id"]].append(data)
    with (
        sqlite_operation("m5.probe_evidence"),
        closing(
            sqlite3.connect(ledger.resolve().as_uri() + "?mode=ro", uri=True)
        ) as db,
        db,
    ):
        liabilities = {
            identity: {"reserved": reserved, "spent": spent, "endpoint": endpoint}
            for identity, reserved, spent, endpoint in db.execute(
                "SELECT id,reserved,spent,endpoint FROM requests WHERE run_id=?",
                (runs[0],),
            )
        }
    used: set[str] = set()
    outcomes = []
    last_timeout = False
    long_valid = late = backoff = 0
    for index, (row, frozen, deadline, decision) in enumerate(
        zip(rows, fixtures, deadlines, decisions, strict=True)
    ):
        snapshot = Observation.model_validate(frozen["observation"])
        if (
            decision["observation"]
            != public_data(snapshot.model_dump(exclude={"lease", "messages"}))
            or decision["memory"] != public_data(frozen.get("memory", {}))
            or row["bot_id"] != snapshot.bot.id
        ):
            raise ValueError("probe observation differs from the frozen input")
        emitted = requests[decision["decision_id"]]
        if any("diagnostic_failure" in event for event in emitted):
            raise ValueError("financial diagnostic storage failed during the probe")
        proposed_choices = proposals[decision["decision_id"]]
        if row["valid"] is True:
            if proposed_choices != [row.get("choice")] or "error" in row:
                raise ValueError("positive probe summary has no matching proposal")
        elif row["valid"] is not False or proposed_choices or "choice" in row:
            raise ValueError("negative probe summary contradicts recorded choices")
        outcome = "valid"
        if len(snapshot.actions) == 1:
            if (
                emitted
                or not row["valid"]
                or row.get("choice") != snapshot.actions[0].id
            ):
                raise ValueError("local choice issued a request or failed")
            outcome = "local_choice"
        else:
            if (
                not emitted
                or len({e["request_id"] for e in emitted}) != 1
                or any(
                    e["endpoint"] != "responses"
                    or e["requested_model"] != config.gateway.alias
                    or e.get("deadline_ms", deadline) != deadline
                    for e in emitted
                )
            ):
                raise ValueError("probe request identity/deadline differs")
            request_id = emitted[0]["request_id"]
            phases = [e["phase"] for e in emitted]
            if phases == ["skipped"]:
                if (
                    deadline == 5000
                    or row["valid"] is not False
                    or row.get("error") != "ProviderBackoff"
                    or not last_timeout
                    or emitted[0].get("reason") != "backoff"
                    or emitted[0]["reserved_nanousd"] != 0
                    or request_id in liabilities
                ):
                    raise ValueError("probe backoff has no causal short deadline")
                backoff += 1
                outcome = "causal_backoff_negative"
            else:
                if (
                    phases not in (["reserved", "finished"], ["reserved", "failed"])
                    or request_id not in liabilities
                    or request_id in used
                ):
                    raise ValueError("probe transmission is not one ledger attempt")
                used.add(request_id)
                cost, reserved, terminal = (
                    liabilities[request_id],
                    emitted[0],
                    emitted[1],
                )
                if (
                    cost["endpoint"] != "responses"
                    or cost["reserved"] <= 0
                    or reserved["reserved_nanousd"] != cost["reserved"]
                ):
                    raise ValueError("probe reservation differs from the ledger")
                if row["valid"]:
                    elapsed = (row.get("elapsed_ms"), terminal.get("elapsed_ms"))
                    if (
                        any(
                            type(value) is not int or value < 0 or value > deadline
                            for value in elapsed
                        )
                        or elapsed[0] < elapsed[1]
                    ):
                        raise ProbeTimingError(
                            "positive probe timing is outside its deadline"
                        )
                    if (
                        terminal["phase"] != "finished"
                        or cost["spent"] is None
                        or terminal["spent_nanousd"] != cost["spent"]
                        or terminal["reserved_nanousd"] != 0
                        or row.get("choice") not in {a.id for a in snapshot.actions}
                    ):
                        raise ValueError("valid probe has no settled response")
                    if (
                        terminal["effective_model"] != config.gateway.effective_model
                        or terminal["gateway"]["deployment_id"]
                        != config.gateway.deployment_id
                    ):
                        raise ValueError("valid probe route differs")
                    long_valid += deadline == 5000
                    last_timeout = False
                elif (
                    deadline != 5000
                    and row["valid"] is False
                    and row.get("error") == "TimeoutError"
                    and terminal["phase"] == "failed"
                    and terminal.get("error") == "TimeoutError"
                    and terminal.get("unsettled") is True
                    and terminal.get("deadline_expired_on_error") is True
                    and terminal.get("timeout_origin") == "outer_deadline"
                    and cost["spent"] is None
                    and terminal["reserved_nanousd"] == cost["reserved"]
                ):
                    total_ms, request_ms = (
                        row.get("elapsed_ms"),
                        terminal.get("elapsed_ms"),
                    )
                    # The outer deadline includes reservation SQL; the request
                    # clock starts afterward and can legitimately be shorter.
                    if (
                        type(total_ms) is not int
                        or total_ms < deadline
                        or type(request_ms) is not int
                        or not 0 <= request_ms <= total_ms
                    ):
                        raise ValueError(
                            "short timeout does not demonstrate deadline expiry"
                        )
                    late += 1
                    last_timeout = True
                    outcome = "deadline_negative_unknown_charge"
                else:
                    raise ValueError("probe technical error or invalid 5s conformance")
        outcomes.append(
            {
                "index": index,
                "deadline_ms": deadline,
                "outcome": outcome,
                "decision_id": decision["decision_id"],
                "request_id": emitted[0]["request_id"] if emitted else None,
            }
        )
    liability = sum(
        c["spent"] if c["spent"] is not None else c["reserved"]
        for c in liabilities.values()
    )
    if used != set(liabilities) or long_valid != 2 or liability > 490_000_000:
        raise ValueError(
            "probe attempts, long conformance or USD0.49 liability cap differ"
        )
    return {
        "accepted_for_game": True,
        "evidence_reconciled": True,
        "policy": SHORT_DEADLINE_POLICY,
        "long_valid": long_valid,
        "late": late,
        "causal_backoff": backoff,
        "technical_invalid": 0,
        "model_opportunities": 5,
        "liability_nanousd": liability,
        "financial_final": not any(c["spent"] is None for c in liabilities.values()),
        "short_contract_coverage_complete": not (late or backoff),
        "case_outcomes": outcomes,
        "root_review_required": False,
        "failure_interpretation": "deadline_controller_performance"
        if late or backoff
        else None,
    }


def write_new(path: Path, data: Any) -> None:
    with path.open("x") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


@contextmanager
def pilot_lease(ledger: Path) -> Iterator[None]:
    """One M5 orchestrator even if two operators select different output paths."""
    descriptor = os.open(
        ledger.with_name("m5-pilot.lock"),
        os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW,
        0o600,
    )
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError(
                "another M5 orchestrator holds the canonical-volume lease"
            ) from None
        yield
    finally:
        os.close(descriptor)


async def execute(plan: Plan) -> dict[str, Any]:
    captured = capture_inputs(plan)
    admitted = preflight(plan, captured)
    assert_frozen_imports(json.loads(captured["source_manifest"]))
    with pilot_lease(plan.canonical_ledger_file):
        if (
            json.loads(captured["admission"]).get("probe_outcome_policy")
            == RECOVERY_POLICY
        ):
            admitted.update(claim_recovery(plan, captured, admitted))
        return await execute_admitted(plan, admitted, captured)


async def execute_admitted(
    plan: Plan, admitted: dict[str, Any], captured: dict[str, bytes]
) -> dict[str, Any]:
    data = {name: json.loads(value) for name, value in captured.items()}
    source = data["source_manifest"]
    os.umask(0o077)
    plan.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    write_new(
        plan.output / "execution-started.json",
        {"plan": plan.model_dump(mode="json"), "preflight": admitted},
    )
    inputs = plan.output / "inputs"
    inputs.mkdir(mode=0o700)
    for name, payload in captured.items():
        if hashlib.sha256(payload).hexdigest() != admitted["input_sha256"][name]:
            raise ValueError("admitted input changed before its snapshot")
        with (inputs / (name + ".json")).open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    result: dict[str, Any] = {
        "probes": {},
        "campaign": None,
        "comparison_scope": "configured_controller_stacks",
        "native_decoding_guarantees_equal": False,
    }
    expected_attempts = sum(
        len(Observation.model_validate(row["observation"]).actions) > 1
        for row in data["decision_fixtures"]
    )
    stage = "m5.probes"
    try:
        for name in ("openai", "gemini"):
            stage = "m5.probe." + name
            source_files(source)
            probe = await decision_fixtures(
                argparse.Namespace(
                    fixtures=ImmutableJSON(captured["decision_fixtures"]),
                    worker_config=ImmutableJSON(captured[name]),
                    live=True,
                )
            )
            # Preserve the completed evaluator output even if reconciliation fails.
            result["probes"][name] = probe
            stage = "m5.probe_ledger." + name
            with (
                sqlite_operation(stage),
                closing(
                    sqlite3.connect(
                        "file:"
                        + quote(str(plan.canonical_ledger_file), safe="/")
                        + "?mode=ro",
                        uri=True,
                    )
                ) as db,
                db,
            ):
                unresolved = sum(
                    db.execute(
                        "SELECT COUNT(*) FROM requests WHERE run_id=? AND spent IS NULL",
                        (run,),
                    ).fetchone()[0]
                    for run in probe["runs"]
                )
                count = sum(
                    db.execute(
                        "SELECT COUNT(*) FROM requests WHERE run_id=?", (run,)
                    ).fetchone()[0]
                    for run in probe["runs"]
                )
                unknown_nanousd = sum(
                    db.execute(
                        "SELECT COALESCE(SUM(reserved),0) FROM requests WHERE run_id=? AND spent IS NULL",
                        (run,),
                    ).fetchone()[0]
                    for run in probe["runs"]
                )
            late = sum(row.get("error") == "TimeoutError" for row in probe["decisions"])
            technical = sum(
                not row["valid"] and row.get("error") != "TimeoutError"
                for row in probe["decisions"]
            )
            probe["qualification"] = {
                "valid": sum(row["valid"] for row in probe["decisions"]),
                "late": late,
                "technical_invalid": technical,
                "unknown_requests": unresolved,
                "unknown_nanousd": unknown_nanousd,
                "ledger_requests": count,
                "expected_model_requests": expected_attempts,
                "root_review_required": not all(
                    row["valid"] for row in probe["decisions"]
                )
                or bool(unresolved),
                "failure_interpretation": "mixed"
                if late and technical
                else "deadline_performance"
                if late
                else "contract_or_provider"
                if technical
                else None,
            }
            admitted_policy = data["admission"].get("probe_outcome_policy")
            performance_policy = admitted_policy in PERFORMANCE_POLICIES
            if performance_policy:
                probe["qualification"].pop("expected_model_requests")
                try:
                    probe["qualification"].update(
                        qualify_short_deadlines(
                            probe,
                            runtime.Configuration.model_validate(data[name]),
                            data["decision_fixtures"],
                            plan.canonical_ledger_file,
                        )
                    )
                    probe["qualification"]["policy"] = admitted_policy
                except (ValueError, TypeError, KeyError, sqlite3.Error) as error:
                    probe["qualification"].update(
                        {
                            "accepted_for_game": False,
                            "policy": admitted_policy,
                            "evidence_reconciled": False,
                            "root_review_required": True,
                            "evidence_failure": failure_metadata(
                                error, "m5.probe_evidence"
                            ),
                            "rejection_reason": "positive_timing_unqualified"
                            if isinstance(error, ProbeTimingError)
                            else "technical_or_unreconciled_evidence",
                        }
                    )
            result["probes"][name] = probe
            write_new(plan.output / (name + "-probe-result.json"), probe)
            if performance_policy:
                if not probe["qualification"]["accepted_for_game"]:
                    raise ValueError(
                        "conformance failed; technical or unreconciled probe evidence"
                    )
                continue
            if not probe["decisions"] or not all(
                row["valid"] for row in probe["decisions"]
            ):
                raise ValueError(
                    "conformance failed; root must review deadline/contract outcomes"
                )
            if count != expected_attempts:
                raise ValueError(
                    "conformance did not record one attempt per model-choice opportunity"
                )
            if unresolved:
                raise ValueError(
                    "conformance has unknown charges; retain reservations and stop"
                )
        source_files(source)
        stage = "m5.campaign"
        result["campaign"] = await run_attested_campaign(
            benchmark.Experiment.model_validate(data["campaign"])
        )
        return result
    except BaseException as error:
        result["error_type"] = type(error).__name__
        result["failure"] = failure_metadata(error, stage)
        raise
    finally:
        export_failed = False
        try:
            probe_runs = [
                run
                for probe in result["probes"].values()
                for run in probe.get("runs", [])
            ]
            write_new(
                plan.output / "ledger.json", ledger_export(plan, probe_runs, captured)
            )
        except Exception as error:  # noqa: BLE001 - preserve the original stage failure too
            export_failed = True
            result["ledger_export_error"] = type(error).__name__
            result["ledger_export_failure"] = failure_metadata(
                error, "m5.ledger_export"
            )
        write_new(plan.output / "execution-result.json", result)
        if export_failed and "error_type" not in result:
            raise RuntimeError("financial export failed; root review is required")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        plan = Plan.model_validate(read_json(args.plan))
        result = preflight(plan) if args.preflight else asyncio.run(execute(plan))
    except Exception as error:  # noqa: BLE001 - API errors can contain credentials
        parser.exit(1, f"M5 stopped: {type(error).__name__}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
