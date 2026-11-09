"""The managed return of ONE quiescent attempt. QA only, never production.

Derived from the approved qa_return_once.py (sha256 52bac981b99d232e3336cb96722e1443bb01939540a05154292d8a98e535d04b):
the same flock, exclusive claims (O_CREAT|O_EXCL, fsync of the file and of its directory) written
BEFORE the command, revalidation after the claim, and an uncertain outcome kept as HOLD (a claim
is consumed for good and never replayed). What changed, and why:

- No global claims by name. Each attempt has its own namespace,
  <project>/runtime/evidence/qa-return-claims/attempts/<attempt>/, with its own lock. The legacy
  flow.lock and the stop-rescue/start-managed claims of the 03:33 recovery are never opened,
  cleaned or reused.
- <attempt> is the canonical key of the quiescent attempt: the sha256 of its quiescent-pre-stop
  receipt. The adapter keys the stop claim by it (<key>.quiescent-stop-game.claim), so it is known
  as soon as the stop was claimed, with or without a slice receipt, and the adapter derives it
  from the same chain for the up.
- The quiescent up (stage2_handoff.py exec-step) and this return share that attempt's lock
  (attempt.lock, flock, held until the mutation finishes, and inherited by the mutation's child).
  The return never waits for it: a busy lock is HOLD. Holding it, the return writes the durable
  ABANDONED marker first; from then on the adapter refuses the up of this attempt.
- No external gate file: the gates are computed here, read-only, right before the claim, and
  recorded in a 0600 gate file whose sha256 the claim cites. Every docker or SQL call is bounded
  (10 s for probes); a timeout is HOLD with no retry.
- The gates bind the adapter (sha256, by the adapter's own check of its copy and revision), the
  manifest (bc4fb5af...), the stop exec-step claim and its result, the window notice, and the
  container IDs and configs. Neither branch needs the historical DB slice: the current data stays
  as it is, with the strict root session probe of the adapter (imported, not copied) and the
  integrity check.

Branch A, `start-managed`: before any up of this attempt was attempted. The managed original is
the exact container the pre-stop sealed, exited 0 with the same StartedAt and RestartCount; the
other games are stopped; no new game/brain container; fresh session, integrity and resource
gates. ONE `docker start <managed full ID>` per attempt, then a fresh health check and a smoke check.

Branch B, `rescue`: after an up of this attempt that ENDED: every up claim needs the adapter's
terminal result correlated with it (the sealed quiescent-up exec receipt of this attempt's chain
that ran the sealed argv, cites that claim and has that exit code). A claim without one, a
malformed or uncorrelated result, `executed: false`, any self-declared field or a free lock is
HOLD with no mutation; reconciling an uncertain up is out of scope here. The managed original is
not presumed to exist. New game/brain containers are identified by full ID through the Compose
project, service, image and ownership labels (working dir, config files, env file), and each
must equal the reviewed render (pinned by its private and sanitized sha256) for its service:
env values (private per-key sha256, the image's env under the render's), every mount, restart,
network, ports, the effective Entrypoint/Cmd (the pinned image's defaults for what the render
omits; see entrypoint_cmd), image and Compose's config-hash label. Only those verified
IDs are stopped, once. Then every game is stopped with restart=no and no session or transaction
is open, and only then the rescue starts ONCE, with its image, config (adapter_config_sha256
626ceb49...) and mounts verified, then a fresh health check and a smoke check. This revises the
managed-only restriction for this case only; the adapter's own fallback stays closed.

Every mutation: the step's complete gate (at most GATE_MAX_AGE old at the claim), the claim, then
the bindings and the SAME complete gate again (DB sessions and transactions, integrity,
resources, identities, projection), equal to the first, and the command within GATE_MAX_AGE of
that second gate. A failure after the claim leaves it consumed with `executed: false`: HOLD.
"""

import argparse
import contextlib
import fcntl
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any

SCHEMA = "qa-return-attempt-v1"
DERIVED_FROM = "52bac981b99d232e3336cb96722e1443bb01939540a05154292d8a98e535d04b"
MANAGED = "eaae6fe2171b91c8eb65ccad334ce029e8cbd3e8deb38653605c6ff1f479fcda"
MANAGED_IMAGE = (
    "sha256:358ee666db065a79625f5b5491efa363f0fc491fba04d14d5c176715f0930181"
)
RESCUE = "64385641c847ad44d6acf1dc7f5d10e206451212b4320973a27ba278e428d608"
RESCUE_IMAGE = "sha256:78327d1a07a743683b0dc8f83c62edc4b4571098aa2b83e51e8bc6fdb0dfff72"
RESCUE_CONFIG_SHA256 = (  # the manifest's rescue_container_config.adapter_config_sha256
    "626ceb4905042d9410effb4a76da5b9c97432ab831cdccd4766ed6608482f4d2"
)
RESCUE_RESULT_SHA256 = (  # the historical 0664 rescue_result receipt, preserved as it is
    "9f68b39c897aa2c274439d0e75d87cdaf8909f404729db5117a487ee0e143d9a"
)
MANIFEST_SHA256 = "bc4fb5af6c1ff5ff76e08ac15125b463222bcbc27dc98b7b35a75f7f4f4202f0"
CLAIM_ROOT = (
    "runtime/evidence/qa-return-claims"  # under the manifest's project directory
)
ATTEMPTS = f"{CLAIM_ROOT}/attempts"  # the adapter's RETURN_ATTEMPTS: the same place
LOCK = "attempt.lock"  # the adapter's ATTEMPT_LOCK
ABANDONED = "ABANDONED"  # the adapter's ABANDONED
STOP = ["docker", "stop", "-t", "180"]
PROBE_TIMEOUT = 10.0  # seconds, every read-only docker or SQL call
STOP_TIMEOUT = 200.0  # docker stop -t 180 plus 20 s for the CLI
START_TIMEOUT = 60.0  # docker start returns once the process runs
# The health cap: the reviewer confirmed 210 s from preserved data, the intervals OBSERVED from
# the start to the first healthy check: 10.319 s (rescue) and 100.507 s (managed game). Observed
# values, NOT a worst case. A timeout is HOLD: no start retry, no automatic fallback; a human decides.
HEALTH_DEADLINE = 210.0
HEALTH_POLL = 10.0
GATE_MAX_AGE = (
    30.0  # monotonic seconds from a gate's first read to its claim, or to the command
)
SETTLED = {
    "created",
    "running",
    "exited",
}  # anything else (restarting, paused, ...) is HOLD
STOPPED = {"created", "exited"}
NEW_INSPECT = (
    '{"id":{{json .Id}},"name":{{json .Name}},"created_at":{{json .Created}},'
    '"image_id":{{json .Image}},"status":{{json .State.Status}},'
    '"restart":{{json .HostConfig.RestartPolicy.Name}},"labels":{{json .Config.Labels}},'
    '"mounts":{{json .Mounts}},"config":{{json .Config}},"host_config":{{json .HostConfig}}}'
)
IMAGE_ENV = (
    "{{json .Config.Env}}"  # the image's own env, under the service's effective env
)
IMAGE_DEFAULTS = (  # the pinned image's own Entrypoint/Cmd, for what the render omits
    '{"entrypoint":{{json .Config.Entrypoint}},"cmd":{{json .Config.Cmd}}}'
)
COMPOSE_HASH = [
    "config",
    "--hash",
    "game,brain",
]  # read-only: the config-hash label Compose writes
BRANCH_A = ("start-managed",)
BRANCH_B = ("stop-new", "start-rescue")
TIMEOUTS = {
    "start-managed": START_TIMEOUT,
    "stop-new": STOP_TIMEOUT,
    "start-rescue": START_TIMEOUT,
}
IDENTITIES = (  # gate entries that must be equal before and after a claim
    "managed",
    "managed_start",
    "others",
    "up_claims",
    "new",
    "new_containers",
    "rescue",
    "candidate",
    "rescue_receipt",
    "containers",
    "network_and_volumes",
)


