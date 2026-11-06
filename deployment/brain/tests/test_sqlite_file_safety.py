"""Cross-process SQLite lock safety using temporary synthetic databases only."""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from canary_brain.recording import Manifest, RecordingStore
from canary_brain.sqlite_files import prepare_database
from canary_brain.store import Store

LOCK_PROBE = """
import fcntl,json,os,sys
descriptor=os.open(sys.argv[1],os.O_RDWR)
try:
    try:
        fcntl.lockf(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB,510,1073741826)
        available=True
    except BlockingIOError:
        available=False
    print(json.dumps({'available':available}))
finally:
    os.close(descriptor)
"""


def exclusive_lock_available(path):
    return json.loads(
        subprocess.check_output(
            [sys.executable, "-c", LOCK_PROBE, str(path)], text=True
        )
    )["available"]


class SQLiteFileSafety(unittest.TestCase):
    def test_concurrent_creators_publish_one_private_closed_inode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.sqlite3"
            barrier = threading.Barrier(12)

            def create(_):
                barrier.wait()
                prepare_database(path)
                return path.stat().st_ino

            with ThreadPoolExecutor(max_workers=12) as pool:
                inodes = list(pool.map(create, range(12)))
            self.assertEqual(len(set(inodes)), 1)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_new_file_is_closed_before_sqlite_can_observe_the_published_name(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.sqlite3"
            original_link = os.link
            readers = []

            def publish(source, destination, **kwargs):
                identity = Path(source).stat()
                for descriptor in Path("/proc/self/fd").iterdir():
                    try:
                        opened = descriptor.stat()
                    except FileNotFoundError:
                        continue
                    self.assertNotEqual(
                        (opened.st_dev, opened.st_ino),
                        (identity.st_dev, identity.st_ino),
                    )
                original_link(source, destination, **kwargs)
                reader = sqlite3.connect(path)
                reader.execute("PRAGMA journal_mode=WAL")
                reader.execute("BEGIN")
                reader.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
                readers.append(reader)

            try:
                with patch("canary_brain.sqlite_files.os.link", publish):
                    prepare_database(path)
                self.assertFalse(exclusive_lock_available(path))
            finally:
                for reader in readers:
                    reader.close()

    def test_symlinks_are_rejected_without_changing_the_target(self):
        for factory in (Store, RecordingStore):
            with (
                self.subTest(factory=factory.__name__),
                tempfile.TemporaryDirectory() as directory,
            ):
                target = Path(directory) / "outside"
                target.write_bytes(b"untouched")
                target.chmod(0o644)
                link = Path(directory) / "synthetic.sqlite3"
                link.symlink_to(target)
                with self.assertRaises(ValueError):
                    factory(link)
                self.assertEqual(target.read_bytes(), b"untouched")
                self.assertEqual(target.stat().st_mode & 0o777, 0o644)

    def test_failed_preparation_removes_only_its_own_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.sqlite3"
            with (
                patch(
                    "canary_brain.sqlite_files.os.fchmod",
                    side_effect=OSError("synthetic chmod failure"),
                ),
                self.assertRaises(OSError),
            ):
                prepare_database(path)
            self.assertEqual(list(path.parent.iterdir()), [])

    def test_reinitializing_never_cancels_an_existing_sqlite_reader_lock(self):
        for factory in (Store, RecordingStore):
            with (
                self.subTest(factory=factory.__name__),
                tempfile.TemporaryDirectory() as directory,
            ):
                path = Path(directory) / "synthetic.sqlite3"
                factory(path)
                reader = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
                try:
                    with reader:
                        reader.execute("BEGIN")
                        reader.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
                    self.assertFalse(exclusive_lock_available(path))
                    factory(path)
                    self.assertFalse(exclusive_lock_available(path))
                finally:
                    reader.close()

    def test_active_read_transaction_survives_reinitialization_and_external_write(self):
        child = "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE external_probe(value)'); c.commit(); c.close()"
        for factory in (Store, RecordingStore):
            with (
                self.subTest(factory=factory.__name__),
                tempfile.TemporaryDirectory() as directory,
            ):
                path = Path(directory) / "synthetic.sqlite3"
                factory(path)
                reader = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
                try:
                    reader.execute("BEGIN")
                    count = reader.execute(
                        "SELECT COUNT(*) FROM sqlite_master"
                    ).fetchone()[0]
                    factory(path)
                    subprocess.run([sys.executable, "-c", child, str(path)], check=True)
                    self.assertTrue(reader.in_transaction)
                    self.assertEqual(
                        reader.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[
                            0
                        ],
                        count,
                    )
                    self.assertFalse(exclusive_lock_available(path))
                    reader.commit()
                    self.assertGreater(
                        reader.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[
                            0
                        ],
                        count,
                    )
                finally:
                    reader.close()

    def test_repeated_initialization_and_external_writers_preserve_wal_for_30_rounds(
        self,
    ):
        child = """
import json,sys
from canary_brain.recording import RecordingStore
from canary_brain.store import Store
kind,path,index=sys.argv[1:]
if kind=='Store':
    Store(__import__('pathlib').Path(path)).put('external',index,{'synthetic':True})
else:
    RecordingStore(__import__('pathlib').Path(path)).append({
        'run':'synthetic:1','key':'external-'+index,'segment':'synthetic','t_ms':int(index),
        'wall':int(index)+1,'kind':'lifecycle','data':{'synthetic':True}})
"""
        for factory in (Store, RecordingStore):
            with (
                self.subTest(factory=factory.__name__),
                tempfile.TemporaryDirectory() as directory,
            ):
                path = Path(directory) / "synthetic.sqlite3"
                store = factory(path)
                if factory is RecordingStore:
                    store.begin(
                        Manifest(
                            run_id="synthetic:1",
                            bot_id=1,
                            lineage="synthetic",
                            synthetic=True,
                        )
                    )
                reader = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
                try:
                    with reader:
                        reader.execute("BEGIN")
                        reader.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
                    before = [
                        Path(str(path) + suffix).stat().st_ino
                        for suffix in ("-wal", "-shm")
                    ]
                    for index in range(30):
                        store = factory(path)
                        if factory is Store:
                            store.reserve(
                                str(index), 100, "2026-11", run_id="synthetic"
                            )
                        subprocess.run(
                            [
                                sys.executable,
                                "-c",
                                child,
                                factory.__name__,
                                str(path),
                                str(index),
                            ],
                            check=True,
                        )
                        if factory is Store:
                            store.settle(str(index), 20)
                        else:
                            store.append(
                                {
                                    "run": "synthetic:1",
                                    "key": "parent-" + str(index),
                                    "segment": "synthetic",
                                    "t_ms": index,
                                    "wall": index + 1,
                                    "kind": "lifecycle",
                                    "data": {"synthetic": True},
                                }
                            )
                    self.assertEqual(
                        [
                            Path(str(path) + suffix).stat().st_ino
                            for suffix in ("-wal", "-shm")
                        ],
                        before,
                    )
                    self.assertEqual(
                        reader.execute("PRAGMA integrity_check").fetchall(), [("ok",)]
                    )
                    self.assertFalse(exclusive_lock_available(path))
                finally:
                    reader.close()


if __name__ == "__main__":
    unittest.main()
