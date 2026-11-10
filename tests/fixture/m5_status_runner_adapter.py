"""Opt-in transport for native status replies and the canonical status consumer.

The runner provides its private fixture SQL transport and an externally verified
epoch. A trace line can enqueue a command, but only an exact processed reply can
create status_observed. The transport never starts a fixture or calls a provider.
"""

import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import time

from m5_status_capture import CaptureHalted, StatusCapture


BOT_NAME = "Grizzle Alyronia"
COMMAND_ID = re.compile(r"[1-9][0-9]*")


class DurableEvents:
    """Exclusive JSONL file; every accepted line is flushed to the filesystem."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        directory = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    def __call__(self, row):
        payload = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
        if os.write(self.fd, payload) != len(payload):
            raise OSError("short status evidence write")
        os.fsync(self.fd)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


class StatusEvidence:
    """Write only accepted native replies to the historical status shape."""

    def __init__(self, events_path, canonical_path, start_mono, clock=time.monotonic):
        self.events = DurableEvents(events_path)
        try:
            self.canonical = DurableEvents(canonical_path)
        except BaseException:
            self.events.close()
            raise
        self.path = self.events.path
        self.canonical_path = self.canonical.path
        self.start_mono = start_mono
        self.clock = clock

    def __call__(self, row):
        self.events(row)
        if row.get("event") == "status_observed":
            self.canonical({"elapsed": self.clock() - self.start_mono,
                            "command_id": row["command_id"], "status": row["status"]})

    def close(self):
        self.events.close()
        self.canonical.close()


def seal_events(driver, sink, seal_path):
    """Seal only a completed attempt with no SQL or queued request outstanding."""
    if (driver.capture.active is not None or driver.capture.queue
            or driver.capture._task is not None):
        return False
    sink.close()
    hashes = {"events_sha256": hashlib.sha256(sink.path.read_bytes()).hexdigest()}
    if hasattr(sink, "canonical_path"):
        hashes["canonical_sha256"] = hashlib.sha256(
            sink.canonical_path.read_bytes()).hexdigest()
    payload = (json.dumps(hashes, sort_keys=True) + "\n").encode()
    fd = os.open(seal_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        if os.write(fd, payload) != len(payload):
            raise OSError("short status seal write")
        os.fsync(fd)
    finally:
        os.close(fd)
    directory = os.open(Path(seal_path).parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    return True


async def cleanup_observer(driver, tasks, stop_task, process, sink, stderr,
                           seal_path, completed_normally, *, lines=0, matched_hints=0):
    """Always stop the log stream and tasks, even when persistence fails."""
    errors = []
    try:
        driver.shutdown()
    except BaseException as error:
        errors.append(error)
    for task in (*tasks, stop_task):
        if not task.done():
            task.cancel()
    try:
        results = await asyncio.gather(*tasks, stop_task, return_exceptions=True)
        errors.extend(value for value in results if isinstance(value, BaseException)
                      and not isinstance(value, asyncio.CancelledError))
    except BaseException as error:
        errors.append(error)
    if process.returncode is None:
        try:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=2)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        except BaseException as error:
            errors.append(error)
    try:
        sink({"event": "trace_source_closed", "at_mono": time.monotonic(),
              "process_exit": process.returncode,
              "lines": lines, "matched_hints": matched_hints,
              "pending_command_id": driver.capture.command_id})
    except BaseException as error:
        errors.append(error)
    try:
        stderr.flush()
        os.fsync(stderr.fileno())
    except BaseException as error:
        errors.append(error)
    if driver.capture.active is None:
        if completed_normally and not errors:
            try:
                if not seal_events(driver, sink, seal_path):
                    errors.append(CaptureHalted("queued status work was discarded at stop"))
                    sink.close()
            except BaseException as error:
                errors.append(error)
        else:
            try:
                sink.close()
            except BaseException as error:
                errors.append(error)
    if errors:
        raise errors[0]


class ExactProcessedTransport:
    """Use the existing fixture's query callable, retaining command identity."""

    def __init__(self, query, verify_epoch):
        self.query = query
        self.verify_epoch = verify_epoch
        self.issued = set()

    async def submit(self, bot_name):
        if bot_name != BOT_NAME:
            raise ValueError("unexpected bot name")
        await asyncio.to_thread(self.verify_epoch)
        raw = await asyncio.to_thread(
            self.query,
            "INSERT INTO bot_commands(bot_name,command) "
            "VALUES('Grizzle Alyronia','status');SELECT LAST_INSERT_ID();",
        )
        value = raw.strip() if isinstance(raw, str) else ""
        if not COMMAND_ID.fullmatch(value):
            raise ValueError("native status submit did not return exactly one ID")
        command_id = int(value)
        if command_id in self.issued:
            raise ValueError("native status command ID was reused")
        self.issued.add(command_id)
        return command_id

    async def fetch(self, command_id):
        if type(command_id) is not int or command_id not in self.issued:
            raise ValueError("foreign status command ID")
        sql = f"SELECT result FROM bot_commands WHERE id={command_id} AND processed=1;"
        for _ in range(20):
            await asyncio.to_thread(self.verify_epoch)
            value = await asyncio.to_thread(self.query, sql)
            if not isinstance(value, str):
                raise TypeError("status query did not return text")
            if value:
                await asyncio.to_thread(self.verify_epoch)
                return value.strip()
            await asyncio.sleep(0.2)
        raise TimeoutError("exact processed status reply did not arrive")


class CaptureDriver:
    """Feed periodic and trace hints to one bounded StatusCapture arbiter."""

    def __init__(self, epoch, transport, events, *, start_mono=None,
                 first_periodic=540.0, period=10.0, clock=time.monotonic):
        # A fixture SQL call allows up to 10s, and submit and fetch are serial.
        # These bounds remain prospective until latency is measured natively.
        self.capture = StatusCapture(epoch, transport.submit, transport.fetch, events,
                                     queue_limit=4, command_timeout=30.0,
                                     max_queue_age=35.0)
        self.events = events
        self.clock = clock
        self.first_periodic = first_periodic
        self.period = period
        self.started = clock() if start_mono is None else start_mono
        self.next_periodic = self.started + first_periodic
        self.closed = False

    def hint(self, line):
        if self.closed:
            raise CaptureHalted("capture driver is closed")
        return self.capture.hint(line)

    def periodic_due(self):
        if self.closed:
            raise CaptureHalted("capture driver is closed")
        if self.capture.fenced:
            raise CaptureHalted("capture is fenced")
        now = self.clock()
        if now < self.next_periodic:
            return None
        if now - self.next_periodic >= self.period:
            self.capture.fenced = True
            self.events({"event": "periodic_deadline_missed", "at_mono": now,
                         "due_mono": self.next_periodic,
                         "pending_command_id": self.capture.command_id})
            raise CaptureHalted("periodic schedule lost evidence")
        self.next_periodic += self.period
        return self.capture.periodic()

    async def drain(self):
        while self.capture.queue:
            await self.capture.capture_next()

    def source_lost(self, *, lines, matched_hints, process_exit):
        self.capture.fenced = True
        self.events({"event": "trace_source_lost", "at_mono": self.clock(),
                     "lines": lines, "matched_hints": matched_hints,
                     "process_exit": process_exit,
                     "pending_command_id": self.capture.command_id})
        raise CaptureHalted("native trace source ended before run stop")

    def shutdown(self):
        if not self.closed:
            self.closed = True
            self.capture.shutdown()
