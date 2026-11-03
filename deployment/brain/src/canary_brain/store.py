"""Private worker persistence. Money is integer nanodollars, never binary float."""

import json
import os
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

USD = 1_000_000_000


class BudgetExceeded(Exception):
    pass


def month_now() -> str:
    return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m")


class Store:
    def __init__(self, path: Path, cap: int = 50 * USD) -> None:
        self.path, self.cap = path, cap
        self._transaction = threading.local()
        if path.is_symlink():
            raise ValueError("state file must not be a symlink")
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        os.close(descriptor)
        os.chmod(path, 0o600)
        with self.connection() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS requests (
                    id TEXT PRIMARY KEY, month TEXT NOT NULL, reserved INTEGER NOT NULL,
                    spent INTEGER, endpoint TEXT NOT NULL DEFAULT '', created REAL DEFAULT (unixepoch())
                );
                CREATE INDEX IF NOT EXISTS requests_month ON requests(month);
                CREATE TABLE IF NOT EXISTS records (
                    kind TEXT NOT NULL, key TEXT NOT NULL, data TEXT NOT NULL,
                    PRIMARY KEY(kind,key)
                );
                PRAGMA user_version=1;
            """)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        active = getattr(self._transaction, "connection", None)
        if active is not None:
            yield active
            return
        db = sqlite3.connect(self.path, timeout=0.2)
        try:
            with db:
                yield db
        finally:
            db.close()

    @contextmanager
    def atomic(self) -> Iterator[None]:
        """Group synchronous record updates; callers must not await inside this scope."""
        with self.connection() as db:
            if getattr(self._transaction, "connection", None) is not None:
                yield
                return
            db.execute("BEGIN IMMEDIATE")
            self._transaction.connection = db
            try:
                yield
            finally:
                self._transaction.connection = None

    def reserve(
        self, request_id: str, amount: int, month: str, endpoint: str = ""
    ) -> None:
        if amount <= 0:
            raise ValueError("reservation must be positive")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            # Unsettled requests from previous months remain liabilities.
            used = db.execute(
                "SELECT COALESCE(SUM(CASE WHEN spent IS NULL THEN reserved ELSE spent END),0) "
                "FROM requests WHERE month=? OR spent IS NULL",
                (month,),
            ).fetchone()[0]
            if used + amount > self.cap:
                raise BudgetExceeded("monthly application budget exhausted")
            db.execute(
                "INSERT INTO requests(id,month,reserved,endpoint) VALUES(?,?,?,?)",
                (request_id, month, amount, endpoint),
            )

    def settle(self, request_id: str, spent: int) -> None:
        if spent < 0:
            raise ValueError("spend must be nonnegative")
        with self.connection() as db:
            row = db.execute(
                "SELECT reserved,spent FROM requests WHERE id=?", (request_id,)
            ).fetchone()
            if row is None:
                raise ValueError("unknown request")
            if row[1] is not None:
                if row[1] != spent:
                    raise ValueError("request already settled differently")
                return
            # Preserve actual liability even if pricing or an estimate changed.
            db.execute("UPDATE requests SET spent=? WHERE id=?", (spent, request_id))

    def budget(self, month: str | None = None) -> dict[str, int]:
        with self.connection() as db:
            spent, reserved = db.execute(
                "SELECT COALESCE(SUM(CASE WHEN month=? THEN spent ELSE 0 END),0),"
                "COALESCE(SUM(CASE WHEN spent IS NULL THEN reserved ELSE 0 END),0) FROM requests",
                (month or month_now(),),
            ).fetchone()
        return {
            "cap": self.cap,
            "spent": spent,
            "reserved": reserved,
            "available": max(0, self.cap - spent - reserved),
        }

    def put(self, kind: str, key: str, data: dict[str, Any]) -> None:
        encoded = json.dumps(data, separators=(",", ":"), allow_nan=False)
        with self.connection() as db:
            db.execute(
                "INSERT INTO records VALUES(?,?,?) ON CONFLICT(kind,key) DO UPDATE SET data=excluded.data",
                (kind, key, encoded),
            )

    def get(self, kind: str, key: str) -> dict[str, Any] | None:
        with self.connection() as db:
            row = db.execute(
                "SELECT data FROM records WHERE kind=? AND key=?", (kind, key)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def records(self, kind: str, limit: int = 100) -> list[tuple[str, dict[str, Any]]]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT key,data FROM records WHERE kind=? ORDER BY rowid DESC LIMIT ?",
                (kind, min(max(limit, 1), 1000)),
            ).fetchall()
        return [(key, json.loads(data)) for key, data in rows]

    def forget(self, kind: str, key: str) -> None:
        if kind not in {"policy", "memory", "profile", "recent"}:
            raise ValueError("only learning and conversation records may be forgotten")
        self.delete(kind, key)

    def delete(self, kind: str, key: str) -> None:
        with self.connection() as db:
            db.execute("DELETE FROM records WHERE kind=? AND key=?", (kind, key))

    def prune(self) -> None:
        """Bound diagnostic history while retaining open work, policies and accounting."""
        with self.connection() as db:
            for kind, maximum in (
                ("episode", 5000),
                ("request", 5000),
                ("reflection", 500),
                ("plan_history", 500),
                ("memory", 500),
            ):
                db.execute(
                    "DELETE FROM records WHERE kind=? AND rowid NOT IN "
                    "(SELECT rowid FROM records WHERE kind=? ORDER BY rowid DESC LIMIT ?) "
                    "AND (? != 'episode' OR json_extract(data,'$.terminal') = 1)",
                    (kind, kind, maximum, kind),
                )
