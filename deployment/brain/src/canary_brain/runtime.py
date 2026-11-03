"""Private local IPC and process lifecycle. No public listener is created."""

import asyncio
import fcntl
import json
import os
import signal
import socket
import stat
import time
from pathlib import Path
from typing import Any, Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field

from .controller import Controller
from .provider import Provider
from .store import USD, Store
from .testing import FakeProvider


class Configuration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["shadow", "active"] = "shadow"
    provider: Literal["openai", "fake"] = "openai"
    socket_directory: Path
    state_file: Path
    budget_file: Path | None = None
    credential_file: Path | None = None
    bots: list[int] = Field(min_length=1, max_length=3)
    monthly_usd: int = Field(default=50, ge=1, le=50)
    decision_timeout: float = Field(default=1.2, ge=0.1, le=3)
    learning: bool = False
    exploration: float = Field(default=0.15, ge=0.05, le=0.5)


def read_credential(path: Path) -> str:
    if (
        path.is_symlink()
        or not path.is_file()
        or stat.S_IMODE(path.stat().st_mode) & 0o077
    ):
        raise ValueError("credential file must be private and must not be a symlink")
    for line in path.read_text().splitlines():
        name, separator, value = line.partition("=")
        if separator and name == "OPENAI_API_KEY" and value.startswith("sk-"):
            return value.strip()
    raise ValueError("credential file has no OpenAI key")


class DatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, controller: Controller, server: str) -> None:
        self.controller, self.server = controller, server
        self.tasks: set[asyncio.Task[None]] = set()

    def datagram_received(self, data: bytes, address: Any) -> None:
        if address != self.server or len(data) > 32768 or len(self.tasks) >= 32:
            return

        async def consume() -> None:
            try:
                packet = json.loads(data)
                if isinstance(packet, dict):
                    await self.controller.handle(packet)
            except (ValueError, KeyError, TypeError):
                pass

        task = asyncio.create_task(consume())
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)


async def run(configuration: Configuration) -> None:
    os.umask(0o077)
    directory = configuration.socket_directory
    if directory.is_symlink() or not directory.is_absolute():
        raise ValueError("private socket directory must be an absolute nonsymlink path")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    endpoint, server = directory / "worker.sock", str(directory / "server.sock")
    descriptor = os.open(
        directory / "worker.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
    )
    transport: asyncio.DatagramTransport | None = None
    controller: Controller | None = None
    client: AsyncOpenAI | None = None
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if endpoint.is_symlink() or (
            endpoint.exists() and not stat.S_ISSOCK(endpoint.stat().st_mode)
        ):
            raise ValueError("worker endpoint must be a socket")
        endpoint.unlink(missing_ok=True)
        store = Store(configuration.state_file, cap=configuration.monthly_usd * USD)
        ledger = Store(
            configuration.budget_file or configuration.state_file,
            cap=configuration.monthly_usd * USD,
        )
        if configuration.provider == "openai":
            if configuration.credential_file is None:
                raise ValueError("OpenAI provider requires a private credential file")
            client = AsyncOpenAI(
                api_key=read_credential(configuration.credential_file),
                max_retries=0,
                base_url="https://api.openai.com/v1",
                timeout=45,
            )
            provider: Provider | FakeProvider = Provider(
                ledger, client, configuration.decision_timeout
            )
        else:
            provider = FakeProvider()

        def send(packet: dict[str, Any]) -> None:
            encoded = json.dumps(
                packet, separators=(",", ":"), ensure_ascii=False
            ).encode()
            if transport is not None and len(encoded) <= 32768:
                transport.sendto(encoded, server)

        active_controller = Controller(
            store,
            provider,
            send,
            configuration.mode,
            set(configuration.bots),
            configuration.learning,
            configuration.exploration,
        )
        controller = active_controller
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: DatagramProtocol(active_controller, server),
            family=socket.AF_UNIX,
            local_addr=str(endpoint),
        )
        stopped = asyncio.Event()
        last_maintenance = time.monotonic()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stopped.set)
        while not stopped.is_set():
            if time.monotonic() - last_maintenance >= 60:
                store.prune()
                if ledger.path != store.path:
                    ledger.prune()
                last_maintenance = time.monotonic()
            if controller.world:
                send({"version": 1, "type": "heartbeat", "world": controller.world})
                controller.reconcile()
            try:
                await asyncio.wait_for(stopped.wait(), timeout=1)
            except TimeoutError:
                pass
        await asyncio.gather(*protocol.tasks, return_exceptions=True)
    finally:
        if controller is not None:
            await controller.close()
        if transport is not None:
            transport.close()
            endpoint.unlink(missing_ok=True)
        if client is not None:
            await client.close()
        os.close(descriptor)
