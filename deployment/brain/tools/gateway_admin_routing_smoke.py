"""Isolated real LiteLLM/PG administration while benchmark requests are pending."""

import asyncio
import hashlib
import json
import os
import socket
import subprocess
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
from openai import APIStatusError, AsyncOpenAI

from canary_brain.gateway import GatewayConfiguration, GatewayProvider
from canary_brain.provider import Prices
from canary_brain.store import Store


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    assert os.environ.get("CANARY_FAKE_ADMIN_DB") == "enabled"
    assert (
        os.environ["DATABASE_URL"]
        == "postgresql://postgres:synthetic-only@127.0.0.1:5432/postgres"
    )
    calls = []

    class Fake(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append(body["model"])
            data = json.dumps(
                {
                    "id": "resp_fixture",
                    "object": "response",
                    "created_at": 1,
                    "model": body["model"],
                    "status": "completed",
                    "output": [],
                    "usage": {
                        "input_tokens": 10,
                        "output_tokens": 2,
                        "total_tokens": 12,
                    },
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="gateway-admin-routing-") as directory:
            root = Path(directory)
            model = {
                "model_name": "test-a",
                "litellm_params": {
                    "model": "openai/model-a",
                    "api_base": f"http://127.0.0.1:{upstream.server_port}/v1",
                    "api_key": "synthetic-only",
                    "num_retries": 0,
                },
                "model_info": {"id": "static-a"},
            }
            config = {
                "model_list": [model],
                "router_settings": {
                    "num_retries": 0,
                    "max_fallbacks": 0,
                    "fallbacks": [],
                    "cache_responses": False,
                },
                "litellm_settings": {
                    "num_retries": 0,
                    "fallbacks": [],
                    "cache": False,
                    "drop_params": False,
                    "turn_off_message_logging": True,
                },
                "general_settings": {
                    "custom_auth": "admin_fixture.authenticate",
                    "custom_auth_settings": {"mode": "auto"},
                    "master_key": "os.environ/LITELLM_MASTER_KEY",
                },
            }
            raw = json.dumps(config).encode()
            (root / "config.json").write_bytes(raw)
            (root / "admin_fixture.py").write_text("""
import asyncio, os
from pathlib import Path
from canary_brain import gateway_policy
async def authenticate(request, api_key):
    result=await gateway_policy.authenticate(request,api_key)
    stage=request.headers.get('x-fixture-pause')
    if stage:
        folder=Path(os.environ['CANARY_FAKE_GATE'])
        (folder/(stage+'.ready')).write_text('ready')
        while not (folder/(stage+'.release')).exists(): await asyncio.sleep(.01)
    return result
""")
            proxy_port = port()
            env = {
                **os.environ,
                "PYTHONPATH": str(root) + os.pathsep + os.environ.get("PYTHONPATH", ""),
                "CANARY_GATEWAY_CONFIG": str(root / "config.json"),
                "CANARY_FAKE_GATE": str(root),
                "LITELLM_MASTER_KEY": "sk-synthetic-admin",
                "LITELLM_WORKER_KEY": "sk-synthetic-worker",
                "LITELLM_SALT_KEY": "synthetic-salt",
                "STORE_MODEL_IN_DB": "True",
                "LITELLM_LOCAL_MODEL_COST_MAP": "True",
            }
            with (root / "proxy.log").open("w") as log:
                proxy = subprocess.Popen(
                    [
                        "litellm",
                        "--config",
                        str(root / "config.json"),
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(proxy_port),
                    ],
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                try:
                    for _ in range(300):
                        try:
                            urllib.request.urlopen(
                                f"http://127.0.0.1:{proxy_port}/health/readiness",
                                timeout=1,
                            )
                            break
                        except OSError:
                            time.sleep(0.1)
                    else:
                        raise RuntimeError("proxy readiness failed")

                    async def exercise():
                        store = Store(root / "ledger.sqlite3")
                        gateway = GatewayConfiguration(
                            base_url=f"http://127.0.0.1:{proxy_port}/v1",
                            alias="test-a",
                            effective_model="model-a",
                            deployment_id="static-a",
                            provider="openai",
                            version="1.108.0",
                            configuration_sha256=hashlib.sha256(raw).hexdigest(),
                            prices=Prices(
                                version="fixture",
                                input_nanousd=1,
                                cached_nanousd=1,
                                cache_write_nanousd=1,
                                output_nanousd=2,
                            ),
                        )

                        async def send(stage=None):
                            async with AsyncOpenAI(
                                api_key="sk-synthetic-worker",
                                base_url=gateway.base_url,
                                max_retries=0,
                                default_headers={"x-fixture-pause": stage}
                                if stage
                                else {},
                            ) as client:
                                provider = GatewayProvider(
                                    store, client, gateway=gateway
                                )
                                try:
                                    await provider._request(
                                        "responses",
                                        {"input": "hello", "max_output_tokens": 4},
                                        30,
                                    )
                                except APIStatusError as error:
                                    assert error.status_code == 409, error.status_code
                                    return "denied"
                                return "expected"

                        async with httpx.AsyncClient(
                            base_url=f"http://127.0.0.1:{proxy_port}",
                            headers={"Authorization": "Bearer sk-synthetic-admin"},
                            timeout=20,
                        ) as admin:

                            async def request(method, path, body=None):
                                response = await admin.request(method, path, json=body)
                                assert response.status_code == 200, (
                                    path,
                                    response.status_code,
                                    response.text,
                                )
                                return response.json()

                            async def pause(stage):
                                pending = asyncio.create_task(send(stage))
                                for _ in range(300):
                                    if (root / (stage + ".ready")).exists():
                                        return pending
                                    if pending.done():
                                        await pending
                                        raise AssertionError("worker did not pause")
                                    await asyncio.sleep(0.01)
                                raise AssertionError("worker auth pause timeout")

                            assert await send() == "expected"
                            pending = await pause("new")
                            rogue = json.loads(json.dumps(model))
                            rogue["litellm_params"]["model"] = "openai/rogue-one"
                            rogue["model_info"]["id"] = "database-rogue"
                            created = await request("POST", "/model/new", rogue)
                            model_info = await request("GET", "/model/info")
                            ids = [
                                r["model_info"]["id"]
                                for r in model_info["data"]
                                if r["litellm_params"]["model"] == "openai/rogue-one"
                            ]
                            assert len(ids) == 1, (created, model_info)
                            rogue_id = ids[0]
                            (root / "new.release").write_text("release")
                            results = [await pending]
                            results.extend([await send() for _ in range(23)])
                            assert "denied" in results, (
                                "random Router never selected DB duplicate"
                            )
                            assert set(calls) == {"model-a"}, calls
                            pending = await pause("update")
                            await request(
                                "PATCH",
                                f"/model/{rogue_id}/update",
                                {"litellm_params": {"model": "openai/rogue-two"}},
                            )
                            updated = await request("GET", "/model/info")
                            assert any(
                                r["litellm_params"]["model"] == "openai/rogue-two"
                                for r in updated["data"]
                            )
                            (root / "update.release").write_text("release")
                            results.append(await pending)
                            results.extend([await send() for _ in range(23)])
                            assert set(calls) == {"model-a"}, calls
                            pending = await pause("delete")
                            await request("POST", "/model/delete", {"id": rogue_id})
                            deleted = await request("GET", "/model/info")
                            assert not any(
                                r["model_info"]["id"] == rogue_id
                                for r in deleted["data"]
                            )
                            (root / "delete.release").write_text("release")
                            assert await pending == "expected"
                            assert set(calls) == {"model-a"}, calls
                            print(
                                json.dumps(
                                    {
                                        "real_admin_operations": [
                                            "model/new",
                                            "model/update",
                                            "model/delete",
                                        ],
                                        "db_alias_duplicates_observed": True,
                                        "selection_cases": len(results),
                                        "denied_before_upstream": results.count(
                                            "denied"
                                        ),
                                        "only_expected_upstream": True,
                                        "fake_upstream_calls": len(calls),
                                        "settled_fixture_nanousd": store.budget()[
                                            "spent"
                                        ],
                                    }
                                )
                            )

                    asyncio.run(exercise())
                except Exception:
                    print((root / "proxy.log").read_text()[-7000:])
                    raise
                finally:
                    proxy.terminate()
                    proxy.wait(timeout=20)
    finally:
        upstream.shutdown()
        upstream.server_close()
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
