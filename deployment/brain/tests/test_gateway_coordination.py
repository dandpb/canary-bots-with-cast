"""Coordination state may use Redis while benchmark response caching stays off."""

import copy
import json
from pathlib import Path

import pytest

from canary_brain.gateway_policy import validate_policy


@pytest.mark.parametrize("cache_section", ["litellm_settings", "router_settings"])
def test_coordination_redis_is_independent_of_forbidden_response_cache(cache_section):
    config = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "gateway/gateway.named-credentials.example.json"
        ).read_text()
    )
    config["general_settings"]["coordination_redis"] = {
        "host": "os.environ/REDIS_HOST",
        "port": "os.environ/REDIS_PORT",
        "password": "os.environ/REDIS_PASSWORD",
        "db": 0,
        "namespace": "canary-bots-wsl:litellm",
    }
    config["litellm_settings"].update(cache=False, enable_redis_auth_cache=True)
    config["router_settings"]["cache_responses"] = False
    original_models = copy.deepcopy(config["model_list"])
    assert validate_policy(config) == {"canary-openai", "canary-gemini"}
    assert config["model_list"] == original_models
    cache_field = "cache" if cache_section == "litellm_settings" else "cache_responses"
    config[cache_section][cache_field] = True
    with pytest.raises(ValueError):
        validate_policy(config)
