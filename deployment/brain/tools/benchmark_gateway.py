"""Serve an inference-only gateway; never sends an inference request."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import signal
import subprocess
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


class GatewayError(ValueError):
    """A static operator message containing no subprocess/credential data."""


def invoke(arguments: list[str], environment: dict[str, str]) -> str:
    # Compose errors may contain expanded credentials; never echo captured output.
    completed = subprocess.run(
        ["docker", *arguments],
        env=environment,
        check=True,
        capture_output=True,
        text=True,
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
        for kind in ("provider", "worker", "ui")
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
    pending = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
    try:
        for identity in owned_containers(env):
            try:
                logs = invoke(["logs", identity], env)
                path = Path(env["CANARY_GATEWAY_RUNTIME"]) / (
                    "benchmark-gateway-" + env["CANARY_BENCHMARK_SESSION"] + ".log"
                )
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, "w") as stream:
                    stream.write(logs)
            finally:
                invoke(["rm", "--force", identity], env)
        if owned_containers(env):
            raise GatewayError("owned gateway still exists after cleanup")
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, pending)


def stop(_number: int, _frame: Any) -> None:
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
    signal.signal(signal.SIGTERM, stop)
    try:
        env = environment(args.runtime, args.policy, args.image, args.revision)
        invoke(compose("config", "--quiet"), env)
        if args.serve:
            serve(env)
        else:
            print("Compose configuration valid; no container or inference started.")
    except KeyboardInterrupt:
        parser.exit(130, "Private gateway stopped; owned containers cleaned.\n")
    except GatewayError as error:
        parser.exit(1, str(error) + "\n")
    except Exception as error:  # noqa: BLE001 - subprocess errors can contain secrets
        parser.exit(
            1,
            f"Private gateway stopped: {type(error).__name__}; check private local diagnostics.\n",
        )


if __name__ == "__main__":
    main()
