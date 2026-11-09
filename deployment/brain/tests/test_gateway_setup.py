"""Gateway setup must preserve database identity and existing credentials."""

import json
import os
import re
import runpy
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import pytest


def test_preparation_preserves_secrets_and_database_connection(tmp_path):
    script = Path(__file__).resolve().parents[2] / "wsl/setup-gateway.py"
    prepare = runpy.run_path(str(script))["prepare"]
    private = tmp_path / "runtime/secrets"
    private.mkdir(parents=True)
    db_password = "private-fixture@:/+"
    database = private / "litellm-db.env"
    database.write_text("POSTGRES_PASSWORD=" + db_password + "\n")
    worker = private / "litellm-worker.env"
    worker.write_text("LITELLM_MASTER_KEY=existing-local-fixture\n")
    result = prepare(tmp_path)
    assert len(result["created"]) == 4
    ui = (private / "litellm-ui.env").read_text()
    assert "postgresql://litellm:" + quote(db_password, safe="") + "@litellm-db:" in ui
    assert "UI_USERNAME=admin\n" in ui
    assert "UI_PASSWORD=" not in ui
    paths = [p for p in tmp_path.rglob("*") if p.is_file()]
    original = {p: p.read_bytes() for p in paths}
    repeated = prepare(tmp_path)
    assert repeated["created"] == []
    assert len(repeated["preserved"]) == 6
    assert original == {p: p.read_bytes() for p in paths}
    assert worker.read_text() == "LITELLM_MASTER_KEY=existing-local-fixture\n"


def test_new_setup_has_private_redis_and_coordination_without_response_cache(tmp_path):
    script = Path(__file__).resolve().parents[2] / "wsl/setup-gateway.py"
    prepare = runpy.run_path(str(script))["prepare"]
    result = prepare(tmp_path)
    assert len(result["created"]) == 6
    redis = tmp_path / "runtime/secrets/litellm-redis.env"
    assert redis.stat().st_mode & 0o777 == 0o600
    values = dict(line.split("=", 1) for line in redis.read_text().splitlines())
    assert values["REDIS_HOST"] == "litellm-redis"
    assert values["REDIS_PORT"] == "6379"
    assert re.fullmatch(r"[0-9a-f]{64}", values["REDIS_PASSWORD"])
    policy = json.loads((tmp_path / "runtime/config/litellm.yaml").read_text())
    assert policy["general_settings"]["coordination_redis"] == {
        "host": "os.environ/REDIS_HOST",
        "port": "os.environ/REDIS_PORT",
        "password": "os.environ/REDIS_PASSWORD",
        "db": 0,
        "namespace": "canary-bots-wsl:litellm",
    }
    assert policy["litellm_settings"]["enable_redis_auth_cache"] is True
    assert policy["litellm_settings"]["cache"] is False
    assert policy["router_settings"]["cache_responses"] is False


def test_coordination_derivative_preserves_original_routes_and_routing_settings(
    tmp_path,
):
    script = Path(__file__).resolve().parents[2] / "wsl/setup-gateway.py"
    setup = runpy.run_path(str(script))
    setup["prepare"](tmp_path)
    policy = tmp_path / "runtime/config/litellm.yaml"
    original = json.loads(policy.read_text())
    original["general_settings"].pop("coordination_redis")
    original["litellm_settings"].pop("enable_redis_auth_cache")
    original["model_list"] = [
        {
            "model_name": "fixture",
            "litellm_params": {"model": "openai/model", "num_retries": 0},
            "model_info": {"id": "fixture-deployment"},
        }
    ]
    policy.write_text(json.dumps(original, separators=(",", ":")) + "\n")
    before = policy.read_bytes()
    setup["prepare"](tmp_path)
    result = setup["prepare_coordination"](tmp_path)
    assert result["created"] == ["runtime/config/litellm-coordination.yaml"]
    target = policy.with_name("litellm-coordination.yaml")
    modified = json.loads(target.read_text())
    assert target.stat().st_mode & 0o777 == 0o600
    assert modified["model_list"] == original["model_list"]
    assert modified["router_settings"] == original["router_settings"]
    assert modified["litellm_settings"]["num_retries"] == 0
    assert modified["litellm_settings"]["fallbacks"] == []
    assert (
        modified["general_settings"]["custom_auth"]
        == original["general_settings"]["custom_auth"]
    )
    target_bytes, target_mtime = target.read_bytes(), target.stat().st_mtime_ns
    repeated = setup["prepare_coordination"](tmp_path)
    assert repeated["preserved"] == ["runtime/config/litellm-coordination.yaml"]
    assert target.read_bytes() == target_bytes
    assert target.stat().st_mtime_ns == target_mtime
    assert policy.read_bytes() == before


