import asyncio
import json

from canary_brain.benchmark import demo
from canary_brain.operator_http import OperatorServer
from canary_brain.recording import ReplayReader


async def test_standalone_viewer_serves_history_without_exposing_game_commands(
    tmp_path,
):
    recording = tmp_path / "demo.db"
    runs = demo(recording)
    api = OperatorServer(None, 0, ReplayReader(recording))
    await api.start()

    async def request(path, method="GET", host=None):
        reader, writer = await asyncio.open_connection("127.0.0.1", api.port)
        writer.write(
            f"{method} {path} HTTP/1.1\r\nHost: {host or f'localhost:{api.port}'}\r\nContent-Length: 0\r\n\r\n".encode()
        )
        await writer.drain()
        response = await reader.read()
        writer.close()
        await writer.wait_closed()
        return response

    try:
        response = await request("/api/replays")
        assert b"200 Response" in response
        assert len(json.loads(response.split(b"\r\n\r\n")[1])["data"]) == 2
        response = await request(f"/api/replay/seek?run={runs[0]}&at=350000")
        assert (
            json.loads(response.split(b"\r\n\r\n")[1])["data"]["sample"]["data"]["bot"][
                "level"
            ]
            == 9
        )
        assert b"405 Response" in await request("/api/command", "POST")
        assert b"404 Response" in await request("/api/state")
        assert b"403 Response" in await request("/api/replays", host="attacker.example")
        assert b"400 Response" in await request("/api/replay/seek?run=missing&at=-1")
        assert b"200 Response" in await request("/replay")
        assert b"204 Response" in await request("/favicon.ico")
    finally:
        await api.close()
