"""Fail-closed policy for the private LiteLLM benchmark gateway."""

from __future__ import annotations

import hashlib
import hmac
import importlib
import importlib.metadata
import json
import os
from contextvars import ContextVar
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from pathlib import Path
from typing import Any

_policy_path = os.environ.get("CANARY_GATEWAY_CONFIG")
_startup_policy = Path(_policy_path).read_bytes() if _policy_path else None


@dataclass(frozen=True)
class DispatchPin:
    alias: str
    model: str
    deployment_id: str
    api_base: str | None
    credential_name: str | None
    api_key: str = dataclass_field(repr=False)
    routing_controls: str = "{}"


_dispatch_pin: ContextVar[DispatchPin | None] = ContextVar(
    "canary_dispatch_pin", default=None
)
_dispatch_guard: Any = None
_ROUTING_CONTROLS = (
    "client",
    "async_client",
    "base_url",
    "api_version",
    "headers",
    "extra_headers",
    "azure_ad_token",
    "azure_endpoint",
    "deployment_id",
    "api_type",
)


def _freeze_dispatch(selected: dict[str, Any]) -> DispatchPin:
    params = selected["litellm_params"]
    name = params.get("litellm_credential_name")
    if name:
        accessor = importlib.import_module(
            "litellm.litellm_core_utils.credential_accessor"
        ).CredentialAccessor
        values = accessor.get_credential_values(name)
        # Credential references must not change routing after the guard runs.
        if set(values) != {"api_key"}:
            raise ValueError("benchmark named credential must contain only api_key")
        key = values["api_key"]
    else:
        key = params.get("api_key", "")
        if isinstance(key, str) and key.startswith("os.environ/"):
            key = os.environ.get(key.removeprefix("os.environ/"), "")
    if not isinstance(key, str) or not key:
        raise ValueError("benchmark credential is unavailable")
    base = params.get("api_base")
    if base is not None and not isinstance(base, str):
        raise ValueError("benchmark api_base must be an explicit string")
    return DispatchPin(
        selected["model_name"],
        params["model"],
        selected["model_info"]["id"],
        base,
        name,
        key,
        json.dumps(
            {name: params[name] for name in _ROUTING_CONTROLS if name in params},
            sort_keys=True,
        ),
    )


def validate_dispatch(kwargs: dict[str, Any], pin: DispatchPin) -> dict[str, Any]:
    """Validate the selected request copy, then detach mutable credential data."""
    metadata = kwargs.get("litellm_metadata") or {}
    info = kwargs.get("model_info") or metadata.get("model_info") or {}
    controls = json.loads(pin.routing_controls)
    model = kwargs.get("model")
    if (
        isinstance(model, str)
        and "/" not in model
        and kwargs.get("custom_llm_provider")
    ):
        model = str(kwargs["custom_llm_provider"]) + "/" + model
    if (
        model != pin.model
        or info.get("id") != pin.deployment_id
        or metadata.get("model_group") != pin.alias
        or kwargs.get("api_base") != pin.api_base
        or kwargs.get("litellm_credential_name") not in {pin.credential_name, None}
        or (
            pin.credential_name is not None
            and kwargs.get("litellm_credential_name") is None
            and kwargs.get("api_key") != pin.api_key
        )
        or metadata.get("attempted_retries", 0) != 0
        or metadata.get("attempted_fallbacks", 0) != 0
        or kwargs.get("num_retries", 0) != 0
        or kwargs.get("caching", False) is not False
        or kwargs.get("custom_llm_provider") not in {None, pin.model.split("/", 1)[0]}
        or any(kwargs.get(name) != controls.get(name) for name in _ROUTING_CONTROLS)
    ):
        raise ValueError("selected deployment differs from the benchmark manifest")
    # load_credentials_from_list runs after this public hook in LiteLLM1.108.0.
    # Remove its reference and bind the authenticated snapshot to this request.
    result = dict(kwargs)
    result.pop("litellm_credential_name", None)
    result["api_key"] = pin.api_key
    result["num_retries"] = 0
    result["caching"] = False
    return result


