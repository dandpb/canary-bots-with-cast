"""Stage-2 handoff adapter for canary-core-qa over the a1d9 brain build. QA only, never production.

Why an adapter: at a1d9 the upgrade gate refuses the brain image its own authorized build made
(stage1_baseline.assert_stage1_upgrade -> assert_images(brain_allowed=False)), and the documented
order has no gate between that build and the up. The a1d9 gates and `preflight.py --record-brain-image`
stay as they are, strict. This file adds explicit phases around them and never relabels anything:
the tooling revision (the a1d9 checkout), the brain image revision (its label) and the game image
revision (its label, 3431b404...) are recorded apart.

How it runs: reviewed and merged in the repo, but executed as a COPY pinned by its sha256, from
outside the a1d9 checkout. `--source-checkout` is the clean a1d9 checkout: only the source of the
read-only tooling (preflight.py, stage1_baseline.py, imported, never patched) and of the a1d9
recorder. The Compose project directory is the ORIGINAL QA runtime directory named by the pinned
bundle manifest (`qa_project_directory`, with its `.env`). Nothing in the source checkout, and no
scratch copy outside the project directory, may become a `-f` file, a mount or the project directory.

What the pinned manifest binds (and the adapter checks, live, against it):
- every receipt by absolute path and sha256 (`receipt_files`);
- the brain image by full ID, platform, revision label and tag (`brain_image`), against live inspect;
- the rescue container's config by `rescue_container_config.config_sha256`, computed exactly as
  `container()` does: sha256(json.dumps({"config", "host_config"}, sort_keys=True)), Python defaults;
- the original `.env` by the sha256 of its raw bytes (`env_file`);
- the render by the sha256 of the raw stdout of `render_argv` and by its sanitized form.

Who executes what:
- The adapter runs every check. Every phase is read-only and writes one sealed JSON receipt that
  cites the previous one (path and sha256). A phase that leads to a mutation seals its exact argv
  in the receipt (`step`).
- Pitagoras, on the WSL host, runs the phases and runs each mutation ONLY as
  `stage2_handoff.py exec-step --receipt <receipt> --receipt-sha256 <sha>`. exec-step refreshes
  every gate of that step right before the mutation, then takes a durable claim (O_CREAT|O_EXCL,
  fsync of the file and of its directory) at a canonical place under the manifest's project
  directory, keyed by the receipt sha256 and the step and never by `--evidence`. Only then the
  sealed argv runs, once. A claim without a result (a crash, a failed receipt write) stays
  consumed: HOLD, never retried. Nobody retypes a command.
- Nothing runs `up` on its own: `bundle` seals the up argv; only an exec-step of that receipt runs it.
  After the up, the a1d9 recorder (`preflight.py --record-brain-image`, from the source checkout) stays the check.
- The return path is `fallback-plan` -> exec-step -> `fallback-verify` -> exec-step (start the
  rescue container once) -> `rescue-verify` (a FRESH health check: the rescue counts as usable only
  then). The a1d9 `stage1_baseline.py rollback` renders Compose from its own checkout directory,
  so it is not run from the isolated source checkout.

The two fallbacks outside Compose (`qa-game-candidate-3431b404`, `qa-old-rescue-20261107`) are
exited with a stale "unhealthy" Health. While stopped that Health is ignored; they must be exited
with code 0, restart=no and match the pinned ID, config and ownership. A started container never
counts on its old Health.

Phases (`<phase> --help` for the inputs):
  post-build       every manifest receipt by path and hash; brain image by ID, platform, label and tag
                   (manifest and live); .env raw bytes; no brain container or volume; identities and
                   the exact DB slice; rescue and candidate stopped; binds equal to the host paths
  pre-stop         fresh live gate (running/healthy + exact slice), rescue and candidate, human
                   exclusion (game roster, QA humans offline, no TCP sessions on the game ports, the
                   coordinator's window notice by sha256); seals `docker stop -t 180 <game ID>`
  post-stop        no running/healthy gate for the game only: same ID, CreatedAt, image and config,
                   exited with code 0. DB and web stay running/healthy EXACTLY; network, volumes and
                   the SAME exact slice. Drift is HOLD
  bundle           the pinned 4 Compose files, 2 fake configs and .env, the post-stop state again,
                   others preserved, zero writers, the render (private and sanitized hash), the
                   environment values per key (hashes only) and the binds; seals the up argv
  fallback-plan    rescue bound to the manifest; seals the stop of the NEW game/brain containers
  fallback-verify  new containers stopped, other games preserved, zero DB writers; seals the
                   single start of the rescue
  rescue-verify    after that start: the rescue runs and is healthy by a check newer than its start
  exec-step        refreshes the gates of one sealed step, claims it, runs its argv once
"""

import argparse
import hashlib
import json
import os
import posixpath
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SCHEMA = "qa-stage2-handoff-v2"
ADAPTER_PATH = "deployment/core-qa/stage2_handoff.py"
TOOLING_REVISION = (
    "a1d9fe803c77da63f4aa1bf943d3d488d3117850"  # the source checkout and its preflight
)
BRAIN_REVISION = (
    "a1d9fe803c77da63f4aa1bf943d3d488d3117850"  # the label of the built brain image
)
BRAIN_IMAGE_ID = (
    "sha256:9ea0a34688db0443dabfa6c64736f78b53e954a19c9ead8c61d52f2bbdefa0cd"
)
BRAIN_PLATFORM = "linux/amd64"
MANIFEST_SHA256 = "bc4fb5af6c1ff5ff76e08ac15125b463222bcbc27dc98b7b35a75f7f4f4202f0"
RESCUE_ID = "64385641c847ad44d6acf1dc7f5d10e206451212b4320973a27ba278e428d608"
CANDIDATE_ID = "4188037d71a5455ef40e76e05d0fa145a9e71d977a10f0774e491286b968b605"
RESCUE_PREFIX = "qa-old-rescue-"
CANDIDATE_PREFIX = "qa-game-candidate-"
PRIVATE_OVERRIDE = "compose.image-ids.yaml"  # pinned by its manifest hash only
COMPOSE_FILES = (
    "compose.yaml",
    "compose.brain-fake.yaml",
    "compose.game-pin.yaml",
    PRIVATE_OVERRIDE,
)
CONFIGS = {
    "brain/server.json": "/etc/canary-core-qa/brain/server.json",
    "brain/worker.json": "/etc/canary-core-qa/brain/worker.json",
}
RECEIPT_KEYS = (  # the receipts post-build also takes on its command line (optional)
    "stage2_full_preflight",
    "brain_before",
    "brain_after",
    "brain_build_log",
)
REQUIRED_RECEIPTS = {*RECEIPT_KEYS, "rescue_result", "stage1_baseline"}
UP_ARGS = ["up", "-d", "--no-build", "--no-deps", "--pull", "never", "--wait"]
UP_ARGS += ["--wait-timeout", "180", "-t", "180", "game", "brain"]
STOP = ["docker", "stop", "-t", "180"]
STEP_MAX_AGE = timedelta(minutes=15)
ATTESTATION_MAX_AGE = timedelta(minutes=30)
CLOCK_SKEW = timedelta(seconds=30)  # WSL host clock vs the Docker Desktop VM clock
CLAIMS = "runtime/evidence/stage2-handoff-claims"  # under the manifest's project directory, only
RUNNING = {"running", "restarting", "paused"}
HEX64 = re.compile(r"[0-9a-f]{64}")
REVISION = re.compile(r"[0-9a-f]{40}")
# Docker Desktop on WSL: inspect shows a bind's host path translated, either path for path under
# /run/desktop/mnt/host/wsl/<distro>/... or as docker-desktop-bind-mounts/<distro>/<sha256 of the
# host path> (what the pinned manifest shows for the world map and the initdb directory).
DESKTOP_ROOT = "/run/desktop/mnt/host/wsl"
DESKTOP_BINDS = f"{DESKTOP_ROOT}/docker-desktop-bind-mounts"
WSL_DISTRO = "Ubuntu"
# Human exclusion. players_online is the game's own roster table: bots (account 65000) are kept
# there by bot_manager.lua, real players by a 10-minute sweep (Game::updatePlayersOnline), so the
# live TCP sessions on the login and game ports are checked too, inside the game container.
BOT_ACCOUNT = 65000
SESSION_PORTS = (17171, 17172)  # GAME_LOGIN_PORT, GAME_PROTOCOL_PORT
ROSTER_SQL = (
    "SELECT 'online', o.player_id, COALESCE(p.account_id, -1) FROM players_online o "
    "LEFT JOIN players p ON p.id = o.player_id ORDER BY o.player_id;"
)
TCP_PROBE = ("cat", "/proc/net/tcp", "/proc/net/tcp6")
TCP_ESTABLISHED = "01"
WRITERS_SQL = (
    "SELECT COUNT(*) FROM information_schema.PROCESSLIST "
    "WHERE ID <> CONNECTION_ID() AND COMMAND <> 'Daemon';"
)
CONTAINER = (
    '{"id":{{json .Id}},"name":{{json .Name}},"created_at":{{json .Created}},'
    '"image_id":{{json .Image}},"status":{{json .State.Status}},'
    '"exit_code":{{json .State.ExitCode}},"restart":{{json .HostConfig.RestartPolicy.Name}},'
    '"health":{{if .State.Health}}{{json .State.Health.Status}}{{else}}null{{end}},'
    '"labels":{{json .Config.Labels}},"mounts":{{json .Mounts}},'
    '"config":{{json .Config}},"host_config":{{json .HostConfig}}}'
)
HEALTH_PROBE = (
    '{"status":{{json .State.Status}},"started_at":{{json .State.StartedAt}},'
    '"health":{{if .State.Health}}{{json .State.Health}}{{else}}null{{end}}}'
)
BRAIN_INSPECT = (
    "{{.Id}}\t{{.Os}}/{{.Architecture}}\t"
    '{{index .Config.Labels "org.opencontainers.image.revision"}}'
)
OWNED = '{{.ID}}\t{{.Label "com.docker.compose.service"}}\t{{.State}}'
IDENTITY = ("id", "name", "created_at", "image_id", "restart", "labels", "mounts")


