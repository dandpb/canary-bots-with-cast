"""Pinned Haiku route against local fake Messages upstream; no external network."""

import asyncio
import json
import os
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from gateway_smoke import free_port
from openai import APIStatusError, AsyncOpenAI

from canary_brain.gateway import GatewayConfiguration, GatewayProvider
from canary_brain.protocol import Observation
from canary_brain.provider import Prices
from canary_brain.recording import digest
from canary_brain.store import Store


def main():
    if "--inside" not in sys.argv:
        root = Path(__file__).resolve().parents[3]
        result = subprocess.run(
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
                "sha256:a0e9d7da7b36ff52f325f1f715123e77de91fa3b6676402c06f34f9312eccf62",
                "/source/deployment/brain/tools/haiku_gateway_smoke.py",
                "--inside",
            ],
            check=False,
        )
        raise SystemExit(result.returncode)
    calls = []

    class Upstream(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append({"path": self.path, "body": body})
            fail = "FAIL_UPSTREAM" in json.dumps(body)
            missing = "MISSING_USAGE" in json.dumps(body)
            value = {
                "id": "msg_fixture",
                "type": "message",
                "role": "assistant",
                "model": "claude-haiku-5-5",
                "stop_reason": "tool_use",
                "stop_sequence": None,
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_fixture",
                        "name": "choose_action",
                        "input": {"candidate_id": "resupply"},
                    }
                ],
                "usage": {
                    "input_tokens": 10,
                    "output_tokens": 2,
                    "cache_read_input_tokens": 3,
                    "cache_creation_input_tokens": 2,
                },
            }
            if missing:
                value.pop("usage")
            if fail:
                value = {
                    "type": "error",
                    "error": {"type": "api_error", "message": "local fixture failure"},
                }
            raw = json.dumps(value).encode()
            self.send_response(500 if fail else 200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    threading.Thread(target=upstream.serve_forever, daemon=True).start()
    with tempfile.TemporaryDirectory(prefix="haiku-qa-") as temporary:
        work = Path(temporary)
        port = free_port()
        config = {
            "model_list": [
                {
                    "model_name": "haiku-fixture",
                    "litellm_params": {
                        "model": "anthropic/claude-haiku-5-5",
                        "api_base": f"http://127.0.0.1:{upstream.server_port}",
                        "api_key": "sk-ant-local-fixture",
                        "num_retries": 0,
                    },
                    "model_info": {"id": "haiku-deployment"},
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
        (work / "gateway.yaml").write_text(
            json.dumps(config, sort_keys=True, separators=(",", ":"))
        )
        with (work / "gateway.log").open("w") as log:
            process = subprocess.Popen(
                [
                    "litellm",
                    "--config",
                    str(work / "gateway.yaml"),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                env={
                    **os.environ,
                    "LITELLM_WORKER_KEY": "sk-local-fixture",
                    "LITELLM_MASTER_KEY": "sk-" + secrets.token_hex(32),
                    "CANARY_GATEWAY_CONFIG": str(work / "gateway.yaml"),
                },
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
                            raise RuntimeError(
                                "local fixture proxy did not become ready"
                            ) from None
                        time.sleep(0.2)

                async def exercise():
                    gateway = GatewayConfiguration(
                        base_url=f"http://127.0.0.1:{port}/v1",
                        alias="haiku-fixture",
                        effective_model="claude-haiku-5-5",
                        deployment_id="haiku-deployment",
                        provider="anthropic",
                        upstream_model="anthropic/claude-haiku-5-5",
                        version="1.108.0",
                        configuration_sha256=digest(config),
                        reasoning=False,
                        prices=Prices(
                            version="unequal-offline-rates",
                            input_nanousd=7,
                            cached_nanousd=2,
                            cache_write_nanousd=11,
                            output_nanousd=13,
                        ),
                    )
                    ledger = Store(work / "ledger.sqlite3")
                    observed = []
                    async with AsyncOpenAI(
                        api_key="sk-local-fixture",
                        base_url=gateway.base_url,
                        max_retries=0,
                    ) as client:

                        class Inspect(GatewayProvider):
                            async def _transmit(self, endpoint, body):
                                data = await super()._transmit(endpoint, body)
                                observed.append(data)
                                return data

                        provider = Inspect(
                            ledger, client, gateway=gateway, decision_timeout=20
                        )
                        packet = Observation.model_validate(
                            {
                                "world": "offline",
                                "sequence": 1,
                                "captured_ms": 1,
                                "lease": "offline",
                                "objective_generation": 0,
                                "mode": "active",
                                "autonomous": True,
                                "bot": {
                                    "id": 7,
                                    "name": "fixture",
                                    "level": 20,
                                    "vocation": 4,
                                    "state": "IDLE",
                                    "position": [1, 2, 7],
                                    "health": 100,
                                    "mana": 100,
                                    "potions": 2,
                                    "xp": 98800,
                                    "alive": True,
                                },
                                "actions": [
                                    {
                                        "id": "continue",
                                        "action": "continue",
                                        "description": "continue",
                                        "ttl_ms": 30000,
                                    },
                                    {
                                        "id": "resupply",
                                        "action": "resupply",
                                        "description": "resupply",
                                        "ttl_ms": 30000,
                                    },
                                ],
                            }
                        )
                        assert await provider.decide(packet) == "resupply"
                        assert len(calls) == 1, calls
                        wire = calls[0]
                        body = wire["body"]
                        tool = body["tools"][0]
                        assert wire["path"] == "/v1/messages", wire["path"]
                        assert body["model"] == "claude-haiku-5-5"
                        assert body["max_tokens"] == 256, body
                        assert (
                            body["tool_choice"]["type"] == "tool"
                            and body["tool_choice"]["name"] == "choose_action"
                        ), body
                        assert (
                            body["tool_choice"].get("disable_parallel_tool_use") is True
                        ), body["tool_choice"]
                        assert tool["input_schema"]["properties"]["candidate_id"][
                            "enum"
                        ] == ["continue", "resupply"], tool
                        native_strict = tool.get("strict") is True
                        usage = observed[-1]["usage"]
                        assert (
                            usage["input_tokens"] == 15 and usage["output_tokens"] == 2
                        ), usage
                        assert usage["input_tokens_details"]["cached_tokens"] == 3, (
                            usage
                        )
                        assert (
                            usage["input_tokens_details"]["cache_write_tokens"] == 2
                        ), usage
                        assert ledger.budget()["spent"] == 124, ledger.budget()
                        for marker in ["MISSING_USAGE", "FAIL_UPSTREAM"]:
                            provider.backoff.clear()
                            try:
                                await provider._request(
                                    "responses",
                                    {"input": marker, "max_output_tokens": 256},
                                    20,
                                )
                            except (TypeError, APIStatusError):
                                pass
                            else:
                                raise AssertionError(
                                    "fault did not retain unknown liability: " + marker
                                )
                        reopened = Store(work / "ledger.sqlite3")
                        assert len(calls) == 3, len(calls)
                        assert (
                            reopened.budget()["spent"] == 124
                            and reopened.budget()["reserved"] > 0
                        ), reopened.budget()
                        return {
                            "route": "anthropic/claude-haiku-5-5",
                            "upstream_calls": len(calls),
                            "usage": usage,
                            "known_fixture_nanousd": 124,
                            "unknown_liability_retained": True,
                            "native_tool_strict": native_strict,
                            "output_bound": 256,
                            "wire_tool": tool,
                        }

                result = asyncio.run(exercise())
                result["contract_qualified"] = result["native_tool_strict"]
                result["account_access"] = "unverified; local mock only"
                print(json.dumps(result, indent=2))
                if not result["contract_qualified"]:
                    raise SystemExit(1)
            finally:
                process.terminate()
                process.wait(timeout=20)
                upstream.shutdown()


if __name__ == "__main__":
    main()