def _install_dispatch_guard() -> None:
    global _dispatch_guard
    litellm: Any = importlib.import_module("litellm")
    if _dispatch_guard is None:
        logger = importlib.import_module(
            "litellm.integrations.custom_logger"
        ).CustomLogger

        async def guard(
            self: Any, kwargs: dict[str, Any], call_type: Any
        ) -> dict[str, Any] | None:
            pin = _dispatch_pin.get()
            if pin is None:
                return None
            try:
                return validate_dispatch(kwargs, pin)
            except ValueError:
                exception = importlib.import_module(
                    "litellm.proxy._types"
                ).ProxyException
                raise exception(
                    message="selected deployment differs from the benchmark manifest",
                    type="auth_error",
                    param=None,
                    code=409,
                ) from None

        # Keep the optional LiteLLM base class out of the worker's import path.
        _dispatch_guard = type(
            "DispatchGuard", (logger,), {"async_pre_call_deployment_hook": guard}
        )()
    callbacks = litellm.callbacks
    if _dispatch_guard not in callbacks:
        litellm.callbacks = [*callbacks, _dispatch_guard]


def validate_native_tools(body: dict[str, Any], model: str) -> None:
    """Permit only the Gemini projection of the same bounded choice schema."""
    if "extra_body" not in body:
        return
    tools = body.get("tools")
    extra = body["extra_body"]
    if (
        not model.startswith("gemini/")
        or not isinstance(tools, list)
        or len(tools) != 1
        or tools[0].get("name") != "choose_action"
        or tools[0].get("strict") is not True
        or body.get("tool_choice") != {"type": "function", "name": "choose_action"}
        or not isinstance(extra, dict)
        or set(extra) != {"tools"}
    ):
        raise ValueError("unsupported native tool projection")
    schema = tools[0].get("parameters")
    if (
        not isinstance(schema, dict)
        or schema.get("type") != "object"
        or schema.get("required") != ["candidate_id"]
        or schema.get("additionalProperties") is not False
        or not isinstance(schema.get("properties"), dict)
        or set(schema["properties"]) != {"candidate_id"}
    ):
        raise ValueError("unsupported native choice schema")
    candidate = schema["properties"]["candidate_id"]
    if (
        not isinstance(candidate, dict)
        or candidate.get("type") != "string"
        or not isinstance(candidate.get("enum"), list)
        or not 1 <= len(candidate["enum"]) <= 32
        or not all(isinstance(value, str) for value in candidate["enum"])
    ):
        raise ValueError("unsupported native choice candidates")
    if extra["tools"] != [
        {
            "functionDeclarations": [
                {
                    "name": "choose_action",
                    "description": "Select one offered candidate.",
                    "parametersJsonSchema": schema,
                }
            ]
        }
    ]:
        raise ValueError("native tool projection differs from the choice schema")


def validate_policy(config: dict[str, Any]) -> set[str]:
    router = config.get("router_settings", {})
    settings = config.get("litellm_settings", {})
    if router.get("num_retries") != 0 or settings.get("num_retries") != 0:
        raise ValueError("benchmark retries must be zero in both gateway layers")
    for section in (router, settings):
        for field in (
            "fallbacks",
            "context_window_fallbacks",
            "content_policy_fallbacks",
            "default_fallbacks",
        ):
            if section.get(field):
                raise ValueError("benchmark gateway cannot fall back")
        if (
            section.get("cache_responses")
            or section.get("enable_weighted_failover")
            or section.get("cache")
        ):
            raise ValueError("benchmark gateway caching and failover must be disabled")
    if settings.get("drop_params") is not False:
        raise ValueError("gateway must reject unsupported parameters")
    names: set[str] = set()
    ids: set[str] = set()
    for model in config.get("model_list", []):
        name = model.get("model_name", "")
        identifier = model.get("model_info", {}).get("id", "")
        params = model.get("litellm_params", {})
        if (
            not name
            or "*" in name
            or name in names
            or not identifier
            or identifier in ids
        ):
            raise ValueError("each explicit alias must have one unique deployment")
        if (
            params.get("num_retries", 0) != 0
            or params.get("order") is not None
            or model.get("order") is not None
        ):
            raise ValueError("deployment retries and ordered failover are forbidden")
        if any(
            params.get(k) for k in ("fallbacks", "context_window_fallbacks", "cache")
        ):
            raise ValueError("deployment cannot override benchmark routing policy")
        if not params.get("model"):
            raise ValueError("explicit upstream model is required")
        names.add(name)
        ids.add(identifier)
    if not names:
        raise ValueError("no benchmark deployments configured")
    return names