def utcnow() -> datetime:
    return datetime.now(UTC)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(argv: list[str]) -> str:
    return sha256(json.dumps(argv, separators=(",", ":")).encode())


def config_digest(config: dict[str, Any]) -> str:
    """The rescue config hash of the manifest: {"config", "host_config"}, sort_keys, Python defaults."""
    return sha256(json.dumps(config, sort_keys=True).encode())


def read(path: Path) -> bytes:
    return path.read_bytes() if path.is_file() else b""


def git_blob(repo: Path, revision: str, path: str) -> bytes | None:
    found = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "blob", f"{revision}:{path}"],
        check=False,
        capture_output=True,
    )
    return None if found.returncode else found.stdout


def execute(argv: list[str]) -> tuple[int, str, str]:
    """The only place a mutation runs: the argv sealed in a receipt, nothing else."""
    result = subprocess.run(argv, check=False, text=True, capture_output=True)
    return result.returncode, result.stdout, result.stderr


def load_tooling(source: Path) -> tuple[Any, Any]:
    """Import preflight and stage1_baseline from the source checkout, read-only, without bytecode."""
    core = (source / "deployment/core-qa").resolve()
    sys.dont_write_bytecode = True
    if str(core) not in sys.path:
        sys.path.insert(0, str(core))
    import preflight
    import stage1_baseline

    for module in (preflight, stage1_baseline):
        if Path(str(module.__file__)).resolve().parent != core:
            raise RuntimeError(
                f"{module.__name__} was not loaded from the source checkout; refused"
            )
    return preflight, stage1_baseline


