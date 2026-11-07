"""Read-only gate before the first canary-core-qa up/build."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from prepare import MAP_SHA256
from verify_myaac import verify as verify_myaac

HERE = Path(__file__).resolve().parent
PROJECT = "canary-core-qa"
SERVICES = {"database", "game", "web"}
VOLUMES = {"database", "game-logs", "authored-data", "website-cache"}
IMAGES = {"canary-core-qa-game:local", "canary-core-qa-web:local"}
BRAIN_IMAGE = "canary-core-qa-brain:local"
BRAIN_VOLUMES = {"brain-socket", "brain-ledger"}
BRAIN_ROOT = Path("/var/lib/canary-human-qa-stage2")
IMAGE_LOCK = json.loads((HERE / "image-lock.json").read_text())
RECEIPT = HERE / "runtime/evidence/preflight-receipt.json"
UPGRADE_RECEIPT = HERE / "runtime/evidence/stage2-upgrade-receipt.json"
GAME_ENTRYPOINT = HERE.parent / "wsl/game-entrypoint.py"
CONFIG_DIST = HERE.parent.parent / "config.lua.dist"
SHUTDOWN_FLAG = "GAME_DISABLE_GLOBAL_SAVE_SHUTDOWN"
SHUTDOWN_KEY = "globalServerSaveShutdown"
CLOSE_KEY = "globalServerSaveClose"  # with both false the daily event calls saveServer() itself


def command(*args, env=None):
    result = subprocess.run(args, cwd=HERE, env=env, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"read-only command failed: {args[0]} {args[1]}")
    return result.stdout


def project_name(name):
    return name == PROJECT or name.startswith(PROJECT + "-") or name.startswith(PROJECT + "_")


def redact(value):
    if isinstance(value, dict):
        return {
            key: "<redacted>" if re.search(r"password|secret|token|api[_-]?key|credential", key, re.I)
            else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def assert_no_resources(brain_fake=False):
    kinds = (
        ("container", ["docker", "ps", "-a"]),
        ("volume", ["docker", "volume", "ls"]),
        ("network", ["docker", "network", "ls"]),
    )
    found = []
    for kind, prefix in kinds:
        names = command(*prefix, "--format", "{{.Names}}" if kind == "container" else "{{.Name}}")
        found += [f"{kind}:{name}" for name in names.splitlines() if project_name(name)]
        labeled = command(*prefix, "--filter", f"label=com.docker.compose.project={PROJECT}",
                          "--format", "{{.Names}}" if kind == "container" else "{{.Name}}")
        found += [f"{kind}:{name}" for name in labeled.splitlines()]
    images = set(command("docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}").splitlines())
    found += [f"image:{image}" for image in (IMAGES | {BRAIN_IMAGE} if brain_fake else IMAGES) & images]
    if found:
        raise RuntimeError("QA resources already exist; review before up: " + ", ".join(sorted(set(found))))


def assert_fake_brain(service, revision):
    """Stage 2 only: an offline fake worker; a real provider must be impossible."""
    if (service.get("network_mode") != "none" or service.get("ports") or service.get("environment")
            or service.get("env_file") or service.get("image") != BRAIN_IMAGE
            or service.get("build", {}).get("args", {}).get("SOURCE_REVISION") != revision):
        raise RuntimeError("QA brain must be the offline fake worker without env or ports")
    worker = json.loads((HERE / "brain/worker.json").read_text())
    paths = [worker.get("socket_directory"), worker.get("state_file"), worker.get("budget_file"),
             worker.get("recording", {}).get("path")]
    if service.get("build", {}).get("pull") is True or (
            f"FROM {IMAGE_LOCK['brain_base']['ref']} AS brain"
            not in (HERE.parent / "wsl/Dockerfile").read_text().splitlines()):
        raise RuntimeError("QA brain build differs from the locked base image")
    if (worker.get("provider") != "fake"
            or {"credential_file", "gateway", "operator_port", "run_cap_nanousd"} & set(worker)
            or not all(path and Path(path).is_relative_to(BRAIN_ROOT) for path in paths)):
        raise RuntimeError("QA worker may only use the fake provider and the disposable ledger")


def lua_setting(config, name):
    """The value Lua ends up with: the last top-level `name = value` assignment, or None when absent."""
    values = re.findall(rf"(?m)^[ \t]*{name}[ \t]*=[ \t]*([^\s-]+)", config)
    return values[-1] if values else None


def render_game_config(environment):
    """config.lua as the game entrypoint renders it for this environment; the DB password is a placeholder."""
    spec = importlib.util.spec_from_file_location("game_entrypoint", GAME_ENTRYPOINT)
    entrypoint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entrypoint)
    environ = {key: str(value) for key, value in environment.items() if value is not None}
    return entrypoint.render({**environ, "MARIADB_PASSWORD": "qa-contract-only"}, CONFIG_DIST.read_text())


def assert_game_config(environment):
    """QA contract: the daily global server save must not shut the QA game down. Fails closed."""
    if environment.get(SHUTDOWN_FLAG) != "1":
        raise RuntimeError(f"QA game must set {SHUTDOWN_FLAG}=1")
    config = render_game_config(environment)
    if lua_setting(config, SHUTDOWN_KEY) != "false":
        raise RuntimeError(f"QA game config.lua must render {SHUTDOWN_KEY} = false")
    if lua_setting(config, CLOSE_KEY) != "false":  # close would kick players; neither state -> explicit save
        raise RuntimeError(f"QA game config.lua must render {CLOSE_KEY} = false so the daily event saves")
    return config


def assert_compose(brain_fake=False):
    env = os.environ.copy()
    revision = env.get("SOURCE_REVISION", "")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("SOURCE_REVISION must be the full reviewed commit SHA")
    for name in ("MARIADB_PASSWORD", "MARIADB_ROOT_PASSWORD", "BOT_PLAYERS_ONLINE"):
        env.pop(name, None)
    data = json.loads(command(
        "docker", "compose", "-p", PROJECT, "-f", "compose.yaml",
        *(["-f", "compose.brain-fake.yaml"] if brain_fake else []), "--env-file", ".env",
        "config", "--format", "json", env=env,
    ))
    expected_volumes = VOLUMES | BRAIN_VOLUMES if brain_fake else VOLUMES
    expected_services = SERVICES | {"brain"} if brain_fake else SERVICES
    if data.get("name") != PROJECT or set(data.get("services", {})) != expected_services:
        raise RuntimeError("Compose project/services differ from the reviewed QA stack")
    volumes = data.get("volumes", {})
    if set(volumes) != expected_volumes or any(
        item.get("external") or item.get("name") != f"{PROJECT}_{name}"
        for name, item in volumes.items()
    ):
        raise RuntimeError("Compose references a foreign volume")
    if any(item.get("external") or item.get("name") != f"{PROJECT}_{name}"
           for name, item in data.get("networks", {}).items()):
        raise RuntimeError("Compose references a foreign network")
    services = data["services"]
    if {services["game"].get("image"), services["web"].get("image")} != IMAGES:
        raise RuntimeError("QA image tags differ from the reviewed stack")
    if services["database"].get("image") != IMAGE_LOCK["database"]["ref"]:
        raise RuntimeError("QA database image differs from the reviewed stack")
    if services["database"].get("pull_policy") != "never":
        raise RuntimeError("QA database must use the locked local image")
    if services["game"].get("build", {}).get("args", {}).get("SOURCE_REVISION") != revision:
        raise RuntimeError("QA game build revision differs from the reviewed source")
    web_build = services["web"].get("build", {})
    if web_build.get("pull") is True or web_build.get("dockerfile") != "deployment/wsl/Web.Dockerfile":
        raise RuntimeError("QA web build differs from the reviewed stack")
    dockerfile = HERE.parent / "wsl/Web.Dockerfile"
    if f"FROM {IMAGE_LOCK['web_base']['ref']}" not in dockerfile.read_text().splitlines():
        raise RuntimeError("QA web base image differs from the image lock")
    runtime = (HERE / "runtime").resolve()
    reviewed = {HERE / "brain/server.json", HERE / "brain/worker.json"} if brain_fake else set()
    for service in services.values():
        for mount in service.get("volumes", []):
            source = Path(mount.get("source", "")).resolve()
            if mount.get("type") == "bind" and not source.is_relative_to(runtime) and not (
                    source in reviewed and mount.get("read_only")):
                raise RuntimeError("Compose has a bind outside the QA runtime")
            if mount.get("type") == "volume" and mount.get("source") not in expected_volumes:
                raise RuntimeError("Compose mounts a foreign volume")
        for port in service.get("ports", []):
            if port.get("host_ip") != "127.0.0.1":
                raise RuntimeError("QA publishes a port outside loopback")
    brain_config = "/etc/canary-core-qa/" + ("brain/server.json" if brain_fake else "disabled-brain.json")
    if services["game"]["environment"].get("CANARY_BRAIN_CONFIG") != brain_config:
        raise RuntimeError("QA brain mode differs from the reviewed config")
    assert_game_config(services["game"]["environment"])
    if brain_fake:
        assert_fake_brain(services["brain"], revision)
    canonical = json.dumps(redact(data), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def assert_image_lock(brain=False):
    observed = {}
    if brain:  # the brain build uses pull: false; only the locked local base is accepted
        spec = IMAGE_LOCK["brain_base"]
        found = command("docker", "image", "inspect", spec["ref"], "--format", "{{.Id}}\t{{json .RepoDigests}}")
        actual, digests = (found.strip().split("\t", 1) + ["[]"])[:2]
        if spec["repo_digest"] not in json.loads(digests):
            raise RuntimeError("brain base image differs from image-lock.json; pull the locked digest")
        observed["brain_base"] = actual
    for kind in ("database", "web_base"):
        spec = IMAGE_LOCK[kind]
        actual = command("docker", "image", "inspect", spec["ref"], "--format", "{{.Id}}").strip()
        if actual != spec["id"]:
            raise RuntimeError(f"{kind} local image ID differs from image-lock.json")
        observed[kind] = actual
    return observed


def assert_source(approved_revision):
    current = command("git", "rev-parse", "HEAD").strip()
    if not approved_revision or approved_revision != current or os.environ["SOURCE_REVISION"] != current:
        raise RuntimeError("approved SHA, SOURCE_REVISION and checkout HEAD must match")
    if command("git", "status", "--porcelain", "--untracked-files=all").strip():
        raise RuntimeError("QA source checkout has uncommitted or untracked files")
    return current


def assert_map():
    path = HERE / "runtime/world/otservbr.otbm"
    if not path.is_file():
        raise RuntimeError("pinned QA map is absent; run prepare.py --download-map first")
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != MAP_SHA256:
        raise RuntimeError("QA map hash differs from the pinned release")
    return actual


def write_receipt(path, approved_revision, compose_sha, images, myaac, map_sha, brain_fake=False,
                  stage1=None):
    receipt = {
        "schema_version": 1,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": PROJECT,
        "approved_source_revision": approved_revision,
        "observed_image_ids": images,
        "entrypoint_sha256": myaac["entrypoint_sha256"],
        "qa_config_sha256": myaac["qa_config_sha256"],
        "compose_redacted_sha256": compose_sha,
        "map_sha256": map_sha,
        "resources_absent": stage1 is None,
        "brain_fake": brain_fake,
        **({"stage1_upgrade": stage1} if stage1 else {}),
    }
    return save_receipt(path, receipt)


def save_receipt(path, receipt):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".preflight-", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.chmod(0o600)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(content).hexdigest()


def record_brain_image(approved_revision, receipt_path=None):
    """After the stage-2 up: bind the built brain image and its source label to the receipt."""
    source = assert_source(approved_revision)
    receipt_path = receipt_path or UPGRADE_RECEIPT
    receipt = json.loads(receipt_path.read_text())
    label = '{{index .Config.Labels "org.opencontainers.image.revision"}}'
    image_id, revision = (command("docker", "image", "inspect", BRAIN_IMAGE, "--format",
                                  "{{.Id}}\t" + label).strip().split("\t") + [""])[:2]
    running = command("docker", "inspect", f"{PROJECT}-brain-1", "--format", "{{.Image}}").strip()
    if receipt.get("approved_source_revision") != source or revision != source or running != image_id:
        raise RuntimeError("brain image, its source label and the receipt must match the approved HEAD")
    receipt["brain_image"] = {"id": image_id, "source_revision": revision}
    return save_receipt(receipt_path, receipt)


def run_preflight(resources_only=False, approved_revision=None, receipt_path=None, brain_fake=False,
                  upgrade=False):
    compose_sha = assert_compose(brain_fake or upgrade)
    if upgrade:  # exact comparison with the reviewed stage-1 baseline, pinned by SHA-256 in stage1_baseline
        import stage1_baseline

        stage1 = stage1_baseline.assert_stage1_upgrade()
    else:  # fresh first up, stage 1 or stage 2: unchanged
        stage1 = None
        assert_no_resources(brain_fake)
    images = assert_image_lock(brain_fake or upgrade)
    myaac = verify_myaac()
    if resources_only:
        return None
    source_sha = assert_source(approved_revision)
    map_sha = assert_map()
    return write_receipt(receipt_path or (UPGRADE_RECEIPT if upgrade or brain_fake else RECEIPT), source_sha,
                         compose_sha, images, myaac, map_sha, brain_fake or upgrade, stage1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources-only", action="store_true",
                        help="audit Compose/resources before downloading the map; not an up gate")
    parser.add_argument("--approved-revision", help="full SHA approved for this smoke; required for the up gate")
    parser.add_argument("--brain-fake", action="store_true",
                        help="QA stage 2: also validate compose.brain-fake.yaml and its fake worker")
    parser.add_argument("--upgrade-from-stage1", action="store_true",
                        help="QA stage 2 over a running stage 1 equal to the pinned stage1-baseline.json")
    parser.add_argument("--record-brain-image", action="store_true",
                        help="after the stage-2 up: record the built brain image in the upgrade receipt")
    parser.add_argument("--capture-stage1-baseline", action="store_true",
                        help="read-only: write a candidate stage-1 baseline for review (never pinned by itself)")
    parser.add_argument("--historical-receipt", type=Path,
                        help="with --capture-stage1-baseline: path to web-rollout-after.json")
    parser.add_argument("--game-rollout-receipt", type=Path,
                        help="with --capture-stage1-baseline: the game receipt after a game-only rollout")
    parser.add_argument("--db-audit", type=Path,
                        help="with --capture-stage1-baseline: DB audit JSON when the DB slice differs from the pin")
    args = parser.parse_args()
    if args.capture_stage1_baseline:
        import stage1_baseline

        if not args.historical_receipt:
            parser.error("--capture-stage1-baseline needs --historical-receipt")
        stage1_baseline.print_capture(*stage1_baseline.capture(
            args.historical_receipt, rollout_receipt=args.game_rollout_receipt, audit=args.db_audit))
        return
    if args.record_brain_image:
        print("Upgrade receipt SHA-256:", record_brain_image(args.approved_revision))
        return
    receipt_sha = run_preflight(args.resources_only, args.approved_revision, brain_fake=args.brain_fake,
                                upgrade=args.upgrade_from_stage1)
    print("QA Compose and Docker resources are isolated; no containers were started.")
    if args.resources_only:
        print("Map check skipped; run the full preflight immediately before up.")
    else:
        print("Sanitized preflight receipt SHA-256:", receipt_sha)


if __name__ == "__main__":
    main()
