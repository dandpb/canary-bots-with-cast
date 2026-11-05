"""Optional same-origin local console; no provider or game credentials are exposed."""

import asyncio
import json
import secrets
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .recording import ReplayReader
from .replay import summary
from .supervision import Supervisor


class OperatorServer:
    def __init__(
        self,
        supervisor: Supervisor | None,
        port: int,
        replay: ReplayReader | None = None,
    ) -> None:
        self.supervisor, self.port = supervisor, port
        self.token = secrets.token_urlsafe(32)
        self.server: asyncio.Server | None = None
        self.busy: set[int] = set()
        self.connections = 0
        self.replay = replay

    async def start(self, host: str = "127.0.0.1") -> None:
        self.server = await asyncio.start_server(
            self.handle, host, self.port, limit=8192
        )
        self.port = int(self.server.sockets[0].getsockname()[1])

    async def close(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def handle(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        self.connections += 1
        try:
            if self.connections > 16:
                await self.respond(
                    writer, 429, {"error": "Muitas conexões; tente novamente."}
                )
                return
            async with asyncio.timeout(50):
                await self.request(reader, writer)
        except (TimeoutError, ConnectionError, asyncio.IncompleteReadError):
            pass
        except (ValueError, UnicodeError, asyncio.LimitOverrunError):
            await self.respond(writer, 400, {"error": "Requisição inválida."})
        except Exception:  # noqa: BLE001 - redact provider/configuration errors at the HTTP boundary
            # Never return exception text that might contain provider/configuration data.
            await self.respond(
                writer, 500, {"error": "O painel não concluiu a solicitação."}
            )
        finally:
            self.connections -= 1
            writer.close()
            try:
                await writer.wait_closed()
            except ConnectionError:
                pass

    async def request(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        header = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 3)
        if len(header) > 8192:
            raise ValueError("headers too large")
        lines = header.decode("ascii").split("\r\n")
        method, path, version = lines[0].split(" ")
        if version != "HTTP/1.1":
            raise ValueError("HTTP/1.1 required")
        headers = {}
        for line in lines[1:]:
            if not line:
                continue
            key, value = line.split(":", 1)
            key = key.lower()
            if key in headers:
                raise ValueError("duplicate header")
            headers[key] = value.strip()
        hosts = {f"127.0.0.1:{self.port}", f"localhost:{self.port}"}
        if headers.get("host") not in hosts:
            await self.respond(
                writer, 403, {"error": "Use o endereço local do painel."}
            )
            return
        if "transfer-encoding" in headers:
            raise ValueError("chunked requests not supported")
        if method == "GET":
            parsed = urlsplit(path)
            if path == "/favicon.ico":
                await self.respond(writer, 204, b"", "image/x-icon")
            elif parsed.path.startswith("/api/replay"):
                await self.replay_request(writer, parsed.path, parse_qs(parsed.query))
            elif path == "/api/state" and self.supervisor is not None:
                await self.respond(
                    writer,
                    200,
                    {
                        **self.supervisor.view(),
                        "token": self.token,
                        "chat_busy": sorted(self.busy),
                    },
                )
            elif path in {
                "/",
                "/app.js",
                "/style.css",
                "/replay",
                "/replay.js",
                "/replay.css",
            }:
                if path == "/" and self.supervisor is None:
                    path = "/replay"
                filename = (
                    "index.html"
                    if path == "/"
                    else "replay.html"
                    if path == "/replay"
                    else path[1:]
                )
                body = (Path(__file__).parent / "dashboard" / filename).read_bytes()
                content_type = {
                    "/": "text/html",
                    "/app.js": "text/javascript",
                    "/style.css": "text/css",
                    "/replay": "text/html",
                    "/replay.js": "text/javascript",
                    "/replay.css": "text/css",
                }[path]
                await self.respond(writer, 200, body, content_type)
            else:
                await self.respond(writer, 404, {"error": "Página não encontrada."})
            return
        if method != "POST" or path != "/api/command" or self.supervisor is None:
            await self.respond(writer, 405, {"error": "Método não permitido."})
            return
        origins = {f"http://{host}" for host in hosts}
        if headers.get("origin") not in origins or not secrets.compare_digest(
            headers.get("x-operator-token", ""), self.token
        ):
            await self.respond(
                writer, 403, {"error": "Atualize o painel e tente novamente."}
            )
            return
        length = int(headers.get("content-length", "0"))
        if (
            not 0 < length <= 4096
            or headers.get("content-type", "").split(";")[0] != "application/json"
        ):
            raise ValueError("bounded JSON required")
        data = json.loads(await asyncio.wait_for(reader.readexactly(length), 3))
        if (
            not isinstance(data, dict)
            or type(data.get("bot")) is not int
            or not isinstance(data.get("operation"), str)
        ):
            raise ValueError("invalid command")
        bot, operation = data["bot"], data["operation"]
        try:
            if operation == "chat":
                if bot in self.busy:
                    await self.respond(
                        writer, 409, {"error": "O bot já está respondendo; aguarde."}
                    )
                    return
                if type(data.get("act", False)) is not bool or not isinstance(
                    data.get("text"), str
                ):
                    raise ValueError("Mensagem inválida.")
                self.busy.add(bot)
                try:
                    result = await self.supervisor.chat(
                        bot, data["text"], data.get("act", False)
                    )
                finally:
                    self.busy.discard(bot)
            else:
                result = self.supervisor.command(bot, operation, data)
            await self.respond(writer, 200, result)
        except ValueError as error:
            await self.respond(writer, 409, {"error": str(error)})

    async def replay_request(
        self, writer: asyncio.StreamWriter, path: str, query: dict[str, list[str]]
    ) -> None:
        if self.replay is None:
            await self.respond(writer, 404, {"error": "Gravação não habilitada."})
            return

        def value(name: str, default: str = "") -> str:
            values = query.get(name, [default])
            if len(values) != 1 or len(values[0]) > 128:
                raise ValueError("invalid replay query")
            return values[0]

        reader = self.replay
        try:
            if path == "/api/replays":
                result: Any = await asyncio.to_thread(
                    reader.runs, int(value("limit", "100"))
                )
            else:
                run = value("run")
                if path == "/api/replay":
                    result = await asyncio.to_thread(reader.run, run)
                elif path == "/api/replay/events":
                    result = await asyncio.to_thread(
                        reader.events,
                        run,
                        int(value("after", "0")),
                        int(value("limit", "500")),
                    )
                elif path == "/api/replay/seek":
                    result = await asyncio.to_thread(
                        reader.seek, run, int(value("at", "0"))
                    )
                elif path == "/api/replay/track":
                    result = await asyncio.to_thread(reader.track, run)
                elif path == "/api/replay/timeline":
                    result = await asyncio.to_thread(
                        reader.timeline, run, int(value("at", "0"))
                    )
                elif path == "/api/replay/summary":
                    result = await asyncio.to_thread(summary, reader, run)
                else:
                    await self.respond(writer, 404, {"error": "Página não encontrada."})
                    return
            await self.respond(writer, 200, {"data": result})
        except ValueError:
            await self.respond(
                writer, 400, {"error": "Gravação ou intervalo inválido."}
            )

    async def respond(
        self,
        writer: asyncio.StreamWriter,
        status: int,
        body: dict[str, Any] | bytes,
        content_type: str = "application/json",
    ) -> None:
        payload = (
            body
            if isinstance(body, bytes)
            else json.dumps(body, ensure_ascii=False).encode()
        )
        headers = (
            f"HTTP/1.1 {status} Response\r\nContent-Type: {content_type}; charset=utf-8\r\n"
            f"Content-Length: {len(payload)}\r\nConnection: close\r\nCache-Control: no-store\r\n"
            "X-Content-Type-Options: nosniff\r\nX-Frame-Options: DENY\r\n"
            "Referrer-Policy: no-referrer\r\n"
            "Content-Security-Policy: default-src 'self'; style-src 'self'; script-src 'self'; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'\r\n\r\n"
        )
        writer.write(headers.encode() + payload)
        await writer.drain()
