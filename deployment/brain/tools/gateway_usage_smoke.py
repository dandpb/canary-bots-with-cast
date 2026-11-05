"""Pinned Responses usage bridge + real accounting, entirely offline."""

import asyncio
import importlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from canary_brain.gateway import GatewayConfiguration, GatewayProvider
from canary_brain.provider import Prices
from canary_brain.store import Store


async def exercise():
    bridge = importlib.import_module(
        "litellm.responses.litellm_completion_transformation.transformation"
    ).LiteLLMCompletionResponsesConfig
    usage = bridge.transform_chat_completion_usage_to_responses_usage(None)
    normalized = usage.model_dump()
    assert normalized["input_tokens"] == normalized["output_tokens"] == 0
    calls = []

    async def create(**body):
        calls.append(body)
        data = {
            "id": "offline-upstream",
            "model": "offline-model",
            "usage": normalized,
            "output": [],
        }
        return SimpleNamespace(
            headers={"x-litellm-model-id": "offline-deployment"},
            parse=lambda: SimpleNamespace(model_dump=lambda **_kwargs: data),
        )

    with tempfile.TemporaryDirectory(prefix="gateway-usage-") as directory:
        path = Path(directory) / "ledger.sqlite3"
        gateway = GatewayConfiguration(
            alias="offline",
            effective_model="offline-model",
            deployment_id="offline-deployment",
            provider="offline-upstream",
            version="1.108.0",
            configuration_sha256="a" * 64,
            prices=Prices(
                version="offline-fixture",
                input_nanousd=100,
                cached_nanousd=10,
                cache_write_nanousd=125,
                output_nanousd=500,
            ),
        )
        client = SimpleNamespace(
            responses=SimpleNamespace(with_raw_response=SimpleNamespace(create=create))
        )
        provider = GatewayProvider(Store(path), client, gateway=gateway)
        rejected = False
        try:
            await provider._request(
                "responses", {"input": "nonempty request", "max_output_tokens": 256}, 10
            )
        except TypeError:
            rejected = True
        budget = Store(path).budget()
        print(
            json.dumps(
                {
                    "normalized_usage": normalized,
                    "rejected": rejected,
                    "calls": len(calls),
                    "budget": budget,
                },
                sort_keys=True,
            )
        )
        assert len(calls) == 1
        assert rejected and budget["reserved"] > 0, (
            "missing upstream usage was normalized and settled as a free request"
        )


def main():
    if "--inside" in sys.argv:
        asyncio.run(exercise())
    else:
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
                "/source/deployment/brain/tools/gateway_usage_smoke.py",
                "--inside",
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
