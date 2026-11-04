"""Optional same-origin local console; no provider or game credentials are exposed."""

import asyncio
import json
import secrets
from pathlib import Path
from typing import Any

from .supervision import Supervisor


class OperatorServer:
    def __init__(self, supervisor: Supervisor, port: int) -> None:
        self.supervisor, self.port = supervisor, port
        self.token = secrets.token_urlsafe(32)
        self.server: asyncio.Server | None = None
        self.busy: set[int] = set()
        self.connections = 0

    async def start(self, host: str = "127.0.0.1") -> None:
        self.server = await asyncio.start_server(
            self.handle, host, self.port, limit=8192
        )

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
            if path == "/api/state":
                await self.respond(
                    writer,
                    200,
                    {
                        **self.supervisor.view(),
                        "token": self.token,
                        "chat_busy": sorted(self.busy),
                    },
                )
            elif path in {"/", "/app.js", "/style.css"}:
                filename = "index.html" if path == "/" else path[1:]
                body = (Path(__file__).parent / "dashboard" / filename).read_bytes()
                content_type = {
                    "/": "text/html",
                    "/app.js": "text/javascript",
                    "/style.css": "text/css",
                }[path]
                await self.respond(writer, 200, body, content_type)
            else:
                await self.respond(writer, 404, {"error": "Página não encontrada."})
            return
        if method != "POST" or path != "/api/command":
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