async def authenticate(request: Any, api_key: str | None) -> Any:
    """Delegate dashboard keys to native auth; worker failures never fall through."""
    _dispatch_pin.set(None)
    HTTPException = importlib.import_module("fastapi").HTTPException
    expected = os.environ.get("LITELLM_WORKER_KEY", "")
    if (
        not isinstance(api_key, str)
        or not expected
        or not hmac.compare_digest(api_key.removeprefix("Bearer "), expected)
    ):
        # With custom_auth_settings.mode=auto, LiteLLM validates admin/session
        # keys using its normal database auth. Unknown keys are still rejected.
        raise HTTPException(status_code=401, detail="invalid worker credential")
    ProxyException = importlib.import_module("litellm.proxy._types").ProxyException
    try:
        return await _authenticate_worker(request, api_key)
    except HTTPException as error:
        # Auto mode explicitly rethrows ProxyException instead of falling back.
        raise ProxyException(
            message=error.detail,
            type="auth_error",
            param=None,
            code=error.status_code,
        ) from None
    except Exception:  # noqa: BLE001 - all worker failures must block native auth fallback
        raise ProxyException(
            message="worker gateway policy could not be validated",
            type="auth_error",
            param=None,
            code=500,
        ) from None


async def _authenticate_worker(request: Any, api_key: str) -> Any:
    # Imported only inside LiteLLM; the worker and offline tests do not need its SDK.
    yaml = importlib.import_module("yaml")
    HTTPException = importlib.import_module("fastapi").HTTPException
    UserAPIKeyAuth = importlib.import_module("litellm.proxy._types").UserAPIKeyAuth

    allowed_paths = {"/v1/responses", "/responses", "/v1/decisions", "/decisions"}
    if request.method != "POST" or request.url.path not in allowed_paths:
        raise HTTPException(
            status_code=403, detail="worker credential cannot administer gateway"
        )
    raw = Path(
        os.environ.get("CANARY_GATEWAY_CONFIG", "/app/gateway.yaml")
    ).read_bytes()
    if _startup_policy is not None and raw != _startup_policy:
        raise HTTPException(
            status_code=409,
            detail="gateway configuration changed; restart and revalidate the campaign",
        )
    configured = hashlib.sha256(raw).hexdigest()
    version = importlib.metadata.version("litellm")
    if (
        request.headers.get("x-canary-gateway-config") != configured
        or request.headers.get("x-canary-gateway-version") != version
    ):
        raise HTTPException(
            status_code=409,
            detail="gateway version or configuration differs from participant manifest",
        )
    try:
        names = validate_policy(yaml.safe_load(raw))
        body = await request.json()
        if body.get("model") not in names:
            raise ValueError("unknown benchmark model alias")
        selected = next(
            m
            for m in yaml.safe_load(raw)["model_list"]
            if m["model_name"] == body["model"]
        )
        if (
            request.headers.get("x-canary-upstream-model")
            != selected["litellm_params"]["model"]
        ):
            raise ValueError("upstream model differs from participant manifest")
        # Prevent a caller from changing routing behavior per request.
        if set(body) - {
            "model",
            "input",
            "instructions",
            "max_output_tokens",
            "tools",
            "tool_choice",
            "parallel_tool_calls",
            "store",
            "reasoning",
            "previous_response_id",
            "questions",
            "extra_body",
        }:
            raise ValueError("request cannot override gateway policy")
        validate_native_tools(body, selected["litellm_params"]["model"])
        pin = _freeze_dispatch(selected)
        _install_dispatch_guard()
        _dispatch_pin.set(pin)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
    return UserAPIKeyAuth(api_key=api_key, models=sorted(names))
