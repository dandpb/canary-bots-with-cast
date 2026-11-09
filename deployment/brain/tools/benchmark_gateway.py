"""Serve an inference-only gateway; never sends an inference request."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import signal
import subprocess
import tempfile
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

PROJECT = "canary-bots-wsl"
NETWORK = PROJECT + "_default"
SERVICE = "benchmark-gateway"
COMPOSE = Path(__file__).resolve().parents[1] / "gateway/compose.benchmark.yaml"
MUTATION_TIMEOUT = 120.0
_defer_stop_depth = 0
_stop_requested = False


class GatewayError(ValueError):
    """A static operator message containing no subprocess/credential data."""


@contextmanager
def defer_stop() -> Iterator[None]:
    """Drain a mutation/cleanup before delivering operator cancellation."""
    global _defer_stop_depth, _stop_requested
    _defer_stop_depth += 1
    try:
        yield
    finally:
        _defer_stop_depth -= 1
        if not _defer_stop_depth and _stop_requested:
            _stop_requested = False
            raise KeyboardInterrupt


def journal_path(env: dict[str, str]) -> Path:
    return Path(env["CANARY_GATEWAY_RUNTIME"]) / (
        "benchmark-gateway-" + env["CANARY_BENCHMARK_SESSION"] + ".json"
    )


def sync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def journal(env: dict[str, str], phase: str, **details: str) -> None:
    target = journal_path(env)
    staged: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=target.parent, prefix=".benchmark-journal-", delete=False
        ) as stream:
            staged = Path(stream.name)
            json.dump(
                {
                    "phase": phase,
                    "session": env["CANARY_BENCHMARK_SESSION"],
                    "project": PROJECT,
                    "service": SERVICE,
                    "image": env["CANARY_BENCHMARK_IMAGE"],
                    **details,
                },
                stream,
            )
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staged, target)
        sync_directory(target.parent)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def journal_phase(env: dict[str, str]) -> str | None:
    path = journal_path(env)
    if not path.exists():
        return None
    if path.is_symlink():
        raise GatewayError("refusing a replaced recovery journal")
    return str(json.loads(path.read_text())["phase"])


def ensure_no_unresolved(runtime: Path) -> None:
    for path in runtime.glob("benchmark-gateway-*.json"):
        if not re.fullmatch(r"benchmark-gateway-[a-f0-9]{32}\.json", path.name):
            continue
        try:
            if path.is_symlink() or json.loads(path.read_text())["phase"] != "cleaned":
                raise ValueError
        except (OSError, ValueError, KeyError, TypeError):
            raise GatewayError(
                "an earlier gateway session needs manual recovery; preserve its journal"
            ) from None


def invoke(arguments: list[str], environment: dict[str, str]) -> str:
    # Compose errors may contain expanded credentials; never echo captured output.
    mutation = arguments[0] in {"start", "stop", "rm"} or (
        arguments[0] == "compose" and "create" in arguments
    )
    if mutation:
        operation = "create" if arguments[0] == "compose" else arguments[0]
        with defer_stop():
            try:
                journal(environment, "mutation_in_flight", operation=operation)
            except OSError:
                # Stopping a verified CID preserves evidence even if storage failed.
                if operation != "stop":
                    raise
            try:
                completed = subprocess.run(
                    ["docker", *arguments],
                    cwd="/",
                    env=environment,
                    check=False,
                    capture_output=True,
                    text=True,
                    start_new_session=True,
                    timeout=MUTATION_TIMEOUT,
                )
            except subprocess.TimeoutExpired:
                journal(environment, "uncertain", operation=operation)
                raise GatewayError(
                    "Docker mutation timed out; manual recovery required"
                ) from None
            if completed.returncode:
                journal(environment, "uncertain", operation=operation)
                raise GatewayError(
                    "Docker did not confirm its mutation; manual recovery required"
                )
            journal(environment, "mutation_drained", operation=operation)
    else:
        completed = subprocess.run(
            ["docker", *arguments],
            cwd="/",
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            start_new_session=True,
        )
    output = (
        completed.stdout + completed.stderr
        if arguments[0] == "logs"
        else completed.stdout
    )
    return output.strip()


def environment(
    runtime: Path, policy: Path, image: str, revision: str
) -> dict[str, str]:
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", image) or not re.fullmatch(
        r"[a-f0-9]{40}", revision
    ):
        raise GatewayError(
            "an immutable image ID and full source revision are required"
        )
    credentials = [
        runtime / "secrets" / ("litellm-" + kind + ".env")
        for kind in ("provider", "worker", "ui", "redis")
    ]
    files = [policy, *credentials]
    if (
        not runtime.is_absolute()
        or runtime.is_symlink()
        or any(
            not path.is_absolute() or path.is_symlink() or not path.is_file()
            for path in files
        )
    ):
        raise GatewayError("existing absolute policy/runtime files are required")
    if any(path.stat().st_mode & 0o077 for path in credentials):
        raise GatewayError("gateway env files must be private (mode 0600)")
    return {
        **os.environ,
        "COMPOSE_DISABLE_ENV_FILE": "1",
        "COMPOSE_REMOVE_ORPHANS": "0",
        "COMPOSE_IGNORE_ORPHANS": "1",
        "CANARY_GATEWAY_RUNTIME": str(runtime),
        "CANARY_GATEWAY_POLICY": str(policy),
        "CANARY_BENCHMARK_IMAGE": image,
        "CANARY_SOURCE_REVISION": revision,
        "CANARY_BENCHMARK_SESSION": uuid.uuid4().hex,
    }


def compose(*arguments: str) -> list[str]:
    return ["compose", "-p", PROJECT, "-f", str(COMPOSE), *arguments]


@contextmanager
def lease(runtime: Path) -> Iterator[None]:
    descriptor = os.open(
        runtime / ".benchmark-gateway.lock",
        os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW,
        0o600,
    )
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(descriptor)


def ensure_free(env: dict[str, str]) -> None:
    if invoke(
        [
            "ps",
            "-aq",
            "--filter",
            "label=com.docker.compose.project=" + PROJECT,
            "--filter",
            "label=com.docker.compose.service=" + SERVICE,
        ],
        env,
    ):
        raise GatewayError("a benchmark-gateway service already exists; preserve it")
    ensure_unique_alias(env, set())


def ensure_unique_alias(env: dict[str, str], owned: set[str]) -> None:
    endpoints = json.loads(
        invoke(["network", "inspect", NETWORK, "--format", "{{json .Containers}}"], env)
    )
    for identity in endpoints or {}:
        networks = json.loads(
            invoke(
                ["inspect", "--format", "{{json .NetworkSettings.Networks}}", identity],
                env,
            )
        )
        network = networks.get(NETWORK, {})
        aliases = (network.get("Aliases") or []) + (network.get("DNSNames") or [])
        if "gateway" in aliases and identity not in owned:
            raise GatewayError(
                "the private gateway alias is already occupied; preserve it"
            )


def owned_containers(env: dict[str, str]) -> list[str]:
    identities = invoke(
        [
            "ps",
            "-aq",
            "--no-trunc",
            "--filter",
            "label=io.canary.benchmark.session=" + env["CANARY_BENCHMARK_SESSION"],
        ],
        env,
    ).split()
    for identity in identities:
        if not re.fullmatch(r"[a-f0-9]{12,64}", identity):
            raise GatewayError("invalid container identity")
        metadata = json.loads(
            invoke(
                [
                    "inspect",
                    "--format",
                    '{"image":{{json .Image}},"labels":{{json .Config.Labels}}}',
                    identity,
                ],
                env,
            )
        )
        labels = metadata["labels"]
        expected = {
            "com.docker.compose.project": PROJECT,
            "com.docker.compose.service": SERVICE,
            "io.canary.benchmark.role": "private-gateway",
            "io.canary.benchmark.session": env["CANARY_BENCHMARK_SESSION"],
        }
        if metadata["image"] != env["CANARY_BENCHMARK_IMAGE"] or any(
            labels.get(key) != value for key, value in expected.items()
        ):
            raise GatewayError(
                "refusing to manage a container owned by another launcher"
            )
    return identities


def serve(env: dict[str, str]) -> None:
    with lease(Path(env["CANARY_GATEWAY_RUNTIME"])):
        ensure_no_unresolved(Path(env["CANARY_GATEWAY_RUNTIME"]))
        ensure_free(env)
        try:
            invoke(
                compose(
                    "create", "--no-recreate", "--no-build", "--pull", "never", SERVICE
                ),
                env,
            )
            identities = owned_containers(env)
            if len(identities) != 1:
                raise GatewayError(
                    "expected one owned gateway; refusing to adopt another service"
                )
            ensure_unique_alias(env, set(identities))
            invoke(["start", identities[0]], env)
            wait_healthy(identities[0], env)
            ensure_unique_alias(env, set(identities))
            print(
                "Private gateway ready at gateway:4000; no inference was sent. Ctrl+C stops it.",
                flush=True,
            )
            invoke(["wait", identities[0]], env)
            raise RuntimeError(
                "the private gateway exited; inspect its preserved evidence"
            )
        finally:
            cleanup(env)


def wait_healthy(identity: str, env: dict[str, str]) -> None:
    deadline = time.monotonic() + 120
    while True:
        state = json.loads(
            invoke(["inspect", "--format", "{{json .State}}", identity], env)
        )
        if (
            state["Status"] != "running"
            or state.get("Health", {}).get("Status") == "unhealthy"
        ):
            raise GatewayError("the private gateway stopped or failed its healthcheck")
        if state.get("Health", {}).get("Status") == "healthy":
            return
        if time.monotonic() >= deadline:
            raise GatewayError(
                "the private gateway did not become healthy within 120 seconds"
            )
        time.sleep(0.5)


def cleanup(env: dict[str, str]) -> None:
    with defer_stop():
        if journal_phase(env) in {"uncertain", "mutation_in_flight"}:
            raise GatewayError(
                "Docker outcome is uncertain; preserve the session for manual recovery"
            )
        for identity in owned_containers(env):
            try:
                logs = invoke(["logs", identity], env)
                path = Path(env["CANARY_GATEWAY_RUNTIME"]) / (
                    "benchmark-gateway-" + env["CANARY_BENCHMARK_SESSION"] + ".log"
                )
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, "w") as stream:
                    stream.write(logs)
                    stream.flush()
                    os.fsync(stream.fileno())
                sync_directory(path.parent)
            except Exception:  # noqa: BLE001 - preserve the CID if logs could not be saved
                stop_outcome = "completed"
                try:
                    invoke(["stop", "--time", "10", identity], env)
                except Exception as error:  # noqa: BLE001 - preserve the CID and classify, without raw diagnostics
                    stop_outcome = type(error).__name__
                if journal_phase(env) not in {"uncertain", "mutation_in_flight"}:
                    journal(
                        env,
                        "evidence_incomplete",
                        container_id=identity,
                        stop_outcome=stop_outcome,
                    )
                raise GatewayError(
                    "logs were not preserved; container retained for manual recovery"
                ) from None
            invoke(["rm", "--force", identity], env)
        if owned_containers(env):
            raise GatewayError("owned gateway still exists after cleanup")
        journal(env, "cleaned")


def stop(_number: int, _frame: Any) -> None:
    global _stop_requested
    if _defer_stop_depth:
        _stop_requested = True
        return
    raise KeyboardInterrupt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--revision", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    previous_term = signal.signal(signal.SIGTERM, stop)
    previous_int = signal.signal(signal.SIGINT, stop)
    env: dict[str, str] | None = None
    try:
        env = environment(args.runtime, args.policy, args.image, args.revision)
        invoke(compose("config", "--quiet"), env)
        if args.serve:
            serve(env)
        else:
            print("Compose configuration valid; no container or inference started.")
    except KeyboardInterrupt:
        confirmed = False
        try:
            confirmed = env is not None and journal_phase(env) == "cleaned"
        except Exception:  # noqa: BLE001 - failure to read a journal is not proof of cleanup
            confirmed = False
        if confirmed:
            parser.exit(130, "Private gateway stopped; owned containers cleaned.\n")
        recovery = "" if env is None else " Session: " + env["CANARY_BENCHMARK_SESSION"]
        parser.exit(
            130,
            "Private gateway interrupted; cleanup unconfirmed, inspect the session journal."
            + recovery
            + "\n",
        )
    except GatewayError as error:
        recovery = "" if env is None else " Session: " + env["CANARY_BENCHMARK_SESSION"]
        parser.exit(1, str(error) + recovery + "\n")
    except Exception as error:  # noqa: BLE001 - subprocess errors can contain secrets
        recovery = "" if env is None else " Session: " + env["CANARY_BENCHMARK_SESSION"]
        parser.exit(
            1,
            f"Private gateway stopped: {type(error).__name__}; check private local diagnostics."
            + recovery
            + "\n",
        )
    finally:
        signal.signal(signal.SIGTERM, previous_term)
        signal.signal(signal.SIGINT, previous_int)


if __name__ == "__main__":
    main()
