"""No Docker, SQL, provider, or fixture is used by these controls."""

import asyncio
import unittest

from m5_status_capture import CaptureHalted, ExternalEpoch, StatusCapture


EPOCH = ExternalEpoch("run-1", "world-sha", "container-id", "started-at", 42,
                      "Grizzle Alyronia", 77)
STATUS = "Bot 'Grizzle Alyronia': state=HUNTING pos=(1,2,7) active=yes hunt=[script=77 phase=LEAVING]"
HINT = "[HUNT:PHASE] mono_ms=123 bot_guid=42 script_id=77 from=PATROLLING to=LEAVING "


class CaptureTests(unittest.IsolatedAsyncioTestCase):
    async def test_periodic_and_hint_share_one_command_total(self):
        replies = [asyncio.Event(), asyncio.Event()]
        first_submitted = asyncio.Event()
        second_submitted = asyncio.Event()
        events = []
        submitted = []

        async def submit(_name):
            command_id = len(submitted) + 100
            submitted.append(command_id)
            first_submitted.set()
            if command_id == 101:
                second_submitted.set()
            return command_id

        async def fetch(command_id):
            await replies[command_id - 100].wait()
            return STATUS

        capture = StatusCapture(EPOCH, submit, fetch, events.append)
        capture.periodic()
        self.assertEqual(capture.hint(HINT), 2)
        first = asyncio.create_task(capture.capture_next())
        await first_submitted.wait()
        second = asyncio.create_task(capture.capture_next())
        await asyncio.sleep(0)
        self.assertEqual(submitted, [100])
        replies[0].set()
        self.assertEqual((await first)["command_id"], 100)
        await asyncio.wait_for(second_submitted.wait(), 1)
        self.assertEqual(submitted, [100, 101])
        replies[1].set()
        self.assertTrue((await second)["hint_phase_matches"])
        observed = [row for row in events if row["event"] == "status_observed"]
        self.assertEqual([row["command_id"] for row in observed], [100, 101])
        self.assertTrue(all(row["internal_epoch"] == "not_demonstrated" and
                            row["hunt_instance_id"] is None for row in observed))

    async def test_timeout_fences_late_reply_and_preserves_command_id(self):
        release = asyncio.Event()
        late = asyncio.Event()
        events = []

        def emit(row):
            events.append(row)
            if row["event"] == "late_reply":
                late.set()

        async def submit(_name):
            return 107

        async def fetch(_identity):
            await release.wait()
            return STATUS

        capture = StatusCapture(EPOCH, submit, fetch, emit, command_timeout=.05)
        capture.hint(HINT)
        with self.assertRaises(CaptureHalted):
            await capture.capture_next()
        self.assertEqual([row["command_id"] for row in events if
                          row["event"] == "timeout_pending"], [107])
        with self.assertRaises(CaptureHalted):
            capture.periodic()
        release.set()
        await asyncio.wait_for(late.wait(), 1)
        self.assertEqual(events[-1]["command_id"], 107)
        self.assertFalse(events[-1]["accepted"])
        self.assertFalse(any(row["event"] == "status_observed" for row in events))

    async def test_epoch_change_during_command_cannot_reassign_reply(self):
        release = asyncio.Event()
        submitted = asyncio.Event()
        events = []

        async def submit(_name):
            submitted.set()
            return 108

        async def fetch(_identity):
            await release.wait()
            return STATUS

        capture = StatusCapture(EPOCH, submit, fetch, events.append)
        capture.periodic()
        task = asyncio.create_task(capture.capture_next())
        await submitted.wait()
        capture.change_epoch(ExternalEpoch("run-2", "world-sha", "container-id",
                                           "new-start", 42, "Grizzle Alyronia", 77))
        release.set()
        with self.assertRaises(CaptureHalted):
            await task
        self.assertEqual(events[-1]["event"], "late_reply")
        self.assertEqual(events[-1]["external_epoch"]["run_id"], "run-1")
        with self.assertRaises(CaptureHalted):
            await capture.capture_next()

    async def test_shutdown_records_pending_without_cancelling_sql(self):
        release = asyncio.Event()
        submitted = asyncio.Event()
        events = []

        async def submit(_name):
            submitted.set()
            return 109

        async def fetch(_identity):
            await release.wait()
            return STATUS

        capture = StatusCapture(EPOCH, submit, fetch, events.append)
        capture.hint(HINT)
        task = asyncio.create_task(capture.capture_next())
        await submitted.wait()
        capture.shutdown()
        self.assertEqual(events[-1]["pending_command_id"], 109)
        release.set()
        with self.assertRaises(CaptureHalted):
            await task
        self.assertEqual(events[-1]["event"], "late_reply")

    async def test_foreign_hint_and_unscoped_status_do_not_claim_phase(self):
        events = []

        async def submit(_name):
            return 110

        async def fetch(_identity):
            return STATUS.replace("script=77", "script=399")

        capture = StatusCapture(EPOCH, submit, fetch, events.append)
        self.assertIsNone(capture.hint(HINT.replace("bot_guid=42", "bot_guid=41")))
        self.assertIsNone(capture.hint(HINT.replace("script_id=77", "script_id=399")))
        self.assertIsNone(capture.hint("not a trace"))
        capture.hint(HINT)
        row = await capture.capture_next()
        self.assertFalse(row["target_script_matches"])
        self.assertFalse(row["hint_phase_matches"])
        self.assertIsNone(row["hunt_instance_id"])

    async def test_bounded_queue_and_stale_request_fail_closed(self):
        events = []

        async def unexpected(_value):
            self.fail("transport must not be called")

        clock = [0.0]
        capture = StatusCapture(EPOCH, unexpected, unexpected, events.append,
                                queue_limit=1, clock=lambda: clock[0])
        capture.periodic()
        with self.assertRaises(CaptureHalted):
            capture.hint(HINT)
        self.assertEqual(events[-1]["event"], "queue_overflow")

        other = StatusCapture(EPOCH, unexpected, unexpected, events.append,
                              clock=lambda: clock[0], max_queue_age=2)
        other.periodic()
        clock[0] = 3.0
        with self.assertRaises(CaptureHalted):
            await other.capture_next()
        self.assertEqual(events[-1]["event"], "queue_expired")

    async def test_invalid_identity_and_status_fail_closed(self):
        events = []

        async def bad_id(_name):
            return 0

        async def fetch(_identity):
            return STATUS

        capture = StatusCapture(EPOCH, bad_id, fetch, events.append)
        capture.periodic()
        with self.assertRaises(CaptureHalted):
            await capture.capture_next()
        self.assertEqual(events[-1]["event"], "command_error")

        async def good_id(_name):
            return 111

        async def wrong(_identity):
            return STATUS.replace("Grizzle Alyronia", "Other Bot")

        capture = StatusCapture(EPOCH, good_id, wrong, events.append)
        capture.periodic()
        with self.assertRaises(CaptureHalted):
            await capture.capture_next()
        self.assertEqual(events[-1]["event"], "invalid_status")

    async def test_cancelled_capture_records_pending_identity(self):
        release = asyncio.Event()
        submitted = asyncio.Event()
        late = asyncio.Event()
        events = []

        def emit(row):
            events.append(row)
            if row["event"] == "late_reply":
                late.set()

        async def submit(_name):
            submitted.set()
            return 112

        async def fetch(_identity):
            await release.wait()
            return STATUS

        capture = StatusCapture(EPOCH, submit, fetch, emit)
        capture.periodic()
        task = asyncio.create_task(capture.capture_next())
        await submitted.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(events[-1]["event"], "cancelled_pending")
        self.assertEqual(events[-1]["command_id"], 112)
        release.set()
        await asyncio.wait_for(late.wait(), 1)
        self.assertFalse(events[-1]["accepted"])

    async def test_cancelled_waiter_fences_active_command_and_late_reply(self):
        release = asyncio.Event()
        submitted = asyncio.Event()
        events = []
        calls = []

        async def submit(_name):
            calls.append(115)
            submitted.set()
            return 115

        async def fetch(command_id):
            self.assertEqual(command_id, 115)
            await release.wait()
            return STATUS

        capture = StatusCapture(EPOCH, submit, fetch, events.append)
        self.assertEqual(capture.periodic(), 1)
        self.assertEqual(capture.hint(HINT), 2)
        active = asyncio.create_task(capture.capture_next())
        await asyncio.wait_for(submitted.wait(), 1)
        waiter = asyncio.create_task(capture.capture_next())
        await asyncio.sleep(0)  # Let B block on A's held arbiter.
        self.assertFalse(waiter.done())
        self.assertEqual(calls, [115])

        waiter.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await waiter
        cancelled = [row for row in events if row["event"] == "cancelled_waiting_arbiter"]
        self.assertEqual(len(cancelled), 1)
        self.assertEqual(cancelled[0]["pending_command_id"], 115)
        self.assertEqual(cancelled[0]["pending_sequence"], 1)
        self.assertEqual(cancelled[0]["queued_sequences"], [2])
        self.assertFalse(active.done())  # B's cancellation did not cancel A's SQL.
        with self.assertRaises(CaptureHalted):
            capture.periodic()

        release.set()
        with self.assertRaises(CaptureHalted):
            await asyncio.wait_for(active, 1)
        late = [row for row in events if row["event"] == "late_reply"]
        self.assertEqual(len(late), 1)
        self.assertEqual(late[0]["command_id"], 115)
        self.assertEqual(late[0]["sequence"], 1)
        self.assertFalse(late[0]["accepted"])
        self.assertFalse(any(row["event"] == "status_observed" for row in events))
        with self.assertRaises(CaptureHalted):
            await capture.capture_next()
        self.assertEqual(calls, [115])

    async def test_submit_timeout_records_unknown_identity_and_late_id(self):
        release = asyncio.Event()
        late = asyncio.Event()
        events = []

        def emit(row):
            events.append(row)
            if row["event"] == "late_reply":
                late.set()

        async def submit(_name):
            await release.wait()
            return 113

        async def fetch(_identity):
            return STATUS

        capture = StatusCapture(EPOCH, submit, fetch, emit, command_timeout=.05)
        capture.periodic()
        with self.assertRaises(CaptureHalted):
            await capture.capture_next()
        self.assertIsNone(events[-1]["command_id"])
        self.assertFalse(events[-1]["pending_identity_known"])
        release.set()
        await asyncio.wait_for(late.wait(), 1)
        self.assertEqual(events[-1]["command_id"], 113)
        with self.assertRaises(CaptureHalted):
            await capture.capture_next()

    async def test_evidence_sink_failure_fences_further_dispatch(self):
        calls = []

        async def submit(_name):
            calls.append("submit")
            return 114

        async def fetch(_identity):
            return STATUS

        def emit(row):
            if row["event"] == "status_observed":
                raise OSError("evidence unavailable")

        capture = StatusCapture(EPOCH, submit, fetch, emit)
        capture.periodic()
        with self.assertRaises(OSError):
            await capture.capture_next()
        with self.assertRaises(CaptureHalted):
            capture.periodic()
        self.assertEqual(calls, ["submit"])


if __name__ == "__main__":
    unittest.main()