class ProbeTimeout(Exception):
    """A bounded call timed out. Not a RuntimeError, so no adapter check reads it as 'absent'."""


_PROBE_CAPS: list[float] = []  # the health deadline's remaining balance, while it runs


@contextlib.contextmanager
def probe_cap(seconds: float) -> Iterator[None]:
    """Every read-only call inside gets at most `seconds` (and never more than PROBE_TIMEOUT)."""
    _PROBE_CAPS.append(seconds)
    try:
        yield
    finally:
        _PROBE_CAPS.pop()


def probe_timeout() -> float:
    return min([PROBE_TIMEOUT, *_PROBE_CAPS])


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_adapter(path: Path, expected: str) -> ModuleType:
    """The reviewed adapter copy, by its sha256, BEFORE any of its code runs."""
    raw = Path(path).read_bytes()
    if sha256(raw) != expected:
        raise RuntimeError("the adapter copy is not --adapter-sha256; refused")
    spec = importlib.util.spec_from_file_location("stage2_handoff", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("the adapter copy cannot be loaded; refused")
    module = importlib.util.module_from_spec(spec)
    sys.modules["stage2_handoff"] = module
    spec.loader.exec_module(module)
    return module


def argv_list(value: Any) -> bool:
    """A JSON list of strings, as Docker and Compose write Entrypoint/Cmd (it may be empty)."""
    return isinstance(value, list) and all(isinstance(part, str) for part in value)


def bound_tooling(qa: ModuleType, run: Callable[..., Any] = subprocess.run) -> None:
    """Every read-only call of the a1d9 tooling in THIS process gets PROBE_TIMEOUT.

    preflight.command has no timeout; the adapter and stage1_baseline call it through the module
    attribute, so this bounds them all here without changing either file.
    """

    def command(*args: str, env: dict[str, str] | None = None) -> str:
        timeout = probe_timeout()  # PROBE_TIMEOUT, or less inside a probe_cap
        try:
            result = run(
                args,
                cwd=qa.HERE,
                env=env,
                text=True,
                capture_output=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            raise ProbeTimeout(
                f"{args[0]} {args[1]} timed out after {timeout:g} s; HOLD, no retry"
            ) from None
        if result.returncode:
            raise RuntimeError(f"read-only command failed: {args[0]} {args[1]}")
        return str(result.stdout)

    setattr(qa, "command", command)  # noqa: B010 - a module attribute, set on purpose


def run_mutation(
    argv: list[str], timeout: float, keep: tuple[int, ...]
) -> tuple[int, bytes, bytes]:
    """The only place a mutation runs. The attempt lock goes to the child (pass_fds): it stays
    held while docker runs, even if this process dies. A timeout propagates: uncertain, HOLD."""
    result = subprocess.run(
        argv, check=False, capture_output=True, timeout=timeout, pass_fds=keep
    )
    return result.returncode, result.stdout, result.stderr


class ReturnAttempt:
    def __init__(
        self,
        adapter: ModuleType,
        handoff: Any,
        attempt: str,
        notice: Path,
        notice_sha256: str,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not adapter.HEX64.fullmatch(attempt or ""):
            raise RuntimeError(
                "--attempt must be the quiescent-pre-stop sha256; refused"
            )
        self.mod, self.h = adapter, handoff
        self.qa, self.s1 = handoff.qa, handoff.s1
        self.key = attempt
        self.notice, self.notice_sha256 = Path(notice), notice_sha256
        self.sleep = sleep
        self.root = handoff.plan["project"] / CLAIM_ROOT
        self.dir = handoff.plan["project"] / ATTEMPTS / attempt
        self.lock_fd: int | None = None
        self.binding: dict[str, Any] = {}

    # -- bindings (static files only) ----------------------------------------------------------

    def bind(self) -> dict[str, Any]:
        """The attempt as the adapter sealed it: stop claim, its result, the chain, the window."""
        h, mod = self.h, self.mod
        provenance = h.header["provenance"]
        if provenance["manifest"]["sha256"] != MANIFEST_SHA256:
            raise RuntimeError("the manifest is not bc4fb5af...; refused")
        rescue_config = h.manifest["rescue_container_config"]
        if (
            h.plan["rescue_config_sha256"] != RESCUE_CONFIG_SHA256
            or rescue_config.get("adapter_config_sha256") != RESCUE_CONFIG_SHA256
            or h.plan["receipts"]["rescue_result"]["sha256"] != RESCUE_RESULT_SHA256
        ):
            raise RuntimeError(
                "the manifest's rescue config or rescue_result is not the reviewed one; refused"
            )
        claim = h.claims / f"{self.key}.quiescent-stop-game.claim"
        try:
            body = json.loads(claim.read_bytes())
            result = json.loads(claim.with_suffix(".result").read_bytes())
        except (OSError, ValueError):
            raise RuntimeError(
                f"the stop claim {claim.name} or its result is absent or unreadable: no "
                "certain quiescent stop of this attempt; HOLD"
            ) from None
        if (
            body.get("receipt_sha256") != self.key
            or body.get("step") != "quiescent-stop-game"
            or result.get("exit_code") != 0
            or not mod.HEX64.fullmatch(str(result.get("sha256")))
        ):
            raise RuntimeError(
                "the stop claim is not this attempt's quiescent stop with exit 0; HOLD"
            )
        run = h.follow(
            Path(result["receipt"]),
            ("exec-step",),
            expected=result["sha256"],
            mode=mod.QUIESCENT,
        )
        h.executed("quiescent-stop-game")
        pre = h.chain[1]
        if (
            pre["phase"] != "quiescent-pre-stop"
            or run["previous"]["sha256"] != self.key
            or Path(run["claim"]) != claim
        ):
            raise RuntimeError(
                "the stop exec-step does not chain to this attempt's pre-stop and claim; refused"
            )
        window, game = pre["window"], pre["game"]
        raw = mod.read(self.notice)
        if (
            not raw
            or sha256(raw) != self.notice_sha256
            or window["notice_sha256"] != self.notice_sha256
        ):
            raise RuntimeError(
                "the window notice is absent or not the one this attempt was stopped under; refused"
            )
        if game["id"] != MANAGED or game["image_id"] != MANAGED_IMAGE:
            raise RuntimeError("the pre-stop sealed another game container; refused")
        self.binding = {
            "attempt": self.key,
            "adapter": provenance["adapter"],
            "manifest_sha256": provenance["manifest"]["sha256"],
            "stop_claim": {
                "path": str(claim),
                "sha256": sha256(claim.read_bytes()),
                "claimed_at_utc": body["claimed_at_utc"],
                "result_sha256": sha256(claim.with_suffix(".result").read_bytes()),
                "exec_step_sha256": result["sha256"],
            },
            "window_notice": {
                "path": str(self.notice.resolve()),
                "sha256": self.notice_sha256,
                "start_utc": window["start_utc"],
                "end_utc": window["end_utc"],
            },
            "managed": game,
            "managed_start": pre["human_absence"]["game"],
            "rescue": {
                "id": RESCUE,
                "image_id": RESCUE_IMAGE,
                "config_sha256": RESCUE_CONFIG_SHA256,
            },
            "executor_sha256": sha256(Path(__file__).read_bytes()),
            "derived_from_sha256": DERIVED_FROM,
        }
        return self.binding

    def stop_claimed_at(self) -> datetime:
        return datetime.fromisoformat(self.binding["stop_claim"]["claimed_at_utc"])

    # -- the attempt's lock and abandonment ----------------------------------------------------

    def attempt_directory(self) -> Path:
        for part in (self.root, self.root / "attempts", self.dir):
            self.mod.private_directory(part)
        return self.dir

    @contextlib.contextmanager
    def locked(self) -> Iterator[None]:
        """The lock shared with the adapter's quiescent up. Never waited for: busy is HOLD."""
        directory = self.attempt_directory()
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(directory / LOCK, flags, 0o600)
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError(
                    "HOLD: the attempt lock is held (a quiescent up or another return runs); "
                    "the return never contends; nothing claimed"
                ) from None
            self.lock_fd = descriptor
            yield
        finally:
            self.lock_fd = None
            os.close(
                descriptor
            )  # the lock lives on only in a still running mutation child

    def abandon(self) -> dict[str, Any]:
        """The durable ABANDONED marker, written under the lock before any gate or claim."""
        path = self.dir / ABANDONED
        body = {
            "schema": SCHEMA + "-abandoned",
            "attempt": self.key,
            "abandoned_at_utc": self.mod.utcnow().isoformat(),
            "pid": os.getpid(),
            "stop_claim_sha256": self.binding["stop_claim"]["sha256"],
            "window_notice_sha256": self.notice_sha256,
            "effect": "the adapter refuses the quiescent up of this attempt for good",
        }
        content = (json.dumps(body, sort_keys=True) + "\n").encode()
        if self.mod.create_exclusive(path, content):
            return {"path": str(path), "sha256": sha256(content), "new": True}
        info = os.lstat(path)
        try:
            found = json.loads(path.read_bytes())
        except ValueError:
            found = {}
        if not stat.S_ISREG(info.st_mode) or found.get("attempt") != self.key:
            raise RuntimeError(f"{path} is not this attempt's marker; HOLD")
        return {"path": str(path), "sha256": sha256(path.read_bytes()), "new": False}

    # -- live gates (read-only, bounded) -------------------------------------------------------

    def up_claims(self) -> list[dict[str, Any]]:
        """Adapter up claims taken since this attempt's stop claim (one window at a time)."""
        since, found = self.stop_claimed_at(), []
        names = ("*.quiescent-up.claim", "*.activate.claim")
        for path in sorted(p for name in names for p in self.h.claims.glob(name)):
            try:
                body = json.loads(path.read_bytes())
                at = datetime.fromisoformat(body["claimed_at_utc"])
            except (OSError, ValueError, KeyError, TypeError):
                raise RuntimeError(
                    f"{path.name} is unreadable: uncertain; HOLD"
                ) from None
            if at >= since:
                found.append({"claim": path.name, "claimed_at_utc": at.isoformat()})
        return found

    def up_terminated(self, ups: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Each up claim has a terminal result correlated with it, or the answer is HOLD.

        Terminal: the adapter's own result {receipt, sha256, exit_code} naming a sealed
        quiescent-up exec receipt of THIS attempt's chain, which ran the sealed argv, cites this
        claim and finished with that exit code. A missing, malformed or uncorrelated result,
        `executed: false`, any other self-declared field, or a free lock is no proof that the up
        ended: no mutation. Reconciling an uncertain up is out of scope here.
        """
        if not ups:
            raise RuntimeError(
                "no up of this attempt was attempted: use start-managed; refused"
            )
        h = self.h
        saved = (h.chain, h.mode, h.previous, h.stopped)
        proven = []
        try:
            for up in ups:
                claim = h.claims / up["claim"]
                try:
                    proven.append(self.correlated(claim))
                except Exception as error:  # noqa: BLE001 - no proof is HOLD
                    raise RuntimeError(
                        f"HOLD: {claim.name} has no correlated terminal result ({error}); "
                        "the up may still run or its outcome is unknown; no mutation "
                        "(reconciling it is out of scope)"
                    ) from None
        finally:
            h.chain, h.mode, h.previous, h.stopped = saved
        return proven

    def correlated(self, claim: Path) -> dict[str, Any]:
        h, mod = self.h, self.mod
        body = json.loads(claim.read_bytes())
        result_path = claim.with_suffix(".result")
        if not result_path.is_file():
            raise RuntimeError("no result")
        raw = result_path.read_bytes()
        result = json.loads(raw)
        if (
            not isinstance(result, dict)
            or set(result) != {"receipt", "sha256", "exit_code"}
            or not isinstance(result["exit_code"], int)
            or isinstance(result["exit_code"], bool)
            or not isinstance(result["receipt"], str)
            or not mod.HEX64.fullmatch(str(result["sha256"]))
        ):
            raise RuntimeError(
                "the result is not the adapter's {receipt, sha256, exit_code}"
            )
        run = h.follow(
            Path(result["receipt"]),
            ("exec-step",),
            expected=result["sha256"],
            results=("pass", "hold"),
            mode=mod.QUIESCENT,
        )
        if run["step"]["name"] != "quiescent-up":
            raise RuntimeError("the result names another step's exec receipt")
        h.executed("quiescent-up")
        bundle = h.chain[1]
        names = {
            h.claims / f"{run['previous']['sha256']}.quiescent-up.claim",
            h.claims / f"{bundle['quiescent_receipt']['sha256']}.activate.claim",
        }
        if (
            h.attempt_key() != self.key
            or body.get("step") != "quiescent-up"
            or body.get("receipt_sha256") != run["previous"]["sha256"]
            or body.get("argv_sha256") != run["step"]["argv_sha256"]
            or claim not in names
            or Path(run["claim"]) not in names
            or run["exit_code"] != result["exit_code"]
            or not run.get("finished_at_utc")
            or datetime.fromisoformat(run["started_at_utc"])
            < datetime.fromisoformat(body["claimed_at_utc"])
        ):
            raise RuntimeError(
                "the exec receipt is not this claim's run of this attempt"
            )
        return {
            "claim": claim.name,
            "result_sha256": sha256(raw),
            "exec_step_sha256": result["sha256"],
            "exit_code": result["exit_code"],
            "finished_at_utc": run["finished_at_utc"],
        }

    def resources(self) -> dict[str, Any]:
        """DB and web exactly as pinned and running/healthy; the network and the 4 volumes."""
        h, s1, found = self.h, self.s1, {}
        for name in (s1.DATABASE, s1.WEB):
            pinned = h.manifest["containers"][name]
            live = h.container(pinned["id"])
            if not live or (
                live["id"],
                live["created_at"],
                live["image_id"],
                live["restart"],
                live["mounts"],
                live["status"],
                live["health"],
            ) != (
                pinned["id"],
                pinned["created_at"],
                pinned["image_id"],
                pinned["restart_policy"],
                self.mod.mounts(pinned["mounts"]),
                "running",
                "healthy",
            ):
                raise RuntimeError(
                    f"{name} is not the pinned container running and healthy; refused"
                )
            found[name] = {k: live[k] for k in ("id", "created_at", "status", "health")}
        expected = s1.comparable(h.baseline)
        network = s1.lines(
            "docker",
            "network",
            "inspect",
            f"{self.qa.PROJECT}_default",
            "--format",
            s1.NETWORK,
        )[0]
        volumes = s1.lines(
            "docker",
            "volume",
            "inspect",
            *sorted(s1.LISTINGS["volume"][3]),
            "--format",
            s1.VOLUME,
        )
        now = {
            "network": {
                **{key: network[key] for key in ("id", "name", "created_at")},
                "compose_labels": s1.compose_labels(network["labels"]),
            },
            "volumes": {
                v["name"]: {
                    "name": v["name"],
                    "created_at": v["created_at"],
                    "compose_labels": s1.compose_labels(v["labels"]),
                }
                for v in volumes
            },
        }
        changes = s1.differences(
            {"network": expected["network"], "volumes": expected["volumes"]}, now
        )
        if changes:
            raise RuntimeError(
                "the network or volumes differ from the baseline; refused:\n"
                + "\n".join(changes)
            )
        return {"containers": found, "network_and_volumes": "equal to the baseline"}

    def database(self) -> dict[str, Any]:
        """The adapter's strict root probe (no other session, no transaction) and integrity."""
        writers = self.h.writers()
        integrity = list(self.s1.db_integrity())
        if integrity:
            raise RuntimeError("database integrity; refused:\n" + "\n".join(integrity))
        return {"db_writers": writers, "db_integrity": "ok"}

    def managed_exact(self, live: dict[str, Any] | None) -> dict[str, Any]:
        sealed = self.binding["managed"]
        keys = (*self.mod.IDENTITY, "config_sha256")
        if not live:
            raise RuntimeError(
                f"the managed original {MANAGED[:12]} is absent; refused"
            )
        changed = [key for key in keys if live[key] != sealed[key]]
        if changed:
            raise RuntimeError(
                f"the managed original changed since the pre-stop ({', '.join(changed)}); refused"
            )
        return live

    def project_containers(self) -> list[dict[str, Any]]:
        """Every container of the QA project other than the pinned DB and web, inspected."""
        h, qa = self.h, self.qa
        rows = qa.command(
            "docker",
            "ps",
            "-a",
            "--no-trunc",
            "--filter",
            f"label=com.docker.compose.project={qa.PROJECT}",
            "--format",
            self.mod.OWNED,
        )
        pinned = {h.manifest["containers"][n]["id"] for n in (h.s1.DATABASE, h.s1.WEB)}
        found = []
        for row in rows.splitlines():
            ident = row.split("\t")[0].strip()
            if not ident or ident in pinned:
                continue
            item = json.loads(
                qa.command("docker", "inspect", ident, "--format", NEW_INSPECT)
            )
            item["name"] = str(item.get("name", "")).lstrip("/")
            found.append(item)
        return found

    def compose_hashes(self) -> dict[str, str]:
        """`docker compose config --hash game,brain` with the pinned render argv (read-only)."""
        render = self.h.plan["render"]
        if render[-3:] != ["config", "--format", "json"]:
            raise RuntimeError(
                "the pinned render argv is not `config --format json`; refused"
            )
        found = {}
        for line in self.qa.command(*render[:-3], *COMPOSE_HASH).splitlines():
            service, _sep, value = line.strip().partition(" ")
            if service:
                found[service] = value.strip()
        if set(found) != {"game", "brain"} or not all(
            self.mod.HEX64.fullmatch(value) for value in found.values()
        ):
            raise RuntimeError("the Compose config hashes are unreadable; HOLD")
        return found

    def projection(
        self,
        item: dict[str, Any],
        render: dict[str, Any],
        service: str,
        config_hash: str,
        image: str,
    ) -> list[str]:
        """The container's effective config against the reviewed render's service, or problems.

        The adapter's proofs, per container: env VALUES as private sha256(KEY=VALUE) (the image's
        env under the render's, nothing else), every mount (a bind names the render's host path
        by desktop_form, a volume is the render's named volume, same mode), restart, network,
        ports, the effective Entrypoint/Cmd (entrypoint_cmd), image, and Compose's config-hash
        label, which proves none of the others.
        """
        mod, qa = self.mod, self.qa
        wanted = render["services"][service]
        config = item.get("config") or {}
        host = item.get("host_config") or {}
        labels = item.get("labels") or {}
        problems = []
        image_env = json.loads(
            qa.command(
                "docker", "image", "inspect", item["image_id"], "--format", IMAGE_ENV
            )
        )
        expected = {**mod.env_pairs(image_env), **(wanted.get("environment") or {})}
        if mod.env_hashes(mod.env_pairs(config.get("Env"))) != mod.env_hashes(expected):
            problems.append("env values")
        want = {str(m.get("target")): m for m in wanted.get("volumes") or []}
        live_mounts = item.get("mounts") or []
        have = {str(m.get("Destination")): m for m in live_mounts}
        if set(have) != set(want) or len(have) != len(live_mounts):
            problems.append("mounts")
        else:
            for target, mount in sorted(want.items()):
                live, rw = have[target], not mount.get("read_only", False)
                if mount.get("type") == "volume":
                    volume = render["volumes"].get(str(mount.get("source"))) or {}
                    same = live.get("Type") == "volume" and live.get(
                        "Name"
                    ) == volume.get("name")
                elif mount.get("type") == "bind":
                    same = live.get("Type") == "bind" and bool(
                        mod.desktop_form(
                            str(live.get("Source")), str(mount.get("source"))
                        )
                    )
                else:
                    same = False
                if not same or live.get("RW") is not rw:
                    problems.append(f"mount {target}")
        if ((host.get("RestartPolicy") or {}).get("Name") or "no") != (
            wanted.get("restart") or "no"
        ):
            problems.append("restart")
        networks = wanted.get("networks") or {"default": None}
        network = wanted.get("network_mode") or (
            ((render.get("networks") or {}).get("default") or {}).get("name")
            if list(networks) == ["default"]
            else None
        )
        if not network or host.get("NetworkMode") != network:
            problems.append("network")
        ports: dict[str, list[tuple[str, str]]] = {}
        for port in wanted.get("ports") or []:
            key = f"{port.get('target')}/{port.get('protocol') or 'tcp'}"
            ports.setdefault(key, []).append(
                (str(port.get("host_ip") or ""), str(port.get("published") or ""))
            )
        bound = {
            key: sorted(
                (str(b.get("HostIp", "")), str(b.get("HostPort", ""))) for b in value
            )
            for key, value in (host.get("PortBindings") or {}).items()
        }
        if bound != {key: sorted(value) for key, value in ports.items()}:
            problems.append("ports")
        problems.extend(self.entrypoint_cmd(config, wanted, image))
        if config.get("Image") != wanted.get("image"):
            problems.append("config image")
        if labels.get("com.docker.compose.config-hash") != config_hash:
            problems.append("config hash")
        return problems

    def entrypoint_cmd(
        self, config: dict[str, Any], wanted: dict[str, Any], image: str
    ) -> list[str]:
        """The container's EFFECTIVE `.Config.Entrypoint`/`.Config.Cmd` against what the reviewed
        render gives, with the pinned image's own defaults for what it omits. Problems, or [].

        The rules (Docker's merge of the create config with the image config, as Compose sends a
        service; Compose's config-hash label is never proof of either value):
        1. The render's `entrypoint`/`command` is omitted (null) or a non-empty list of strings:
           `config --format json` writes the string form as a list (the reviewed render has
           lists). Any other shape, an explicit empty list included, is refused: its effect is
           not provable here.
        2. The render sets `entrypoint`: Entrypoint = the render's; Cmd = the render's `command`
           if set, else null (an entrypoint override resets the image's Cmd).
        3. The render omits `entrypoint`: Entrypoint = the pinned image's; Cmd = the render's
           `command` if set, else the pinned image's. The defaults come from
           `docker image inspect <pinned full image ID>` (bounded, PROBE_TIMEOUT); a failure,
           an unreadable answer or a timeout is HOLD.
        4. Each field is compared on its own (not the joined argv), as exact JSON: null and an
           empty list are different values, and a mismatch either way is refused.
        """
        given = {key: wanted.get(key) for key in ("entrypoint", "command")}
        for key, value in given.items():
            if value is not None and not (value and argv_list(value)):
                return [f"{key} form"]
        entrypoint, cmd = given["entrypoint"], given["command"]
        if entrypoint is None:
            try:
                defaults = json.loads(
                    self.qa.command(
                        "docker", "image", "inspect", image, "--format", IMAGE_DEFAULTS
                    )
                )
            except (RuntimeError, ValueError):
                defaults = None
            if not (
                isinstance(defaults, dict)
                and set(defaults) == {"entrypoint", "cmd"}
                and all(v is None or argv_list(v) for v in defaults.values())
            ):
                raise RuntimeError(
                    f"the pinned image {image[7:19]} Entrypoint/Cmd are unreadable; HOLD"
                )
            entrypoint = defaults["entrypoint"]
            if cmd is None:
                cmd = defaults["cmd"]
        return [
            key
            for key, field, expected in (
                ("entrypoint", "Entrypoint", entrypoint),
                ("command", "Cmd", cmd),
            )
            if json.dumps(config.get(field)) != json.dumps(expected)
        ]

    def new_containers(self) -> list[dict[str, Any]]:
        """New game/brain containers of THIS up, each verified by full ID and effective config.

        Verified before any of them is adopted or stopped, and again after each claim. The env
        stays private: only a sanitized hash of the per-key hashes and booleans are recorded.
        """
        plan, mod = self.h.plan, self.mod
        files = ",".join(
            plan["files"][name]["absolute_path"] for name in mod.COMPOSE_FILES
        )
        images = {"game": MANAGED_IMAGE, "brain": plan["brain"]["id"]}
        since = self.stop_claimed_at() - mod.CLOCK_SKEW
        render, render_hashes = (
            self.h.fresh_render()
        )  # validated, pinned (private, sanitized)
        compose = self.compose_hashes()
        verified = []
        for item in self.project_containers():
            if item["id"] == MANAGED:
                continue
            labels = item.get("labels") or {}
            service = labels.get("com.docker.compose.service")
            try:
                created = self.s1.docker_time(item.get("created_at"))
            except RuntimeError:
                created = None
            problems = [
                problem
                for problem, failed in (
                    ("full ID", not mod.HEX64.fullmatch(str(item.get("id")))),
                    (
                        "project",
                        labels.get("com.docker.compose.project") != self.qa.PROJECT,
                    ),
                    ("service", service not in images),
                    ("image", item.get("image_id") != images.get(str(service))),
                    (
                        "working dir",
                        labels.get("com.docker.compose.project.working_dir")
                        != str(plan["project"]),
                    ),
                    (
                        "config files",
                        labels.get("com.docker.compose.project.config_files") != files,
                    ),
                    (
                        "env file",
                        labels.get("com.docker.compose.project.environment_file")
                        != str(plan["env_file"]),
                    ),
                    ("one-off", labels.get("com.docker.compose.oneoff") != "False"),
                    ("created after the stop", created is None or created < since),
                    ("settled state", item.get("status") not in SETTLED),
                )
                if failed
            ]
            if not problems:
                problems = self.projection(
                    item,
                    render,
                    str(service),
                    compose[str(service)],
                    images[str(service)],
                )
            if problems:
                raise RuntimeError(
                    f"unverified container {str(item.get('id'))[:12]} in the QA project "
                    f"({', '.join(problems)}); nothing is stopped or adopted; HOLD"
                )
            env = mod.env_hashes(mod.env_pairs((item.get("config") or {}).get("Env")))
            verified.append(
                {
                    key: item[key]
                    for key in (
                        "id",
                        "name",
                        "created_at",
                        "image_id",
                        "status",
                        "restart",
                    )
                }
                | {
                    "service": service,
                    "mounts": mod.mounts(item.get("mounts")),
                    "config_sha256": mod.config_digest(
                        {"config": item["config"], "host_config": item["host_config"]}
                    ),
                    "compose_config_hash": compose[str(service)],
                    "env": {
                        "keys": len(env),
                        "sha256_of_key_hashes": sha256(
                            json.dumps(env, sort_keys=True).encode()
                        ),
                        "equal_to_render": True,
                    },
                    "render": render_hashes,
                    "projection": "equal to the reviewed render",
                }
            )
        return sorted(verified, key=lambda row: row["id"])

    def games_stopped(self, new: list[dict[str, Any]]) -> dict[str, Any]:
        """Every game stopped with restart=no: managed (if present), new ones, rescue, candidate."""
        h = self.h
        bad = [
            row["id"][:12]
            for row in new
            if row["status"] not in STOPPED or row["restart"] != "no"
        ]
        managed = h.container(MANAGED)
        if managed and (
            managed["status"] in self.mod.RUNNING or managed["restart"] != "no"
        ):
            bad.append(MANAGED[:12])
        if bad:
            raise RuntimeError(
                f"games are not all stopped with restart=no: {', '.join(bad)}; refused"
            )
        return {
            "managed": managed and {k: managed[k] for k in ("id", "status", "restart")},
            "new": new,
            "rescue": h.rescue(),  # exited 0, restart=no, pinned ID/image/mounts/config
            "candidate": h.candidate(),
        }

    def rescue_receipt(self) -> dict[str, Any]:
        """The historical rescue_result: the original as it is, and an exclusive 0600 copy."""
        bound, raw = self.h.bound_receipt("rescue_result")
        original = Path(bound["path"])
        mode = stat.S_IMODE(os.lstat(original).st_mode)
        private = self.mod.private_directory(self.dir / "private")
        copy = private / f"rescue-result-{RESCUE_RESULT_SHA256[:12]}.json"
        if not self.mod.create_exclusive(copy, raw):
            info = os.lstat(copy)
            if (
                not stat.S_ISREG(info.st_mode)
                or stat.S_IMODE(info.st_mode) != 0o600
                or sha256(copy.read_bytes()) != RESCUE_RESULT_SHA256
            ):
                raise RuntimeError(f"{copy} is not the exact 0600 copy; HOLD")
        return {
            "original": {
                "path": str(original),
                "sha256": bound["sha256"],
                "mode": f"{mode:04o}",
            },
            "private_copy": {
                "path": str(copy),
                "sha256": sha256(copy.read_bytes()),
                "mode": "0600",
            },
            "binding": "this attempt only; the manifest is never rewritten",
        }

    # -- gates per step ------------------------------------------------------------------------

    def state_managed(self) -> dict[str, Any]:
        """The docker state Branch A needs; checked before the claim and again after it."""
        h = self.h
        ups = self.up_claims()
        if ups:
            raise RuntimeError(
                "an up of this attempt was attempted ("
                + ", ".join(u["claim"] for u in ups)
                + "): start-managed is closed; use the rescue branch; refused"
            )
        new = self.project_containers()
        others = [row["id"][:12] for row in new if row["id"] != MANAGED]
        if others:
            raise RuntimeError(f"new QA containers exist: {', '.join(others)}; refused")
        live = self.managed_exact(h.container(MANAGED))
        if (live["status"], live["exit_code"], live["restart"]) != ("exited", 0, "no"):
            raise RuntimeError(
                "the managed original is not stopped with exit 0 and restart=no; refused"
            )
        start = h.assert_not_restarted(self.binding["managed_start"])
        h.s1.qa_objects(stage2=False)  # no brain container or volume, nothing foreign
        return {"managed": live, "managed_start": start, "others": h.fallbacks()}

    def gate_managed(self) -> dict[str, Any]:
        return {**self.state_managed(), **self.resources(), **self.database()}

    def state_rescue(self) -> dict[str, Any]:
        """The docker state Branch B needs before the start; checked again after the claim."""
        ups = self.up_terminated(self.up_claims())
        self.h.s1.qa_objects(
            stage2=True
        )  # the brain container/volumes may exist; nothing foreign
        return {"up_claims": ups, **self.games_stopped(self.new_containers())}

    def gate_rescue(self) -> dict[str, Any]:
        state = self.state_rescue()
        return {
            **state,
            "rescue_receipt": self.rescue_receipt(),
            **self.resources(),
            **self.database(),
        }

    def gate_stop(self) -> dict[str, Any]:
        """Before stop-new: every up ended (proven), then the new IDs, verified by projection."""
        ups = self.up_terminated(self.up_claims())
        new = self.new_containers()
        managed = self.h.container(MANAGED)
        if managed and managed["status"] in self.mod.RUNNING:
            raise RuntimeError("the managed original runs again: uncertain; HOLD")
        return {"up_claims": ups, "new_containers": new}

    # -- claims and the mutation ---------------------------------------------------------------

    def consumed(self, claim: Path) -> RuntimeError:
        result = claim.with_suffix(".result")
        if result.is_file():
            done = json.loads(result.read_bytes() or b"{}")
            return RuntimeError(
                f"HOLD: {claim.name} is consumed (exit {done.get('exit_code')}, executed "
                f"{done.get('executed', True)}); never replayed"
            )
        return RuntimeError(
            f"HOLD: {claim.name} is claimed without a result: interrupted or uncertain; "
            "inspect the state; never replayed"
        )

    def record(self, name: str, body: dict[str, Any]) -> tuple[Path, str]:
        stamp = f"{self.mod.utcnow():%Y%m%dT%H%M%S%fZ}"
        path = self.dir / f"{name}-{stamp}.json"
        content = (json.dumps(body, sort_keys=True, default=str) + "\n").encode()
        if not self.mod.create_exclusive(path, content):
            raise RuntimeError(f"{path.name} already exists; refused")
        return path, sha256(content)

    def mutate(
        self,
        step: str,
        argv: list[str],
        gate: Callable[[], dict[str, Any]],
        first: tuple[float, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """The step's complete gate, its claim, the SAME complete gate again, then the command.

        Before the claim: the gate is at most GATE_MAX_AGE old, or nothing is claimed. After
        the claim: the bindings and the complete gate again (DB sessions and transactions,
        integrity, resources, identities, projection), equal to the first, and the command
        within GATE_MAX_AGE of that second gate's first read. Any failure there leaves the claim
        consumed with `executed: false`: HOLD, no mutation.
        """
        mod = self.mod
        claim = self.dir / f"{step}.claim"
        if claim.exists():
            raise self.consumed(claim)
        timeout = TIMEOUTS[step]
        began, found = first if first else (mod.monotonic(), gate())
        gate_path, gate_sha = self.record(
            f"gate-{step}",
            {
                "schema": SCHEMA + "-gate",
                "step": step,
                "argv": argv,
                **self.binding,
                "gate": found,
            },
        )
        if mod.monotonic() - began > GATE_MAX_AGE:
            raise RuntimeError(
                f"the {step} gate is older than {GATE_MAX_AGE:g} s; refused, nothing claimed"
            )
        body = {
            "schema": SCHEMA + "-claim",
            "attempt": self.key,
            "step": step,
            "argv": argv,
            "gate": {"path": str(gate_path), "sha256": gate_sha},
            "timeout_seconds": timeout,
            "executor_sha256": self.binding["executor_sha256"],
            "pid": os.getpid(),
            "claimed_at_utc": mod.utcnow().isoformat(),
        }
        if not mod.create_exclusive(
            claim, (json.dumps(body, sort_keys=True) + "\n").encode()
        ):
            raise self.consumed(claim)
        # From here every failure leaves the claim consumed. Nothing below retries a mutation.
        try:
            again = mod.monotonic()
            self.rebind()
            after = gate()
            changed = [
                key
                for key in IDENTITIES
                if key in found
                and json.dumps(found[key], sort_keys=True, default=str)
                != json.dumps(after.get(key), sort_keys=True, default=str)
            ]
            if changed:
                raise RuntimeError(f"{', '.join(changed)} changed since the gate")
            self.record(
                f"gate-{step}-after-claim",
                {
                    "schema": SCHEMA + "-gate",
                    "step": step,
                    "claim": body,
                    "gate": after,
                },
            )
            if mod.monotonic() - again > GATE_MAX_AGE:
                raise RuntimeError(
                    f"the gate after the claim is older than {GATE_MAX_AGE:g} s"
                )
        except Exception as error:  # noqa: BLE001 - certainly not executed: HOLD
            mod.create_exclusive(
                claim.with_suffix(".result"),
                (
                    json.dumps(
                        {"executed": False, "reason": str(error)}, sort_keys=True
                    )
                    + "\n"
                ).encode(),
            )
            raise RuntimeError(
                f"HOLD: the gate failed after the claim ({error}); claim consumed, no mutation"
            ) from None
        started = mod.utcnow()
        keep = () if self.lock_fd is None else (self.lock_fd,)
        try:
            code, out, err = run_mutation(argv, timeout, keep)
            result = {
                "schema": SCHEMA + "-result",
                "step": step,
                "claim_sha256": sha256(claim.read_bytes()),
                "exit_code": code,
                "started_at_utc": started.isoformat(),
                "finished_at_utc": mod.utcnow().isoformat(),
                "stdout_sha256": sha256(out),
                "stderr_sha256": sha256(err),
                "stderr_tail": err[-2000:].decode(errors="replace"),
            }
            mod.create_exclusive(
                claim.with_suffix(".result"),
                (json.dumps(result, sort_keys=True) + "\n").encode(),
            )
        except BaseException as error:
            raise RuntimeError(
                f"HOLD: the outcome of {step} is uncertain ({type(error).__name__}); claim "
                "consumed; inspect the state; never replayed"
            ) from error
        if code:
            raise RuntimeError(f"HOLD: {step} exited {code}; claim consumed")
        return result

    def rebind(self) -> None:
        """The bindings again (adapter, manifest, stop claim and result, window, executor)."""
        sealed = json.dumps(self.binding, sort_keys=True, default=str)
        if json.dumps(self.bind(), sort_keys=True, default=str) != sealed:
            raise RuntimeError("the bindings changed since the gate")

    def health(self, ident: str, since: datetime) -> dict[str, Any]:
        """The container's own health check (the port check of its healthcheck), polled every
        HEALTH_POLL s until a healthy check newer than the start, within HEALTH_DEADLINE s.

        The deadline is checked before each probe, after each probe and after `fresh_health`
        returns; each sleep is min(HEALTH_POLL, remaining) and each probe's timeout at most the
        remaining balance (probe_cap). A success observed at or after the deadline, or a probe
        that finishes past it, is HOLD like a timeout, `unhealthy` or a stopped container. Never
        a start retry, never a fallback start, no smoke: the return stops there and a human decides.
        """
        mod = self.mod
        deadline = mod.monotonic() + HEALTH_DEADLINE
        status: Any = None

        def remaining() -> float:
            left = deadline - mod.monotonic()
            if left <= 0:
                raise RuntimeError(
                    f"HOLD: {ident[:12]} has no healthy check within {HEALTH_DEADLINE:g} s "
                    f"of its start (health {status}); no retry, no fallback: a human decides"
                )
            return left

        while True:
            cap = remaining()  # before each probe
            try:
                with probe_cap(cap):
                    probe = json.loads(
                        self.qa.command(
                            "docker", "inspect", ident, "--format", mod.HEALTH_PROBE
                        )
                    )
            except (RuntimeError, ValueError):
                probe = {}
            status = (probe.get("health") or {}).get("Status")
            remaining()  # a probe that finishes past the deadline is HOLD, healthy or not
            if probe.get("status") != "running":
                raise RuntimeError(f"HOLD: {ident[:12]} is not running after its start")
            if status == "healthy":
                with probe_cap(remaining()):
                    fresh = dict(self.h.fresh_health(ident, since))
                status = "healthy, but confirmed after the deadline"
                remaining()  # a fresh_health that straddles the deadline is HOLD
                return fresh
            if status != "starting":
                raise RuntimeError(
                    f"HOLD: {ident[:12]} has no healthy check within {HEALTH_DEADLINE:g} s "
                    f"of its start (health {status}); no retry, no fallback: a human decides"
                )
            self.sleep(min(HEALTH_POLL, remaining()))

    def smoke(self) -> str:
        """The smoke check, separate from the health check and only after it passed."""
        failed = list(self.s1.playable())
        if failed:
            raise RuntimeError("HOLD: the smoke check failed:\n" + "\n".join(failed))
        return "ports 17171-17173 listen on loopback; login.php answers playersonline"

    def post_start(
        self, ident: str, started_at: str, expected: dict[str, Any]
    ) -> dict[str, Any]:
        """After the start: health (within HEALTH_DEADLINE), the same identity, then the smoke."""
        health = self.health(ident, datetime.fromisoformat(started_at))
        live = self.h.container(ident)
        changed = [
            key for key, value in expected.items() if not live or live.get(key) != value
        ]
        if changed:
            raise RuntimeError(
                f"HOLD: the started container is not the verified one ({', '.join(changed)})"
            )
        smoke = self.smoke()
        resources = self.resources()
        return {"health": health, "identity": expected, "smoke": smoke, **resources}

    def finish(self, step: str, verify: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        """The post-start checks, recorded whatever their outcome; a failure is HOLD."""
        try:
            outcome = {"result": "pass", **verify()}
        except (RuntimeError, ProbeTimeout) as error:
            self.record(f"verify-{step}", {"result": "hold", "problem": str(error)})
            raise
        path, digest = self.record(f"verify-{step}", outcome)
        return {"verify": {"path": str(path), "sha256": digest}, **outcome}

    # -- the two branches ----------------------------------------------------------------------

    def start_managed(self) -> dict[str, Any]:
        self.bind()
        with self.locked():
            marker = self.abandon()
            if (self.dir / "start-managed.claim").exists():  # early answer
                raise self.consumed(self.dir / "start-managed.claim")
            for other in BRANCH_B:
                if (self.dir / f"{other}.claim").exists():
                    raise RuntimeError(
                        f"the rescue branch already claimed {other}; refused"
                    )
            argv = ["docker", "start", MANAGED]
            result = self.mutate("start-managed", argv, self.gate_managed)
            sealed = self.binding["managed"]
            expected = {k: sealed[k] for k in ("id", "name", "created_at", "image_id")}
            expected |= {"config_sha256": sealed["config_sha256"], "restart": "no"}
            done = self.finish(
                "start-managed",
                lambda: self.post_start(MANAGED, result["started_at_utc"], expected),
            )
            return {"branch": "A", "abandoned": marker, "start": result, **done}

    def rescue(self) -> dict[str, Any]:
        self.bind()
        with self.locked():
            marker = self.abandon()
            for other in (*BRANCH_A, "start-rescue"):
                claim = self.dir / f"{other}.claim"
                if claim.exists():
                    raise (
                        self.consumed(claim)
                        if other == "start-rescue"
                        else RuntimeError(
                            "start-managed was claimed: Branch A ran; refused"
                        )
                    )
            stopped = self.stop_new()
            argv = ["docker", "start", RESCUE]
            result = self.mutate("start-rescue", argv, self.gate_rescue)
            name, pinned = self.h.plan["rescue"]
            expected = {
                "id": RESCUE,
                "name": name,
                "created_at": pinned["created_at"],
                "image_id": RESCUE_IMAGE,
                "config_sha256": RESCUE_CONFIG_SHA256,
                "mounts": self.mod.mounts(pinned["mounts"]),
                "restart": "no",
            }
            done = self.finish(
                "start-rescue",
                lambda: self.post_start(RESCUE, result["started_at_utc"], expected),
            )
            return {
                "branch": "B",
                "abandoned": marker,
                "stop_new": stopped,
                "start": result,
                **done,
            }

    def stop_new(self) -> dict[str, Any] | None:
        """Stop only the verified new IDs, once. A certain earlier stop is not replayed."""
        claim = self.dir / "stop-new.claim"
        if claim.exists():
            result = claim.with_suffix(".result")
            done = json.loads(result.read_bytes()) if result.is_file() else {}
            if done.get("exit_code") != 0:
                raise self.consumed(claim)
            return {
                "already": done
            }  # it ran once with exit 0; the gate below re-checks the state
        began, gate = self.mod.monotonic(), self.gate_stop()
        ids = [row["id"] for row in gate["new_containers"]]
        if not ids:
            return None
        return self.mutate("stop-new", [*STOP, *ids], self.gate_stop, (began, gate))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--adapter", type=Path, required=True, help="the pinned adapter copy"
    )
    parser.add_argument("--adapter-sha256", required=True)
    parser.add_argument("--adapter-revision", required=True)
    parser.add_argument("--adapter-repo", type=Path)
    parser.add_argument("--source-checkout", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", default=MANIFEST_SHA256)
    parser.add_argument(
        "--attempt",
        required=True,
        help="the quiescent-pre-stop receipt sha256 (the stop claim key)",
    )
    parser.add_argument("--window-notice", type=Path, required=True)
    parser.add_argument("--window-notice-sha256", required=True)
    parser.add_argument("branch", choices=("start-managed", "rescue"))
    args = parser.parse_args()
    try:
        profile = os.environ.get("CORE_QA_PROFILE", "stage1")
        if profile != "stage1":  # stage 1 only; before the adapter, git or Docker
            raise RuntimeError(
                f"the managed return is stage-1 only; refused under CORE_QA_PROFILE={profile}"
            )
        adapter = load_adapter(args.adapter, args.adapter_sha256)
        qa, _s1 = adapter.load_tooling(args.source_checkout.resolve())
        bound_tooling(qa)
        handoff = adapter.Handoff(
            args.source_checkout,
            args.manifest,
            args.manifest_sha256,
            None,
            args.adapter_sha256,
            args.adapter_revision,
            args.adapter_repo,
        )
        attempt = ReturnAttempt(
            adapter,
            handoff,
            args.attempt,
            args.window_notice,
            args.window_notice_sha256,
        )
        done = (
            attempt.start_managed()
            if args.branch == "start-managed"
            else attempt.rescue()
        )
        print(json.dumps(done, sort_keys=True, default=str))
    except Exception as error:  # noqa: BLE001 - every failure, a ProbeTimeout too, is HOLD
        text = str(error)
        print(text if text.startswith("HOLD") else f"HOLD: {text}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
