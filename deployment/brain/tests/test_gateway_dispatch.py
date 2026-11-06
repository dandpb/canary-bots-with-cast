"""Pin the post-router request, before provider dispatch, without SDK test deps."""

import copy
import hashlib
import json
from types import SimpleNamespace

import pytest

from canary_brain import gateway_policy


def native_body():
    schema = {
        "type": "object",
        "properties": {
            "candidate_id": {"type": "string", "enum": ["continue", "resupply"]}
        },
        "required": ["candidate_id"],
        "additionalProperties": False,
    }
    return {
        "tools": [
            {
                "type": "function",
                "name": "choose_action",
                "strict": True,
                "parameters": schema,
            }
        ],
        "tool_choice": {"type": "function", "name": "choose_action"},
        "extra_body": {
            "tools": [
                {
                    "functionDeclarations": [
                        {
                            "name": "choose_action",
                            "description": "Select one offered candidate.",
                            "parametersJsonSchema": copy.deepcopy(schema),
                        }
                    ]
                }
            ]
        },
    }


def test_only_matching_native_gemini_schema_can_bypass_lossy_vendor_projection():
    body = native_body()
    gateway_policy.validate_native_tools(body, "gemini/gemini-3.5-flash-lite")
    with pytest.raises(ValueError):
        gateway_policy.validate_native_tools(body, "openai/model-a")
    for change in (
        "routing",
        "tool_config",
        "different_schema",
        "forced_choice",
        "no_closed_schema",
    ):
        body = native_body()
        if change == "routing":
            body["extra_body"]["api_base"] = "https://rogue.invalid"
        elif change == "tool_config":
            body["extra_body"]["toolConfig"] = {
                "functionCallingConfig": {"mode": "AUTO"}
            }
        elif change == "different_schema":
            body["extra_body"]["tools"][0]["functionDeclarations"][0][
                "parametersJsonSchema"
            ]["additionalProperties"] = True
        elif change == "forced_choice":
            body["tool_choice"] = "auto"
        else:
            body["tools"][0]["parameters"].pop("additionalProperties")
        with pytest.raises(ValueError):
            gateway_policy.validate_native_tools(body, "gemini/gemini-3.5-flash-lite")


def pin():
    return gateway_policy.DispatchPin(
        "alias-a",
        "openai/model-a",
        "id-a",
        "https://expected.invalid/v1",
        "named-a",
        "private-fixture",
    )


def request():
    return {
        "model": "openai/model-a",
        "api_base": "https://expected.invalid/v1",
        "model_info": {"id": "id-a"},
        "litellm_metadata": {"model_group": "alias-a"},
        "litellm_credential_name": "named-a",
        "num_retries": 0,
        "caching": False,
    }


@pytest.mark.parametrize(
    "override",
    [
        {"model": "openai/rogue"},
        {"api_base": "https://rogue.invalid/v1"},
        {"model_info": {"id": "rogue"}},
        {"litellm_credential_name": "rogue"},
        {"litellm_metadata": {"model_group": "rogue"}},
        {"litellm_metadata": {"model_group": "alias-a", "attempted_retries": 1}},
        {"litellm_metadata": {"model_group": "alias-a", "attempted_fallbacks": 1}},
        {"num_retries": 1},
        {"caching": True},
        {"litellm_credential_name": None, "api_key": "rogue"},
        {"custom_llm_provider": "rogue"},
        {"client": object()},
        {"extra_headers": {"Authorization": "rogue"}},
        {"base_url": "https://rogue.invalid"},
    ],
)
def test_reject_effective_routing_mutations_before_dispatch(override):
    with pytest.raises(ValueError, match="selected deployment"):
        gateway_policy.validate_dispatch(request() | override, pin())


def test_detach_named_credential_from_mutable_lookup():
    selected = request()
    actual = gateway_policy.validate_dispatch(selected, pin())
    assert "litellm_credential_name" not in actual
    assert actual["api_key"] == "private-fixture"
    assert selected["litellm_credential_name"] == "named-a"
    assert "private-fixture" not in repr(pin())
    # An internal bridge can run the public hook again with its normalized model.
    nested = actual | {"model": "model-a", "custom_llm_provider": "openai"}
    assert (
        gateway_policy.validate_dispatch(nested, pin())["api_key"] == "private-fixture"
    )


@pytest.mark.parametrize(
    "field",
    [
        "litellm_credential_name",
        "custom_llm_provider",
        "specific_deployment",
        "model_info",
        "litellm_metadata",
        "api_key",
        "api_base",
        "fallbacks",
        "num_retries",
        "cache",
        "caching",
        "mock_response",
        "client",
        "extra_body",
    ],
)
async def test_worker_cannot_override_routing_even_with_matching_static_manifest(
    monkeypatch, tmp_path, field
):
    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code, self.detail = status_code, detail

    config = {
        "model_list": [
            {
                "model_name": "alias-a",
                "litellm_params": {
                    "model": "openai/model-a",
                    "api_key": "private-fixture",
                },
                "model_info": {"id": "id-a"},
            }
        ],
        "router_settings": {"num_retries": 0},
        "litellm_settings": {"num_retries": 0, "drop_params": False},
    }
    raw = json.dumps(config).encode()
    policy = tmp_path / "policy.json"
    policy.write_bytes(raw)
    modules = {
        "yaml": SimpleNamespace(safe_load=json.loads),
        "fastapi": SimpleNamespace(HTTPException=HTTPException),
        "litellm.proxy._types": SimpleNamespace(UserAPIKeyAuth=lambda **kwargs: kwargs),
    }
    monkeypatch.setattr(gateway_policy.importlib, "import_module", modules.__getitem__)
    monkeypatch.setattr(
        gateway_policy.importlib.metadata, "version", lambda _: "1.108.0"
    )
    monkeypatch.setattr(gateway_policy, "_startup_policy", None)
    monkeypatch.setattr(gateway_policy, "_install_dispatch_guard", lambda: None)
    monkeypatch.setenv("CANARY_GATEWAY_CONFIG", str(policy))

    async def body():
        return {"model": "alias-a", field: "unexpected-routing-value"}

    incoming = SimpleNamespace(
        method="POST",
        url=SimpleNamespace(path="/v1/responses"),
        headers={
            "x-canary-gateway-config": hashlib.sha256(raw).hexdigest(),
            "x-canary-gateway-version": "1.108.0",
            "x-canary-upstream-model": "openai/model-a",
        },
        json=body,
    )
    with pytest.raises(HTTPException) as denied:
        await gateway_policy._authenticate_worker(incoming, "private-fixture")
    assert denied.value.status_code == 400
