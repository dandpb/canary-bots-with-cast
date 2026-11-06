"""Bounded background recording; replay never participates in game execution."""

from __future__ import annotations

import contextvars
import hashlib
import json
import queue
import re
import sqlite3
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .protocol import Observation
from .sqlite_files import prepare_database, sqlite_operation

SCHEMA = 1
request_context: contextvars.ContextVar[tuple[int, str]] = contextvars.ContextVar(
    "recording_request", default=(0, "")
)
KINDS = {
    "sample",
    "decision",
    "proposal",
    "intent",
    "outcome",
    "request",
    "operator",
    "lifecycle",
    "gap",
    "segment",
    "level",
    "configuration",
}


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal[1] = 1
    run_id: str = Field(pattern=r"^[\w.:-]{1,128}$")
    bot_id: int = Field(gt=0)
    lineage: str = Field(min_length=1, max_length=128)
    experiment: str | None = Field(default=None, max_length=128)
    scenario: str = Field(default="lifetime", max_length=128)
    participant: str = Field(default="existing-controller", max_length=128)
    model: str = Field(default="gpt-6-luna", max_length=128)
    provider: str = Field(default="openai", max_length=128)
    memory_mode: Literal["existing", "frozen", "independent"] = "existing"
    initial_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    configuration_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    source_revision: str = Field(default="unknown", max_length=128)
    sample_ms: int = Field(default=1000, ge=250, le=60000)
    synthetic: bool = False


class RecordingConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: Path
    namespace: str = Field(pattern=r"^[\w.-]{1,64}$")
    sample_ms: int = Field(default=1000, ge=250, le=60000)
    queue_size: int = Field(default=2048, ge=16, le=65536)
    max_bytes: int = Field(default=512 * 1024 * 1024, ge=1024 * 1024)
    manifests: list[Manifest] = Field(default_factory=list, max_length=3)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def public_data(value: Any) -> Any:
    """Defense in depth for game text; credentials are never recorder inputs."""
    if isinstance(value, dict):
        return {
            str(k): public_data(v)
            for k, v in value.items()
            if str(k).lower()
            not in {
                "secret",
                "credential",
                "authorization",
                "api_key",
                "token",
                "lease",
                "credential_file",
                "master_key",
                "gateway_key",
            }
        }
    if isinstance(value, list):
        return [public_data(v) for v in value]
    if isinstance(value, str):
        return re.sub(r"(?:sk-|lzl_)[A-Za-z0-9_.-]+|Bearer\s+\S+", "[redacted]", value)
    return value


@contextmanager
def attribution(bot: int, decision: str | None = None) -> Iterator[str]:
    identity = decision or uuid.uuid4().hex
    token = request_context.set((bot, identity))
    try:
        yield identity
    finally:
        request_context.reset(token)


class RecordingStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        if path.is_symlink():
            raise ValueError("recording path must not be a symlink")
        prepare_database(path)
        with self.connect() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, SCHEMA):
                raise ValueError("unsupported recording schema")
            if (
                version == SCHEMA
                and not db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='replay_runs'"
                ).fetchone()
            ):
                raise ValueError("destination is not a recording database")
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS replay_runs(
                    id TEXT PRIMARY KEY, manifest TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    incomplete INTEGER NOT NULL DEFAULT 0,
                    started REAL NOT NULL, updated REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS replay_events(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, run TEXT NOT NULL,
                    event_key TEXT NOT NULL, segment TEXT NOT NULL,
                    t_ms INTEGER NOT NULL, wall REAL NOT NULL,
                    kind TEXT NOT NULL, data TEXT NOT NULL,
                    UNIQUE(run,event_key),
                    FOREIGN KEY(run) REFERENCES replay_runs(id)
                );
                CREATE INDEX IF NOT EXISTS replay_time ON replay_events(run,t_ms,id);
                PRAGMA user_version=1;
            """)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        with sqlite_operation("recording.write"):
            db = sqlite3.connect(self.path, timeout=0.2)
            try:
                db.execute("PRAGMA foreign_keys=ON")
                with db:
                    yield db
            finally:
                db.close()

    def begin(self, manifest: Manifest) -> tuple[int, float | None]:
        encoded = canonical(manifest.model_dump())
        with self.connect() as db:
            row = db.execute(
                "SELECT manifest,status FROM replay_runs WHERE id=?", (manifest.run_id,)
            ).fetchone()
            if row:
                old = Manifest.model_validate_json(row[0])
                incompatible = (
                    old.bot_id != manifest.bot_id or old.lineage != manifest.lineage
                )
                if (
                    row[1] != "running"
                    or incompatible
                    or (manifest.experiment and row[0] != encoded)
                ):
                    raise ValueError(
                        "run identity already has a different manifest or is closed"
                    )
            now = time.time()
            db.execute(
                "INSERT OR IGNORE INTO replay_runs(id,manifest,started,updated) VALUES(?,?,?,?)",
                (manifest.run_id, encoded, now, now),
            )
            previous = db.execute(
                "SELECT t_ms,wall FROM replay_events WHERE run=? ORDER BY t_ms DESC,id DESC LIMIT 1",
                (manifest.run_id,),
            ).fetchone()
        return (previous[0], previous[1]) if previous else (0, None)

    def append(self, event: dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO replay_events(run,event_key,segment,t_ms,wall,kind,data) VALUES(?,?,?,?,?,?,?)",
                (
                    event["run"],
                    event["key"],
                    event["segment"],
                    event["t_ms"],
                    event["wall"],
                    event["kind"],
                    canonical(event["data"]),
                ),
            )
            db.execute(
                "UPDATE replay_runs SET updated=?, incomplete=MAX(incomplete,?) WHERE id=?",
                (
                    event["wall"],
                    int(event["kind"] == "gap"),
                    event["run"],
                ),
            )

    def finish(self, run: str, status: str) -> None:
        if status not in {"completed", "failed", "budget_stop", "interrupted"}:
            raise ValueError("invalid terminal run status")
        with self.connect() as db:
            row = db.execute(
                "SELECT status FROM replay_runs WHERE id=?", (run,)
            ).fetchone()
            if row is None or row[0] not in {"running", status}:
                raise ValueError("invalid run transition")
            db.execute(
                "UPDATE replay_runs SET status=?,updated=? WHERE id=?",
                (status, time.time(), run),
            )

    def import_run(
        self, manifest: Manifest, metadata: dict[str, Any], events: list[dict[str, Any]]
    ) -> None:
        """Archive import owns a new identity and commits its entire history once."""
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute(
                "SELECT 1 FROM replay_runs WHERE id=?", (manifest.run_id,)
            ).fetchone():
                raise ValueError(
                    "run identity already exists; import into a new recording"
                )
            db.execute(
                "INSERT INTO replay_runs(id,manifest,status,incomplete,started,updated) VALUES(?,?,?,?,?,?)",
                (
                    manifest.run_id,
                    canonical(manifest.model_dump()),
                    metadata["status"],
                    int(
                        metadata["incomplete"]
                        or any(e["kind"] == "gap" for e in events)
                    ),
                    metadata["started"],
                    metadata["updated"],
                ),
            )
            db.executemany(
                "INSERT INTO replay_events(run,event_key,segment,t_ms,wall,kind,data) VALUES(?,?,?,?,?,?,?)",
                (
                    (
                        manifest.run_id,
                        e["key"],
                        e["segment"],
                        e["t_ms"],
                        e["wall"],
                        e["kind"],
                        canonical(e["data"]),
                    )
                    for e in events
                ),
            )


class ReplayReader:
    """Read-only connections: viewing cannot create or mutate a recording."""

    def __init__(
        self, path: Path, *, _connection: sqlite3.Connection | None = None
    ) -> None:
        if path.is_symlink() or not path.is_file():
            raise ValueError("recording is unavailable")
        self.path = path
        self._connection = _connection
        with self.connect() as db:
            if db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA:
                raise ValueError("unsupported recording schema")

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        with sqlite_operation("recording.read"):
            if self._connection is not None:
                yield self._connection
                return
            db = sqlite3.connect(
                self.path.resolve().as_uri() + "?mode=ro", uri=True, timeout=0.2
            )
            try:
                db.execute("BEGIN")
                yield db
            finally:
                db.close()

    @contextmanager
    def snapshot(self) -> Iterator[ReplayReader]:
        """Pin every query/paginated batch to the same read-only WAL snapshot."""
        with self.connect() as db:
            yield ReplayReader(self.path, _connection=db)

    def runs(
        self, limit: int = 100, before: float | None = None
    ) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT id,manifest,status,incomplete,started,updated FROM replay_runs WHERE updated<? ORDER BY updated DESC,id LIMIT ?",
                (before or 1e20, min(max(limit, 1), 100)),
            ).fetchall()
        return [
            {
                "id": r[0],
                "manifest": json.loads(r[1]),
                "status": r[2],
                "incomplete": bool(r[3]),
                "started": r[4],
                "updated": r[5],
            }
            for r in rows
        ]

    def run(self, run: str) -> dict[str, Any]:
        with self.connect() as db:
            row = db.execute(
                "SELECT manifest,status,incomplete,started,updated FROM replay_runs WHERE id=?",
                (run,),
            ).fetchone()
            if row is None:
                raise ValueError("unknown recording")
            count, end = db.execute(
                "SELECT COUNT(*),COALESCE(MAX(t_ms),0) FROM replay_events WHERE run=?",
                (run,),
            ).fetchone()
        return {
            "id": run,
            "manifest": json.loads(row[0]),
            "status": row[1],
            "incomplete": bool(row[2]),
            "started": row[3],
            "updated": row[4],
            "event_count": count,
            "duration_ms": end,
        }

    def events(
        self, run: str, after: int = 0, limit: int = 500, until_ms: int | None = None
    ) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT id,event_key,segment,t_ms,wall,kind,data FROM replay_events WHERE run=? AND id>? AND t_ms<=? ORDER BY id LIMIT ?",
                (
                    run,
                    max(0, after),
                    until_ms if until_ms is not None else 2**63 - 1,
                    min(max(limit, 1), 1000),
                ),
            ).fetchall()
        return [
            {
                "id": r[0],
                "key": r[1],
                "segment": r[2],
                "t_ms": r[3],
                "wall": r[4],
                "kind": r[5],
                "data": json.loads(r[6]),
            }
            for r in rows
        ]

    def all_events(self, run: str) -> Iterator[dict[str, Any]]:
        after = 0
        while rows := self.events(run, after, 1000):
            yield from rows
            after = rows[-1]["id"]

    def ordered_events(self, run: str, until_ms: int) -> Iterator[dict[str, Any]]:
        """Stream a chronological prefix without loading a bot's entire life."""
        with self.connect() as db:
            cursor = db.execute(
                "SELECT id,event_key,segment,t_ms,wall,kind,data FROM replay_events "
                "WHERE run=? AND t_ms<=? ORDER BY t_ms,id",
                (run, until_ms),
            )
            while rows := cursor.fetchmany(1000):
                for row in rows:
                    yield {
                        "id": row[0],
                        "key": row[1],
                        "segment": row[2],
                        "t_ms": row[3],
                        "wall": row[4],
                        "kind": row[5],
                        "data": json.loads(row[6]),
                    }

    def track(self, run: str, limit: int = 2000) -> list[dict[str, Any]]:
        duration = self.run(run)["duration_ms"]
        bucket = max(1, (duration + limit - 1) // min(max(limit, 1), 2000))
        with self.connect() as db:
            rows = db.execute(
                "SELECT t_ms,data FROM replay_events WHERE id IN (SELECT MAX(id) FROM replay_events WHERE run=? AND kind='sample' GROUP BY CAST(t_ms/? AS INTEGER)) ORDER BY t_ms,id",
                (run, bucket),
            ).fetchall()
        return [{"t_ms": row[0], "data": json.loads(row[1])} for row in rows]

    def timeline(self, run: str, at_ms: int, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT id,t_ms,kind,data FROM replay_events WHERE run=? AND kind!='sample' AND t_ms<=? ORDER BY t_ms DESC,id DESC LIMIT ?",
                (run, max(0, at_ms), min(max(limit, 1), 200)),
            ).fetchall()
        return [
            {"id": r[0], "t_ms": r[1], "kind": r[2], "data": json.loads(r[3])}
            for r in rows
        ]

    def seek(self, run: str, t_ms: int) -> dict[str, Any]:
        self.run(run)
        with self.connect() as db:
            row = db.execute(
                "SELECT id,t_ms,data FROM replay_events WHERE run=? AND kind='sample' AND t_ms<=? ORDER BY t_ms DESC,id DESC LIMIT 1",
                (run, max(0, t_ms)),
            ).fetchone()
            gap = db.execute(
                "SELECT t_ms,data FROM replay_events WHERE run=? AND kind='gap' AND t_ms<=? ORDER BY t_ms DESC,id DESC LIMIT 1",
                (run, max(0, t_ms)),
            ).fetchone()
        return {
            "at_ms": t_ms,
            "sample": None
            if row is None
            else {"id": row[0], "t_ms": row[1], "data": json.loads(row[2])},
            "gap": None
            if gap is None
            else {"t_ms": gap[0], "data": json.loads(gap[1])},
        }


class Recorder:
    def __init__(
        self, config: RecordingConfiguration, manifests: list[Manifest]
    ) -> None:
        self.config, self.store = config, RecordingStore(config.path)
        self.manifests = {m.bot_id: m for m in manifests}
        if len(self.manifests) != len(manifests):
            raise ValueError("duplicate recording bot")
        self.segment = uuid.uuid4().hex
        self.started = time.monotonic()
        self.offsets: dict[int, int] = {}
        self.samples: dict[int, tuple[str, int, int, int, int]] = {}
        self.last_state: dict[int, tuple[int, bool, int, str]] = {}
        self.native: dict[int, tuple[str, int]] = {}
        self.queue: queue.Queue[dict[str, Any] | None] = queue.Queue(config.queue_size)
        self.dropped: dict[int, int] = {}
        self.errors = 0
        self.closed = False
        for m in manifests:
            end, previous_wall = self.store.begin(m)
            gap = (
                max(0, int((time.time() - previous_wall) * 1000))
                if previous_wall
                else 0
            )
            self.offsets[m.bot_id] = end + gap
            self.emit(
                m.bot_id,
                "segment",
                {"phase": "started", "recording_begins_midlife": True},
            )
            if previous_wall is not None:
                self.emit(
                    m.bot_id, "gap", {"reason": "worker_restart", "duration_ms": gap}
                )
        self.thread = threading.Thread(
            target=self._write, name="brain-recorder", daemon=True
        )
        self.thread.start()

    def emit(
        self, bot: int, kind: str, data: dict[str, Any], key: str | None = None
    ) -> bool:
        if self.closed or bot not in self.manifests:
            return False
        if kind not in KINDS:
            raise ValueError("unknown recording event kind")
        cleaned = public_data(data)
        if len(canonical(cleaned).encode()) > 65536:
            self.dropped[bot] = self.dropped.get(bot, 0) + 1
            return False
        event = {
            "run": self.manifests[bot].run_id,
            "key": key or uuid.uuid4().hex,
            "segment": self.segment,
            "t_ms": self.offsets[bot]
            + max(0, int((time.monotonic() - self.started) * 1000)),
            "wall": time.time(),
            "kind": kind,
            "data": cleaned,
        }
        try:
            self.queue.put_nowait(event)
        except queue.Full:
            self.dropped[bot] = self.dropped.get(bot, 0) + 1
            return False
        return True

    def observe(self, observation: Observation) -> None:
        bot = observation.bot.id
        if bot not in self.manifests:
            return
        previous = self.samples.get(bot)
        if (
            previous
            and previous[0] == observation.world
            and observation.sequence <= previous[1]
        ):
            return
        # Persist the selected sample as a full checkpoint, not an interpolated state.
        now = int(time.monotonic() * 1000)
        if previous and previous[0] != observation.world:
            self.emit(
                bot,
                "gap",
                {"reason": "engine_generation_changed", "world": observation.world},
            )
        elif previous and observation.sequence > previous[1] + 1:
            self.emit(
                bot,
                "lifecycle",
                {
                    "phase": "observation_sequence_jump",
                    "jump": observation.sequence - previous[1] - 1,
                    "note": "Native validation also advances this counter; this is not proof of packet loss.",
                },
            )
        if previous and now - previous[2] > 5000:
            self.emit(
                bot,
                "gap",
                {"reason": "observation_timeout", "duration_ms": now - previous[2]},
            )
        level = observation.bot.level
        state = (
            observation.bot.position[2],
            observation.bot.alive,
            observation.objective_generation,
            observation.bot.objective,
        )
        critical = self.last_state.get(bot) != state
        self.last_state[bot] = state
        if previous and level > previous[4]:
            self.emit(
                bot,
                "level",
                {"from": previous[4], "to": level, "xp": observation.bot.xp},
            )
        sampled = previous[3] if previous else -100000
        if (
            now - sampled >= self.manifests[bot].sample_ms
            or not previous
            or level != previous[4]
            or critical
        ) and self.emit(
            bot,
            "sample",
            observation.model_dump(exclude={"lease", "messages"}),
            f"sample:{observation.world}:{observation.sequence}",
        ):
            sampled = now
        self.samples[bot] = (
            observation.world,
            observation.sequence,
            now,
            sampled,
            level,
        )

    def native_event(
        self, bot: int, world: str, sequence: int, data: dict[str, Any]
    ) -> None:
        previous = self.native.get(bot)
        if previous and previous[0] == world and sequence <= previous[1]:
            return
        self.native[bot] = (world, sequence)
        if previous and previous[0] == world and sequence > previous[1] + 1:
            self.emit(
                bot,
                "gap",
                {
                    "reason": "native_telemetry_loss",
                    "missing": sequence - previous[1] - 1,
                },
            )
        self.emit(
            bot,
            "lifecycle",
            {"world": world, **data},
            f"native:{world}:{bot}:{sequence}",
        )

    def health(self) -> dict[str, Any]:
        return {
            "queued": self.queue.qsize(),
            "dropped": sum(self.dropped.values()),
            "errors": self.errors,
            "closed": self.closed,
        }

    def _write(self) -> None:
        while True:
            event = self.queue.get()
            try:
                if event is None:
                    return
                bot = next(
                    m.bot_id
                    for m in self.manifests.values()
                    if m.run_id == event["run"]
                )
                dropped = self.dropped.pop(bot, 0)
                if dropped:
                    self.store.append(
                        {
                            **event,
                            "key": uuid.uuid4().hex,
                            "kind": "gap",
                            "data": {"reason": "recorder_loss", "count": dropped},
                        }
                    )
                size = sum(
                    p.stat().st_size
                    for p in (self.config.path, Path(str(self.config.path) + "-wal"))
                    if p.exists()
                )
                if size >= self.config.max_bytes and event["kind"] != "gap":
                    self.store.append(
                        {
                            **event,
                            "key": "storage_limit:" + self.segment,
                            "kind": "gap",
                            "data": {"reason": "storage_limit"},
                        }
                    )
                    continue
                self.store.append(event)
            except (sqlite3.Error, OSError):
                self.errors += 1
                if event is not None:
                    self.dropped[bot] = self.dropped.get(bot, 0) + 1
            finally:
                self.queue.task_done()

    def flush(self) -> None:
        self.queue.join()

    def close(self) -> None:
        if self.closed:
            return
        self.flush()
        for bot in self.manifests:
            self.emit(bot, "segment", {"phase": "stopped", "errors": self.errors})
        self.flush()
        self.closed = True
        self.queue.put(None)
        self.thread.join(timeout=5)
