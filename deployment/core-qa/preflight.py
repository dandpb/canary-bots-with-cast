"""Read-only gate before the first canary-core-qa up/build."""

import argparse
import hashlib
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
    if (worker.get("provider") != "fake"
            or {"credential_file", "gateway", "operator_port", "run_cap_nanousd"} & set(worker)
            or not all(path and Path(path).is_relative_to(BRAIN_ROOT) for path in paths)):
        raise RuntimeError("QA worker may only use the fake provider and the disposable ledger")


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
    if brain_fake:
        assert_fake_brain(services["brain"], revision)
    canonical = json.dumps(redact(data), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def assert_image_lock():
    observed = {}
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


def write_receipt(path, approved_revision, compose_sha, images, myaac, map_sha, brain_fake=False):
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
        "resources_absent": True,
        "brain_fake": brain_fake,
    }
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


def run_preflight(resources_only=False, approved_revision=None, receipt_path=RECEIPT, brain_fake=False):
    compose_sha = assert_compose(brain_fake)
    assert_no_resources(brain_fake)
    images = assert_image_lock()
    myaac = verify_myaac()
    if resources_only:
        return None
    source_sha = assert_source(approved_revision)
    map_sha = assert_map()
    return write_receipt(receipt_path, source_sha, compose_sha, images, myaac, map_sha, brain_fake)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources-only", action="store_true",
                        help="audit Compose/resources before downloading the map; not an up gate")
    parser.add_argument("--approved-revision", help="full SHA approved for this smoke; required for the up gate")
    parser.add_argument("--brain-fake", action="store_true",
                        help="QA stage 2: also validate compose.brain-fake.yaml and its fake worker")
    args = parser.parse_args()
    receipt_sha = run_preflight(args.resources_only, args.approved_revision, brain_fake=args.brain_fake)
    print("QA Compose and Docker resources are isolated; no containers were started.")
    if args.resources_only:
        print("Map check skipped; run the full preflight immediately before up.")
    else:
        print("Sanitized preflight receipt SHA-256:", receipt_sha)


if __name__ == "__main__":
    main()
