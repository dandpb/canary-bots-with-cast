"""Fail-closed policy for the private LiteLLM benchmark gateway."""

from __future__ import annotations

import hashlib
import hmac
import importlib
import importlib.metadata
import os
from pathlib import Path
from typing import Any

_policy_path = os.environ.get("CANARY_GATEWAY_CONFIG")
_startup_policy = Path(_policy_path).read_bytes() if _policy_path else None


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
    # Imported only inside LiteLLM; the worker and offline tests do not need its SDK.
    yaml = importlib.import_module("yaml")
    HTTPException = importlib.import_module("fastapi").HTTPException
    UserAPIKeyAuth = importlib.import_module("litellm.proxy._types").UserAPIKeyAuth

    allowed_paths = {"/v1/responses", "/responses", "/v1/decisions", "/decisions"}
    if request.method != "POST" or request.url.path not in allowed_paths:
        raise HTTPException(
            status_code=403, detail="worker credential cannot administer gateway"
        )
    expected = os.environ.get("LITELLM_WORKER_KEY", "")
    if (
        not isinstance(api_key, str)
        or not expected
        or not hmac.compare_digest(api_key.removeprefix("Bearer "), expected)
    ):
        raise HTTPException(status_code=401, detail="invalid worker credential")
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
        if any(
            field in body
            for field in (
                "fallbacks",
                "num_retries",
                "api_key",
                "api_base",
                "model_list",
                "caching",
                "cache",
                "mock_response",
            )
        ):
            raise ValueError("request cannot override gateway policy")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None
    return UserAPIKeyAuth(api_key=api_key, models=sorted(names))
