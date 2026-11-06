"""Prepare the optional local gateway without replacing existing configuration."""

import argparse
import json
import os
import secrets
from pathlib import Path
from urllib.parse import quote


def add_coordination(policy: dict[str, object]) -> None:
    """Configure coordination/auth state without enabling response caching."""
    for name in ("general_settings", "litellm_settings", "router_settings"):
        section = policy.setdefault(name, {})
        if not isinstance(section, dict):
            raise TypeError("gateway settings must be JSON objects")
    general = policy["general_settings"]
    settings = policy["litellm_settings"]
    router = policy["router_settings"]
    assert isinstance(general, dict) and isinstance(settings, dict)
    assert isinstance(router, dict)
    general["coordination_redis"] = {
        "host": "os.environ/REDIS_HOST",
        "port": "os.environ/REDIS_PORT",
        "password": "os.environ/REDIS_PASSWORD",
        "db": 0,
        "namespace": "canary-bots-wsl:litellm",
    }
    settings["enable_redis_auth_cache"] = True
    settings["cache"] = False
    router["cache_responses"] = False


def prepare_coordination(directory: Path) -> dict[str, object]:
    """Create a new policy; refuse to rewrite an already different target."""
    policy = directory / "runtime/config/litellm.yaml"
    target = policy.with_name("litellm-coordination.yaml")
    if policy.is_symlink() or target.is_symlink():
        raise ValueError("gateway policy files must not be symlinks")
    original = json.loads(policy.read_text())
    if not isinstance(original, dict):
        raise TypeError("gateway policy must be a JSON object")
    add_coordination(original)
    encoded = json.dumps(original, indent=2) + "\n"
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if target.read_text() != encoded:
            raise ValueError(
                "coordination target differs; preserve and review it"
            ) from None
        return {"created": [], "preserved": [str(target.relative_to(directory))]}
    with os.fdopen(descriptor, "w") as stream:
        stream.write(encoded)
    return {"created": [str(target.relative_to(directory))], "preserved": []}


def prepare(directory: Path) -> dict[str, object]:
    os.umask(0o077)
    config = directory / "runtime/config"
    private = directory / "runtime/secrets"
    for folder in (config, private):
        folder.mkdir(parents=True, exist_ok=True)
    database = private / "litellm-db.env"
    if database.exists():
        db_values = dict(
            line.split("=", 1)
            for line in database.read_text().splitlines()
            if "=" in line and not line.startswith("#")
        )
        db_password = db_values["POSTGRES_PASSWORD"]
    else:
        db_password = secrets.token_hex(32)
    policy: dict[str, object] = {
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
            "custom_auth_settings": {"mode": "auto"},
        },
    }
    add_coordination(policy)
    files = {
        config / "litellm.yaml": json.dumps(policy, indent=2) + "\n",
        private
        / "litellm-provider.env": "# Add approved provider credentials here when configuring models.\n",
        private / "litellm-worker.env": (
            "LITELLM_WORKER_KEY=sk-canary-" + secrets.token_hex(32) + "\n"
            "LITELLM_MASTER_KEY=sk-canary-admin-" + secrets.token_hex(32) + "\n"
        ),
        database: "POSTGRES_DB=litellm\nPOSTGRES_USER=litellm\nPOSTGRES_PASSWORD="
        + db_password
        + "\n",
        private / "litellm-ui.env": (
            "DATABASE_URL=postgresql://litellm:"
            + quote(db_password, safe="")
            + "@litellm-db:5432/litellm\n"
            "UI_USERNAME=admin\nLITELLM_SALT_KEY=sk-salt-"
            + secrets.token_hex(32)
            + "\n"
            "STORE_MODEL_IN_DB=True\n"
        ),
        private / "litellm-redis.env": (
            "REDIS_HOST=litellm-redis\nREDIS_PORT=6379\nREDIS_PASSWORD="
            + secrets.token_hex(32)
            + "\n"
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directory", type=Path, default=Path(__file__).resolve().parent
    )
    parser.add_argument("--coordination", action="store_true")
    args = parser.parse_args()
    result = prepare(args.directory)
    if args.coordination:
        result["coordination"] = prepare_coordination(args.directory)
    print(json.dumps(result, indent=2))
