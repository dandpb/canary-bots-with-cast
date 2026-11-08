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
  consumed: HOLD, never retried. The stop runs within STOP_DEADLINE (5) monotonic seconds of
  its final session check (see within_deadline). Nobody retypes a command.
- Nothing runs `up` on its own: `bundle` seals the up argv; only an exec-step of that receipt runs it.
  After the up, the a1d9 recorder (`preflight.py --record-brain-image`, from the source checkout) stays the check.
- The return path is `fallback-plan` -> exec-step -> `fallback-verify` -> exec-step (start the
  rescue container once) -> `rescue-verify` (a FRESH health check: the rescue counts as usable only
  then). The a1d9 `stage1_baseline.py rollback` renders Compose from its own checkout directory,
  so it is not run from the isolated source checkout.

The two fallbacks outside Compose (`qa-game-candidate-3431b404`, `qa-old-rescue-20261107`) are
exited with a stale "unhealthy" Health. While stopped that Health is ignored; they must be exited
with code 0, restart=no and match the pinned ID and ownership; the rescue also its pinned config
hash (the candidate has NO config hash in the manifest). A started container never
counts on its old Health.

Phases (`<phase> --help` for the inputs):
  post-build       every manifest receipt by path and hash; brain image by ID, platform, label and tag
                   (manifest and live); .env raw bytes; no brain container or volume; identities and
                   the exact DB slice; rescue and candidate stopped; binds equal to the host paths
  pre-stop         fresh live gate (running/healthy + exact slice), rescue and candidate, human
                   absence (zero anchors in the last, fresh bot_hibernation.lua diagnostic of the
                   game container, QA humans offline, no TCP sessions on the game ports, the
                   coordinator's window notice by sha256); seals `docker stop -t 180 <game ID>`
  post-stop        no running/healthy gate for the game only: same ID, CreatedAt, image and config,
                   exited with code 0. DB and web stay running/healthy EXACTLY; network, volumes and
                   the SAME exact slice. Drift is HOLD
  bundle           the pinned 4 Compose files, 2 fake configs and .env, the post-stop state again,
                   others preserved, the DB session gate, the render (private and sanitized hash), the
                   environment values per key (hashes only) and the binds; seals the up argv
  fallback-plan    rescue bound to the manifest; seals the stop of the NEW game/brain containers
  fallback-verify  new containers stopped, other games preserved, the DB session gate; seals the
                   single start of the rescue
  rescue-verify    after that start: the rescue runs and is healthy by a check newer than its start
  exec-step        refreshes the gates of one sealed step, claims it, runs its argv once

Quiescent mode (a SEPARATE chain; its phases never mix with the normal ones, in either direction):
  quiescent-post-build  post-build with ONE waiver: the live DB slice is not compared with the
                   baseline's historical slice before the stop (it moves while the game runs).
                   Every other identity, health, config, image, bind and fallback check stays
  quiescent-pre-stop    the pre-stop gates (same waiver only) and a bounded QA window: a JSON notice
                   with window_start_utc/window_end_utc, at most 30 minutes long. It
                   seals `quiescent-stop-game`: a stop that only collects evidence, NEVER an up
  quiescent-slice  after that stop: the game exited 0 with the same StartedAt/RestartCount; DB and
                   web exact; the strict writers gate; integrity; two reads of the UNCHANGED
                   s1.db_slice (equal reads only corroborate). Writes the quiescent receipt, which
                   authorizes nothing by itself
  quiescent-bundle the quiescent receipt pinned by --quiescent-receipt-sha256 AND an independent
                   --approval (file + sha256) citing exactly that receipt sha, the stop exec-step
                   (receipt sha and claim) and the window (notice sha, start, end); then the bundle
                   gates with the slice compared EXACTLY to the quiescent receipt's full slice
                   (counts, projection sha, method, sql_sha256) and the strict writers gate. Seals
                   `quiescent-up`; its exec-step re-checks everything and also claims
                   `<quiescent receipt sha>.activate` (single use). A game start or the window end
                   voids the receipt and any approval
  managed return   qa_return_attempt.py, a separate executor. The attempt is keyed by the
                   quiescent-pre-stop receipt sha (the stop claim's key). The quiescent up holds
                   that attempt's lock (<project>/runtime/evidence/qa-return-claims/attempts/
                   <key>/attempt.lock) from before its precheck to the end of the up, and
                   refuses when it is busy or when the return wrote ABANDONED there

Privacy: receipts and the raw game log captures (kept for audit, never replaced by the extracted
lines) are written 0600 inside a 0700 evidence directory; a SANITIZED copy for sharing holds only
the strictly parsed bot_hibernation.lua lines and records the raw file's sha256. An existing
group/world-accessible directory or file, a symlinked component or target, or a directory owned
by someone else is refused, never repaired: existing evidence is not rewritten.
"""

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import posixpath
import re
import secrets
import stat
import subprocess
import sys
import time
from collections.abc import Iterator
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
QUIESCENT = "quiescent"
NORMAL = "normal"
QUIESCENT_PHASES = (
    "quiescent-post-build",
    "quiescent-pre-stop",
    "quiescent-slice",
    "quiescent-bundle",
)
NORMAL_PHASES = ("post-build", "pre-stop", "post-stop", "bundle")
QUIESCENT_STEPS = ("quiescent-stop-game", "quiescent-up")
NORMAL_STEPS = ("stop-game", "up")
STOP_STEPS = ("stop-game", "quiescent-stop-game")
QUIESCENT_MAX_WINDOW = timedelta(minutes=30)  # the game is never stopped indefinitely
APPROVAL_SCHEMA = "qa-stage2-quiescent-approval-v1"
APPROVAL_AUDIT_FIELDS = ("auditor", "audited_at_utc", "explanation")
REVISION = re.compile(r"[0-9a-f]{40}")
# Docker Desktop on WSL: inspect shows a bind's host path translated, either path for path under
# /run/desktop/mnt/host/wsl/<distro>/... or as docker-desktop-bind-mounts/<distro>/<sha256 of the
# host path> (what the pinned manifest shows for the world map and the initdb directory).
DESKTOP_ROOT = "/run/desktop/mnt/host/wsl"
DESKTOP_BINDS = f"{DESKTOP_ROOT}/docker-desktop-bind-mounts"
WSL_DISTRO = "Ubuntu"
# Human absence (no native roster exists: bot_active_players is an async mirror without an epoch
# or watermark). Proof: the LAST anchor diagnostic of bot_hibernation.lua at 3431b404 (lines
# 84-89 build the anchors: every non-bot player and every cast-watched bot; lines 133-141 log
# them every 60 ticks of 300 ms, nominally every 18 s) says 0 anchors, fresh, from this game
# container; plus zero TCP sessions on the game ports and the QA humans offline in SQL.
# players_online is corroboration only (real players enter it by a 10-minute sweep) and account
# 65000 proves no type. The spdlog pattern of 3431 is "[%Y-%d-%m %H:%M:%S.%e] [%^%l%$] %v ".
BOT_ACCOUNT = 65000  # SQL corroboration only: NOT proof that a GUID is a bot
GAME_REVISION = "3431b4046602875b161216ddb7be464eb4842f1a"
HIBERNATION_SCRIPT = "/canary/data/scripts/globalevents/bot_hibernation.lua"
HIBERNATION_SHA256 = (  # git show 3431b404:data/scripts/globalevents/bot_hibernation.lua
    "b2496d782f27b31b4f027ddae2b5b26704c2fc379e66501610a665687f92bf01"
)
ANCHOR_MARKER = (
    "[BotHibernation]"  # EVERY line with it is a candidate, whatever its suffix
)
LOG_PREFIX = (  # docker logs --timestamps + the 3431 spdlog pattern, level info
    r"(?P<docker>\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,9})?Z) "
    r"\[\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3}\] \[info\] "
)
ANCHOR_LINE = re.compile(  # bot_hibernation.lua:140-141, parsed strictly
    LOG_PREFIX
    + r"\[BotHibernation\] \d+ bots: hibernated=\d+ awake=\d+, (?P<anchors>\d+) real players ?"
)
BENIGN_LINES = (  # the ONLY [BotHibernation] lines skipped over: bot_hibernation.lua:66-67
    re.compile(LOG_PREFIX + r"\[BotHibernation\] tick #\d+ firing ?"),
)  # anything else last (getBotHibernationStates returned nil, truncated, unknown) refuses
ANSI = re.compile(r"\x1b\[[0-9;]*m")  # spdlog colors the level only on a terminal
ANCHOR_MAX_AGE = timedelta(seconds=30)
LOG_WINDOW = "120s"  # the last anchor older than 30 s refuses anyway
LOG_TIMEOUT = 20.0  # seconds, for each read-only capture
STOP_DEADLINE = 5.0  # monotonic seconds from the final session check to the stop
SESSION_PORTS = (17171, 17172)  # GAME_LOGIN_PORT, GAME_PROTOCOL_PORT
ROSTER_SQL = (
    "SELECT 'online', o.player_id, COALESCE(p.account_id, -1) FROM players_online o "
    "LEFT JOIN players p ON p.id = o.player_id ORDER BY o.player_id;"
)
TCP_FILES = ("/proc/net/tcp", "/proc/net/tcp6")
TCP_ESTABLISHED = "01"
GAME_START = (
    '{"id":{{json .Id}},"image_id":{{json .Image}},"status":{{json .State.Status}},'
    '"started_at":{{json .State.StartedAt}},"restart_count":{{json .RestartCount}}}'
)
LIMITATIONS = [
    (
        "The Docker log timestamp is the freshness of the log emission (spdlog async logger, "
        "flushed at least every 3 s), not an independent clock of the onThink callback."
    ),
    (
        "Zero anchors means no non-bot player and no cast-watched bot at that tick; it is not "
        "a roster and proves no GUID type."
    ),
    "The bot count in that line comes from a Lua/C++ cache and is never a native total.",
    (
        "players_online is corroboration only and potentially stale (10-minute sweep); "
        "account 65000 proves no type."
    ),
    (
        "Between the last diagnostic (nominal 18 s cadence) and the stop, a login is caught "
        "only by the TCP check; the stop runs within 5 monotonic seconds of that check."
    ),
]
# The strict DB session gate: the existing admin account (root@localhost, which has PROCESS),
# by `docker exec` on the pinned DB container. The password comes from the container's own env
# inside `sh -c` (never argv, receipts or logs). ONE mariadb invocation, so one session, runs
# the statements in this order; the probe never selects INFO (query text).
DB_PROBE_ACCOUNT = "root@localhost"
DB_PROBE_SCRIPT = 'MYSQL_PWD="$MARIADB_ROOT_PASSWORD" exec mariadb -uroot -N -B -e "$0"'
DB_PROBE_SQL = (
    "SELECT 'begin', CONNECTION_ID(), CURRENT_USER(), UTC_TIMESTAMP(6); "
    "SELECT 'privilege', 'PROCESS', COUNT(*) > 0 FROM information_schema.USER_PRIVILEGES "
    "WHERE GRANTEE = CONCAT(CHAR(39), SUBSTRING_INDEX(CURRENT_USER(), '@', 1), CHAR(39), '@', "
    "CHAR(39), SUBSTRING_INDEX(CURRENT_USER(), '@', -1), CHAR(39)) "
    "AND PRIVILEGE_TYPE = 'PROCESS'; "
    "SELECT 'process', ID, USER, HOST, IFNULL(DB, ''), COMMAND, IFNULL(TIME, -1), "
    "IFNULL(STATE, '') FROM information_schema.PROCESSLIST ORDER BY ID; "
    "SELECT 'trx', trx_mysql_thread_id, trx_state, trx_rows_modified "
    "FROM information_schema.INNODB_TRX ORDER BY trx_mysql_thread_id; "
    "SELECT 'end', CONNECTION_ID(), UTC_TIMESTAMP(6);"
)
DB_PROBE_SEQUENCE = (
    "1 begin: CONNECTION_ID(), CURRENT_USER(), UTC_TIMESTAMP(6)",
    "2 privilege: information_schema.USER_PRIVILEGES, PROCESS (name and boolean only)",
    "3 processlist: ID, USER, HOST, DB, COMMAND, TIME, STATE (never INFO)",
    "4 innodb_trx: trx_mysql_thread_id, trx_state, trx_rows_modified",
    "5 end: CONNECTION_ID(), UTC_TIMESTAMP(6)",
)
DB_PROBE_FIELDS = {"begin": 4, "privilege": 3, "process": 8, "trx": 4, "end": 3}
DB_PROBE_LIMITATIONS = [
    (
        "The statements run in sequence in ONE session (the same CONNECTION_ID at begin and "
        "end); this is not an atomic snapshot."
    ),
    (
        "Excluded: only the probe's own connection, by ID, and COMMAND='Daemon'. No user "
        "allowlist; any innodb_trx row refuses, an excluded session's included."
    ),
    (
        "A collision with the DB healthcheck (healthcheck.sh, every 10 s) refuses as HOLD: "
        "there is no healthcheck exception and no automatic retry."
    ),
    (
        "An IP is matched to a container by the CURRENT docker inspect of the pinned IDs: an "
        "observed association, never proof of the process that opened the session; a stopped "
        "container's IP counts as unknown. No retrospective attribution."
    ),
]
LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")
DB_PROBE_TIMEOUT = 10.0  # seconds, capped further by the time left in a QA window
QUIESCENT_RETURN = (
    "a quiescent chain never uses the adapter's fallback: return only through the approved "
    "managed-return procedure (Pitagoras); refused"
)
# The managed return (qa_return_attempt.py) of a quiescent attempt: the same directory, lock and
# marker. The attempt key is the quiescent-pre-stop receipt sha, the key of the stop claim.
# Under the project directory. HELD_LOCKS go to the up's child: a crashed parent cannot free them.
RETURN_ATTEMPTS = "runtime/evidence/qa-return-claims/attempts"
ATTEMPT_LOCK = "attempt.lock"
ABANDONED = "ABANDONED"
HELD_LOCKS: list[int] = []
MAP_FILE = "runtime/world/otservbr.otbm"  # under the deployment project directory; the game mounts it
NETWORK_PROBE = (
    '{"id":{{json .Id}},"name":{{json .Name}},"status":{{json .State.Status}},'
    '"ips":[{{range $name, $net := .NetworkSettings.Networks}}{{json $net.IPAddress}},{{end}}""]}'
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


def collect(argv: list[str], timeout: float = LOG_TIMEOUT) -> bytes:
    """A read-only capture with a timeout: the raw stdout bytes. Any failure refuses."""
    try:
        result = subprocess.run(argv, check=False, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"read-only command timed out after {timeout:g} s: {argv[0]} {argv[1]}; refused"
        ) from None
    if result.returncode:
        raise RuntimeError(f"read-only command failed: {argv[0]} {argv[1]}; refused")
    return result.stdout


def monotonic() -> float:
    return time.monotonic()


def execute(argv: list[str]) -> tuple[int, str, str]:
    """The only place a mutation runs: the argv sealed in a receipt, nothing else."""
    result = subprocess.run(
        argv, check=False, text=True, capture_output=True, pass_fds=tuple(HELD_LOCKS)
    )
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
    """Create path atomically (O_CREAT|O_EXCL, 0600), write and fsync it and its directory. False if it exists."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
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


def private_directory(path: Path) -> Path:
    """The 0700 directory for receipts and raw game logs: missing components are created 0700; an
    existing one must be a real directory, never a symlink, and the leaf owned by this user with no
    group/world bits. Unsafe paths are refused and never repaired."""
    path = Path(os.path.abspath(path))
    current = Path(path.anchor)
    info = os.lstat(current)
    for part in path.parts[1:]:
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            os.mkdir(current, 0o700)
            os.chmod(current, 0o700)  # mkdir honours the umask; 0700 exactly
            info = os.lstat(current)
        if stat.S_ISLNK(info.st_mode):
            raise RuntimeError(f"{current} is a symlinked path component; refused")
        if not stat.S_ISDIR(info.st_mode):
            raise RuntimeError(f"{current} is not a directory; refused")
    if info.st_uid != os.getuid():
        raise RuntimeError(f"{path} is not owned by the current user; refused")
    if info.st_mode & 0o077:
        raise RuntimeError(
            f"{path} is group- or world-accessible ({stat.S_IMODE(info.st_mode):04o}); "
            "refused, never repaired"
        )
    return path


def private_target(path: Path) -> Path:
    """A new 0600 file in a private directory: an existing file or symlink at its path refuses."""
    private_directory(path.parent)
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return path
    if stat.S_ISLNK(info.st_mode):
        raise RuntimeError(f"{path} is a symlink target; refused")
    if info.st_mode & 0o077:
        raise RuntimeError(
            f"{path} exists and is group- or world-accessible; refused, never repaired"
        )
    raise RuntimeError(f"{path.name} already exists; refused")


def write_private(path: Path, content: bytes) -> str:
    """Write a new private file (0600 in a 0700 directory) and return its sha256."""
    if not create_exclusive(private_target(path), content):
        raise RuntimeError(f"{path.name} already exists; refused")
    return sha256(content)


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
            Path(  # NOT resolved: a symlinked component must stay visible and refuse
                os.path.abspath(evidence or project / "runtime/evidence/stage2-handoff")
            )
        )
        self.claims = (project / CLAIMS).resolve()  # canonical: never from --evidence
        self.outside_source(self.evidence, self.evidence.resolve(), self.claims)
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
        self.deadline: float | None = None
        self.refreshed: dict[str, Any] | None = None
        self.session_checked = 0.0
        self.fresh_until = datetime.min.replace(tzinfo=UTC)
        self.mode = NORMAL
        self.window_end: datetime | None = None
        self.expired = ""
        self.attempt_lock: int | None = None

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

    def live_gate(self, historical_slice: bool = True) -> dict[str, Any]:
        """Running/healthy stage 1 equal to the baseline with the exact DB slice. Only before the stop.

        historical_slice=False is the ONLY quiescent waiver: the live slice is recorded, not
        compared with the baseline's historical one. Nothing else is waived.
        """
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
        expected = s1.comparable(self.baseline)
        moving = None
        if not historical_slice:
            if self.mode != QUIESCENT:
                raise RuntimeError(
                    "the historical slice may be waived only in quiescent mode; refused"
                )
            moving = now.pop("db_slice", None)
            expected.pop("db_slice", None)
        changes = s1.differences(expected, now)
        if changes:
            raise RuntimeError(
                "stage 1 differs from the pinned baseline; refused:\n"
                + "\n".join(changes)
            )
        if historical_slice:
            return dict(now)
        return {
            **now,
            "db_slice_waived": {
                "informational_live_slice": moving,
                "waiver": "historical slice comparison before the stop (quiescent mode only)",
            },
        }

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

    def writers(self) -> dict[str, Any]:
        """The strict DB session gate, as root@localhost in ONE session (see DB_PROBE_SQL).

        HOLD on an error, an incomplete or malformed output, another effective account, no
        PROCESS visibility or a probe that does not see itself. Refused on ANY other session
        (from any user or host, COMMAND='Daemon' aside) and on ANY innodb_trx row.
        """
        ident = self.manifest["containers"][self.s1.DATABASE]["id"]
        timeout = DB_PROBE_TIMEOUT
        if self.window_end is not None:  # never past the window, never extending it
            timeout = min(timeout, (self.window_end - utcnow()).total_seconds())
        if timeout <= 0:
            raise RuntimeError(
                "HOLD: no time left in the QA window for the DB session probe; no retry, "
                "no activation; refused"
            )
        argv = ["docker", "exec", ident, "sh", "-c", DB_PROBE_SCRIPT, DB_PROBE_SQL]
        wall_start, mono_start = utcnow(), monotonic()
        try:
            out = collect(argv, timeout).decode(errors="replace")
        except RuntimeError as error:  # a timeout or a failure stays the primary error
            raise RuntimeError(
                f"HOLD: the DB session probe did not complete ({error}); timeout "
                f"{timeout:g} s, elapsed {monotonic() - mono_start:.3f} s; no retry, no "
                "activation; refused"
            ) from None
        wall_end, mono_end = utcnow(), monotonic()
        rows = [line.split("\t") for line in out.splitlines() if line.strip()]
        tags = [row[0] for row in rows]
        middle = tags[2:-1]
        try:
            if (
                tags[:2] != ["begin", "privilege"]
                or tags[-1:] != ["end"]
                or any(tag not in ("process", "trx") for tag in middle)
                or middle != sorted(middle, key=lambda tag: tag != "process")
                or any(len(row) != DB_PROBE_FIELDS[row[0]] for row in rows)
            ):
                raise ValueError("order or shape")
            begin, privilege, end = rows[0], rows[1], rows[-1]
            connection = int(begin[1])
            sessions: list[dict[str, Any]] = [
                {
                    "id": int(row[1]),
                    "user": row[2],
                    "host": row[3],
                    "db": row[4],
                    "command": row[5],
                    "time_seconds": int(row[6]),
                    "state": row[7],
                }
                for row in rows
                if row[0] == "process"
            ]
            transactions = [
                {
                    "thread_id": int(row[1]),
                    "state": row[2],
                    "rows_modified": int(row[3]),
                }
                for row in rows
                if row[0] == "trx"
            ]
        except (ValueError, IndexError, KeyError):
            raise RuntimeError(
                "HOLD: the DB session probe output is incomplete or malformed; refused"
            ) from None
        if int(end[1]) != connection:
            raise RuntimeError(
                "HOLD: the DB session probe did not run in one session; refused"
            )
        if begin[2] != DB_PROBE_ACCOUNT:
            raise RuntimeError(
                f"HOLD: the DB session probe ran as another account, not {DB_PROBE_ACCOUNT}; refused"
            )
        if privilege[1:] != ["PROCESS", "1"]:
            raise RuntimeError(
                "HOLD: the DB session probe has no PROCESS visibility; refused"
            )
        if not any(row["id"] == connection for row in sessions):
            raise RuntimeError(
                "HOLD: the DB session probe does not see its own session; refused"
            )
        others = [
            row
            for row in sessions
            if row["id"] != connection and row["command"] != "Daemon"
        ]
        record = {
            "account": DB_PROBE_ACCOUNT,
            "privilege": {"PROCESS": True},
            "connection_id": connection,
            "timeout_seconds": timeout,
            "sequence": list(DB_PROBE_SEQUENCE),
            "server_utc": {"begin": begin[3], "end": end[2]},
            "wall_clock_utc": {
                "start": wall_start.isoformat(),
                "end": wall_end.isoformat(),
            },
            "monotonic_seconds": {"start": mono_start, "end": mono_end},
            "excluded": {
                "own_connection_id": connection,
                "daemon_sessions": sum(row["command"] == "Daemon" for row in sessions),
            },
            "other_sessions": len(others),
            "transactions": len(transactions),
            "limitations": DB_PROBE_LIMITATIONS,
        }
        if others or transactions:
            seen = self.observed_ips()
            for row in others:
                address = row["host"].rpartition(":")[0] or row["host"]
                row["observed_association"] = (
                    "database container (local socket or loopback)"
                    if address in LOCAL_HOSTS
                    else seen.get(address, "unknown")
                )
            refused = {
                "sessions": others,
                "innodb_trx": transactions,
                "note": DB_PROBE_LIMITATIONS[3],
            }
            raise RuntimeError(
                f"the database has {len(others)} other connection(s) (writers or unknown) and "
                f"{len(transactions)} transaction(s); refused: "
                + json.dumps(refused, sort_keys=True)
            )
        return record

    def assert_map(self) -> dict[str, str]:
        """The map bytes at the ORIGINAL operational path (the project's file the game mounts)
        against the approved pin: prepare.MAP_SHA256 of the a1d9 tooling, which must also be the
        map_sha256 of the bound a1d9 preflight receipt. Never derived from the current file and
        never read from the source checkout's copy."""
        pin = self.qa.MAP_SHA256
        _bound, raw = self.bound_receipt("stage2_full_preflight")
        if not HEX64.fullmatch(str(pin)) or json.loads(raw).get("map_sha256") != pin:
            raise RuntimeError(
                "the approved map pin and the a1d9 preflight receipt's map_sha256 differ; refused"
            )
        path = self.plan["project"] / MAP_FILE
        self.outside_source(path)
        try:
            with path.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
        except OSError:
            actual = ""
        if actual != pin:
            raise RuntimeError(f"the QA map at {path} is not the approved pin; refused")
        return {
            "path": str(path),
            "sha256": actual,
            "pin_source": "prepare.MAP_SHA256 (a1d9) = map_sha256 of the bound a1d9 preflight receipt",
        }

    def observed_ips(self) -> dict[str, str]:
        """IP -> name of the pinned containers that RUN now (current docker inspect only)."""
        pinned = [item["id"] for item in self.baseline["containers"]]
        pinned += [RESCUE_ID, CANDIDATE_ID]
        found: dict[str, str] = {}
        for ident in pinned:
            try:
                item = json.loads(
                    self.qa.command(
                        "docker", "inspect", ident, "--format", NETWORK_PROBE
                    )
                )
            except (RuntimeError, ValueError):
                continue
            if item.get("status") != "running":
                continue  # a stopped container's IP counts as unknown
            for address in item.get("ips") or []:
                if address:
                    found[address] = str(item.get("name", "")).lstrip("/")
        return found

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
        """A fallback outside Compose while stopped: exited 0, restart=no, pinned ID, owner (and config if pinned).

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

    def game_connections(self) -> dict[str, int]:
        """Established TCP sessions on the login and game ports, per file, from inside the game."""
        ports = {f"{port:04X}" for port in SESSION_PORTS}
        found = {}
        for name in TCP_FILES:
            text = self.qa.command("docker", "exec", self.game["id"], "cat", name)
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
            if headers != 1:
                raise RuntimeError(
                    f"the game TCP probe of {name} returned an unexpected shape; refused"
                )
            found[Path(name).name] = count
        return found

    def game_start(self, started_at: str | None = None) -> dict[str, Any]:
        """The live game by full ID: the pinned image (revision 3431) and an unchanged StartedAt."""
        try:
            live = json.loads(
                self.qa.command(
                    "docker", "inspect", self.game["id"], "--format", GAME_START
                )
            )
        except (RuntimeError, ValueError):
            live = {}
        if (
            live.get("id") != self.game["id"]
            or live.get("image_id") != self.game["image_id"]
            or self.game["image_source_revision"] != GAME_REVISION
            or live.get("status") != "running"
        ):
            raise RuntimeError(
                "the game is not the running container of image "
                f"{self.game['image_id']} (revision {GAME_REVISION}); refused"
            )
        if started_at is not None and live.get("started_at") != started_at:
            raise RuntimeError(
                "the game container restarted (StartedAt changed); refused"
            )
        return {
            "id": live["id"],
            "image_id": live["image_id"],
            "source_revision": GAME_REVISION,
            "started_at": live["started_at"],
            "restart_count": live.get("restart_count"),
        }

    def assert_not_restarted(self, start: dict[str, Any]) -> dict[str, Any]:
        """Since the quiescent stop: the game is exited with the same StartedAt and RestartCount.

        Any start (Docker or a person) changes StartedAt (and a policy restart RestartCount), so it
        voids the quiescent receipt and any approval of it, for good.
        """
        try:
            live = json.loads(
                self.qa.command(
                    "docker", "inspect", self.game["id"], "--format", GAME_START
                )
            )
        except (RuntimeError, ValueError):
            live = {}
        if (
            live.get("id") != self.game["id"]
            or live.get("status") != "exited"
            or live.get("started_at") != start.get("started_at")
            or live.get("restart_count") != start.get("restart_count")
        ):
            raise RuntimeError(
                "the game started again since the quiescent stop (StartedAt/RestartCount "
                "changed) or is not exited: the quiescent receipt and any approval are void; "
                "refused"
            )
        return {
            "status": "exited",
            "started_at": live["started_at"],
            "restart_count": live["restart_count"],
        }

    def window(self, notice: Path, notice_sha256: str) -> dict[str, Any]:
        """The bounded QA window from the coordinator's JSON notice, pinned by its sha256."""
        raw = read(Path(notice))
        if (
            not raw
            or not HEX64.fullmatch(notice_sha256)
            or sha256(raw) != notice_sha256
        ):
            raise RuntimeError(
                "the coordinator's window notice is absent or not the given sha256; refused"
            )
        try:
            body = json.loads(raw)
            start = datetime.fromisoformat(body["window_start_utc"])
            end = datetime.fromisoformat(body["window_end_utc"])
        except (ValueError, KeyError, TypeError):
            raise RuntimeError(
                "the quiescent window notice must be JSON with window_start_utc and "
                "window_end_utc; refused"
            ) from None
        if (
            start.utcoffset() != timedelta(0)
            or end.utcoffset() != timedelta(0)
            or not start < end
            or end - start > QUIESCENT_MAX_WINDOW
        ):
            raise RuntimeError(
                "the quiescent window must be UTC, start before its end and last at most "
                f"{QUIESCENT_MAX_WINDOW}; refused"
            )
        found = {
            "notice_path": str(Path(notice).resolve()),
            "notice_sha256": notice_sha256,
            "start_utc": start.isoformat(),
            "end_utc": end.isoformat(),
        }
        if utcnow() < start:
            raise RuntimeError("the quiescent window has not started; refused")
        self.check_window(found)
        return found

    def check_window(self, window: dict[str, Any]) -> None:
        end = datetime.fromisoformat(window["end_utc"])
        self.window_end = end
        if utcnow() >= end:
            raise RuntimeError(
                f"the QA window ended at {window['end_utc']}: the quiescent receipt and any "
                "approval are void for activation; return through the reviewed managed "
                "return; refused"
            )

    def anchor_diagnostic(self, started_at: str | None = None) -> dict[str, Any]:
        """The native evidence: the script bytes, the raw logs and their LAST anchor diagnostic."""
        game = self.game_start(started_at)
        script = collect(["docker", "exec", game["id"], "cat", HIBERNATION_SCRIPT])
        if sha256(script) != HIBERNATION_SHA256:
            raise RuntimeError(
                "the deployed bot_hibernation.lua is not the 3431b404 bytes; refused"
            )
        argv = ["docker", "logs", "--timestamps", "--since", LOG_WINDOW, game["id"]]
        wall_start, mono_start = utcnow(), monotonic()
        raw = collect(argv)
        wall_end, mono_end = utcnow(), monotonic()
        files = self.keep_logs(
            raw
        )  # the raw capture is kept for audit, refusals included
        self.game_start(game["started_at"])  # no restart during the collection
        text = raw.decode(errors="surrogateescape")
        candidates = [  # every [BotHibernation] line, NOT only the well-formed ones
            ANSI.sub("", line).rstrip("\r")
            for line in text.splitlines()
            if ANCHOR_MARKER in line
        ]
        candidates = [
            line
            for line in candidates
            if not any(benign.fullmatch(line) for benign in BENIGN_LINES)
        ]
        if not candidates:
            raise RuntimeError(
                "no anchor diagnostic of bot_hibernation.lua in the game logs; refused"
            )
        last = candidates[-1]
        found = ANCHOR_LINE.fullmatch(last)
        if not found:
            raise RuntimeError(
                "the last [BotHibernation] line is malformed or unknown (not a well-formed "
                "anchor diagnostic nor an allowlisted tick); refused"
            )
        when = self.s1.docker_time(found["docker"])
        anchors = int(found["anchors"])
        if anchors != 0:
            raise RuntimeError(
                f"the last anchor diagnostic shows {anchors} anchor(s) (non-bot players or "
                "cast-watched bots); refused"
            )
        if when > wall_end:
            raise RuntimeError(
                "the last anchor diagnostic is dated in the future; refused"
            )
        if wall_end - when > ANCHOR_MAX_AGE:
            raise RuntimeError("the last anchor diagnostic is older than 30 s; refused")
        if when <= self.s1.docker_time(game["started_at"]):
            raise RuntimeError(
                "the last anchor diagnostic is not after the game's StartedAt; refused"
            )
        self.fresh_until = when + ANCHOR_MAX_AGE
        return {
            "game": game,
            "script": {"path": HIBERNATION_SCRIPT, "sha256": sha256(script)},
            "logs": {
                "argv": argv,
                "timeout_seconds": LOG_TIMEOUT,
                "raw": text,
                "raw_encoding": "utf-8, surrogateescape",
                "sha256": sha256(raw),
                **files,
                "wall_clock_utc": {
                    "start": wall_start.isoformat(),
                    "end": wall_end.isoformat(),
                },
                "monotonic_seconds": {"start": mono_start, "end": mono_end},
            },
            "last_anchor_diagnostic": {
                "line": last,
                "docker_timestamp": found["docker"],
                "anchors": 0,
                "age_seconds_at_collection_end": (wall_end - when).total_seconds(),
            },
        }

    def keep_logs(self, raw: bytes) -> dict[str, Any]:
        """The raw capture as is (0600), and a sanitized copy for sharing bound to its sha256."""
        stem = f"game-log-{utcnow():%Y%m%dT%H%M%S%fZ}-{secrets.token_hex(4)}"
        raw_path = self.evidence / f"{stem}.raw.log"
        raw_sha256 = write_private(raw_path, raw)
        lines = [
            ANSI.sub("", line).rstrip("\r")
            for line in raw.decode(errors="surrogateescape").splitlines()
        ]
        kept = [
            line
            for line in lines
            if ANCHOR_MARKER in line
            and any(p.fullmatch(line) for p in (ANCHOR_LINE, *BENIGN_LINES))
        ]
        sanitized_body = {
            "schema": "qa-stage2-game-log-sanitized-v1",
            "raw_sha256": raw_sha256,
            "raw_file": raw_path.name,
            "raw_bytes": len(raw),
            "raw_lines": len(lines),
            "kept": "only strictly parsed bot_hibernation.lua lines (anchor diagnostic, tick)",
            "lines": kept,
            "withheld_bothibernation_lines": sum(
                ANCHOR_MARKER in line for line in lines
            )
            - len(kept),
        }
        sanitized_path = self.evidence / f"{stem}.sanitized.json"
        sanitized_sha256 = write_private(
            sanitized_path,
            (json.dumps(sanitized_body, indent=2, sort_keys=True) + "\n").encode(
                errors="surrogateescape"
            ),
        )
        return {
            "raw_file": {"path": str(raw_path), "sha256": raw_sha256, "mode": "0600"},
            "sanitized_file": {
                "path": str(sanitized_path),
                "sha256": sanitized_sha256,
                "raw_sha256": raw_sha256,
            },
        }

    def human_absence(
        self, notice: Path, notice_sha256: str, started_at: str | None = None
    ) -> dict[str, Any]:
        """Absence of humans: zero fresh native anchors, QA humans offline, no sessions, notice.

        The TCP read is the final session check; the stop must follow it within STOP_DEADLINE
        monotonic seconds (see exec_step).
        """
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
        native = self.anchor_diagnostic(started_at)
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
                f"{len(humans)} known QA human character(s) are online in players_online; "
                "every QA human must be offline; refused"
            )
        sessions = self.game_connections()
        self.session_checked = monotonic()
        if any(sessions.values()):
            raise RuntimeError(
                f"established TCP session(s) on the game ports "
                f"{', '.join(map(str, SESSION_PORTS))}: {sessions}; refused"
            )
        return {
            "contract": "zero anchors in the last bot_hibernation.lua diagnostic "
            "(3431b404, lines 84-89 and 133-141)",
            "native_roster_unavailable": True,
            "native_anchors": 0,
            **native,
            "sql_corroboration": {
                "source": "players_online",
                "potentially_stale": True,
                "online_rows": len(online),
                "rows_sha256": sha256(json.dumps(online).encode()),
                "qa_humans_online": 0,
            },
            "game_port_sessions": sessions,
            "final_session_check_monotonic": self.session_checked,
            "window_notice": {
                "path": str(Path(notice).resolve()),
                "sha256": notice_sha256,
            },
            "limitations": LIMITATIONS,
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

    def stop_gate(
        self,
        notice: Path,
        notice_sha256: str,
        started_at: str | None = None,
        historical_slice: bool = True,
    ) -> dict[str, Any]:
        """Everything the stop needs, refreshed: live gate, game, fallbacks, binds, human exclusion."""
        stage1 = self.live_gate(historical_slice)
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
        world = self.assert_map()
        people = self.human_absence(notice, notice_sha256, started_at)
        return {
            "stage1": stage1,
            "game": game,
            "fallbacks": fallbacks,
            "binds": binds,
            "map": world,
            "human_absence": people,
        }

    def up_gate(self, quiescent: dict[str, Any] | None = None) -> dict[str, Any]:
        """Everything the up needs, refreshed: post-stop state EXACT, bundle, render, env, binds.

        With a quiescent receipt, the slice is compared EXACTLY with its full slice (counts,
        projection sha, method and sql_sha256) instead of the baseline's historical one, and
        the attempt's lock and ABANDONED marker are consulted first.
        """
        if quiescent is not None:
            # alone (quiescent-bundle) a check; inside exec-step the held lock, re-entrant
            with self.attempt_guard():
                pass
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
        if quiescent is None:
            expected = self.s1.comparable(self.baseline)["db_slice"]
        else:
            slice_now, expected = self.full_slice(slice_now), quiescent["db_slice"]
        if slice_now != expected:
            raise RuntimeError(
                "the DB slice drifted since the stop; refused (never accepted implicitly)"
            )
        others = self.others_preserved()
        new = self.owned()
        if new:
            raise RuntimeError(
                f"new game/brain containers already exist: {', '.join(r['id'][:12] for r in new)}; refused"
            )
        world = self.assert_map()
        writers = self.writers()
        render, hashes = self.fresh_render()
        return {
            "map": world,
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

    def full_slice(self, read_slice: dict[str, Any]) -> dict[str, Any]:
        """The UNCHANGED s1.db_slice read, with the method and the exact query that produced it."""
        return {
            **read_slice,
            "method": self.s1.DB_SLICE_METHOD,
            "sql_sha256": self.s1.DB_SLICE_SQL_SHA256,
        }

    # -- receipts ------------------------------------------------------------------------------

    def follow(
        self,
        path: Path,
        phases: tuple[str, ...],
        expected: str | None = None,
        results: tuple[str, ...] = ("pass",),
        mode: str | None = NORMAL,
        quiescent_refusal: str | None = None,
    ) -> dict[str, Any]:
        """Load a receipt and its whole chain; every link sealed, hashed and from this same handoff.

        A chain is quiescent when its root is quiescent-post-build, else normal; no receipt or step
        of the other mode may appear in it, and a phase of one mode never accepts the other.
        """
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
        if chain[-1]["phase"] not in ("post-build", "quiescent-post-build"):
            raise RuntimeError(
                f"receipt {Path(path).name} does not chain to a post-build; refused"
            )
        found = QUIESCENT if chain[-1]["phase"] == "quiescent-post-build" else NORMAL
        other_phases, other_steps = (
            (NORMAL_PHASES, NORMAL_STEPS)
            if found == QUIESCENT
            else (QUIESCENT_PHASES, QUIESCENT_STEPS)
        )
        if any(
            r["phase"] in other_phases
            or (r.get("step") or {}).get("name") in other_steps
            for r in chain
        ):
            raise RuntimeError(
                f"receipt {Path(path).name} mixes normal and quiescent phases; refused"
            )
        if found == QUIESCENT and quiescent_refusal:
            raise RuntimeError(quiescent_refusal)
        if mode is not None and mode != found:
            raise RuntimeError(
                f"receipt {Path(path).name} is from a {found} chain; this {mode} phase never "
                "accepts it; refused"
            )
        if head["phase"] not in phases or head["result"] not in results:
            raise RuntimeError(
                f"receipt {Path(path).name} is {head['phase']}/{head['result']}, expected {'/'.join(phases)}; refused"
            )
        self.mode = found
        self.chain = chain
        self.previous = {
            "path": str(Path(path).resolve()),
            "sha256": sha256(read(Path(path))),
            "phase": head["phase"],
        }
        self.stopped = any(
            r["phase"] == "exec-step" and r["step"]["name"] in STOP_STEPS for r in chain
        )
        return head

    def find(self, phase: str) -> dict[str, Any]:
        if phase == "post-build" and self.mode == QUIESCENT:
            phase = "quiescent-post-build"  # the root of a quiescent chain
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
        path = private_target(  # 0600 in a 0700 directory: it may hold the raw game log
            self.evidence / f"{name}-{utcnow():%Y%m%dT%H%M%S%fZ}.json"
        )
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
        self, receipts: dict[str, Path] | None, render: Path, quiescent: bool = False
    ) -> tuple[Path, str]:
        self.mode = QUIESCENT if quiescent else NORMAL
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
        stage1 = self.live_gate(historical_slice=not quiescent)
        pins = self.assert_stage1_pins()
        fallbacks = self.fallbacks()
        binds = self.bind_equivalence(json.loads(raw))
        return self.write(
            "quiescent-post-build" if quiescent else "post-build",
            {
                **({"mode": QUIESCENT} if quiescent else {}),
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
        attestation = self.attestation(attested_by, attested_at)
        gate = self.stop_gate(notice, notice_sha256)
        return self.write(
            "pre-stop",
            {"attestation": attestation, **gate},
            step=("stop-game", [*STOP, gate["game"]["id"]]),
        )

    def attestation(self, attested_by: str, attested_at: str) -> dict[str, str]:
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
        return {"by": attested_by.strip(), "at_utc": when.isoformat()}

    def quiescent_pre_stop(
        self,
        previous: Path,
        attested_by: str,
        attested_at: str,
        notice: Path,
        notice_sha256: str,
    ) -> tuple[Path, str]:
        """The pre-stop gates with the one waiver, inside a bounded window. Seals a stop that only
        collects evidence: nothing in this chain runs an up without an independent approval."""
        self.follow(previous, ("quiescent-post-build",), mode=QUIESCENT)
        attestation = self.attestation(attested_by, attested_at)
        window = self.window(notice, notice_sha256)
        gate = self.stop_gate(notice, notice_sha256, historical_slice=False)
        return self.write(
            "quiescent-pre-stop",
            {
                "mode": QUIESCENT,
                "authorizes": "only the stop that collects quiescent evidence; never an up",
                "attestation": attestation,
                "window": window,
                **gate,
            },
            step=("quiescent-stop-game", [*STOP, gate["game"]["id"]]),
        )

    def post_stop(self, previous: Path) -> tuple[Path, str]:
        self.follow(previous, ("exec-step",), results=("pass", "hold"))
        if self.mode != NORMAL:
            raise RuntimeError("post-stop never accepts a quiescent chain; refused")
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
        before = self.find(
            "quiescent-pre-stop" if self.mode == QUIESCENT else "pre-stop"
        )["game"]
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

    def quiescent_slice(self, previous: Path) -> tuple[Path, str]:
        """After the evidence stop: the quiescent receipt. It authorizes nothing by itself."""
        self.follow(previous, ("exec-step",), results=("pass", "hold"), mode=QUIESCENT)
        run = self.executed("quiescent-stop-game")
        pre = self.find("quiescent-pre-stop")
        before, start = pre["game"], pre["human_absence"]["game"]
        after, problems = self.container(before["id"]), []
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
        first = second = writers = None
        integrity: list[str] | None = None
        checks: list[tuple[str, Any]] = [
            ("restart", lambda: self.assert_not_restarted(start)),
            ("window", lambda: self.check_window(pre["window"])),
            ("objects", lambda: self.s1.qa_objects(stage2=False)),
            ("brain", self.assert_brain_image),
        ]
        for _name, check in checks:
            try:
                check()
            except RuntimeError as error:
                problems.append(str(error))
        try:  # DB and web exactly as before; only the game moved to exited
            problems += self.stage1_after_stop()
            first = self.full_slice(self.s1.db_slice())
            writers = self.writers()  # strict: any other connection refuses
            integrity = list(self.s1.db_integrity())
            problems += integrity
            second = self.full_slice(self.s1.db_slice())
        except RuntimeError as error:
            problems.append(str(error))
        if first is not None and second is not None and first != second:
            problems.append(
                "two reads of the DB slice differ: the DB is not stable; HOLD"
            )
        historical = self.s1.comparable(self.baseline)["db_slice"]
        stop_link = dict(self.previous or {})
        return self.hold(
            "quiescent-slice",
            {
                "mode": QUIESCENT,
                "authorizes": (
                    "nothing by itself: activation needs an independent --approval citing this "
                    "receipt sha, the stop exec-step (receipt sha and claim) and the window"
                ),
                "baseline_sha256": self.s1.BASELINE_SHA256,
                "game": after,
                "game_start": start,
                "stop_exec_step": {
                    "path": stop_link.get("path"),
                    "sha256": stop_link.get("sha256"),
                    "claim": run.get("claim"),
                },
                "window": pre["window"],
                "db_slice": first,
                "db_writers": writers,
                "db_integrity": integrity
                if integrity
                else ("ok" if integrity == [] else None),
                "corroboration": {
                    "second_read": second,
                    "equal": first is not None and first == second,
                    "note": "two equal reads corroborate; they never prove the absence of writers",
                },
                "supersedes_db_slice": historical,
                "historical_slice_equal": first is not None
                and {k: first[k] for k in historical} == historical,
            },
            problems,
        )

    def activation(
        self,
        quiescent: dict[str, Any],
        quiescent_sha256: str,
        approval: Path,
        approval_sha256: str,
    ) -> dict[str, Any]:
        """The independent approval cites EXACTLY this receipt, its stop exec-step and its window.

        The CLI sha only pins bytes; the approval file is the link to the external review of the
        slice and its audit. Every reference is checked against the chain and the claim files.
        """
        raw = read(Path(approval))
        try:
            body = json.loads(raw) if raw else {}
        except ValueError:
            body = {}
        if (
            not raw
            or not HEX64.fullmatch(approval_sha256)
            or sha256(raw) != approval_sha256
            or not isinstance(body, dict)
            or body.get("schema") != APPROVAL_SCHEMA
        ):
            raise RuntimeError(
                "the approval is absent, not the given sha256 or not a quiescent approval; refused"
            )
        self.outside_source(Path(approval))
        stop, window = quiescent["stop_exec_step"], quiescent["window"]
        try:
            approved_at = datetime.fromisoformat(body.get("approved_at_utc", ""))
        except (TypeError, ValueError):
            approved_at = None
        found_audit = body.get("audit")
        audit: dict[str, Any] = found_audit if isinstance(found_audit, dict) else {}
        reviewer = body.get("reviewer")
        if (
            not isinstance(reviewer, str)
            or not reviewer.strip()
            or not all(
                isinstance(audit.get(key), str) and audit[key].strip()
                for key in APPROVAL_AUDIT_FIELDS
            )
        ):
            raise RuntimeError(
                "the approval needs a reviewer and an audit (auditor, audited_at_utc, "
                "explanation); refused"
            )
        if (
            approved_at is None
            or approved_at.utcoffset() != timedelta(0)
            or approved_at < datetime.fromisoformat(quiescent["recorded_at_utc"])
            or approved_at > utcnow()
            or approved_at >= datetime.fromisoformat(window["end_utc"])
        ):
            raise RuntimeError(
                "the approval time is not UTC, after the quiescent receipt and inside the "
                "window; refused"
            )
        if body.get("quiescent_receipt_sha256") != quiescent_sha256:
            raise RuntimeError("the approval cites another quiescent receipt; refused")
        if body.get("stop_exec_step") != {
            "receipt_sha256": stop["sha256"],
            "claim": stop["claim"],
        }:
            raise RuntimeError(
                "the approval cites another stop exec-step or claim; refused"
            )
        if body.get("window") != {
            "notice_sha256": window["notice_sha256"],
            "start_utc": window["start_utc"],
            "end_utc": window["end_utc"],
        }:
            raise RuntimeError("the approval cites another window; refused")
        if body.get("db_slice") != quiescent["db_slice"]:
            raise RuntimeError(
                "the approval does not name the receipt's exact full slice; refused"
            )
        run = self.chain_link("exec-step", stop["sha256"])
        canonical = (
            self.claims / f"{run['previous']['sha256']}.quiescent-stop-game.claim"
        )
        if (
            quiescent["previous"]["sha256"] != stop["sha256"]
            or run["step"]["name"] != "quiescent-stop-game"
            or run["claim"] != stop["claim"]
            or Path(stop["claim"]) != canonical
        ):
            raise RuntimeError(
                "the quiescent receipt does not chain to its stop exec-step and canonical claim; refused"
            )
        result = json.loads(read(Path(stop["claim"]).with_suffix(".result")) or b"{}")
        if result.get("sha256") != stop["sha256"] or result.get("exit_code") != 0:
            raise RuntimeError(
                "the stop claim has no result naming that exec-step; refused"
            )
        pre = self.find("quiescent-pre-stop")
        if (
            quiescent["baseline_sha256"] != self.s1.BASELINE_SHA256
            or pre["window"] != window
            or quiescent["db_slice"] is None
            or quiescent["db_slice"].get("sql_sha256") != self.s1.DB_SLICE_SQL_SHA256
            or quiescent["db_slice"].get("method") != self.s1.DB_SLICE_METHOD
        ):
            raise RuntimeError(
                "the quiescent receipt is not bound to this baseline, window and slice method; refused"
            )
        self.check_window(window)
        self.assert_not_restarted(quiescent["game_start"])
        return {
            "path": str(Path(approval).resolve()),
            "sha256": approval_sha256,
            "reviewer": reviewer.strip(),
            "approved_at_utc": approved_at.isoformat(),
            "audit": {key: audit[key] for key in APPROVAL_AUDIT_FIELDS},
        }

    def chain_link(self, phase: str, link_sha256: str) -> dict[str, Any]:
        """The receipt of the loaded chain with this phase whose file has this sha256."""
        for receipt, below in zip(self.chain, self.chain[1:], strict=False):
            if below["phase"] == phase and receipt["previous"]["sha256"] == link_sha256:
                return below
        raise RuntimeError(f"no {phase} receipt with that sha256 in the chain; refused")

    def quiescent_bundle(
        self,
        quiescent: Path,
        quiescent_sha256: str,
        approval: Path,
        approval_sha256: str,
    ) -> tuple[Path, str]:
        """The quiescent receipt pinned by sha AND approved independently; then the bundle gates."""
        head = self.follow(
            quiescent, ("quiescent-slice",), expected=quiescent_sha256, mode=QUIESCENT
        )
        approved = self.activation(head, quiescent_sha256, approval, approval_sha256)
        gate = self.up_gate(head)
        return self.write(
            "quiescent-bundle",
            {
                "mode": QUIESCENT,
                "quiescent_receipt": {
                    "path": str(Path(quiescent).resolve()),
                    "sha256": quiescent_sha256,
                },
                "approval": approved,
                **gate,
                "replaces": "preflight.assert_compose (3 files, brain build/tag) for this 4-file render by image IDs",
            },
            step=("quiescent-up", self.plan["up"]),
        )

    def fallback_plan(
        self, previous: Path, rescue_id: str | None = None, receipt: Path | None = None
    ) -> tuple[Path, str]:
        self.follow(
            previous,
            ("post-stop", "bundle", "exec-step"),
            results=("pass", "hold"),
            mode=None,
            quiescent_refusal=QUIESCENT_RETURN,
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
        head = self.follow(
            previous,
            ("fallback-plan", "exec-step"),
            mode=None,
            quiescent_refusal=QUIESCENT_RETURN,
        )
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
        self.follow(
            previous, ("exec-step",), mode=None, quiescent_refusal=QUIESCENT_RETURN
        )
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
        if name in STOP_STEPS:
            game = receipt["game"]
            if (
                argv != [*STOP, game["id"]]
                or not HEX64.fullmatch(argv[-1])
                or self.stopped
            ):
                raise RuntimeError(
                    "the stop must target the verified game container ID; refused"
                )
            people = receipt["human_absence"]
            notice = people["window_notice"]
            if name == "quiescent-stop-game":
                self.check_window(receipt["window"])
            gate = self.stop_gate(
                Path(notice["path"]),
                notice["sha256"],
                people["game"]["started_at"],
                historical_slice=name == "stop-game",
            )
            self.refreshed = gate["human_absence"]
            self.deadline = self.session_checked + STOP_DEADLINE
            if gate["game"] != game:
                raise RuntimeError(
                    "the game container changed since the pre-stop gate; refused"
                )
        elif name == "up":
            if argv != self.plan["up"]:
                raise RuntimeError("the up argv is not the pinned 4-file argv; refused")
            self.up_gate()
        elif name == "quiescent-up":
            if argv != self.plan["up"]:
                raise RuntimeError("the up argv is not the pinned 4-file argv; refused")
            pinned = receipt["quiescent_receipt"]
            quiescent = self.chain[1]
            if (
                quiescent["phase"] != "quiescent-slice"
                or receipt["previous"]["sha256"] != pinned["sha256"]
            ):
                raise RuntimeError(
                    "the quiescent bundle does not chain to its pinned quiescent receipt; refused"
                )
            approval = receipt["approval"]
            self.activation(
                quiescent, pinned["sha256"], Path(approval["path"]), approval["sha256"]
            )
            self.up_gate(quiescent)  # strict writers gate, right before the up
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

    def attempt_key(self) -> str:
        """The quiescent attempt of the loaded chain: its quiescent-pre-stop receipt sha256, the
        key of its stop claim (<key>.quiescent-stop-game.claim) and of the managed return."""
        stops = [
            receipt
            for receipt in self.chain
            if receipt["phase"] == "exec-step"
            and receipt["step"]["name"] == "quiescent-stop-game"
        ]
        key = str(stops[0]["previous"]["sha256"]) if len(stops) == 1 else ""
        if not HEX64.fullmatch(key):
            raise RuntimeError("no single quiescent stop keys this attempt; refused")
        return key

    @contextlib.contextmanager
    def attempt_guard(self) -> Iterator[None]:
        """The lock shared with the managed return, and its ABANDONED marker.

        Never waited for: busy refuses. Re-entrant in one Handoff (exec-step holds it across
        its precheck, claim, up and result). A marker this check does not see cannot exist:
        the return writes it only while it holds the same lock.
        """
        directory = self.plan["project"] / RETURN_ATTEMPTS / self.attempt_key()
        for part in (directory.parent.parent, directory.parent, directory):
            private_directory(part)
        owner = self.attempt_lock is None
        if owner:
            flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(directory / ATTEMPT_LOCK, flags, 0o600)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                os.close(descriptor)
                raise RuntimeError(
                    "the attempt lock is held: the managed return of this quiescent attempt "
                    "is running; no up, refused"
                ) from None
            self.attempt_lock = descriptor
        try:
            if os.path.lexists(directory / ABANDONED):
                raise RuntimeError(
                    "this quiescent attempt was abandoned for the managed return (ABANDONED); "
                    "no up, refused"
                )
            yield
        finally:
            if owner:
                self.attempt_lock = None
                os.close(descriptor)

    def claim_paths(self, receipt_sha256: str, receipt: dict[str, Any]) -> list[Path]:
        """Canonical claim files: the receipt's step, for the rescue start the container itself,
        and for a quiescent up the quiescent receipt (single use, whatever bundle cites it)."""
        step = receipt["step"]
        paths = [self.claims / f"{receipt_sha256}.{step['name']}.claim"]
        if step["name"] == "start-rescue":
            paths.append(self.claims / f"start-rescue.{RESCUE_ID}.claim")
        if step["name"] == "quiescent-up":
            pinned = receipt["quiescent_receipt"]["sha256"]
            paths.append(self.claims / f"{pinned}.activate.claim")
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

    def within_deadline(self, receipt: dict[str, Any]) -> None:
        """The stop runs within STOP_DEADLINE monotonic seconds of the final session check.

        Checked twice. Before the claim, an expiry refuses with nothing claimed (nothing ran,
        and the same pre-stop receipt may be tried again, with every gate refreshed). After
        the claim, an expiry also refuses with no mutation, but the claim stays consumed, with
        a result saying it was not executed: the atomic-claim rule (one claim, never retried)
        is kept, and the stop needs a new pre-stop receipt.
        """
        if self.window_end is not None and utcnow() >= self.window_end:
            self.expired = "QA window expired"
            raise RuntimeError(
                "the QA window ended: the quiescent receipt and any approval are void; "
                "refused, no mutation"
            )
        if self.deadline is None:
            return
        now = utcnow()
        if (
            monotonic() > self.deadline
            or now > self.fresh_until
            or now - datetime.fromisoformat(receipt["recorded_at_utc"]) > STEP_MAX_AGE
        ):
            self.expired = "stop deadline expired"
            raise RuntimeError(
                f"the stop missed its {STOP_DEADLINE:g} s deadline after the final session "
                "check (or another freshness limit); refused, no mutation"
            )

    def exec_step(self, path: Path, expected: str) -> tuple[Path, str]:
        receipt = self.follow(
            path,
            (
                "pre-stop",
                "bundle",
                "fallback-plan",
                "fallback-verify",
                "quiescent-pre-stop",
                "quiescent-bundle",
            ),
            expected=expected,
            mode=None,
        )
        step = receipt.get("step")
        if not step or digest(step["argv"]) != step["argv_sha256"]:
            raise RuntimeError(f"receipt {path.name} seals no valid step; refused")
        if self.mode == QUIESCENT and step["name"] not in QUIESCENT_STEPS:
            raise RuntimeError(QUIESCENT_RETURN)
        claims = self.claim_paths(expected, receipt)
        for claim in claims:  # early answer; the atomic claim below is what decides
            if claim.exists():
                raise RuntimeError(self.claimed(claim))
        with contextlib.ExitStack() as guard:
            # the quiescent up holds the attempt lock to its end, and so does its child
            if step["name"] == "quiescent-up":
                guard.enter_context(self.attempt_guard())
                if self.attempt_lock is None:  # the guard just took it
                    raise RuntimeError("the attempt lock is not held; refused")
                HELD_LOCKS[:] = [self.attempt_lock]
                guard.callback(HELD_LOCKS.clear)
            return self.claim_and_run(path, expected, receipt, step, claims)

    def claim_and_run(
        self,
        path: Path,
        expected: str,
        receipt: dict[str, Any],
        step: dict[str, Any],
        claims: list[Path],
    ) -> tuple[Path, str]:
        age = utcnow() - datetime.fromisoformat(receipt["recorded_at_utc"])
        if age < timedelta(0):
            raise RuntimeError(f"receipt {path.name} is dated in the future; refused")
        if age > STEP_MAX_AGE:
            raise RuntimeError(
                f"receipt {path.name} is stale; rerun its phase; refused"
            )
        self.deadline, self.refreshed, self.window_end = None, None, None
        self.precheck(receipt, step["argv"])
        self.within_deadline(
            receipt
        )  # expired here: refused, nothing claimed, nothing ran
        body = {
            "receipt_sha256": expected,
            "step": step["name"],
            "argv_sha256": step["argv_sha256"],
            "pid": os.getpid(),
            "claimed_at_utc": utcnow().isoformat(),
        }
        for claim in claims:
            self.claim(claim, body)
        try:
            self.within_deadline(receipt)
        except (
            RuntimeError
        ):  # expired after the claim: consumed, certainly not executed
            for claim in claims:
                create_exclusive(
                    claim.with_suffix(".result"),
                    (
                        json.dumps({"executed": False, "reason": self.expired}) + "\n"
                    ).encode(),
                )
            raise
        started = utcnow()
        try:
            code, out, err = execute(step["argv"])
            data = {
                "step": {key: step[key] for key in ("name", "argv", "argv_sha256")},
                "exit_code": code,
                "claim": str(claims[0]),
                "started_at_utc": started.isoformat(),
                "finished_at_utc": utcnow().isoformat(),
                **(
                    {"refreshed_human_absence": self.refreshed}
                    if self.refreshed
                    else {}
                ),
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
    quiescent_post_build = phases.add_parser("quiescent-post-build")
    for key in RECEIPT_KEYS:
        quiescent_post_build.add_argument(
            f"--{key.replace('_', '-')}",
            type=Path,
            help="optional: must be the manifest's absolute path",
        )
    quiescent_post_build.add_argument("--sanitized-render", type=Path, required=True)
    stops = {
        name: phases.add_parser(name) for name in ("pre-stop", "quiescent-pre-stop")
    }
    for name, sub in stops.items():
        sub.add_argument(
            "--attested-by",
            required=True,
            help="the person in the session who authorizes the stop",
        )
        sub.add_argument(
            "--attested-at",
            required=True,
            help="UTC time of that authorization, ISO 8601",
        )
        sub.add_argument(
            "--window-notice",
            type=Path,
            required=True,
            help="the coordinator's window notice (file)"
            + (
                "; JSON with window_start_utc and window_end_utc"
                if name.startswith("quiescent")
                else ""
            ),
        )
        sub.add_argument(
            "--window-notice-sha256", required=True, help="sha256 of that file"
        )
    quiescent_bundle = phases.add_parser("quiescent-bundle")
    quiescent_bundle.add_argument("--quiescent-receipt", type=Path, required=True)
    quiescent_bundle.add_argument(
        "--quiescent-receipt-sha256",
        required=True,
        help="pins the bytes; it is not the approval",
    )
    quiescent_bundle.add_argument(
        "--approval",
        type=Path,
        required=True,
        help="the independent approval JSON (" + APPROVAL_SCHEMA + ")",
    )
    quiescent_bundle.add_argument("--approval-sha256", required=True)
    for name in (
        "pre-stop",
        "quiescent-pre-stop",
        "post-stop",
        "quiescent-slice",
        "bundle",
        "fallback-plan",
        "fallback-verify",
        "rescue-verify",
    ):
        sub = stops.get(name) or phases.add_parser(name)
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
    if args.phase in ("post-build", "quiescent-post-build"):
        given = {key: getattr(args, key) for key in RECEIPT_KEYS if getattr(args, key)}
        path, sha = handoff.post_build(
            given, args.sanitized_render, quiescent=args.phase == "quiescent-post-build"
        )
    elif args.phase in ("pre-stop", "quiescent-pre-stop"):
        phase = (
            handoff.pre_stop if args.phase == "pre-stop" else handoff.quiescent_pre_stop
        )
        path, sha = phase(
            args.previous,
            args.attested_by,
            args.attested_at,
            args.window_notice,
            args.window_notice_sha256,
        )
    elif args.phase == "post-stop":
        path, sha = handoff.post_stop(args.previous)
    elif args.phase == "quiescent-slice":
        path, sha = handoff.quiescent_slice(args.previous)
    elif args.phase == "quiescent-bundle":
        path, sha = handoff.quiescent_bundle(
            args.quiescent_receipt,
            args.quiescent_receipt_sha256,
            args.approval,
            args.approval_sha256,
        )
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
