"""Private SQLite file preparation without disturbing existing POSIX locks."""

import os
import re
import sqlite3
import stat
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


def prepare_database(path: Path) -> None:
    """Publish a closed private inode; never raw-open an existing database."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        path.lstat()
    except FileNotFoundError:
        temporary = path.with_name("." + path.name + "." + uuid.uuid4().hex + ".new")
        descriptor = os.open(
            temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        try:
            try:
                os.fchmod(descriptor, 0o600)
            finally:
                # No SQLite caller can observe the final name before this close.
                os.close(descriptor)
            try:
                os.link(temporary, path, follow_symlinks=False)
            except FileExistsError:
                pass  # Another creator published its already-closed inode first.
        finally:
            temporary.unlink()
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        raise ValueError("SQLite database must not be a symlink")
    if not stat.S_ISREG(mode):
        raise ValueError("SQLite database must be a regular file")
    os.chmod(path, 0o600, follow_symlinks=False)


@contextmanager
def sqlite_operation(stage: str) -> Iterator[None]:
    """Keep the original SQLite exception while identifying its operation."""
    try:
        yield
    except sqlite3.Error as error:
        if not isinstance(getattr(error, "canary_sqlite_stage", None), str):
            vars(error)["canary_sqlite_stage"] = stage
        raise


def failure_metadata(error: BaseException, stage: str) -> dict[str, Any]:
    """Allowlisted diagnostics only; never exception text, SQL, paths or headers."""
    origin = getattr(error, "canary_sqlite_stage", stage)
    if (
        not isinstance(origin, str)
        or re.fullmatch(r"[a-zA-Z0-9_.-]{1,100}", origin) is None
    ):
        origin = stage
    result: dict[str, Any] = {"error_type": type(error).__name__, "stage": origin}
    if isinstance(error, sqlite3.Error):
        code, name = (
            getattr(error, "sqlite_errorcode", None),
            getattr(error, "sqlite_errorname", None),
        )
        if type(code) is int:
            result["sqlite_errorcode"] = code
        if isinstance(name, str) and re.fullmatch(r"SQLITE_[A-Z0-9_]{1,80}", name):
            result["sqlite_errorname"] = name
    return result
