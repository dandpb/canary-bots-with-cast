"""Offline controls for the short native opt-in runner; no Docker or SQL."""

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import unittest

from m5_status_capture import CaptureHalted, ExternalEpoch
from m5_status_runner_adapter import (CaptureDriver, StatusEvidence,
                                      cleanup_observer, seal_events)


SOURCE = Path(__file__).with_name("m5_current_qualification.py")
WANTED = {"short_status_options", "short_clock_ready", "require_first_periodic_window",
          "wait_for_trace_boundary", "HeldFetchAfterFence", "apply_short_trace_guid",
          "terminate_owned_log_after_observed"}
nodes = [node for node in ast.parse(SOURCE.read_text()).body
         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
         and node.name in WANTED]
assert {node.name for node in nodes} == WANTED
namespace = {"asyncio": asyncio, "Path": Path, "time": time,
             "WORLD": Path("/tmp/canary-lifecycle-qa-world.otbm")}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), namespace)
short_status_options = namespace["short_status_options"]
short_clock_ready = namespace["short_clock_ready"]
wait_for_trace_boundary = namespace["wait_for_trace_boundary"]
HeldFetchAfterFence = namespace["HeldFetchAfterFence"]
apply_short_trace_guid = namespace["apply_short_trace_guid"]
terminate_owned_log_after_observed = namespace["terminate_owned_log_after_observed"]


def options(root, **changes):
    data = dict(status_capture_opt_in=True, mode="native", seconds=10,
                status_script_id=77, status_first_periodic=1.0,
                status_period=3.0, world_map=root / "world.otbm",
                fixture_root=root / "fixture", status_hold_first_fetch=False,
                status_terminate_log_after_observed=False)
    data.update(changes)
    return SimpleNamespace(**data)


