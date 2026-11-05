"""Prepare the optional local gateway without replacing existing configuration."""

import json
import os
import secrets
from pathlib import Path


def prepare(directory: Path) -> dict[str, object]:
    os.umask(0o077)
    config = directory / "runtime/config"
    private = directory / "runtime/secrets"
    for folder in (config, private):
        folder.mkdir(parents=True, exist_ok=True)
    policy = {
        "model_list": [],
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
            "set_verbose": False,
        },
        "general_settings": {
            "master_key": "os.environ/LITELLM_MASTER_KEY",
            "custom_auth": "gateway_policy.authenticate",
        },
    }
    files = {
        config / "litellm.yaml": json.dumps(policy, indent=2) + "\n",
        private
        / "litellm-provider.env": "# Add approved provider credentials here when configuring models.\n",
        private / "litellm-worker.env": (
            "LITELLM_WORKER_KEY=sk-canary-" + secrets.token_hex(32) + "\n"
            "LITELLM_MASTER_KEY=sk-canary-admin-" + secrets.token_hex(32) + "\n"
        ),
    }
    created, preserved = [], []
    for path, content in files.items():
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            preserved.append(str(path.relative_to(directory)))
        else:
            with os.fdopen(descriptor, "w") as stream:
                stream.write(content)
            created.append(str(path.relative_to(directory)))
    return {"created": created, "preserved": preserved}


if __name__ == "__main__":
    print(json.dumps(prepare(Path(__file__).resolve().parent), indent=2))
