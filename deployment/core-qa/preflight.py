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
# The Compose projects this directory drives, picked by CORE_QA_PROFILE. stage1 is the live canary-core-qa and
# the default: unset, everything renders and runs exactly as before. Any other profile is its own project from
# its own overlays (name, image tags, host ports, CPU/memory limits) with its own evidence directory; the
# stage-1 baseline, handoff and return tools refuse it, and its gates never see stage-1 objects as its own.
PROFILES = {
    "stage1": {"project": "canary-core-qa", "overlays": (), "brain_overlays": (), "evidence": "runtime/evidence",
               "ports": {"login": 17171, "game": 17172, "status": 17173, "web": 18080}, "limits": False,
               "server_name": "Canary core QA"},
    "b1": {"project": "canary-qa-b1", "overlays": ("compose.b1.yaml",), "brain_overlays": ("compose.b1-brain.yaml",),
           "evidence": "runtime/b1/evidence", "ports": {"login": 27171, "game": 27172, "status": 27173, "web": 28080},
           "limits": True, "server_name": "Canary QA B1"},
}


def load_profile(name):
    """The named profile; another profile than stage1 must not share its name prefix, ports or evidence."""
    if name not in PROFILES:
        raise RuntimeError(f"unknown CORE_QA_PROFILE {name!r} (known: {', '.join(PROFILES)}); refused")
    profile, stage1 = PROFILES[name], PROFILES["stage1"]
    if name != "stage1" and (
            profile["project"].startswith(stage1["project"]) or stage1["project"].startswith(profile["project"])
            or set(profile["ports"].values()) & set(stage1["ports"].values())
            or profile["evidence"] == stage1["evidence"] or not profile["overlays"]):
        raise RuntimeError(f"profile {name} is not isolated from stage 1 (project prefix, ports, evidence or "
                           "overlay); refused")
    return {"name": name, **profile}


PROFILE = load_profile(os.environ.get("CORE_QA_PROFILE", "stage1"))
PROJECT = PROFILE["project"]
SERVICES = {"database", "game", "web"}
VOLUMES = {"database", "game-logs", "authored-data", "website-cache"}
GAME_TAG = f"{PROJECT}-game:local"
WEB_TAG = f"{PROJECT}-web:local"
IMAGES = {GAME_TAG, WEB_TAG}
BRAIN_IMAGE = f"{PROJECT}-brain:local"
BRAIN_VOLUMES = {"brain-socket", "brain-ledger"}
BRAIN_ROOT = Path("/var/lib/canary-human-qa-stage2")
IMAGE_LOCK = json.loads((HERE / "image-lock.json").read_text())
RECEIPT = HERE / PROFILE["evidence"] / "preflight-receipt.json"
UPGRADE_RECEIPT = HERE / PROFILE["evidence"] / "stage2-upgrade-receipt.json"
# Stage-2 upgrade only: runs the game of the pinned stage-1 baseline by its exact image ID, never a rebuild.
GAME_PIN = HERE / "compose.game-pin.yaml"
GAME_ENTRYPOINT = HERE.parent / "wsl/game-entrypoint.py"
CONFIG_DIST = HERE.parent.parent / "config.lua.dist"
SHUTDOWN_FLAG = "GAME_DISABLE_GLOBAL_SAVE_SHUTDOWN"
SHUTDOWN_KEY = "globalServerSaveShutdown"
CLOSE_KEY = "globalServerSaveClose"  # with both false the daily event calls saveServer() itself
GAME_DOCKERFILE = HERE.parent / "wsl/Dockerfile"
GAME_BASE_STAGES = {"FROM ${BASE_IMAGE} AS build", "FROM ${BASE_IMAGE} AS game"}
SHA256_ID = re.compile(r"sha256:[0-9a-f]{64}")


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


def game_base_spec():
    """The Ubuntu base locked for the QA game build; a placeholder or malformed pin fails closed."""
    spec = IMAGE_LOCK["game_base"]
    name, _, digest = spec["repo_digest"].partition("@")
    if (name != spec["ref"].split(":", 1)[0] or not SHA256_ID.fullmatch(digest)
            or not SHA256_ID.fullmatch(spec["id"]) or not re.fullmatch(r"linux/[a-z0-9]+", spec["platform"])):
        raise RuntimeError("game_base in image-lock.json is not a reviewed digest pin; fill it from the host receipt")
    return spec, f"{spec['ref']}@{digest}"


def assert_game_build(build):
    """QA builds the game FROM the digest-pinned base, without pull; production keeps the Dockerfile default."""
    _spec, pinned = game_base_spec()
    if (build.get("pull") is True or build.get("dockerfile") != "deployment/wsl/Dockerfile"
            or build.get("args", {}).get("BASE_IMAGE") != pinned):
        raise RuntimeError("QA game build must use the digest-pinned base from image-lock.json without pull")
    if not GAME_BASE_STAGES <= set(GAME_DOCKERFILE.read_text().splitlines()):
        raise RuntimeError("QA game Dockerfile stages do not build FROM ${BASE_IMAGE}")


