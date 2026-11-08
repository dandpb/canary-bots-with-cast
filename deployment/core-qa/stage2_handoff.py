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

Who executes what:
- The adapter runs every check. Every phase is read-only and writes one sealed JSON receipt that
  cites the previous one (path and sha256). A phase that leads to a mutation seals its exact argv
  in the receipt (`step`).
- Pitagoras, on the WSL host, runs the phases and runs each mutation ONLY as
  `stage2_handoff.py exec-step --receipt <receipt> --receipt-sha256 <sha>`: it re-checks that
  phase's preconditions, runs the sealed argv once, and writes an exec receipt with the argv
  hash and exit code. Nobody retypes a command; the next phase refuses unless the exec receipt's
  argv hash equals the sealed one and the observed state matches.
- Nothing runs `up` on its own: `bundle` seals the up argv; only an exec-step of that receipt runs it.
  After the up, the a1d9 recorder (`preflight.py --record-brain-image`, from the source checkout) stays the check.
- The return path is `fallback-plan` -> exec-step -> `fallback-verify` -> exec-step (start the
  rescue container once). The a1d9 `stage1_baseline.py rollback` renders Compose from its own
  checkout directory, so it is not run from the isolated source checkout.

Phases (`<phase> --help` for the inputs):
  post-build       brain image by full ID, platform and label; preflight/build receipts by the manifest
                   hashes; no brain container or volume; tags; identities and the exact DB slice
  pre-stop         fresh live gate (running/healthy + exact slice) and a human attestation; seals
                   `docker stop -t 180 <verified game container ID>`
  post-stop        no running/healthy gate: same game ID, CreatedAt, image and config, exited with
                   code 0; DB, web, network, volumes and the SAME exact slice. Drift is HOLD
  bundle           the pinned 4 Compose files and 2 fake configs, the render with the original
                   project directory and .env (replaces preflight.assert_compose here); seals the up argv
  fallback-plan    rescue bound to manifest ID, image, mounts and ownership, stopped with restart=no;
                   seals the stop of the NEW game/brain containers (found by ownership labels)
  fallback-verify  new containers stopped, other games preserved, zero DB writers; seals the
                   single start of the rescue
  exec-step        runs the argv sealed in one receipt, once
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SCHEMA = "qa-stage2-handoff-v1"
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
MANIFEST_SHA256 = "d30b6d90c7d96b8863a689994da6b26e47f93fef3cc6d0d69dd6da80bb4d97e5"
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
RECEIPT_KEYS = (
    "stage2_full_preflight",
    "brain_before",
    "brain_after",
    "brain_build_log",
)
UP_ARGS = ["up", "-d", "--no-build", "--no-deps", "--pull", "never", "--wait"]
UP_ARGS += ["--wait-timeout", "180", "-t", "180", "game", "brain"]
STOP = ["docker", "stop", "-t", "180"]
STEP_MAX_AGE = timedelta(minutes=15)
ATTESTATION_MAX_AGE = timedelta(minutes=30)
RESCUE_PREFIX = "qa-old-rescue-"
RUNNING = {"running", "restarting", "paused"}
HEX64 = re.compile(r"[0-9a-f]{64}")
REVISION = re.compile(r"[0-9a-f]{40}")
WRITERS_SQL = (
    "SELECT COUNT(*) FROM information_schema.PROCESSLIST "
    "WHERE ID <> CONNECTION_ID() AND COMMAND <> 'Daemon';"
)
CONTAINER = (
    '{"id":{{json .Id}},"name":{{json .Name}},"created_at":{{json .Created}},'
    '"image_id":{{json .Image}},"status":{{json .State.Status}},'
    '"exit_code":{{json .State.ExitCode}},"restart":{{json .HostConfig.RestartPolicy.Name}},'
    '"labels":{{json .Config.Labels}},"mounts":{{json .Mounts}},'
    '"config":{{json .Config}},"host_config":{{json .HostConfig}}}'
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


def sanitized(render: dict[str, Any]) -> bytes:
    """The render with every environment value hidden, as Pitagoras's sanitized render is written."""
    copy = json.loads(json.dumps(render))
    for service in copy.get("services", {}).values():
        if service.get("environment"):
            service["environment"] = {
                key: "<redacted>" for key in service["environment"]
            }
    return (json.dumps(copy, indent=2, sort_keys=True) + "\n").encode()


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
        self.outside_source(self.evidence)
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
                    "id": BRAIN_IMAGE_ID,
                    "source_revision": BRAIN_REVISION,
                    "platform": BRAIN_PLATFORM,
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

    def manifest_plan(self) -> dict[str, Any]:
        """The pinned manifest, offline: paths, a1d9 bytes, argv and the stage-1 identities of the baseline."""
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
            "files": files,
            "render": render,
            "up": up,
        }

    def check_bundle_files(self) -> dict[str, Any]:
        for name, entry in self.plan["files"].items():
            data = read(Path(entry["absolute_path"]))
            if len(data) != entry["bytes"] or sha256(data) != entry["sha256"]:
                raise RuntimeError(
                    f"bundle file {name} differs from the pinned manifest; refused"
                )
        if not self.plan["env_file"].is_file():
            raise RuntimeError("the original .env is absent; refused")
        return {
            name: {"path": e["absolute_path"], "sha256": e["sha256"]}
            for name, e in self.plan["files"].items()
        }

    # -- live checks (read-only) ---------------------------------------------------------------

    def assert_brain_image(self) -> dict[str, str]:
        """By full ID and by tag: exactly the built image, its platform and its own label."""
        for ref in (BRAIN_IMAGE_ID, self.qa.BRAIN_IMAGE):
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
            if found != [BRAIN_IMAGE_ID, BRAIN_PLATFORM, BRAIN_REVISION]:
                raise RuntimeError(
                    f"brain image {ref} is not {BRAIN_IMAGE_ID} {BRAIN_PLATFORM} labelled {BRAIN_REVISION}; refused"
                )
        return {
            "id": BRAIN_IMAGE_ID,
            "platform": BRAIN_PLATFORM,
            "source_revision": BRAIN_REVISION,
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

    def container(self, ident: str) -> dict[str, Any] | None:
        try:
            item = json.loads(
                self.qa.command("docker", "inspect", ident, "--format", CONTAINER)
            )
        except RuntimeError:
            return None
        config = {"config": item.pop("config"), "host_config": item.pop("host_config")}
        item["config_sha256"] = sha256(json.dumps(config, sort_keys=True).encode())
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

    def post_build(self, receipts: dict[str, Path], render: Path) -> tuple[Path, str]:
        bound, texts = {}, {}
        for key in RECEIPT_KEYS:
            raw = read(receipts[key])
            if not raw or sha256(raw) != self.manifest["receipts"][key]:
                raise RuntimeError(
                    f"{key} receipt {receipts[key].name} is not the one the manifest pins; refused"
                )
            bound[key], texts[key] = (
                {"path": str(receipts[key].resolve()), "sha256": sha256(raw)},
                raw.decode(errors="replace"),
            )
        pre = json.loads(texts["stage2_full_preflight"])
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
        image = BRAIN_IMAGE_ID.removeprefix("sha256:")
        if image in texts["brain_before"] or image not in texts["brain_after"]:
            raise RuntimeError(
                "brain_before/brain_after do not show the build of the pinned brain image; refused"
            )
        raw = read(render)
        services = json.loads(raw).get("services", {}) if raw else {}
        if (
            sha256(raw) != self.manifest["render_sanitized_sha256"]
            or services.get("brain", {}).get("image") != BRAIN_IMAGE_ID
            or services.get("game", {}).get("image") != self.game["image_id"]
        ):
            raise RuntimeError(
                "the sanitized render is not the pinned one for the brain and game image IDs; refused"
            )
        brain = self.assert_brain_image()
        stage1 = self.live_gate()
        return self.write(
            "post-build",
            {
                "receipts": bound,
                "sanitized_render": {
                    "path": str(render.resolve()),
                    "sha256": sha256(raw),
                },
                "brain_image": brain,
                "stage1": stage1,
            },
        )

    def pre_stop(
        self, previous: Path, attested_by: str, attested_at: str
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
        return self.write(
            "pre-stop",
            {
                "attestation": {"by": attested_by.strip(), "at_utc": when.isoformat()},
                "stage1": stage1,
                "game": game,
            },
            step=("stop-game", [*STOP, game["id"]]),
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
        try:  # no running/healthy gate here: identities without status, then the same exact slice
            self.s1.qa_objects(stage2=False)
            self.assert_brain_image()
            self.s1.assert_persistent_stage1(self.baseline, "post-stop")
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
            "brain": BRAIN_IMAGE_ID,
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
        files = self.check_bundle_files()
        game = self.assert_game_stopped()
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
        return self.write(
            "bundle",
            {
                "files": files,
                "env_file": str(self.plan["env_file"]),
                "game": game,
                "render": {
                    "argv": self.plan["render"],
                    "private_sha256": private,
                    "sanitized_sha256": public,
                },
                "replaces": "preflight.assert_compose (3 files, brain build/tag) for this 4-file render by image IDs",
            },
            step=("up", self.plan["up"]),
        )

    def rescue(self, rescue_id: str, receipt: Path) -> dict[str, Any]:
        """The rescue container: bound to the manifest's ID, image, mounts and ownership; stopped, restart=no."""
        named = [
            (n, c)
            for n, c in self.manifest["containers"].items()
            if c["id"] == rescue_id and n.startswith(RESCUE_PREFIX)
        ]
        raw = read(receipt)
        if (
            len(named) != 1
            or not HEX64.fullmatch(rescue_id)
            or sha256(raw) != self.manifest["receipts"]["rescue_result"]
            or rescue_id.encode() not in raw
        ):
            raise RuntimeError(
                "the rescue container is not the one the manifest and the rescue receipt name; refused"
            )
        name, pinned = named[0]
        live = self.container(rescue_id)
        expected = {
            "id": rescue_id,
            "name": name,
            "created_at": pinned["created_at"],
            "image_id": pinned["image_id"],
            "restart": pinned["restart_policy"],
            "mounts": mounts(pinned["mounts"]),
            "labels": {k: v for k, v in pinned["compose_labels"].items() if v},
        }
        if not live or any(live[key] != value for key, value in expected.items()):
            raise RuntimeError(
                f"rescue {name} differs from the manifest (ID, image, mounts or ownership); refused"
            )
        if live["status"] != "exited" or live["restart"] != "no":
            raise RuntimeError(
                f"rescue {name} must be stopped with restart=no before any mutation; refused"
            )
        return live

    def others_preserved(self, rescue_id: str) -> None:
        for name, pinned in self.manifest["containers"].items():
            if (
                name in {c["name"] for c in self.baseline["containers"]}
                or pinned["id"] == rescue_id
            ):
                continue
            live = self.container(pinned["id"])
            if (
                not live
                or live["status"] != "exited"
                or (live["created_at"], live["image_id"])
                != (pinned["created_at"], pinned["image_id"])
            ):
                raise RuntimeError(
                    f"other game {name} is not preserved and stopped; refused"
                )
        old = self.container(self.game["id"])
        if old and old["status"] in RUNNING:
            raise RuntimeError("the stage-1 game container is running again; refused")

    def fallback_plan(
        self, previous: Path, rescue_id: str, receipt: Path
    ) -> tuple[Path, str]:
        self.follow(
            previous, ("post-stop", "bundle", "exec-step"), results=("pass", "hold")
        )
        if not self.stopped:
            raise RuntimeError(
                "the fallback starts only after the stage-1 game was stopped by this handoff; refused"
            )
        rescue = self.rescue(rescue_id, receipt)
        self.others_preserved(rescue_id)
        new = self.owned()
        step = ("stop-new", [*STOP, *[row["id"] for row in new]]) if new else None
        return self.write(
            "fallback-plan", {"rescue": rescue, "new_containers": new}, step=step
        )

    def fallback_state(self, rescue_id: str, receipt: Path) -> dict[str, Any]:
        rescue = self.rescue(rescue_id, receipt)
        self.others_preserved(rescue_id)
        running = [row["id"] for row in self.owned() if row["state"] in RUNNING]
        if running:
            raise RuntimeError(
                f"new game/brain containers still run: {', '.join(i[:12] for i in running)}; refused"
            )
        writers = self.s1.mariadb(WRITERS_SQL).split()
        if writers != ["0"]:
            raise RuntimeError(
                f"the database still has {writers or 'unknown'} other connections (writers); refused"
            )
        return {
            "rescue": rescue,
            "rescue_receipt": {
                "path": str(receipt.resolve()),
                "sha256": sha256(read(receipt)),
            },
            "db_writers": 0,
        }

    def fallback_verify(
        self, previous: Path, rescue_id: str, receipt: Path
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
            step=("start-rescue", ["docker", "start", rescue_id]),
        )

    # -- the one mutating entry point ------------------------------------------------------------

    def precheck(self, receipt: dict[str, Any], argv: list[str]) -> None:
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
            if self.container(game["id"]) != game:
                raise RuntimeError(
                    "the game container changed since the pre-stop gate; refused"
                )
        elif name == "up":
            if argv != self.plan["up"]:
                raise RuntimeError("the up argv is not the pinned 4-file argv; refused")
            self.check_bundle_files()
            self.assert_game_stopped()
            self.s1.qa_objects(stage2=False)
            self.assert_brain_image()
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
            if argv != ["docker", "start", rescue["id"]] or list(
                self.evidence.glob("exec-step-start-rescue-*.json")
            ):
                raise RuntimeError(
                    "the rescue starts once, by its verified ID; refused"
                )
            bound = receipt["rescue_receipt"]
            if sha256(read(Path(bound["path"]))) != bound["sha256"]:
                raise RuntimeError(
                    "the rescue receipt changed since fallback-verify; refused"
                )
            if (
                self.fallback_state(rescue["id"], Path(bound["path"]))["rescue"]
                != rescue
            ):
                raise RuntimeError("the rescue changed since fallback-verify; refused")
        else:
            raise RuntimeError(f"unknown step {name}; refused")

    def exec_step(self, path: Path, expected: str) -> tuple[Path, str]:
        receipt = self.follow(
            path,
            ("pre-stop", "bundle", "fallback-plan", "fallback-verify"),
            expected=expected,
        )
        step = receipt.get("step")
        if not step or digest(step["argv"]) != step["argv_sha256"]:
            raise RuntimeError(f"receipt {path.name} seals no valid step; refused")
        for done in self.evidence.glob("exec-step-*.json"):
            if (json.loads(done.read_bytes()).get("previous") or {}).get(
                "sha256"
            ) == expected:
                raise RuntimeError(
                    f"the step of {path.name} already ran ({done.name}); refused"
                )
        if utcnow() - datetime.fromisoformat(receipt["recorded_at_utc"]) > STEP_MAX_AGE:
            raise RuntimeError(
                f"receipt {path.name} is stale; rerun its phase; refused"
            )
        self.precheck(receipt, step["argv"])
        started = utcnow()
        code, out, err = execute(step["argv"])
        data = {
            "step": {key: step[key] for key in ("name", "argv", "argv_sha256")},
            "exit_code": code,
            "started_at_utc": started.isoformat(),
            "finished_at_utc": utcnow().isoformat(),
            "stdout_sha256": sha256(out.encode()),
            "stdout_tail": out[-2000:],
            "stderr_tail": err[-2000:],
        }
        written = self.write("exec-step", data, result="pass" if code == 0 else "hold")
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
        help="receipt directory (default: <project>/runtime/evidence/stage2-handoff)",
    )
    phases = parser.add_subparsers(dest="phase", required=True)
    post_build = phases.add_parser("post-build")
    for key in RECEIPT_KEYS:
        post_build.add_argument(f"--{key.replace('_', '-')}", type=Path, required=True)
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
    for name in ("pre-stop", "post-stop", "bundle", "fallback-plan", "fallback-verify"):
        sub = pre_stop if name == "pre-stop" else phases.add_parser(name)
        sub.add_argument("--previous", type=Path, required=True)
        if name.startswith("fallback"):
            sub.add_argument("--rescue-id", required=True)
            sub.add_argument("--rescue-receipt", type=Path, required=True)
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
        path, sha = handoff.post_build(
            {key: getattr(args, key) for key in RECEIPT_KEYS}, args.sanitized_render
        )
    elif args.phase == "pre-stop":
        path, sha = handoff.pre_stop(args.previous, args.attested_by, args.attested_at)
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
    else:
        path, sha = handoff.exec_step(args.receipt, args.receipt_sha256)
    print(f"{args.phase}: receipt {path} SHA-256 {sha}")
    if json.loads(path.read_bytes()).get("step"):
        print(
            f"Next, only this runs its sealed argv: exec-step --receipt {path} --receipt-sha256 {sha}"
        )


if __name__ == "__main__":
    main()
