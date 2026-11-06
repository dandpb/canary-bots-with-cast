"""An observer failure must stop and flush a real async worker, then surface."""

import asyncio
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import m5_current_qualification as qualification
from m5_current_qualification import (
    QualificationObserverError,
    read_native_status,
    run_with_status_observer,
)
from m5_qualification_gates import native_phase_cycle


class StatusObserverTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.configuration = SimpleNamespace(
            state_file=self.directory / "worker.sqlite3"
        )
        self.stopped = asyncio.Event()

    def diagnostic(self):
        data = json.loads((self.directory / "observer-error.json").read_text())
        self.assertIsInstance(data["error_type"], str)
        self.assertTrue(data["error_type"])
        instant = datetime.fromisoformat(data["at_utc"])
        self.assertEqual(instant.utcoffset(), timedelta(0))
        return data

    async def test_processed_native_status_is_returned_after_pending_poll(self):
        status = "Bot 'Grizzle Alyronia': state=HUNTING pos=(1,2,7) active=yes"
        responses = iter(("7\n", "", status))
        with patch.object(qualification.asyncio, "sleep", new_callable=AsyncMock):
            self.assertEqual(
                await read_native_status(lambda _: next(responses)), (7, status)
            )

    async def test_malformed_or_blank_processed_status_is_rejected(self):
        for result in ("   \n", "NULL\n", "Bot not found", "unexpected response"):
            with self.subTest(result=result):
                responses = iter(("7\n", result))
                with self.assertRaises(ValueError):
                    await read_native_status(
                        lambda _, responses=responses: next(responses)
                    )

    async def test_lost_status_after_valid_cycle_stops_flushes_and_rejects(self):
        statuses = [
            {
                "elapsed": 540 + index * 10,
                "status": f"hunt=[script=399 phase={phase}]",
            }
            for index, phase in enumerate(
                ("PATROLLING", "LEAVING", "RESUPPLYING", "PATROLLING")
            )
        ]
        self.assertTrue(native_phase_cycle(statuses)["complete"])
        (self.directory / "phase-status.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in statuses)
        )
        with sqlite3.connect(self.configuration.state_file) as db:
            db.execute("CREATE TABLE requests (id INTEGER)")
        state = {"flushed": False, "polls": 0}

        def query(sql):
            if sql.startswith("INSERT"):
                return "8\n"
            state["polls"] += 1
            return ""

        async def worker(_configuration, stopped):
            try:
                await stopped.wait()
            finally:
                state["flushed"] = True

        async def observer(_configuration, _stopped):
            await read_native_status(query)

        with (
            patch.object(qualification.asyncio, "sleep", new_callable=AsyncMock),
            self.assertRaises(QualificationObserverError),
        ):
            await asyncio.wait_for(
                run_with_status_observer(
                    self.configuration, self.stopped, worker, observer
                ),
                timeout=2,
            )
        self.assertTrue(state["flushed"])
        self.assertEqual(state["polls"], 20)
        self.assertEqual(self.diagnostic()["error_type"], "TimeoutError")
        reader = SimpleNamespace(all_events=lambda _: [])
        with (
            patch.object(qualification, "summary", return_value={"metrics": {}}),
            patch.object(
                qualification,
                "qualify_run",
                return_value={"accepted": True, "checks": {"hunt_cycle": True}},
            ),
        ):
            result = qualification.validate_result(
                reader,
                {"id": "prior-valid-cycle"},
                1800,
                self.configuration.state_file,
                {},
                {},
                True,
                "native",
            )
        self.assertFalse(result["accepted"])
        self.assertFalse(result["checks"]["status_observer_healthy"])
        self.assertTrue(result["checks"]["hunt_cycle"])

    async def test_observer_error_requests_stop_and_awaits_worker_flush(self):
        started = asyncio.Event()
        state = {"stop_observed": False, "cancelled": False, "flushed": False}

        async def worker(_configuration, stopped):
            started.set()
            try:
                await stopped.wait()
                state["stop_observed"] = True
            except asyncio.CancelledError:
                state["cancelled"] = True
                raise
            finally:
                await asyncio.sleep(0)
                state["flushed"] = True

        async def observer(_configuration, _stopped):
            await started.wait()
            raise OSError("status transport unavailable")

        with self.assertRaises(QualificationObserverError):
            await asyncio.wait_for(
                run_with_status_observer(
                    self.configuration, self.stopped, worker, observer
                ),
                timeout=2,
            )
        self.assertTrue(self.stopped.is_set())
        self.assertEqual(
            state, {"stop_observed": True, "cancelled": False, "flushed": True}
        )
        self.assertEqual(self.diagnostic()["error_type"], "OSError")

    async def test_healthy_worker_completion_cancels_and_closes_observer(self):
        observing = asyncio.Event()
        state = {
            "worker_flushed": False,
            "observer_cancelled": False,
            "observer_closed": False,
        }

        async def worker(_configuration, _stopped):
            try:
                await observing.wait()
            finally:
                await asyncio.sleep(0)
                state["worker_flushed"] = True

        async def observer(_configuration, _stopped):
            observing.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                state["observer_cancelled"] = True
                raise
            finally:
                await asyncio.sleep(0)
                state["observer_closed"] = True

        await asyncio.wait_for(
            run_with_status_observer(
                self.configuration, self.stopped, worker, observer
            ),
            timeout=2,
        )
        self.assertTrue(all(state.values()), state)
        self.assertFalse((self.directory / "observer-error.json").exists())

    async def test_observer_return_before_stop_is_a_visible_failure(self):
        started = asyncio.Event()
        state = {"stop_observed": False, "flushed": False}

        async def worker(_configuration, stopped):
            started.set()
            try:
                await stopped.wait()
                state["stop_observed"] = True
            finally:
                await asyncio.sleep(0)
                state["flushed"] = True

        async def observer(_configuration, _stopped):
            await started.wait()
            # Returning silently would otherwise leave an unobserved long run.

        with self.assertRaises(QualificationObserverError):
            await asyncio.wait_for(
                run_with_status_observer(
                    self.configuration, self.stopped, worker, observer
                ),
                timeout=2,
            )
        self.assertTrue(self.stopped.is_set())
        self.assertTrue(all(state.values()), state)
        self.diagnostic()

    async def test_worker_error_is_preserved_while_observer_is_cancelled(self):
        observing = asyncio.Event()
        worker_error = ValueError("worker failed before its horizon")
        state = {
            "worker_flushed": False,
            "observer_cancelled": False,
            "observer_closed": False,
        }

        async def worker(_configuration, _stopped):
            try:
                await observing.wait()
                raise worker_error
            finally:
                await asyncio.sleep(0)
                state["worker_flushed"] = True

        async def observer(_configuration, _stopped):
            observing.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                state["observer_cancelled"] = True
                raise
            finally:
                await asyncio.sleep(0)
                state["observer_closed"] = True

        with self.assertRaises(ValueError) as caught:
            await asyncio.wait_for(
                run_with_status_observer(
                    self.configuration, self.stopped, worker, observer
                ),
                timeout=2,
            )
        self.assertIs(caught.exception, worker_error)
        self.assertTrue(all(state.values()), state)
        self.assertFalse((self.directory / "observer-error.json").exists())


if __name__ == "__main__":
    unittest.main()
