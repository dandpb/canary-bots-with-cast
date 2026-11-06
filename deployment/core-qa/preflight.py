"""Read-only gate before the first canary-core-qa up/build."""

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

from prepare import MAP_SHA256
from verify_myaac import verify as verify_myaac

HERE = Path(__file__).resolve().parent
PROJECT = "canary-core-qa"
SERVICES = {"database", "game", "web"}
VOLUMES = {"database", "game-logs", "authored-data", "website-cache"}
IMAGES = {"canary-core-qa-game:local", "canary-core-qa-web:local"}
IMAGE_LOCK = json.loads((HERE / "image-lock.json").read_text())


def command(*args, env=None):
    result = subprocess.run(args, cwd=HERE, env=env, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"read-only command failed: {args[0]} {args[1]}")
    return result.stdout


def project_name(name):
    return name == PROJECT or name.startswith(PROJECT + "-") or name.startswith(PROJECT + "_")


def assert_no_resources():
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
    found += [f"image:{image}" for image in IMAGES & images]
    if found:
        raise RuntimeError("QA resources already exist; review before up: " + ", ".join(sorted(set(found))))


def assert_compose():
    env = os.environ.copy()
    revision = env.get("SOURCE_REVISION", "")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("SOURCE_REVISION must be the full reviewed commit SHA")
    for name in ("MARIADB_PASSWORD", "MARIADB_ROOT_PASSWORD", "BOT_PLAYERS_ONLINE"):
        env.pop(name, None)
    data = json.loads(command(
        "docker", "compose", "-p", PROJECT, "-f", "compose.yaml", "--env-file", ".env",
        "config", "--format", "json", env=env,
    ))
    if data.get("name") != PROJECT or set(data.get("services", {})) != SERVICES:
        raise RuntimeError("Compose project/services differ from the reviewed QA stack")
    volumes = data.get("volumes", {})
    if set(volumes) != VOLUMES or any(
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
    for service in services.values():
        for mount in service.get("volumes", []):
            if mount.get("type") == "bind" and not Path(mount["source"]).resolve().is_relative_to(runtime):
                raise RuntimeError("Compose has a bind outside the QA runtime")
            if mount.get("type") == "volume" and mount.get("source") not in VOLUMES:
                raise RuntimeError("Compose mounts a foreign volume")
        for port in service.get("ports", []):
            if port.get("host_ip") != "127.0.0.1":
                raise RuntimeError("QA publishes a port outside loopback")
    if services["game"]["environment"].get("CANARY_BRAIN_CONFIG") != "/etc/canary-core-qa/disabled-brain.json":
        raise RuntimeError("QA brain mode differs from the reviewed disabled config")


def assert_image_lock():
    for kind in ("database", "web_base"):
        spec = IMAGE_LOCK[kind]
        actual = command("docker", "image", "inspect", spec["ref"], "--format", "{{.Id}}").strip()
        if actual != spec["id"]:
            raise RuntimeError(f"{kind} local image ID differs from image-lock.json")


def assert_source(approved_revision):
    current = command("git", "rev-parse", "HEAD").strip()
    if not approved_revision or approved_revision != current or os.environ["SOURCE_REVISION"] != current:
        raise RuntimeError("approved SHA, SOURCE_REVISION and checkout HEAD must match")
    if command("git", "status", "--porcelain", "--untracked-files=all").strip():
        raise RuntimeError("QA source checkout has uncommitted or untracked files")


def assert_map():
    path = HERE / "runtime/world/otservbr.otbm"
    if not path.is_file():
        raise RuntimeError("pinned QA map is absent; run prepare.py --download-map first")
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != MAP_SHA256:
            raise RuntimeError("QA map hash differs from the pinned release")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources-only", action="store_true",
                        help="audit Compose/resources before downloading the map; not an up gate")
    parser.add_argument("--approved-revision", help="full SHA approved for this smoke; required for the up gate")
    args = parser.parse_args()
    assert_compose()
    assert_no_resources()
    assert_image_lock()
    verify_myaac()
    if not args.resources_only:
        assert_source(args.approved_revision)
        assert_map()
    print("QA Compose and Docker resources are isolated; no containers were started.")
    if args.resources_only:
        print("Map check skipped; run the full preflight immediately before up.")


if __name__ == "__main__":
    main()
