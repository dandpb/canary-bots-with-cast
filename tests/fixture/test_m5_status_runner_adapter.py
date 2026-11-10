"""Offline doubles only: no Docker, SQL connection, provider, or fixture."""

import asyncio
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from m5_status_capture import CaptureHalted, ExternalEpoch
from m5_status_runner_adapter import (CaptureDriver, DurableEvents,
                                     ExactProcessedTransport, seal_events)


EPOCH = ExternalEpoch("run-1", "world-sha", "container-id", "started-at", 42,
                      "Grizzle Alyronia", 77)
STATUS = "Bot 'Grizzle Alyronia': state=HUNTING pos=(1,2,7) active=yes hunt=[script=77 phase=LEAVING]"
HINT = "[HUNT:PHASE] mono_ms=123 bot_guid=42 script_id=77 from=PATROLLING to=LEAVING "


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_exact_processed_id_and_foreign_id_rejected(self):
        queries = []

        def query(sql):
            queries.append(sql)
            return "105\n" if "LAST_INSERT_ID" in sql else STATUS

        transport = ExactProcessedTransport(query, lambda: None)
        command_id = await transport.submit(EPOCH.bot_name)
        self.assertEqual(command_id, 105)
        self.assertEqual(await transport.fetch(command_id), STATUS)
        self.assertIn("WHERE id=105 AND processed=1", queries[-1])
        with self.assertRaises(ValueError):
            await transport.fetch(106)
        self.assertEqual(len(queries), 2)

    async def test_missing_or_reused_submit_id_fails_closed(self):
        for raw in ("", "105\n106", "0", "not-an-id"):
            with self.subTest(raw=raw):
                transport = ExactProcessedTransport(lambda _sql: raw, lambda: None)
                with self.assertRaises(ValueError):
                    await transport.submit(EPOCH.bot_name)
        transport = ExactProcessedTransport(lambda _sql: "105", lambda: None)
        await transport.submit(EPOCH.bot_name)
        with self.assertRaises(ValueError):
            await transport.submit(EPOCH.bot_name)

    async def test_periodic_hint_race_and_late_reply_keep_one_identity(self):
        release = asyncio.Event()
        submitted = asyncio.Event()
        events = []
        issued = []

        async def submit(_bot):
            command_id = 100 + len(issued)
            issued.append(command_id)
            submitted.set()
            return command_id

        async def fetch(_command_id):
            await release.wait()
            return STATUS

        clock = [540.0]
        driver = CaptureDriver(EPOCH, type("T", (), {"submit": staticmethod(submit),
                                                     "fetch": staticmethod(fetch)})(),
                               events.append, start_mono=0, clock=lambda: clock[0])
        self.assertEqual(driver.periodic_due(), 1)
        self.assertEqual(driver.hint(HINT), 2)
        first = asyncio.create_task(driver.capture.capture_next())
        await submitted.wait()
        self.assertEqual(issued, [100])
        driver.shutdown()
        release.set()
        with self.assertRaises(CaptureHalted):
            await first
        self.assertFalse(any(row["event"] == "status_observed" for row in events))
        self.assertEqual([row["command_id"] for row in events if row["event"] == "late_reply"], [100])
        self.assertEqual(issued, [100])

    async def test_epoch_change_and_sink_loss_block_following_dispatch(self):
        events = []

        async def submit(_bot):
            return 107

        async def fetch(_id):
            return STATUS

        transport = type("T", (), {"submit": staticmethod(submit),
                                    "fetch": staticmethod(fetch)})()
        driver = CaptureDriver(EPOCH, transport, events.append)
        driver.hint(HINT)
        driver.capture.change_epoch(ExternalEpoch("run-2", "world-sha", "container-id",
                                                  "new-start", 42, "Grizzle Alyronia", 77))
        with self.assertRaises(CaptureHalted):
            await driver.drain()
        self.assertEqual(events[-1]["event"], "epoch_changed")

        def failing_sink(_row):
            raise OSError("evidence disk unavailable")

        other = CaptureDriver(EPOCH, transport, failing_sink)
        with self.assertRaises(OSError):
            other.hint(HINT)
        self.assertTrue(other.capture.fenced)
        with self.assertRaises(CaptureHalted):
            other.periodic_due()

    async def test_pending_shutdown_and_durable_evidence(self):
        release = asyncio.Event()
        submitted = asyncio.Event()

        async def submit(_bot):
            submitted.set()
            return 108

        async def fetch(_id):
            await release.wait()
            return STATUS

        with tempfile.TemporaryDirectory() as directory:
            sink = DurableEvents(Path(directory) / "capture.jsonl")
            driver = CaptureDriver(EPOCH, type("T", (), {"submit": staticmethod(submit),
                                                         "fetch": staticmethod(fetch)})(), sink)
            driver.hint(HINT)
            task = asyncio.create_task(driver.drain())
            await submitted.wait()
            driver.shutdown()
            release.set()
            with self.assertRaises(CaptureHalted):
                await task
            self.assertFalse(seal_events(driver, sink, Path(directory) / "seal.json"))
            self.assertFalse((Path(directory) / "seal.json").exists())
            sink.close()
            rows = [json.loads(line) for line in (Path(directory) / "capture.jsonl").read_text().splitlines()]
            self.assertEqual([row["pending_command_id"] for row in rows if row["event"] == "shutdown"], [108])
            self.assertFalse(any(row["event"] == "status_observed" for row in rows))

    async def test_idle_evidence_seals_exact_bytes_once(self):
        async def submit(_bot):
            return 109

        async def fetch(_id):
            return STATUS

        with tempfile.TemporaryDirectory() as directory:
            events_path = Path(directory) / "capture.jsonl"
            seal_path = Path(directory) / "seal.json"
            sink = DurableEvents(events_path)
            driver = CaptureDriver(EPOCH, type("T", (), {"submit": staticmethod(submit),
                                                         "fetch": staticmethod(fetch)})(), sink)
            driver.hint(HINT)
            await driver.drain()
            driver.shutdown()
            self.assertTrue(seal_events(driver, sink, seal_path))
            self.assertEqual(json.loads(seal_path.read_text())["events_sha256"],
                             hashlib.sha256(events_path.read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError):
                seal_events(driver, sink, seal_path)

    async def test_trace_source_loss_fences_without_synthetic_status(self):
        events = []

        async def forbidden(_value):
            self.fail("loss must not dispatch a command")

        driver = CaptureDriver(EPOCH, type("T", (), {"submit": staticmethod(forbidden),
                                                     "fetch": staticmethod(forbidden)})(),
                               events.append)
        driver.hint(HINT)
        with self.assertRaises(CaptureHalted):
            driver.source_lost(lines=12, matched_hints=1, process_exit=1)
        self.assertEqual(events[-1]["event"], "trace_source_lost")
        self.assertTrue(driver.capture.fenced)
        with self.assertRaises(CaptureHalted):
            await driver.drain()
        self.assertFalse(any(row["event"] == "status_observed" for row in events))


if __name__ == "__main__":
    unittest.main()