def test_divergent_coordination_target_is_not_overwritten(tmp_path):
    script = Path(__file__).resolve().parents[2] / "wsl/setup-gateway.py"
    setup = runpy.run_path(str(script))
    setup["prepare"](tmp_path)
    policy = tmp_path / "runtime/config/litellm.yaml"
    before = policy.read_bytes()
    target = policy.with_name("litellm-coordination.yaml")
    previous = '{"operator":"preserve this policy"}\n'
    target.write_text(previous)
    with pytest.raises(ValueError, match="target differs"):
        setup["prepare_coordination"](tmp_path)
    assert target.read_text() == previous
    assert policy.read_bytes() == before


def test_coordination_cli_does_not_print_secret_values(tmp_path):
    script = Path(__file__).resolve().parents[2] / "wsl/setup-gateway.py"
    result = subprocess.run(
        [sys.executable, str(script), "--directory", str(tmp_path), "--coordination"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "runtime/config/litellm-coordination.yaml" in result.stdout
    for path in (tmp_path / "runtime/secrets").glob("*.env"):
        for line in path.read_text().splitlines():
            if "=" not in line or line.startswith("#"):
                continue
            name, value = line.split("=", 1)
            if any(marker in name for marker in ("PASSWORD", "KEY", "DATABASE_URL")):
                assert value not in result.stdout + result.stderr
    assert result.stderr == ""


@pytest.mark.skipif(
    sys.platform == "win32", reason="Redis bootstrap uses a POSIX shell"
)
def test_redis_bootstrap_keeps_password_in_private_config_not_argv_or_output(tmp_path):
    compose = Path(__file__).resolve().parents[2] / "wsl/compose.yaml"
    service = (
        compose.read_text()
        .split("  litellm-redis:\n", 1)[1]
        .split("  litellm-db:\n", 1)[0]
    )
    command = service.split("    command:\n      - |\n", 1)[1].split("    volumes:", 1)[
        0
    ]
    script = "\n".join(line[8:] for line in command.splitlines())
    config = tmp_path / "redis.conf"
    script = script.replace("$$", "$").replace("/tmp/redis.conf", str(config))
    fake = tmp_path / "redis-server"
    proof = tmp_path / "argv.json"
    fake.write_text(
        "#!" + sys.executable + "\nimport json, os, sys\n"
        "from pathlib import Path\n"
        "Path(os.environ['FAKE_REDIS_PROOF']).write_text(json.dumps(sys.argv[1:]))\n"
    )
    fake.chmod(0o700)
    password = "e" * 64
    result = subprocess.run(
        ["/bin/sh", "-ec", script],
        env={
            **os.environ,
            "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"],
            "REDIS_PASSWORD": password,
            "FAKE_REDIS_PROOF": str(proof),
        },
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(proof.read_text()) == [str(config)]
    assert config.stat().st_mode & 0o777 == 0o600
    assert "requirepass " + password + "\n" in config.read_text()
    assert "appendonly yes\n" in config.read_text()
    assert "maxmemory 128mb\nmaxmemory-policy noeviction\n" in config.read_text()
    assert password not in result.stdout + result.stderr
    assert result.stdout == result.stderr == ""
