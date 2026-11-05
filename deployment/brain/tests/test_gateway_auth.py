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