class ShortStatusControls(unittest.IsolatedAsyncioTestCase):
    def test_private_world_and_cadence_only_for_native_short_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fixture").mkdir()
            world = root / "world.otbm"
            world.write_bytes(b"fixture-world")
            world.chmod(0o600)
            self.assertEqual(short_status_options(options(root)), (world, 1.0, 3.0))
            for changes in ({"mode": "fake"}, {"seconds": 1800},
                            {"status_capture_opt_in": False},
                            {"status_first_periodic": 2.0},
                            {"status_period": None},
                            {"status_hold_first_fetch": True, "mode": "fake"},
                            {"status_terminate_log_after_observed": True,
                             "status_capture_opt_in": False},
                            {"world_map": None}):
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    short_status_options(options(root, **changes))
            link = root / "world-link.otbm"
            link.symlink_to(world)
            with self.assertRaises(ValueError):
                short_status_options(options(root, world_map=link))
            with self.assertRaisesRegex(ValueError, "separate trials"):
                short_status_options(options(
                    root, status_first_periodic=None, status_period=None,
                    status_hold_first_fetch=True,
                    status_terminate_log_after_observed=True))

    async def test_short_clock_readiness_is_bounded_and_keeps_worker_origin(self):
        reads = iter((None, {"monotonic": time.monotonic()}))
        value, ready = await short_clock_ready(lambda: next(reads), 1.0)
        self.assertLess(ready, value["monotonic"] + 1.0)
        with self.assertRaisesRegex(ValueError, "lacks the observed worker clock"):
            await short_clock_ready(lambda: None, 1.0, timeout=0.02)
        with self.assertRaisesRegex(ValueError, "missed first periodic window"):
            await short_clock_ready(lambda: {"monotonic": 10.0}, 1.0,
                                    clock=lambda: 11.1)

    async def test_first_stream_line_must_precede_original_periodic_deadline(self):
        ready = asyncio.Event()
        ready.set()
        self.assertEqual(await wait_for_trace_boundary(
            ready, 10.0, 1.0, lambda: 10.4, clock=lambda: 10.5), 11.0)
        with self.assertRaisesRegex(ValueError, "missed first periodic stream window"):
            await wait_for_trace_boundary(ready, 10.0, 1.0,
                                          lambda: 11.01, clock=lambda: 11.02)
        unobserved = asyncio.Event()
        with self.assertRaisesRegex(ValueError, "timely observed log stream"):
            await wait_for_trace_boundary(unobserved, time.monotonic(), 0.02,
                                          lambda: None)

    def test_trace_guid_only_in_native_short_render(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for mode, seconds, opt_in in (("native", 10, True),
                                          ("fake", 10, True),
                                          ("native", 1800, True),
                                          ("native", 10, False)):
                compose = {"services": {"game": {"environment": {"GAME_PUBLIC_IP": "127.0.0.1"}}}}
                result = apply_short_trace_guid(compose,
                    options(root, mode=mode, seconds=seconds,
                            status_capture_opt_in=opt_in), 65001)
                trace = result["services"]["game"]["environment"].get(
                    "CANARY_QA_HUNT_PHASE_TRACE_GUID")
                self.assertEqual(trace, "65001" if (mode, seconds, opt_in)
                                 == ("native", 10, True) else None)

    async def test_processed_reply_released_after_shutdown_is_late_and_unsealed(self):
        rows = []
        class Transport:
            async def submit(self, _bot):
                return 501
            async def fetch(self, command_id):
                self_outer.assertEqual(command_id, 501)
                return "Bot 'Grizzle Alyronia': state=HUNTING pos=(1,2,7) active=yes hunt=[script=77 phase=LEAVING]"

        self_outer = self
        held = HeldFetchAfterFence(Transport(), rows.append)
        epoch = ExternalEpoch("short-1", "world-sha", "game-id", "started-at",
                              65001, "Grizzle Alyronia", 77)
        driver = CaptureDriver(epoch, held, rows.append, start_mono=0,
                               first_periodic=1, period=3, clock=lambda: 1.1)
        self.assertEqual(driver.periodic_due(), 1)
        pending = asyncio.create_task(driver.drain())
        await asyncio.wait_for(held.held.wait(), timeout=1)
        self.assertEqual(driver.capture.command_id, 501)
        driver.shutdown()  # STOP/fence is recorded before release; cleanup has not run.
        self.assertFalse(held.fenced.is_set())
        held.release_after_shutdown()
        with self.assertRaises(CaptureHalted):
            await asyncio.wait_for(pending, timeout=1)
        events = [row["event"] for row in rows]
        self.assertLess(events.index("shutdown"), events.index("test_fetch_released_after_fence"))
        late = [row for row in rows if row["event"] == "late_reply"]
        self.assertEqual([(row["command_id"], row["accepted"]) for row in late],
                         [(501, False)])
        self.assertFalse(any(row["event"] == "status_observed" for row in rows))
        self.assertIsNotNone(driver.capture.active)
        with tempfile.TemporaryDirectory() as directory:
            seal = Path(directory) / "status-capture-seal.json"
            self.assertFalse(seal_events(driver, object(), seal))
            self.assertFalse(seal.exists())
        with self.assertRaises(CaptureHalted):
            driver.periodic_due()

    async def test_cleanup_releases_held_reply_only_after_fence_without_sealing(self):
        class Transport:
            async def submit(self, _bot):
                return 502
            async def fetch(self, _command_id):
                return "Bot 'Grizzle Alyronia': state=HUNTING pos=(1,2,7) active=yes hunt=[script=77 phase=LEAVING]"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = StatusEvidence(root / "events.jsonl", root / "phase-status.jsonl", 0)
            late = asyncio.Event()
            rows = []

            def record(row):
                evidence(row)
                rows.append(row)
                if row.get("event") == "late_reply":
                    late.set()

            held = HeldFetchAfterFence(Transport(), record)
            epoch = ExternalEpoch("short-2", "world-sha", "game-id", "started-at",
                                  65001, "Grizzle Alyronia", 77)
            driver = CaptureDriver(epoch, held, record, start_mono=0,
                                   first_periodic=1, period=3, clock=lambda: 1.1)
            original_shutdown = driver.shutdown

            def shutdown_and_release():
                original_shutdown()
                held.release_after_shutdown()

            driver.shutdown = shutdown_and_release
            driver.periodic_due()
            pending = asyncio.create_task(driver.drain())
            await asyncio.wait_for(held.held.wait(), timeout=1)
            stopped = asyncio.Event()
            stop_task = asyncio.create_task(stopped.wait())
            process = SimpleNamespace(returncode=0)
            seal = root / "seal.json"
            with (root / "stderr").open("wb") as stderr:
                await cleanup_observer(driver, [pending], stop_task, process,
                                       evidence, stderr, seal, False)
            await asyncio.wait_for(late.wait(), timeout=1)
            evidence.close()
            self.assertFalse(seal.exists())
            self.assertEqual([row["command_id"] for row in rows
                              if row.get("event") == "late_reply"], [502])
            self.assertFalse(any(row.get("event") == "status_observed" for row in rows))
            self.assertLess(next(i for i, row in enumerate(rows)
                                 if row.get("event") == "shutdown"),
                            next(i for i, row in enumerate(rows)
                                 if row.get("event") == "late_reply"))

    async def test_stream_loss_targets_only_own_log_process(self):
        terminated = asyncio.Event()
        class OwnLog:
            pid = 9001
            returncode = None
            terminated = False
            def terminate(self):
                self.terminated = True
                self.returncode = -15
                terminated.set()

        ready, stopped = asyncio.Event(), asyncio.Event()
        log = OwnLog()
        rows = []
        task = asyncio.create_task(terminate_owned_log_after_observed(
            ready, stopped, log, rows.append, "game-full-id"))
        self.assertFalse(log.terminated)
        ready.set()
        await asyncio.wait_for(terminated.wait(), timeout=1)
        self.assertFalse(task.done())  # read_trace, not injector, must report EOF
        stopped.set()
        await asyncio.wait_for(task, timeout=1)
        self.assertTrue(log.terminated)
        self.assertEqual(rows[0]["event"], "test_trace_log_termination")
        self.assertEqual(rows[0]["game_container_id"], "game-full-id")


if __name__ == "__main__":
    unittest.main()