def mounts(items: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Docker inspect mounts in the manifest's shape, sorted by destination."""
    normal = [
        {
            "destination": item.get("Destination", item.get("destination")),
            "rw": item.get("RW", item.get("rw")),
            "source": item.get("Source", item.get("source")),
            "type": item.get("Type", item.get("type")),
        }
        for item in items or []
    ]
    return sorted(normal, key=lambda item: str(item["destination"]))


def desktop_form(inspected: str, host: str) -> str | None:
    """How an inspected bind source names a host path, or None when it names another path.

    Explicit and exact: the host path itself, Docker Desktop's path translation
    /run/desktop/mnt/host/wsl/<distro><host path>, or its hashed form
    /run/desktop/mnt/host/wsl/docker-desktop-bind-mounts/<distro>/<sha256(host path)>.
    Only the pinned distro, only a normalized absolute host path.
    """
    if not host.startswith("/") or posixpath.normpath(host) != host:
        return None
    forms = {
        host: "host",
        f"{DESKTOP_ROOT}/{WSL_DISTRO}{host}": "desktop-path",
        f"{DESKTOP_BINDS}/{WSL_DISTRO}/{sha256(host.encode())}": "desktop-hash",
    }
    return forms.get(inspected)


def env_pairs(env: list[str] | None) -> dict[str, str]:
    """Docker Config.Env as KEY -> VALUE (the last one wins, as in Docker)."""
    pairs = {}
    for entry in env or []:
        key, _sep, value = entry.partition("=")
        pairs[key] = value
    return pairs


def env_hashes(pairs: dict[str, Any]) -> dict[str, str]:
    """Per key, sha256 of KEY=VALUE. Values never leave this function."""
    return {
        key: sha256(f"{key}={'' if value is None else value}".encode())
        for key, value in sorted(pairs.items())
    }


def sanitized(render: dict[str, Any]) -> bytes:
    """The render with every environment value hidden, as Pitagoras's sanitized render is written."""
    copy = json.loads(json.dumps(render))
    for service in copy.get("services", {}).values():
        if service.get("environment"):
            service["environment"] = {
                key: "<redacted>" for key in service["environment"]
            }
    return (json.dumps(copy, indent=2, sort_keys=True) + "\n").encode()


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def create_exclusive(path: Path, content: bytes) -> bool:
    """Create path atomically (O_CREAT|O_EXCL), write and fsync it and its directory. False if it exists."""
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    try:
        view = memoryview(content)
        while view:
            view = view[os.write(descriptor, view) :]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    fsync_directory(path.parent)
    return True


class Handoff:
    def __init__(
        self,
        source: Path,
        manifest: Path,
        manifest_sha256: str = MANIFEST_SHA256,
        evidence: Path | None = None,
        adapter_sha256: str = "",
        adapter_revision: str = "",
        adapter_repo: Path | None = None,
    ) -> None:
        self.source = source.resolve()
        content = Path(__file__).read_bytes()
        if sha256(content) != adapter_sha256:
            raise RuntimeError(
                "this adapter copy differs from its pinned sha256; refused"
            )
        repo = adapter_repo or self.source
        if (
            not REVISION.fullmatch(adapter_revision)
            or git_blob(repo, adapter_revision, ADAPTER_PATH) != content
        ):
            raise RuntimeError(
                "this adapter is not the reviewed file at --adapter-revision; refused"
            )
        self.qa, self.s1 = load_tooling(self.source)
        raw = read(manifest)
        if not raw or sha256(raw) != manifest_sha256:
            raise RuntimeError(
                f"bundle manifest {manifest.name} is absent or not the pinned one; refused"
            )
        self.manifest = json.loads(raw)
        self.baseline = self.s1.load_baseline()
        self.game = next(
            c for c in self.baseline["containers"] if c["name"] == self.s1.GAME
        )
        self.plan = self.manifest_plan()
        self.assert_source_checkout()
        project = self.plan["project"]
        self.evidence = (
            evidence or project / "runtime/evidence/stage2-handoff"
        ).resolve()
        self.claims = (project / CLAIMS).resolve()  # canonical: never from --evidence
        self.outside_source(self.evidence, self.claims)
        brain = self.plan["brain"]
        self.header = {
            "source_checkout": {"path": str(self.source), "revision": TOOLING_REVISION},
            "deployment_project_directory": str(project),
            "provenance": {
                "adapter": {"sha256": adapter_sha256, "revision": adapter_revision},
                "manifest": {
                    "path": str(manifest.resolve()),
                    "sha256": manifest_sha256,
                },
                "stage1_baseline_sha256": self.s1.BASELINE_SHA256,
                "tooling_revision": TOOLING_REVISION,
                "brain_image": {
                    "id": brain["id"],
                    "source_revision": brain["source_revision_label"],
                    "platform": brain["platform"],
                },
                "game_image": {
                    "id": self.game["image_id"],
                    "source_revision": self.game["image_source_revision"],
                },
            },
        }
        self.chain: list[dict[str, Any]] = []
        self.previous: dict[str, Any] | None = None
        self.stopped = False

    # -- static checks ---------------------------------------------------------------------------

    def outside_source(self, *paths: Path) -> None:
        for path in paths:
            if Path(path).is_relative_to(self.source) or self.source.is_relative_to(
                path
            ):
                raise RuntimeError(
                    f"{path} is inside the source checkout (or contains it); refused"
                )

    def assert_source_checkout(self) -> None:
        head = self.qa.command("git", "rev-parse", "HEAD").strip()
        dirty = self.qa.command(
            "git", "status", "--porcelain", "--untracked-files=all"
        ).strip()
        if head != TOOLING_REVISION or dirty:
            raise RuntimeError(
                f"source checkout must be clean at {TOOLING_REVISION}; refused"
            )

    def pinned_outside_compose(self, prefix: str, ident: str) -> tuple[str, dict]:
        """The one manifest container named <prefix>*: the reviewed ID, no Compose owner, stopped, restart=no."""
        named = [
            (name, item)
            for name, item in self.manifest["containers"].items()
            if name.startswith(prefix)
        ]
        if (
            len(named) != 1
            or named[0][1].get("id") != ident
            or named[0][1].get("name") != named[0][0]
            or any(named[0][1].get("compose_labels", {}).values())
            or named[0][1].get("restart_policy") != "no"
            or named[0][1].get("status") != "exited"
        ):
            raise RuntimeError(
                f"manifest {prefix}* is not the one stopped, unowned container {ident[:12]}; refused"
            )
        return named[0]

    def manifest_plan(self) -> dict[str, Any]:
        """The pinned manifest, offline: paths, hashes, a1d9 bytes, argv and the stage-1 identities."""
        m, qa, core = self.manifest, self.qa, self.source / "deployment/core-qa"
        project, bundle = Path(m["qa_project_directory"]), Path(m["bundle_directory"])
        env_file = Path(m["env_file_path"])
        if (
            m.get("approved_revision") != TOOLING_REVISION
            or m["receipts"].get("stage1_baseline") != self.s1.BASELINE_SHA256
        ):
            raise RuntimeError(
                "manifest names another revision or stage-1 baseline; refused"
            )
        if (
            not project.is_absolute()
            or env_file != project / ".env"
            or not bundle.is_relative_to(project)
        ):
            raise RuntimeError(
                "manifest project directory, .env or bundle directory are inconsistent; refused"
            )
        self.outside_source(project, bundle, env_file)
        brain = m.get("brain_image") or {}
        if brain != {
            "id": BRAIN_IMAGE_ID,
            "platform": BRAIN_PLATFORM,
            "source_revision_label": BRAIN_REVISION,
            "tag": qa.BRAIN_IMAGE,
        } or (
            m.get("brain_image_id"),
            m.get("brain_platform"),
            m.get("brain_revision"),
        ) != (
            BRAIN_IMAGE_ID,
            BRAIN_PLATFORM,
            BRAIN_REVISION,
        ):
            raise RuntimeError(
                "manifest brain_image is not the reviewed ID, platform, label and tag; refused"
            )
        receipts = m.get("receipt_files") or {}
        if set(receipts) != set(m["receipts"]) or not REQUIRED_RECEIPTS <= set(
            receipts
        ):
            raise RuntimeError(
                "manifest receipt_files do not cover every pinned receipt; refused"
            )
        for key, entry in receipts.items():
            path = Path(str(entry.get("absolute_path", "")))
            if (
                not path.is_absolute()
                or posixpath.normpath(str(path)) != str(path)
                or entry.get("sha256") != m["receipts"][key]
                or not HEX64.fullmatch(str(entry.get("sha256")))
            ):
                raise RuntimeError(
                    f"manifest receipt {key} has no absolute path or another sha256; refused"
                )
            self.outside_source(path)
        env = m.get("env_file") or {}
        if Path(str(env.get("absolute_path", ""))) != env_file or not HEX64.fullmatch(
            str(env.get("sha256"))
        ):
            raise RuntimeError(
                "manifest env_file has no raw-bytes sha256 for the original .env; refused"
            )
        verification = m.get("verification") or {}
        if verification != {
            "brain_id_in_brain_after": True,
            "brain_id_in_brain_before": False,
            "render_private_recomputed_sha256": m.get("render_private_sha256"),
            "render_recomputed_equal_to_original_stdout_bytes": True,
        } or not HEX64.fullmatch(str(m.get("render_private_sha256"))):
            raise RuntimeError(
                "manifest verification does not confirm the render and brain receipts; refused"
            )
        files = {}
        for name in (*COMPOSE_FILES, *CONFIGS):
            entry = m["bundle_files"].get(name) or {}
            if Path(
                entry.get("absolute_path", "")
            ) != bundle / name or not HEX64.fullmatch(str(entry.get("sha256"))):
                raise RuntimeError(
                    f"manifest entry for {name} is missing or outside the bundle; refused"
                )
            if name != PRIVATE_OVERRIDE and (
                entry.get("matches_a1d9_source") is not True
                or sha256(read(core / name)) != entry["sha256"]
            ):
                raise RuntimeError(
                    f"bundle {name} is not byte-identical to the a1d9 source; refused"
                )
            files[name] = entry
        if set(m["bundle_files"]) != set(files):
            raise RuntimeError(
                "manifest has bundle files beyond the 4 Compose files and 2 fake configs; refused"
            )
        drop = self.s1.COMPOSE_ENV_DROP
        prefix = [
            "env",
            *[part for key in drop for part in ("-u", key)],
            f"SOURCE_REVISION={TOOLING_REVISION}",
        ]
        prefix += [
            "docker",
            "compose",
            "--project-directory",
            str(project),
            "-p",
            qa.PROJECT,
        ]
        prefix += [
            part
            for name in COMPOSE_FILES
            for part in ("-f", files[name]["absolute_path"])
        ]
        prefix += ["--env-file", str(env_file)]
        render, up = prefix + ["config", "--format", "json"], prefix + UP_ARGS
        for key, argv in (("render_argv", render), ("future_up_argv_not_executed", up)):
            if m.get(key) != argv or m[key].count("-f") != len(COMPOSE_FILES):
                raise RuntimeError(
                    f"manifest {key} is not the 4-file argv with the original project and .env; refused"
                )
        if sorted(m["env_file_variable_names_only"]) != sorted(drop):
            raise RuntimeError(
                "the .env holds variables the sanitized env does not drop; refused"
            )
        for item in self.baseline["containers"]:
            pinned = m["containers"].get(item["name"]) or {}
            if any(
                pinned.get(key) != item[key] for key in ("id", "image_id", "created_at")
            ):
                raise RuntimeError(
                    f"manifest {item['name']} differs from the pinned baseline; refused"
                )
        rescue = self.pinned_outside_compose(RESCUE_PREFIX, RESCUE_ID)
        candidate = self.pinned_outside_compose(CANDIDATE_PREFIX, CANDIDATE_ID)
        known = {c["name"] for c in self.baseline["containers"]}
        if set(m["containers"]) != known | {rescue[0], candidate[0]}:
            raise RuntimeError(
                "manifest containers are not the 3 stage-1 ones, the rescue and the candidate; refused"
            )
        config = m.get("rescue_container_config") or {}
        stopped = m.get("rescue_stopped_state") or {}
        if (
            config.get("container_id") != RESCUE_ID
            or not HEX64.fullmatch(str(config.get("config_sha256")))
            or config.get("adapter_config_sha256") != config.get("config_sha256")
            or (
                stopped.get("status"),
                stopped.get("exit_code"),
                stopped.get("restart_policy"),
            )
            != ("exited", 0, "no")
        ):
            raise RuntimeError(
                "manifest rescue config hash or stopped state is not the adapter's; refused"
            )
        network = self.baseline["network"]
        volumes = {v["name"]: v["created_at"] for v in self.baseline["volumes"]}
        if (m["network"]["id"], m["network"]["created_at"]) != (
            network["id"],
            network["created_at"],
        ) or {v["name"]: v["created_at"] for v in m["volumes"].values()} != volumes:
            raise RuntimeError(
                "manifest network or volumes differ from the pinned baseline; refused"
            )
        return {
            "project": project,
            "bundle": bundle,
            "env_file": env_file,
            "env_sha256": env["sha256"],
            "files": files,
            "receipts": receipts,
            "render": render,
            "up": up,
            "brain": brain,
            "rescue": rescue,
            "candidate": candidate,
            "rescue_config_sha256": config["config_sha256"],
        }

    def check_env_file(self) -> dict[str, str]:
        raw = read(self.plan["env_file"])
        if not raw or sha256(raw) != self.plan["env_sha256"]:
            raise RuntimeError(
                "the original .env is absent or its raw bytes differ from the pinned sha256; refused"
            )
        return {"path": str(self.plan["env_file"]), "sha256": sha256(raw)}

    def check_bundle_files(self) -> dict[str, Any]:
        for name, entry in self.plan["files"].items():
            data = read(Path(entry["absolute_path"]))
            if len(data) != entry["bytes"] or sha256(data) != entry["sha256"]:
                raise RuntimeError(
                    f"bundle file {name} differs from the pinned manifest; refused"
                )
        self.check_env_file()
        return {
            name: {"path": e["absolute_path"], "sha256": e["sha256"]}
            for name, e in self.plan["files"].items()
        }

    def bound_receipt(self, key: str) -> tuple[dict[str, str], bytes]:
        """A receipt by the manifest's absolute path and sha256, nothing else."""
        entry = self.plan["receipts"][key]
        path, raw = Path(entry["absolute_path"]), read(Path(entry["absolute_path"]))
        if not raw or sha256(raw) != entry["sha256"]:
            raise RuntimeError(
                f"{key} receipt at {path} is absent or not the one the manifest pins; refused"
            )
        return {"path": str(path), "sha256": entry["sha256"]}, raw

    # -- live checks (read-only) ---------------------------------------------------------------

    def assert_brain_image(self) -> dict[str, str]:
        """By full ID and by tag: exactly the manifest's image, its platform and its own label."""
        brain = self.plan["brain"]
        expected = [brain["id"], brain["platform"], brain["source_revision_label"]]
        for ref in (brain["id"], brain["tag"]):
            try:
                found = (
                    self.qa.command(
                        "docker", "image", "inspect", ref, "--format", BRAIN_INSPECT
                    )
                    .strip()
                    .split("\t")
                )
            except RuntimeError:
                found = []
            if found != expected:
                raise RuntimeError(
                    f"brain image {ref} is not {brain['id']} {brain['platform']} labelled "
                    f"{brain['source_revision_label']}; refused"
                )
        return {
            "id": brain["id"],
            "platform": brain["platform"],
            "source_revision": brain["source_revision_label"],
            "tag": brain["tag"],
        }

    def live_gate(self) -> dict[str, Any]:
        """Running/healthy stage 1 equal to the baseline with the exact DB slice. Only before the stop."""
        s1 = self.s1
        if self.stopped:
            raise RuntimeError(
                "a running/healthy gate was called after the stop; refused"
            )
        s1.qa_objects(stage2=False)  # no brain container or volume, nothing foreign
        self.assert_brain_image()
        s1.assert_web_image(self.baseline)
        s1.assert_game_image(self.baseline)
        if self.baseline["db_logical_snapshot"].get("sql_sha256") not in (
            None,
            s1.DB_SLICE_SQL_SHA256,
        ):
            raise RuntimeError(
                "the baseline DB slice was taken with another query; refused"
            )
        now = s1.comparable(s1.observe())
        changes = s1.differences(s1.comparable(self.baseline), now)
        if changes:
            raise RuntimeError(
                "stage 1 differs from the pinned baseline; refused:\n"
                + "\n".join(changes)
            )
        return dict(now)

    def stage1_after_stop(self) -> list[str]:
        """Differences from the baseline once the game is stopped: only the game may be exited.

        DB and web keep their exact identity, status and health; the game keeps its identity,
        its status must be exited and only its (now stale) health is left out.
        """
        expected = self.s1.comparable(self.baseline)
        expected.pop("db_slice", None)
        now = self.s1.comparable(self.s1.observe(db=False))
        want, got = (
            expected["containers"].get(self.s1.GAME),
            now["containers"].get(self.s1.GAME),
        )
        if want is not None and got is not None:
            want, got = {**want, "status": "exited"}, dict(got)
            want.pop("health", None)
            got.pop("health", None)
            expected["containers"][self.s1.GAME] = want
            now["containers"][self.s1.GAME] = got
        return list(self.s1.differences(expected, now))

    def container(self, ident: str) -> dict[str, Any] | None:
        try:
            item = json.loads(
                self.qa.command("docker", "inspect", ident, "--format", CONTAINER)
            )
        except RuntimeError:
            return None
        config = {"config": item.pop("config"), "host_config": item.pop("host_config")}
        item["config_sha256"] = config_digest(config)
        item["env_sha256"] = env_hashes(env_pairs((config["config"] or {}).get("Env")))
        item["name"] = item["name"].lstrip("/")
        item["labels"] = {
            k: v
            for k, v in self.s1.compose_labels(
                item["labels"], ("project", "service", "config-hash")
            ).items()
            if v
        }
        item["mounts"] = mounts(item["mounts"])
        return dict(item)

    def owned(self) -> list[dict[str, str]]:
        """game/brain containers of the QA project by ownership labels, other than the stage-1 game."""
        rows = self.qa.command(
            "docker",
            "ps",
            "-a",
            "--no-trunc",
            "--filter",
            f"label=com.docker.compose.project={self.qa.PROJECT}",
            "--format",
            OWNED,
        )
        found = [
            dict(zip(("id", "service", "state"), row.split("\t"), strict=True))
            for row in rows.splitlines()
            if row.strip()
        ]
        return [
            row
            for row in found
            if row["service"] in ("game", "brain") and row["id"] != self.game["id"]
        ]

    def writers(self) -> int:
        found = self.s1.mariadb(WRITERS_SQL).split()
        if found != ["0"]:
            raise RuntimeError(
                f"the database still has {found or 'unknown'} other connections (writers); refused"
            )
        return 0

    def assert_stage1_pins(self) -> dict[str, Any]:
        """database, game and web: the manifest's ID, image, CreatedAt, restart policy and mounts."""
        found = {}
        for item in self.baseline["containers"]:
            pinned = self.manifest["containers"][item["name"]]
            live = self.container(item["id"])
            if not live or (
                live["id"],
                live["image_id"],
                live["created_at"],
                live["restart"],
                live["mounts"],
            ) != (
                pinned["id"],
                pinned["image_id"],
                pinned["created_at"],
                pinned["restart_policy"],
                mounts(pinned["mounts"]),
            ):
                raise RuntimeError(
                    f"{item['name']} differs from the manifest (ID, image, restart or mounts); refused"
                )
            found[item["name"]] = live
        return found

    def stopped_outside_compose(
        self, pinned: tuple[str, dict], config_sha256: str | None = None
    ) -> dict[str, Any]:
        """A fallback outside Compose while stopped: exited 0, restart=no, pinned ID, config and owner.

        Its Health field is stale while it is exited ("unhealthy" in the manifest) and is ignored
        here; a start only counts after `fresh_health`.
        """
        name, item = pinned
        live = self.container(item["id"])
        expected = {
            "id": item["id"],
            "name": name,
            "created_at": item["created_at"],
            "image_id": item["image_id"],
            "restart": item["restart_policy"],
            "mounts": mounts(item["mounts"]),
            "labels": {k: v for k, v in item["compose_labels"].items() if v},
        }
        if config_sha256:
            expected["config_sha256"] = config_sha256
        if not live:
            raise RuntimeError(f"{name} {item['id'][:12]} is absent; refused")
        changed = [key for key, value in expected.items() if live[key] != value]
        if changed:
            raise RuntimeError(
                f"{name} differs from the manifest ({', '.join(changed)}); refused"
            )
        if (live["status"], live["exit_code"], live["restart"]) != ("exited", 0, "no"):
            raise RuntimeError(
                f"{name} must be stopped (exited, exit code 0) with restart=no, it is "
                f"{live['status']}/{live['exit_code']}/{live['restart']}; refused"
            )
        return live

    def rescue(
        self, rescue_id: str | None = None, receipt: Path | None = None
    ) -> dict[str, Any]:
        """The rescue container: the manifest's ID, config hash, image, mounts and ownership; stopped."""
        entry = self.plan["receipts"]["rescue_result"]
        if (rescue_id is not None and rescue_id != RESCUE_ID) or (
            receipt is not None
            and Path(receipt).resolve() != Path(entry["absolute_path"]).resolve()
        ):
            raise RuntimeError(
                "the rescue container is not the one the manifest and the rescue receipt name; refused"
            )
        self.bound_receipt("rescue_result")
        return self.stopped_outside_compose(
            self.plan["rescue"], self.plan["rescue_config_sha256"]
        )

    def candidate(self) -> dict[str, Any]:
        return self.stopped_outside_compose(self.plan["candidate"])

    def fallbacks(self) -> dict[str, Any]:
        """Before any forward mutation: the rescue and the candidate exist, stopped, as pinned."""
        return {"rescue": self.rescue(), "candidate": self.candidate()}

    def others_preserved(self, rescue_id: str | None = None) -> dict[str, Any]:
        try:
            found = self.fallbacks()
        except RuntimeError as error:
            raise RuntimeError(
                f"other games are not preserved and stopped: {error}"
            ) from None
        old = self.container(self.game["id"])
        if old and old["status"] in RUNNING:
            raise RuntimeError("the stage-1 game container is running again; refused")
        return found

    def fresh_health(self, ident: str, since: datetime) -> dict[str, Any]:
        """A started container counts only on a health check newer than its start (and than `since`)."""
        try:
            probe = json.loads(
                self.qa.command("docker", "inspect", ident, "--format", HEALTH_PROBE)
            )
        except RuntimeError:
            probe = {}
        health = probe.get("health") or {}
        last = (health.get("Log") or [{}])[-1]
        try:
            started = self.s1.docker_time(probe.get("started_at"))
            checked = self.s1.docker_time(last.get("End"))
        except RuntimeError:
            started = checked = None
        if (
            probe.get("status") != "running"
            or health.get("Status") != "healthy"
            or last.get("ExitCode") != 0
            or started is None
            or checked is None
            or started < since - CLOCK_SKEW
            or checked <= started
        ):
            raise RuntimeError(
                f"container {ident[:12]} has no fresh healthy check since its start; a stale Health "
                "never counts; refused"
            )
        return {
            "status": "running",
            "health": "healthy",
            "started_at": probe["started_at"],
            "last_check_end": last["End"],
        }

    def game_connections(self) -> int:
        """Established TCP sessions on the login and game ports, from inside the stage-1 game."""
        text = self.qa.command("docker", "exec", self.game["id"], *TCP_PROBE)
        ports = {f"{port:04X}" for port in SESSION_PORTS}
        headers, count = 0, 0
        for line in text.splitlines():
            fields = line.split()
            if fields[:1] == ["sl"]:
                headers += 1
            elif (
                len(fields) >= 4
                and fields[1].rpartition(":")[2] in ports
                and fields[3] == TCP_ESTABLISHED
            ):
                count += 1
        if headers != len(TCP_PROBE) - 1:
            raise RuntimeError(
                "the game TCP probe returned an unexpected shape; refused"
            )
        return count

    def human_exclusion(self, notice: Path, notice_sha256: str) -> dict[str, Any]:
        """Evidence that no human plays: roster, QA humans offline, no sessions, the window notice."""
        raw = read(Path(notice))
        if (
            not raw
            or not HEX64.fullmatch(notice_sha256)
            or sha256(raw) != notice_sha256
        ):
            raise RuntimeError(
                "the coordinator's window notice is absent or not the given sha256; refused"
            )
        self.outside_source(Path(notice))
        rows = [
            r.split("\t") for r in self.s1.mariadb(ROSTER_SQL).splitlines() if r.strip()
        ]
        if any(
            len(r) != 3
            or r[0] != "online"
            or not all(re.fullmatch(r"-?\d+", x) for x in r[1:])
            for r in rows
        ):
            raise RuntimeError(
                "the game roster probe returned an unexpected shape; refused"
            )
        online = [(int(r[1]), int(r[2])) for r in rows]
        humans = [
            player
            for player, account in online
            if account != BOT_ACCOUNT or player >= self.s1.QA_PLAYER_FLOOR
        ]
        if humans:
            raise RuntimeError(
                f"{len(humans)} non-bot character(s) are online in the game roster "
                "(players_online); every QA human must be offline; refused"
            )
        sessions = self.game_connections()
        if sessions:
            raise RuntimeError(
                f"{sessions} established TCP session(s) on the game ports "
                f"{', '.join(map(str, SESSION_PORTS))}; refused"
            )
        return {
            "window_notice": {
                "path": str(Path(notice).resolve()),
                "sha256": notice_sha256,
            },
            "roster": {
                "source": "players_online",
                "online": len(online),
                "bot_only": True,
                "rows_sha256": sha256(json.dumps(online).encode()),
            },
            "qa_humans_online": 0,
            "game_port_sessions": 0,
        }

    def bind_equivalence(self, render: dict[str, Any]) -> list[dict[str, Any]]:
        """Every bind of the live DB, game, rescue and candidate names the render's host path."""
        services = render.get("services", {})
        configs = set(CONFIGS.values())
        live = {
            "database": (
                self.manifest["containers"][self.s1.DATABASE]["id"],
                "database",
            ),
            "game": (self.game["id"], "game"),
            "rescue": (RESCUE_ID, "game"),
            "candidate": (CANDIDATE_ID, "game"),
        }
        found = []
        for label, (ident, service) in live.items():
            item = self.container(ident)
            wanted = {
                m["target"]: m
                for m in services.get(service, {}).get("volumes", [])
                if m.get("type") == "bind" and m.get("target") not in configs
            }
            have = {
                m["destination"]: m
                for m in (item or {}).get("mounts", [])
                if m["type"] == "bind"
            }
            if not item or set(have) != set(wanted):
                raise RuntimeError(
                    f"{label} binds {sorted(have)} differ from the render's {sorted(wanted)}; refused"
                )
            for target, mount in sorted(have.items()):
                host = str(wanted[target]["source"])
                form = desktop_form(str(mount["source"]), host)
                if not form or mount["rw"] != (not wanted[target].get("read_only")):
                    raise RuntimeError(
                        f"{label} bind at {target} is not the host path {host} (or its mode differs); refused"
                    )
                found.append(
                    {"container": label, "target": target, "host": host, "form": form}
                )
        return found

    def env_comparison(self, render: dict[str, Any]) -> dict[str, Any]:
        """Effective environment VALUES, privately: per key sha256(KEY=VALUE), live vs render.

        Only the manifest's expected differences are allowed (the game's brain config, and the
        key the stage-1 game never had). No value is printed or stored.
        """
        expected = self.manifest["local_env_comparison_no_values"]
        idents = {
            "database": self.manifest["containers"][self.s1.DATABASE]["id"],
            "web": self.manifest["containers"][self.s1.WEB]["id"],
            "game": self.game["id"],
        }
        result: dict[str, dict[str, Any]] = {}
        for service, ident in idents.items():
            rendered = env_hashes(render["services"][service].get("environment") or {})
            item = self.container(ident)
            live = {
                k: v
                for k, v in (item or {}).get("env_sha256", {}).items()
                if k in rendered
            }
            missing = sorted(set(rendered) - set(live))
            different = sorted(k for k in live if live[k] != rendered[k])
            pinned = expected.get(service) or {}
            if (
                not item
                or sorted(rendered) != sorted(pinned.get("expected_env_keys", []))
                or missing != sorted(pinned.get("missing_env_keys", []))
                or different != sorted(pinned.get("different_env_keys", []))
            ):
                raise RuntimeError(
                    f"live {service} environment values differ from the render beyond the manifest "
                    f"(missing {missing}, different {different}); refused"
                )
            result[service] = {
                "render": rendered,
                "live": live,
                "missing": missing,
                "different": different,
            }
        game, database = result["game"]["render"], result["database"]["live"]
        if game.get("MARIADB_PASSWORD") != database.get("MARIADB_PASSWORD"):
            raise RuntimeError(
                "the render's game MARIADB_PASSWORD is not the live database's; refused"
            )
        return result

    def fresh_render(self) -> tuple[dict[str, Any], dict[str, str]]:
        raw = self.qa.command(*self.plan["render"])  # read-only `docker compose config`
        render = json.loads(raw)
        self.validate_render(render)
        private, public = sha256(raw.encode()), sha256(sanitized(render))
        if (
            private != self.manifest["render_private_sha256"]
            or public != self.manifest["render_sanitized_sha256"]
        ):
            raise RuntimeError(
                "the live render differs from the pinned render (private or sanitized hash); refused"
            )
        return render, {"private_sha256": private, "sanitized_sha256": public}

    def pinned_render(self) -> dict[str, Any]:
        """The sanitized render bound by post-build (its host paths are not redacted)."""
        bound = self.find("post-build")["sanitized_render"]
        raw = read(Path(bound["path"]))
        if (
            sha256(raw) != bound["sha256"]
            or bound["sha256"] != self.manifest["render_sanitized_sha256"]
        ):
            raise RuntimeError("the sanitized render changed since post-build; refused")
        return dict(json.loads(raw))

    def stop_gate(self, notice: Path, notice_sha256: str) -> dict[str, Any]:
        """Everything the stop needs, refreshed: live gate, game, fallbacks, binds, human exclusion."""
        stage1 = self.live_gate()
        game = self.container(self.game["id"])
        if (
            not game
            or game["status"] != "running"
            or game["created_at"] != self.game["created_at"]
        ):
            raise RuntimeError(
                "the verified stage-1 game container is not the running baseline game; refused"
            )
        self.assert_stage1_pins()
        fallbacks = self.fallbacks()
        binds = self.bind_equivalence(self.pinned_render())
        people = self.human_exclusion(notice, notice_sha256)
        return {
            "stage1": stage1,
            "game": game,
            "fallbacks": fallbacks,
            "binds": binds,
            "human_exclusion": people,
        }

    def up_gate(self) -> dict[str, Any]:
        """Everything the up needs, refreshed: post-stop state EXACT, bundle, render, env, binds."""
        files = self.check_bundle_files()
        env_file = self.check_env_file()
        game = self.assert_game_stopped()
        self.s1.qa_objects(stage2=False)
        brain = self.assert_brain_image()
        changes = self.stage1_after_stop()
        if changes:
            raise RuntimeError(
                "stage 1 after the stop differs from the baseline (DB and web must stay "
                "running/healthy exactly); refused:\n" + "\n".join(changes)
            )
        slice_now = self.s1.db_slice()
        if slice_now != self.s1.comparable(self.baseline)["db_slice"]:
            raise RuntimeError(
                "the DB slice drifted since the stop; refused (never accepted implicitly)"
            )
        others = self.others_preserved()
        new = self.owned()
        if new:
            raise RuntimeError(
                f"new game/brain containers already exist: {', '.join(r['id'][:12] for r in new)}; refused"
            )
        writers = self.writers()
        render, hashes = self.fresh_render()
        return {
            "files": files,
            "env_file": env_file,
            "brain_image": brain,
            "game": game,
            "db_slice": slice_now,
            "others": others,
            "db_writers": writers,
            "render": {"argv": self.plan["render"], **hashes},
            "environment_sha256": self.env_comparison(render),
            "binds": self.bind_equivalence(render),
        }

    # -- receipts ------------------------------------------------------------------------------

    def follow(
        self,
        path: Path,
        phases: tuple[str, ...],
        expected: str | None = None,
        results: tuple[str, ...] = ("pass",),
    ) -> dict[str, Any]:
        """Load a receipt and its whole chain; every link sealed, hashed and from this same handoff."""
        chain: list[dict[str, Any]] = []
        current: tuple[Path, str | None] | None = (Path(path), expected)
        while current:
            link, sha = current
            raw = read(link)
            receipt = json.loads(raw) if raw else {}
            if (
                not raw
                or (sha and sha256(raw) != sha)
                or receipt.get("schema") != SCHEMA
                or receipt.get("content_sha256") != self.s1.sealed(receipt)
            ):
                raise RuntimeError(
                    f"receipt {link.name} is absent, tampered or not the one given; refused"
                )
            if any(receipt.get(key) != value for key, value in self.header.items()):
                raise RuntimeError(
                    f"receipt {link.name} comes from another adapter, manifest or checkout; refused"
                )
            chain.append(receipt)
            previous = receipt.get("previous")
            current = (Path(previous["path"]), previous["sha256"]) if previous else None
        head = chain[0]
        if (
            head["phase"] not in phases
            or head["result"] not in results
            or chain[-1]["phase"] != "post-build"
        ):
            raise RuntimeError(
                f"receipt {Path(path).name} is {head['phase']}/{head['result']}, expected {'/'.join(phases)}; refused"
            )
        self.chain = chain
        self.previous = {
            "path": str(Path(path).resolve()),
            "sha256": sha256(read(Path(path))),
            "phase": head["phase"],
        }
        self.stopped = any(
            r["phase"] == "exec-step" and r["step"]["name"] == "stop-game"
            for r in chain
        )
        return head

    def find(self, phase: str) -> dict[str, Any]:
        return next(receipt for receipt in self.chain if receipt["phase"] == phase)

    def executed(self, step: str) -> dict[str, Any]:
        """The exec receipt at the head of the chain ran exactly the argv sealed in the receipt before it."""
        run, sealed_by = self.chain[0], self.chain[1]
        if (
            run["step"]["name"] != step
            or run["step"]["argv_sha256"] != sealed_by["step"]["argv_sha256"]
            or run["step"]["argv"] != sealed_by["step"]["argv"]
        ):
            raise RuntimeError(
                f"exec receipt did not run the sealed {step} argv; refused"
            )
        return run

    def write(
        self,
        phase: str,
        data: dict[str, Any],
        step: tuple[str, list[str]] | None = None,
        result: str = "pass",
    ) -> tuple[Path, str]:
        receipt = {
            "schema": SCHEMA,
            "phase": phase,
            "result": result,
            **self.header,
            "previous": self.previous,
            "recorded_at_utc": utcnow().isoformat(),
            **data,
        }
        if step:
            receipt["step"] = {
                "name": step[0],
                "argv": step[1],
                "argv_sha256": digest(step[1]),
            }
        receipt["content_sha256"] = self.s1.sealed(receipt)
        name = f"{phase}-{data['step']['name']}" if phase == "exec-step" else phase
        path = self.evidence / f"{name}-{utcnow():%Y%m%dT%H%M%S%fZ}.json"
        if path.exists():
            raise RuntimeError(f"{path.name} already exists; refused")
        return path, self.qa.save_receipt(path, receipt)

    def hold(
        self, phase: str, data: dict[str, Any], problems: list[str]
    ) -> tuple[Path, str]:
        """A refusal after a mutation: the failing receipt is written and kept, then the phase stops."""
        if not problems:
            return self.write(phase, data)
        path, _sha = self.write(phase, {**data, "problems": problems}, result="hold")
        raise RuntimeError(f"HOLD, receipt {path.name} kept:\n" + "\n".join(problems))

    # -- phases --------------------------------------------------------------------------------

    def post_build(
        self, receipts: dict[str, Path] | None, render: Path
    ) -> tuple[Path, str]:
        for key, given in (receipts or {}).items():
            pinned = self.plan["receipts"].get(key) or {}
            if (
                Path(given).resolve()
                != Path(pinned.get("absolute_path", "/")).resolve()
            ):
                raise RuntimeError(
                    f"{key} receipt {Path(given).name} is not at the manifest's absolute path; refused"
                )
        bound, raws = {}, {}
        for key in sorted(self.plan["receipts"]):
            bound[key], raws[key] = self.bound_receipt(key)
        pre = json.loads(raws["stage2_full_preflight"])
        if (
            pre.get("approved_source_revision") != TOOLING_REVISION
            or pre.get("brain_fake") is not True
            or (pre.get("stage1_upgrade") or {}).get("baseline_sha256")
            != self.s1.BASELINE_SHA256
            or pre.get("game_image_pin") != self.game["image_id"]
        ):
            raise RuntimeError(
                "the stage-2 preflight receipt is not the a1d9 upgrade preflight; refused"
            )
        brain = self.plan["brain"]
        full = brain["id"].removeprefix("sha256:").encode()
        try:
            before = json.loads(raws["brain_before"])
        except ValueError:
            before = {}
        images = before.get("images") if isinstance(before, dict) else None
        if (
            not isinstance(images, dict)
            or brain["tag"] not in images
            or images[brain["tag"]] is not None
            or full in raws["brain_before"]
            or full not in raws["brain_after"]
        ):
            raise RuntimeError(
                "brain_before/brain_after do not show the build of the pinned brain image; refused"
            )
        raw = read(render)
        services = json.loads(raw).get("services", {}) if raw else {}
        if (
            sha256(raw) != self.manifest["render_sanitized_sha256"]
            or services.get("brain", {}).get("image") != brain["id"]
            or services.get("game", {}).get("image") != self.game["image_id"]
        ):
            raise RuntimeError(
                "the sanitized render is not the pinned one for the brain and game image IDs; refused"
            )
        env_file = self.check_env_file()
        image = self.assert_brain_image()
        stage1 = self.live_gate()
        pins = self.assert_stage1_pins()
        fallbacks = self.fallbacks()
        binds = self.bind_equivalence(json.loads(raw))
        return self.write(
            "post-build",
            {
                "receipts": bound,
                "sanitized_render": {
                    "path": str(render.resolve()),
                    "sha256": sha256(raw),
                },
                "env_file": env_file,
                "brain_image": image,
                "stage1": stage1,
                "stage1_containers": pins,
                "fallbacks": fallbacks,
                "binds": binds,
            },
        )

    def pre_stop(
        self,
        previous: Path,
        attested_by: str,
        attested_at: str,
        notice: Path,
        notice_sha256: str,
    ) -> tuple[Path, str]:
        self.follow(previous, ("post-build",))
        try:
            when = datetime.fromisoformat(attested_at)
        except ValueError:
            when = None
        if (
            not attested_by.strip()
            or not when
            or when.utcoffset() != timedelta(0)
            or not (
                utcnow() - ATTESTATION_MAX_AGE
                <= when
                <= utcnow() + timedelta(minutes=2)
            )
        ):
            raise RuntimeError(
                "the stop needs a fresh human attestation: --attested-by and a UTC --attested-at; refused"
            )
        gate = self.stop_gate(notice, notice_sha256)
        return self.write(
            "pre-stop",
            {
                "attestation": {"by": attested_by.strip(), "at_utc": when.isoformat()},
                **gate,
            },
            step=("stop-game", [*STOP, gate["game"]["id"]]),
        )

    def post_stop(self, previous: Path) -> tuple[Path, str]:
        self.follow(previous, ("exec-step",), results=("pass", "hold"))
        run = self.executed("stop-game")
        before, problems = self.find("pre-stop")["game"], []
        after = self.container(before["id"])
        if run["exit_code"] != 0:
            problems.append(f"docker stop exited {run['exit_code']}")
        if not after:
            problems.append(f"game container {before['id'][:12]} is gone")
        else:
            problems += [
                f"game {key} changed: {before[key]!r} -> {after[key]!r}"
                for key in (*IDENTITY, "config_sha256")
                if after[key] != before[key]
            ]
            if after["status"] != "exited" or after["exit_code"] != 0:
                problems.append(
                    f"game is {after['status']} with exit code {after['exit_code']}, expected a graceful save (exited, 0)"
                )
        slice_now = None
        try:  # DB and web exactly as before (running/healthy); only the game moved to exited
            self.s1.qa_objects(stage2=False)
            self.assert_brain_image()
            problems += self.stage1_after_stop()
            slice_now = self.s1.db_slice()
        except RuntimeError as error:
            problems.append(str(error))
        if (
            slice_now is not None
            and slice_now != self.s1.comparable(self.baseline)["db_slice"]
        ):
            problems.append(
                "the DB slice drifted after the save; HOLD (the slice is never accepted implicitly)"
            )
        return self.hold("post-stop", {"game": after, "db_slice": slice_now}, problems)

    def assert_game_stopped(self) -> dict[str, Any]:
        before = self.find("pre-stop")["game"]
        now = self.container(before["id"])
        if (
            not now
            or now["status"] != "exited"
            or now["exit_code"] != 0
            or any(now[key] != before[key] for key in (*IDENTITY, "config_sha256"))
        ):
            raise RuntimeError(
                "the stopped stage-1 game is no longer the same exited container; refused"
            )
        return now

    def validate_render(self, render: dict[str, Any]) -> None:
        """What preflight.assert_compose checks, for the 4-file handoff render with images by ID and no build."""
        qa, plan = self.qa, self.plan
        services, volumes = render.get("services", {}), render.get("volumes", {})
        expected_volumes = qa.VOLUMES | qa.BRAIN_VOLUMES
        if render.get("name") != qa.PROJECT or set(services) != qa.SERVICES | {"brain"}:
            raise RuntimeError(
                "render project/services differ from the reviewed stage-2 stack; refused"
            )
        for kind, items in (
            ("volume", volumes),
            ("network", render.get("networks", {})),
        ):
            if any(
                item.get("external") or item.get("name") != f"{qa.PROJECT}_{key}"
                for key, item in items.items()
            ):
                raise RuntimeError(f"render references a foreign {kind}; refused")
        if set(volumes) != expected_volumes:
            raise RuntimeError(
                "render volumes differ from the 4 stage-1 and 2 brain volumes; refused"
            )
        images = {
            "database": qa.IMAGE_LOCK["database"]["ref"],
            "web": qa.WEB_TAG,
            "game": self.game["image_id"],
            "brain": plan["brain"]["id"],
        }
        configs = {
            plan["files"][name]["absolute_path"]: target
            for name, target in CONFIGS.items()
        }
        names = self.manifest["rendered_service_environment_names_only"]
        for name, service in services.items():
            if (
                service.get("image") != images[name]
                or service.get("pull_policy") != "never"
                or "build" in service
            ):
                raise RuntimeError(
                    f"render {name} is not image {images[name]} with pull_policy never and no build; refused"
                )
            if sorted(service.get("environment") or {}) != sorted(names[name]):
                raise RuntimeError(
                    f"render {name} environment names differ from the manifest; refused"
                )
            if any(
                port.get("host_ip") != "127.0.0.1" for port in service.get("ports", [])
            ):
                raise RuntimeError("render publishes a port outside loopback; refused")
            for mount in service.get("volumes", []):
                source = Path(str(mount.get("source")))
                if (
                    mount.get("type") == "volume"
                    and mount.get("source") in expected_volumes
                ):
                    continue
                if mount.get("type") != "bind" or source.is_relative_to(self.source):
                    raise RuntimeError(
                        f"render {name} mounts {source}, which is not allowed; refused"
                    )
                if str(source) in configs:
                    if configs[str(source)] != mount.get("target") or not mount.get(
                        "read_only"
                    ):
                        raise RuntimeError(
                            f"render {name} mounts {source} not read-only at its target; refused"
                        )
                elif not source.is_relative_to(
                    plan["project"]
                ) or source.is_relative_to(plan["bundle"]):
                    raise RuntimeError(
                        f"render {name} binds {source}, outside the project directory and the manifest; refused"
                    )
        brain, game = services["brain"], services["game"]
        if (
            brain.get("network_mode") != "none"
            or brain.get("ports")
            or brain.get("environment")
            or brain.get("env_file")
        ):
            raise RuntimeError(
                "render brain is not the offline fake worker without env or ports; refused"
            )
        if (
            game["environment"].get("CANARY_BRAIN_CONFIG")
            != CONFIGS["brain/server.json"]
        ):
            raise RuntimeError(
                "render game does not use the fake brain config; refused"
            )
        qa.assert_game_config(game["environment"])

    def bundle(self, previous: Path) -> tuple[Path, str]:
        self.follow(previous, ("post-stop",))
        gate = self.up_gate()
        return self.write(
            "bundle",
            {
                **gate,
                "replaces": "preflight.assert_compose (3 files, brain build/tag) for this 4-file render by image IDs",
            },
            step=("up", self.plan["up"]),
        )

    def fallback_plan(
        self, previous: Path, rescue_id: str | None = None, receipt: Path | None = None
    ) -> tuple[Path, str]:
        self.follow(
            previous, ("post-stop", "bundle", "exec-step"), results=("pass", "hold")
        )
        if not self.stopped:
            raise RuntimeError(
                "the fallback starts only after the stage-1 game was stopped by this handoff; refused"
            )
        rescue = self.rescue(rescue_id, receipt)
        self.others_preserved()
        new = self.owned()
        step = ("stop-new", [*STOP, *[row["id"] for row in new]]) if new else None
        return self.write(
            "fallback-plan", {"rescue": rescue, "new_containers": new}, step=step
        )

    def fallback_state(
        self, rescue_id: str | None = None, receipt: Path | None = None
    ) -> dict[str, Any]:
        rescue = self.rescue(rescue_id, receipt)
        self.others_preserved()
        running = [row["id"] for row in self.owned() if row["state"] in RUNNING]
        if running:
            raise RuntimeError(
                f"new game/brain containers still run: {', '.join(i[:12] for i in running)}; refused"
            )
        bound, _raw = self.bound_receipt("rescue_result")
        return {"rescue": rescue, "rescue_receipt": bound, "db_writers": self.writers()}

    def fallback_verify(
        self, previous: Path, rescue_id: str | None = None, receipt: Path | None = None
    ) -> tuple[Path, str]:
        head = self.follow(previous, ("fallback-plan", "exec-step"))
        if head["phase"] == "fallback-plan" and head.get("step"):
            raise RuntimeError(
                "run the sealed stop of the new containers first; refused"
            )
        if head["phase"] == "exec-step":
            self.executed("stop-new")
        state = self.fallback_state(rescue_id, receipt)
        return self.write(
            "fallback-verify",
            state,
            step=("start-rescue", ["docker", "start", RESCUE_ID]),
        )

    def rescue_verify(self, previous: Path) -> tuple[Path, str]:
        """After the single start: the rescue counts as usable only on a fresh health check."""
        self.follow(previous, ("exec-step",))
        run = self.executed("start-rescue")
        problems, health, live = [], None, self.container(RESCUE_ID)
        try:
            health = self.fresh_health(
                RESCUE_ID, datetime.fromisoformat(run["started_at_utc"])
            )
        except RuntimeError as error:
            problems.append(str(error))
        name, pinned = self.plan["rescue"]
        if not live or any(
            live[key] != value
            for key, value in (
                ("id", RESCUE_ID),
                ("name", name),
                ("created_at", pinned["created_at"]),
                ("image_id", pinned["image_id"]),
                ("config_sha256", self.plan["rescue_config_sha256"]),
            )
        ):
            problems.append("the started rescue is not the pinned container; refused")
        return self.hold("rescue-verify", {"rescue": live, "health": health}, problems)

    # -- the one mutating entry point ------------------------------------------------------------

    def precheck(self, receipt: dict[str, Any], argv: list[str]) -> None:
        """Refresh, right before the mutation, every gate the step depends on."""
        name = receipt["step"]["name"]
        if name == "stop-game":
            game = receipt["game"]
            if (
                argv != [*STOP, game["id"]]
                or not HEX64.fullmatch(argv[-1])
                or self.stopped
            ):
                raise RuntimeError(
                    "the stop must target the verified game container ID; refused"
                )
            notice = receipt["human_exclusion"]["window_notice"]
            gate = self.stop_gate(Path(notice["path"]), notice["sha256"])
            if gate["game"] != game:
                raise RuntimeError(
                    "the game container changed since the pre-stop gate; refused"
                )
        elif name == "up":
            if argv != self.plan["up"]:
                raise RuntimeError("the up argv is not the pinned 4-file argv; refused")
            self.up_gate()
        elif name == "stop-new":
            ids = [row["id"] for row in receipt["new_containers"]]
            if (
                argv != [*STOP, *ids]
                or not all(HEX64.fullmatch(i) for i in ids)
                or not {row["id"] for row in self.owned()} >= set(ids)
            ):
                raise RuntimeError(
                    "the stop of new containers must target their verified IDs; refused"
                )
        elif name == "start-rescue":
            rescue = receipt["rescue"]
            if argv != ["docker", "start", RESCUE_ID] or rescue["id"] != RESCUE_ID:
                raise RuntimeError(
                    "the rescue starts once, by its verified ID; refused"
                )
            if self.fallback_state()["rescue"] != rescue:
                raise RuntimeError("the rescue changed since fallback-verify; refused")
        else:
            raise RuntimeError(f"unknown step {name}; refused")

    def claim_paths(self, receipt_sha256: str, step: dict[str, Any]) -> list[Path]:
        """Canonical claim files: the receipt's step, and for the rescue start the container itself."""
        paths = [self.claims / f"{receipt_sha256}.{step['name']}.claim"]
        if step["name"] == "start-rescue":
            paths.append(self.claims / f"start-rescue.{RESCUE_ID}.claim")
        return paths

    def claimed(self, path: Path) -> str:
        result = path.with_suffix(".result")
        if result.is_file():
            done = json.loads(read(result) or b"{}")
            return (
                f"{path.name} is already claimed: it ran (exec receipt "
                f"{Path(done.get('receipt', '?')).name}, exit {done.get('exit_code')}); refused"
            )
        return (
            f"{path.name} is already claimed without a result: interrupted or uncertain; "
            "HOLD, it is never retried; refused"
        )

    def claim(self, path: Path, body: dict[str, Any]) -> None:
        created = not path.parent.is_dir()
        path.parent.mkdir(parents=True, exist_ok=True)
        if created:
            fsync_directory(path.parent.parent)
        if not create_exclusive(
            path, (json.dumps(body, sort_keys=True) + "\n").encode()
        ):
            raise RuntimeError(self.claimed(path))

    def exec_step(self, path: Path, expected: str) -> tuple[Path, str]:
        receipt = self.follow(
            path,
            ("pre-stop", "bundle", "fallback-plan", "fallback-verify"),
            expected=expected,
        )
        step = receipt.get("step")
        if not step or digest(step["argv"]) != step["argv_sha256"]:
            raise RuntimeError(f"receipt {path.name} seals no valid step; refused")
        claims = self.claim_paths(expected, step)
        for claim in claims:  # early answer; the atomic claim below is what decides
            if claim.exists():
                raise RuntimeError(self.claimed(claim))
        age = utcnow() - datetime.fromisoformat(receipt["recorded_at_utc"])
        if age < timedelta(0):
            raise RuntimeError(f"receipt {path.name} is dated in the future; refused")
        if age > STEP_MAX_AGE:
            raise RuntimeError(
                f"receipt {path.name} is stale; rerun its phase; refused"
            )
        self.precheck(receipt, step["argv"])
        body = {
            "receipt_sha256": expected,
            "step": step["name"],
            "argv_sha256": step["argv_sha256"],
            "pid": os.getpid(),
            "claimed_at_utc": utcnow().isoformat(),
        }
        for claim in claims:
            self.claim(claim, body)
        started = utcnow()
        try:
            code, out, err = execute(step["argv"])
            data = {
                "step": {key: step[key] for key in ("name", "argv", "argv_sha256")},
                "exit_code": code,
                "claim": str(claims[0]),
                "started_at_utc": started.isoformat(),
                "finished_at_utc": utcnow().isoformat(),
                "stdout_sha256": sha256(out.encode()),
                "stdout_tail": out[-2000:],
                "stderr_tail": err[-2000:],
            }
            written = self.write(
                "exec-step", data, result="pass" if code == 0 else "hold"
            )
            result = {
                "receipt": str(written[0]),
                "sha256": written[1],
                "exit_code": code,
            }
            for claim in claims:
                create_exclusive(
                    claim.with_suffix(".result"),
                    (json.dumps(result, sort_keys=True) + "\n").encode(),
                )
        except BaseException as error:
            error.add_note(
                f"HOLD: claim {claims[0].name} stays consumed; the outcome of {step['name']} "
                "is uncertain and it is never retried"
            )
            raise
        if code:
            raise RuntimeError(
                f"step {step['name']} exited {code}; HOLD, receipt {written[0].name} kept"
            )
        return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--source-checkout",
        type=Path,
        required=True,
        help="the clean a1d9 checkout (tooling only)",
    )
    parser.add_argument(
        "--manifest", type=Path, required=True, help="the pinned bundle manifest"
    )
    parser.add_argument("--manifest-sha256", default=MANIFEST_SHA256)
    parser.add_argument(
        "--adapter-sha256", required=True, help="sha256 of this copy, as reviewed"
    )
    parser.add_argument(
        "--adapter-revision",
        required=True,
        help="the repo commit that holds this exact file",
    )
    parser.add_argument(
        "--adapter-repo",
        type=Path,
        help="a git repo holding --adapter-revision (default: the source checkout)",
    )
    parser.add_argument(
        "--evidence",
        type=Path,
        help="receipt directory (default: <project>/runtime/evidence/stage2-handoff); "
        "claims always live in <project>/" + CLAIMS,
    )
    phases = parser.add_subparsers(dest="phase", required=True)
    post_build = phases.add_parser("post-build")
    for key in RECEIPT_KEYS:
        post_build.add_argument(
            f"--{key.replace('_', '-')}",
            type=Path,
            help="optional: must be the manifest's absolute path",
        )
    post_build.add_argument("--sanitized-render", type=Path, required=True)
    pre_stop = phases.add_parser("pre-stop")
    pre_stop.add_argument(
        "--attested-by",
        required=True,
        help="the person in the session who authorizes the stop",
    )
    pre_stop.add_argument(
        "--attested-at", required=True, help="UTC time of that authorization, ISO 8601"
    )
    pre_stop.add_argument(
        "--window-notice",
        type=Path,
        required=True,
        help="the coordinator's window notice (file)",
    )
    pre_stop.add_argument(
        "--window-notice-sha256", required=True, help="sha256 of that file"
    )
    for name in (
        "pre-stop",
        "post-stop",
        "bundle",
        "fallback-plan",
        "fallback-verify",
        "rescue-verify",
    ):
        sub = pre_stop if name == "pre-stop" else phases.add_parser(name)
        sub.add_argument("--previous", type=Path, required=True)
        if name.startswith("fallback"):
            sub.add_argument("--rescue-id", help="optional: must be the manifest's")
            sub.add_argument(
                "--rescue-receipt",
                type=Path,
                help="optional: must be the manifest's absolute path",
            )
    exec_step = phases.add_parser("exec-step")
    exec_step.add_argument("--receipt", type=Path, required=True)
    exec_step.add_argument("--receipt-sha256", required=True)
    args = parser.parse_args()
    handoff = Handoff(
        args.source_checkout,
        args.manifest,
        args.manifest_sha256,
        args.evidence,
        args.adapter_sha256,
        args.adapter_revision,
        args.adapter_repo,
    )
    if args.phase == "post-build":
        given = {key: getattr(args, key) for key in RECEIPT_KEYS if getattr(args, key)}
        path, sha = handoff.post_build(given, args.sanitized_render)
    elif args.phase == "pre-stop":
        path, sha = handoff.pre_stop(
            args.previous,
            args.attested_by,
            args.attested_at,
            args.window_notice,
            args.window_notice_sha256,
        )
    elif args.phase == "post-stop":
        path, sha = handoff.post_stop(args.previous)
    elif args.phase == "bundle":
        path, sha = handoff.bundle(args.previous)
    elif args.phase == "fallback-plan":
        path, sha = handoff.fallback_plan(
            args.previous, args.rescue_id, args.rescue_receipt
        )
    elif args.phase == "fallback-verify":
        path, sha = handoff.fallback_verify(
            args.previous, args.rescue_id, args.rescue_receipt
        )
    elif args.phase == "rescue-verify":
        path, sha = handoff.rescue_verify(args.previous)
    else:
        path, sha = handoff.exec_step(args.receipt, args.receipt_sha256)
    print(f"{args.phase}: receipt {path} SHA-256 {sha}")
    if json.loads(path.read_bytes()).get("step"):
        print(
            f"Next, only this runs its sealed argv: exec-step --receipt {path} --receipt-sha256 {sha}"
        )


if __name__ == "__main__":
    main()
