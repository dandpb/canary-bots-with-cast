"""Actual proxy/Router/SDK boundary with synthetic concurrent routing changes."""

import asyncio
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from openai import APIStatusError, AsyncOpenAI

from canary_brain.gateway import GatewayConfiguration, GatewayProvider
from canary_brain.provider import Prices
from canary_brain.store import Store


def free_port():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return server.getsockname()[1]


def main():
    calls = []

    class Upstream(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append((body["model"], self.headers.get("Authorization")))
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

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="gateway-routing-") as directory:
            root = Path(directory)
            base = f"http://127.0.0.1:{upstream.server_port}/v1"
            deployment = {
                "model_name": "test-a",
                "litellm_params": {
                    "model": "openai/model-a",
                    "api_base": base,
                    "litellm_credential_name": "fixture",
                    "num_retries": 0,
                },
                "model_info": {"id": "deployment-a"},
            }
            config = {
                "model_list": [deployment],
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
                    "custom_auth": "boundary_fixture.authenticate",
                    "custom_auth_settings": {"mode": "auto"},
                    "master_key": "os.environ/LITELLM_MASTER_KEY",
                },
            }
            raw = json.dumps(config).encode()
            (root / "gateway.json").write_bytes(raw)
            # Mutation occurs after real application auth has snapshotted the pin,
            # but before LiteLLM's actual Router makes its deployment selection.
            fixture = """
import json, os
from pathlib import Path
import litellm
from litellm.types.router import Deployment
from litellm.types.utils import CredentialItem
from canary_brain import gateway_policy

async def authenticate(request, api_key):
    from litellm.proxy.proxy_server import llm_router
    original=json.loads(Path(os.environ['CANARY_GATEWAY_CONFIG']).read_text())['model_list'][0]
    for deployment in list(llm_router.model_list):
        llm_router.delete_deployment(deployment['model_info']['id'])
    llm_router.add_deployment(Deployment(**original))
    litellm.credential_list=[CredentialItem(credential_name='fixture',credential_values={'api_key':'synthetic-before'},credential_info={})]
    result=await gateway_policy.authenticate(request,api_key)
    mode=request.headers.get('x-fixture-mutation','valid')
    if mode=='credential-value':
        litellm.credential_list=[CredentialItem(credential_name='fixture',credential_values={'api_key':'synthetic-after','api_base':'https://rogue.invalid'},credential_info={})]
    elif mode!='valid':
        rogue=json.loads(json.dumps(original))
        if mode=='model': rogue['litellm_params']['model']='openai/rogue'
        elif mode=='id': rogue['model_info']['id']='rogue-id'
        elif mode=='api_base': rogue['litellm_params']['api_base']='https://rogue.invalid/v1'
        elif mode=='credential-reference': rogue['litellm_params']['litellm_credential_name']='rogue-credential'
        elif mode=='retry': rogue['litellm_params']['num_retries']=1
        else: raise ValueError('unknown fixture mutation')
        llm_router.delete_deployment('deployment-a')
        llm_router.add_deployment(Deployment(**rogue))
    return result

"""
            (root / "boundary_fixture.py").write_text(fixture)
            port = free_port()
            environment = {
                **os.environ,
                "PYTHONPATH": str(root) + os.pathsep + os.environ.get("PYTHONPATH", ""),
                "LITELLM_WORKER_KEY": "sk-fixture-worker",
                "LITELLM_MASTER_KEY": "sk-" + secrets.token_hex(32),
                "CANARY_GATEWAY_CONFIG": str(root / "gateway.json"),
            }
            with (root / "proxy.log").open("w") as log:
                process = subprocess.Popen(
                    [
                        "litellm",
                        "--config",
                        str(root / "gateway.json"),
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(port),
                    ],
                    env=environment,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                try:
                    for _ in range(150):
                        try:
                            urllib.request.urlopen(
                                f"http://127.0.0.1:{port}/health/readiness", timeout=1
                            )
                            break
                        except OSError:
                            time.sleep(0.1)
                    else:
                        raise RuntimeError("Proxy readiness failed")

                    async def exercise():
                        store = Store(root / "ledger.sqlite3")
                        gateway = GatewayConfiguration(
                            base_url=f"http://127.0.0.1:{port}/v1",
                            alias="test-a",
                            effective_model="model-a",
                            deployment_id="deployment-a",
                            provider="openai",
                            version="1.108.0",
                            configuration_sha256=hashlib.sha256(raw).hexdigest(),
                            prices=Prices(
                                version="synthetic",
                                input_nanousd=1,
                                cached_nanousd=1,
                                cache_write_nanousd=1,
                                output_nanousd=2,
                            ),
                        )
                        denied = []
                        for mode in (
                            "valid",
                            "model",
                            "id",
                            "api_base",
                            "credential-reference",
                            "retry",
                            "credential-value",
                        ):
                            async with AsyncOpenAI(
                                api_key="sk-fixture-worker",
                                base_url=gateway.base_url,
                                max_retries=0,
                                default_headers={"x-fixture-mutation": mode},
                            ) as client:
                                provider = GatewayProvider(
                                    store, client, gateway=gateway
                                )
                                before = len(calls)
                                try:
                                    await provider._request(
                                        "responses",
                                        {"input": "hello", "max_output_tokens": 4},
                                        15,
                                    )
                                except APIStatusError:
                                    assert mode not in {"valid", "credential-value"}, (
                                        mode
                                    )
                                    assert len(calls) == before, (mode, calls)
                                    denied.append(mode)
                                else:
                                    assert mode in {"valid", "credential-value"}, mode
                                    assert len(calls) == before + 1 and calls[-1] == (
                                        "model-a",
                                        "Bearer synthetic-before",
                                    ), calls
                        assert len(denied) == 5
                        with store.connection() as db:
                            unsettled = db.execute(
                                "SELECT COUNT(*) FROM requests WHERE spent IS NULL"
                            ).fetchone()[0]
                        assert unsettled == 5 and store.budget()["spent"] == 28
                        return {
                            "denied_before_upstream": denied,
                            "safe_upstream_calls": len(calls),
                            "credential_snapshot_preserved": True,
                            "settled_fixture_nanousd": 28,
                            "unsettled_attempts": unsettled,
                        }

                    print(json.dumps(asyncio.run(exercise()), indent=2))
                except Exception:
                    print((root / "proxy.log").read_text()[-5000:], file=sys.stderr)
                    raise
                finally:
                    process.terminate()
                    process.wait(timeout=15)
    finally:
        upstream.shutdown()
        upstream.server_close()
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
