"""Bad gateway credentials must be rejected before configuration or provider IO."""

from types import SimpleNamespace

import pytest

from canary_brain import gateway_policy


@pytest.mark.parametrize("key", [None, "", "not-the-worker-key"])
async def test_missing_or_invalid_key_returns_401_without_extra_gateway_packages(
    monkeypatch, key
):
    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code
            super().__init__(detail)

    dependencies = {
        "yaml": SimpleNamespace(),
        "fastapi": SimpleNamespace(HTTPException=HTTPException),
        "litellm.proxy._types": SimpleNamespace(UserAPIKeyAuth=object),
    }
    monkeypatch.setattr(
        gateway_policy.importlib, "import_module", dependencies.__getitem__
    )
    monkeypatch.setenv("LITELLM_WORKER_KEY", "private-unit-fixture")
    request = SimpleNamespace(method="POST", url=SimpleNamespace(path="/v1/responses"))
    with pytest.raises(HTTPException) as rejected:
        await gateway_policy.authenticate(request, key)
    assert rejected.value.status_code == 401


@pytest.mark.parametrize("status", [400, 403, 409, 500])
async def test_recognized_worker_failure_cannot_fall_through_to_native_auth(
    monkeypatch, status
):
    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code, self.detail = status_code, detail

    class ProxyException(Exception):
        def __init__(self, *, message, type, param, code):
            self.code = code

    dependencies = {
        "fastapi": SimpleNamespace(HTTPException=HTTPException),
        "litellm.proxy._types": SimpleNamespace(ProxyException=ProxyException),
    }
    monkeypatch.setattr(
        gateway_policy.importlib, "import_module", dependencies.__getitem__
    )
    monkeypatch.setenv("LITELLM_WORKER_KEY", "private-unit-fixture")

    async def deny(*args):
        if status == 500:
            raise OSError("unreadable policy")
        raise HTTPException(status, "denied policy")

    monkeypatch.setattr(gateway_policy, "_authenticate_worker", deny)
    # The pinned LiteLLM enterprise_custom_auth(mode=auto) rethrows this type;
    # ordinary HTTPException would instead attempt native/database auth.
    with pytest.raises(ProxyException) as rejected:
        await gateway_policy.authenticate(object(), "private-unit-fixture")
    assert rejected.value.code == status


async def test_private_benchmark_gateway_never_falls_back_to_admin_auth(monkeypatch):
    class HTTPException(Exception):
        pass

    class ProxyException(Exception):
        def __init__(self, **kwargs):
            self.code = kwargs["code"]

    modules = {
        "fastapi": SimpleNamespace(HTTPException=HTTPException),
        "litellm.proxy._types": SimpleNamespace(ProxyException=ProxyException),
    }
    monkeypatch.setattr(gateway_policy.importlib, "import_module", modules.__getitem__)
    monkeypatch.setenv("LITELLM_WORKER_KEY", "fixture-worker")
    monkeypatch.setenv("CANARY_BENCHMARK_GATEWAY_ONLY", "1")
    with pytest.raises(ProxyException) as denied:
        await gateway_policy.authenticate(object(), "fixture-master")
    assert denied.value.code == 401


@pytest.mark.parametrize("path", ["/model/info", "/lens/tracing/keys", "/key/generate"])
async def test_spend_owner_identity_does_not_grant_worker_management_access(
    monkeypatch, path
):
    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code

    modules = {
        "yaml": SimpleNamespace(),
        "fastapi": SimpleNamespace(HTTPException=HTTPException),
        "litellm.proxy._types": SimpleNamespace(UserAPIKeyAuth=object),
    }
    monkeypatch.setattr(gateway_policy.importlib, "import_module", modules.__getitem__)
    monkeypatch.setenv("CANARY_GATEWAY_WORKER_USER_ID", "trace-owner")
    request = SimpleNamespace(method="POST", url=SimpleNamespace(path=path))
    with pytest.raises(HTTPException) as rejected:
        await gateway_policy._authenticate_worker(request, "fixture-worker")
    assert rejected.value.status_code == 403