def assert_game_base():
    """Read-only: the locked base is already local with the locked ID, platform and digest. Never pulls."""
    spec, _pinned = game_base_spec()
    try:
        found = command("docker", "image", "inspect", spec["repo_digest"], "--format",
                        "{{.Id}}\t{{.Os}}/{{.Architecture}}\t{{json .RepoDigests}}")
    except RuntimeError:
        raise RuntimeError("game base image is absent locally at the locked digest; review and load it "
                           "explicitly, the build never pulls it") from None
    actual, platform, digests = (found.strip().split("\t", 2) + ["", "[]"])[:3]
    if actual != spec["id"] or platform != spec["platform"] or spec["repo_digest"] not in json.loads(digests):
        raise RuntimeError("game base image differs from image-lock.json (ID, platform or digest)")
    return actual


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


def assert_compose(brain_fake=False, game_pin=None):
    """The rendered QA Compose. game_pin (stage-2 upgrade): the baseline game image ID that
    compose.game-pin.yaml must pin, so the game is never rebuilt, pulled or taken from a mutable tag."""
    env = os.environ.copy()
    revision = env.get("SOURCE_REVISION", "")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("SOURCE_REVISION must be the full reviewed commit SHA")
    if game_pin is not None and (not SHA256_ID.fullmatch(game_pin) or not GAME_PIN.is_file()):
        raise RuntimeError(f"{GAME_PIN.name} is absent or the baseline game image ID is malformed; "
                           "the stage-2 upgrade runs the baseline game image by its exact ID")
    for name in ("MARIADB_PASSWORD", "MARIADB_ROOT_PASSWORD", "BOT_PLAYERS_ONLINE"):
        env.pop(name, None)
    data = json.loads(command(
        "docker", "compose", "-p", PROJECT, "-f", "compose.yaml",
        *(["-f", "compose.brain-fake.yaml"] if brain_fake else []),
        *(["-f", GAME_PIN.name] if game_pin is not None else []),
        *[part for name in PROFILE["overlays"] + (PROFILE["brain_overlays"] if brain_fake else ())
          for part in ("-f", name)], "--env-file", ".env",
        "config", "--format", "json", env=env,
    ))
    expected_volumes = VOLUMES | BRAIN_VOLUMES if brain_fake else VOLUMES
    expected_services = SERVICES | {"brain"} if brain_fake else SERVICES
    if data.get("name") != PROJECT or set(data.get("services", {})) != expected_services:
        raise RuntimeError("Compose project/services differ from the reviewed QA stack")
    assert_profile_render(data)
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
    if services["web"].get("image") != WEB_TAG or services["game"].get("image") != (game_pin or GAME_TAG):
        raise RuntimeError("QA image tags differ from the reviewed stack" if game_pin is None else
                           f"{GAME_PIN.name} does not pin the baseline game image ID {game_pin}")
    if game_pin is not None and services["game"].get("pull_policy") != "never":
        raise RuntimeError(f"{GAME_PIN.name} must set pull_policy: never for the pinned game image")
    if services["database"].get("image") != IMAGE_LOCK["database"]["ref"]:
        raise RuntimeError("QA database image differs from the reviewed stack")
    if services["database"].get("pull_policy") != "never":
        raise RuntimeError("QA database must use the locked local image")
    if services["game"].get("build", {}).get("args", {}).get("SOURCE_REVISION") != revision:
        raise RuntimeError("QA game build revision differs from the reviewed source")
    assert_game_build(services["game"].get("build", {}))
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


