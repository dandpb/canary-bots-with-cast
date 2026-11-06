"""Pinned Gemini function JSON schema on the wire; no external network."""

import asyncio
import json
import os
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from gateway_smoke import free_port
from openai import AsyncOpenAI

from canary_brain.gateway import GatewayConfiguration, GatewayProvider
from canary_brain.protocol import Observation
from canary_brain.provider import Prices
from canary_brain.recording import digest
from canary_brain.store import Store


def main():
    if "--inside" not in sys.argv:
        root = Path(__file__).resolve().parents[3]
        return subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--entrypoint",
                "python",
                "-v",
                f"{root}:/source:ro",
                "-e",
                "PYTHONPATH=/source/deployment/brain/src",
                "sha256:6b2498fa2e23faa4a23a99420fc47bc77a87f8e19e493fac80ff02e3ddb3ff48",
                "/source/deployment/brain/tools/gemini_gateway_smoke.py",
                "--inside",
            ],
            check=False,
        ).returncode
    calls = []

    class Upstream(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            calls.append(
                json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            )
            value = {
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [
                                {
                                    "functionCall": {
                                        "name": "choose_action",
                                        "args": {"candidate_id": "resupply"},
                                    }
                                }
                            ],
                        },
                        "finishReason": "STOP",
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 10,
                    "candidatesTokenCount": 2,
                    "thoughtsTokenCount": 5,
                    "totalTokenCount": 17,
                },
                "modelVersion": "gemini-3.5-flash-lite",
            }
            raw = json.dumps(value).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    threading.Thread(target=upstream.serve_forever, daemon=True).start()
    try:
        with tempfile.TemporaryDirectory(prefix="gemini-wire-") as directory:
            work = Path(directory)
            port = free_port()
            config = {
                "model_list": [
                    {
                        "model_name": "gemini-fixture",
                        "litellm_params": {
                            "model": "gemini/gemini-3.5-flash-lite",
                            "api_base": f"http://127.0.0.1:{upstream.server_port}",
                            "api_key": "synthetic-only",
                            "num_retries": 0,
                        },
                        "model_info": {"id": "gemini-deployment"},
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
            policy = work / "gateway.yaml"
            policy.write_text(json.dumps(config, sort_keys=True, separators=(",", ":")))
            with (work / "proxy.log").open("w") as log:
                process = subprocess.Popen(
                    [
                        "litellm",
                        "--config",
                        str(policy),
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(port),
                    ],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env={
                        **os.environ,
                        "LITELLM_WORKER_KEY": "synthetic-worker",
                        "LITELLM_MASTER_KEY": "sk-" + secrets.token_hex(32),
                        "CANARY_GATEWAY_CONFIG": str(policy),
                    },
                )
                try:
                    deadline = time.monotonic() + 45
                    while True:
                        try:
                            urllib.request.urlopen(
                                f"http://127.0.0.1:{port}/health/readiness", timeout=1
                            ).close()
                            break
                        except OSError:
                            assert (
                                process.poll() is None and time.monotonic() < deadline
                            ), "Gateway startup failed"
                            time.sleep(0.2)

                    async def exercise():
                        gateway = GatewayConfiguration(
                            base_url=f"http://127.0.0.1:{port}/v1",
                            alias="gemini-fixture",
                            effective_model="gemini-3.5-flash-lite",
                            deployment_id="gemini-deployment",
                            provider="gemini",
                            upstream_model="gemini/gemini-3.5-flash-lite",
                            version="1.108.0",
                            configuration_sha256=digest(config),
                            prices=Prices(
                                version="offline",
                                input_nanousd=7,
                                cached_nanousd=2,
                                cache_write_nanousd=11,
                                output_nanousd=13,
                            ),
                        )
                        ledger = Store(work / "ledger.sqlite3")
                        async with AsyncOpenAI(
                            base_url=gateway.base_url,
                            api_key="synthetic-worker",
                            max_retries=0,
                        ) as client:
                            adapter = GatewayProvider(
                                ledger, client, gateway=gateway, decision_timeout=20
                            )
                            observation = Observation.model_validate(
                                {
                                    "version": 1,
                                    "type": "observation",
                                    "world": "fixture",
                                    "sequence": 1,
                                    "captured_ms": 0,
                                    "lease": "fixture",
                                    "objective_generation": 1,
                                    "bot": {
                                        "id": 7,
                                        "name": "fixture",
                                        "level": 20,
                                        "vocation": 4,
                                        "state": "HUNTING",
                                        "position": [100, 100, 7],
                                        "health": 30,
                                        "mana": 30,
                                        "potions": 1,
                                        "xp": 98800,
                                        "alive": True,
                                    },
                                    "actions": [
                                        {
                                            "id": "continue",
                                            "action": "continue",
                                            "description": "continue",
                                            "ttl_ms": 20000,
                                        },
                                        {
                                            "id": "resupply",
                                            "action": "resupply",
                                            "description": "resupply",
                                            "ttl_ms": 20000,
                                        },
                                    ],
                                }
                            )
                            assert await adapter.decide(observation, {}) == "resupply"
                        assert len(calls) == 1
                        declaration = calls[0]["tools"][0]["functionDeclarations"][0]
                        schema = declaration["parametersJsonSchema"]
                        assert schema == {
                            "type": "object",
                            "properties": {
                                "candidate_id": {
                                    "type": "string",
                                    "enum": ["continue", "resupply"],
                                }
                            },
                            "required": ["candidate_id"],
                            "additionalProperties": False,
                        }
                        assert calls[0]["toolConfig"]["functionCallingConfig"] == {
                            "mode": "ANY",
                            "allowed_function_names": ["choose_action"],
                        }
                        assert calls[0]["generationConfig"]["max_output_tokens"] == 256
                        assert (
                            ledger.budget()["spent"] == 161
                            and ledger.budget()["reserved"] == 0
                        )
                        print(
                            json.dumps(
                                {
                                    "checks": "passed",
                                    "upstream_requests": len(calls),
                                    "native_body": calls[0],
                                    "spent_fixture_nanousd": 161,
                                    "reasoning_output_tokens": 5,
                                }
                            )
                        )

                    asyncio.run(exercise())
                finally:
                    process.terminate()
                    process.wait(timeout=10)
    finally:
        upstream.shutdown()
        upstream.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
