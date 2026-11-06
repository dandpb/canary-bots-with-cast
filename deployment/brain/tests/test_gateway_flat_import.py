"""LiteLLM's flat-file loader does not register the module in sys.modules."""

import importlib.util
import sys
from pathlib import Path

from canary_brain import gateway_policy


def test_policy_loads_without_sys_modules_registration(monkeypatch):
    monkeypatch.delenv("CANARY_GATEWAY_CONFIG", raising=False)
    name = "canary_flat_policy_regression"
    assert name not in sys.modules
    spec = importlib.util.spec_from_file_location(name, Path(gateway_policy.__file__))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert name not in sys.modules
    assert callable(module.authenticate)
    pin = module.DispatchPin("alias", "openai/model", "id", None, None, "synthetic")
    assert pin.deployment_id == "id" and "synthetic" not in repr(pin)