def assert_profile_render(data, profile=None):
    """The render belongs to this profile: its project, host ports only from its own set (the game listens on
    the port it publishes and MyAAC advertises), and CPU/memory limits where the profile requires them.
    A stage-1 render under another profile, or another profile's render under stage 1, is refused."""
    profile = profile or PROFILE
    ports, services = profile["ports"], data.get("services", {})
    if data.get("name") != profile["project"]:
        raise RuntimeError(f"Compose project {data.get('name')!r} is not the {profile['name']} project "
                           f"{profile['project']}; refused")
    published = {"game": {ports["login"], ports["game"], ports["status"]}, "web": {ports["web"]}}
    expected = {
        "game": {"GAME_LOGIN_PORT": ports["login"], "GAME_PROTOCOL_PORT": ports["game"],
                 "GAME_STATUS_PORT": ports["status"]},
        "web": {"CANARY_SERVER_NAME": profile["server_name"], "CANARY_LOGIN_PORT": ports["login"],
                "CANARY_GAME_PORT": ports["game"],
                "CANARY_STATUS_PORT": ports["status"], "MYAAC_SITE_URL": f"http://127.0.0.1:{ports['web']}"},
    }
    for name, service in services.items():
        for port in service.get("ports", []):
            host = int(port.get("published") or 0)
            if host not in published.get(name, set()) or (name == "game" and host != int(port.get("target") or 0)):
                raise RuntimeError(f"{name} publishes {host}, not a {profile['name']} port; refused")
        environment = service.get("environment") or {}
        wrong = sorted(key for key, value in expected.get(name, {}).items()
                       if key in environment and str(environment[key]) != str(value))
        if wrong:
            raise RuntimeError(f"{name} {', '.join(wrong)} differ from profile {profile['name']}; refused")
        if profile["limits"] and not (service.get("cpus") and service.get("mem_limit")):
            raise RuntimeError(f"profile {profile['name']} needs CPU and memory limits on {name}; refused")


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
    observed["game_base"] = assert_game_base()
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
                  stage1=None, game_pin=None):
    receipt = {
        "schema_version": 1,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": PROJECT,
        **({"profile": PROFILE["name"]} if PROFILE["name"] != "stage1" else {}),
        "approved_source_revision": approved_revision,
        "observed_image_ids": images,
        "entrypoint_sha256": myaac["entrypoint_sha256"],
        "qa_config_sha256": myaac["qa_config_sha256"],
        "compose_redacted_sha256": compose_sha,
        "map_sha256": map_sha,
        "resources_absent": stage1 is None,
        "brain_fake": brain_fake,
        **({"stage1_upgrade": stage1} if stage1 else {}),
        # The tooling revision is approved_source_revision (HEAD); the game image keeps its own source
        # revision, recorded in stage1_upgrade.observed and never relabelled as HEAD.
        **({"game_image_pin": game_pin} if game_pin else {}),
        # Another profile: what its MyAAC config was attested from (stage-1 receipts keep their keys).
        **({"myaac_attestation": myaac["attestation"]} if "attestation" in myaac else {}),
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
    if receipt.get("project", PROFILES["stage1"]["project"]) != PROJECT:  # a receipt without one is stage 1's
        raise RuntimeError(f"receipt {receipt_path.name} is not of project {PROJECT}; refused")
    label = '{{index .Config.Labels "org.opencontainers.image.revision"}}'
    image_id, revision = (command("docker", "image", "inspect", BRAIN_IMAGE, "--format",
                                  "{{.Id}}\t" + label).strip().split("\t") + [""])[:2]
    running = command("docker", "inspect", f"{PROJECT}-brain-1", "--format", "{{.Image}}").strip()
    if receipt.get("approved_source_revision") != source or revision != source or running != image_id:
        raise RuntimeError("brain image, its source label and the receipt must match the approved HEAD")
    receipt["brain_image"] = {"id": image_id, "source_revision": revision}
    if "stage1_upgrade" in receipt:  # upgrade: the game before and after, and the stage-1 identities kept
        import stage1_baseline

        receipt["stage2_game"] = stage1_baseline.stage2_game(receipt["stage1_upgrade"])
    return save_receipt(receipt_path, receipt)


def run_preflight(resources_only=False, approved_revision=None, receipt_path=None, brain_fake=False,
                  upgrade=False):
    game_pin = None
    if upgrade:  # exact comparison with the reviewed stage-1 baseline, pinned by SHA-256 in stage1_baseline
        import stage1_baseline

        game_pin = stage1_baseline.baseline_game_image()
        compose_sha = assert_compose(True, game_pin=game_pin)
        stage1 = stage1_baseline.assert_stage1_upgrade()
    else:  # fresh first up, stage 1 or stage 2: unchanged
        compose_sha = assert_compose(brain_fake)
        stage1 = None
        assert_no_resources(brain_fake)
    images = assert_image_lock(brain_fake or upgrade)
    myaac = verify_myaac(PROFILE)
    if resources_only:
        return None
    source_sha = assert_source(approved_revision)
    map_sha = assert_map()
    return write_receipt(receipt_path or (UPGRADE_RECEIPT if upgrade or brain_fake else RECEIPT), source_sha,
                         compose_sha, images, myaac, map_sha, brain_fake or upgrade, stage1, game_pin)


def require_stage1(action):
    """Stage-1-only tools (baseline, rollout, rollback, upgrade, capture) refuse another profile at dispatch,
    before any git, Docker or file read: they act only on the pinned canary-core-qa."""
    if PROFILE["name"] != "stage1":
        raise RuntimeError(f"{action} is stage-1 only (project {PROFILES['stage1']['project']}); refused under "
                           f"CORE_QA_PROFILE={PROFILE['name']} (project {PROJECT})")


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
    if args.capture_stage1_baseline or args.upgrade_from_stage1:
        require_stage1("--capture-stage1-baseline" if args.capture_stage1_baseline else "--upgrade-from-stage1")
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
