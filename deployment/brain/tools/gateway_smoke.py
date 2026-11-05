"""Real pinned LiteLLM + a local fake upstream. Never contacts a real model."""

import asyncio
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from canary_brain.gateway import GatewayConfiguration, GatewayProvider
from canary_brain.provider import Prices
from canary_brain.recording import digest
from canary_brain.store import Store
from openai import APIStatusError, AsyncOpenAI


def free_port():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return server.getsockname()[1]


def main():
    if "--inside" not in sys.argv:
        source = Path(__file__).resolve().parents[3]
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--entrypoint",
                "python",
                "-v",
                f"{source}:/source:ro",
                "-e",
                "PYTHONPATH=/source/deployment/brain/src",
                "canary-litellm:1.108.0",
                "/source/deployment/brain/tools/gateway_smoke.py",
                "--inside",
            ],
            check=True,
        )
        return
    counts = []

    class Upstream(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            counts.append(body["model"])
            fail = "FAIL_UPSTREAM" in json.dumps(body)
            result = (
                {"error": {"message": "fixture failure", "type": "server_error"}}
                if fail
                else {
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
            )
            encoded = json.dumps(result).encode()
            self.send_response(500 if fail else 200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    with tempfile.TemporaryDirectory(prefix="gateway-qa-") as tmp:
        root = Path(tmp)
        port = free_port()
        config = {
            "model_list": [
                {
                    "model_name": "test-a",
                    "litellm_params": {
                        "model": "openai/model-a",
                        "api_base": f"http://127.0.0.1:{upstream.server_port}/v1",
                        "api_key": "local-fixture",
                        "num_retries": 0,
                    },
                    "model_info": {
                        "id": "deployment-a",
                        "supported_endpoints": ["/v1/responses"],
                    },
                }
            ],
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
                "custom_auth": "gateway_policy.authenticate",
                "master_key": "os.environ/LITELLM_MASTER_KEY",
            },
        }
        raw = json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
        (root / "gateway.yaml").write_bytes(raw)
        log = (root / "gateway.log").open("w")
        environment = dict(
            os.environ,
            LITELLM_WORKER_KEY="sk-local-fixture",
            LITELLM_MASTER_KEY="sk-" + secrets.token_hex(32),
            CANARY_GATEWAY_CONFIG=str(root / "gateway.yaml"),
        )
        process = subprocess.Popen(
            [
                "litellm",
                "--config",
                str(root / "gateway.yaml"),
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
            deadline = time.monotonic() + 50
            while True:
                try:
                    urllib.request.urlopen(
                        f"http://127.0.0.1:{port}/health/readiness", timeout=1
                    ).close()
                    break
                except (OSError, urllib.error.URLError):
                    if process.poll() is not None or time.monotonic() > deadline:
                        log.flush()
                        raise RuntimeError(
                            (root / "gateway.log").read_text()[-5000:]
                        ) from None
                    time.sleep(0.2)

            async def exercise():
                gateway = GatewayConfiguration(
                    base_url=f"http://127.0.0.1:{port}/v1",
                    alias="test-a",
                    effective_model="model-a",
                    deployment_id="deployment-a",
                    provider="fake-upstream",
                    upstream_model="openai/model-a",
                    version="1.108.0",
                    configuration_sha256=digest(config),
                    prices=Prices(
                        version="fixture",
                        input_nanousd=1,
                        cached_nanousd=1,
                        cache_write_nanousd=1,
                        output_nanousd=2,
                    ),
                )
                async with AsyncOpenAI(
                    api_key="sk-local-fixture", base_url=gateway.base_url, max_retries=0
                ) as client:

                    class InspectProvider(GatewayProvider):
                        async def _transmit(self, endpoint, body):
                            data = await super()._transmit(endpoint, body)
                            if data["model"] == "unexpected-gateway-identity":
                                raise AssertionError(
                                    json.dumps(
                                        {
                                            "model": data.get("effective_model"),
                                            "gateway": data.get("gateway"),
                                        }
                                    )
                                )
                            return data

                    provider = InspectProvider(
                        Store(root / "budget.db"), client, gateway=gateway
                    )
                    result = await provider._request(
                        "responses", {"input": "hello", "max_output_tokens": 4}, 20
                    )
                    assert result["effective_model"] == "model-a"
                    assert counts == ["model-a"], counts
                    try:
                        await provider._request(
                            "responses",
                            {"input": "FAIL_UPSTREAM", "max_output_tokens": 4},
                            20,
                        )
                    except APIStatusError as error:
                        assert error.status_code == 500
                    else:
                        raise AssertionError(
                            "failing upstream must not be replaced with success"
                        )
                    assert counts == ["model-a", "model-a"], counts
                    assert provider.store.budget()["reserved"] > 0
                return {
                    "upstream_calls": len(counts),
                    "settled_nanousd": provider.store.budget()["spent"],
                    "unknown_liability_retained": True,
                }

            print(json.dumps(asyncio.run(exercise()), indent=2))
        finally:
            process.terminate()
            process.wait(timeout=20)
            log.close()
            upstream.shutdown()


if __name__ == "__main__":
    main()
