"""Offline controls for the short native opt-in runner; no Docker or SQL."""

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import unittest

from m5_status_capture import CaptureHalted, ExternalEpoch
from m5_status_runner_adapter import CaptureDriver, seal_events


SOURCE = Path(__file__).with_name("m5_current_qualification.py")
WANTED = {"short_status_options", "HeldFetchAfterFence", "apply_short_trace_guid",
          "terminate_owned_log_after_observed"}
nodes = [node for node in ast.parse(SOURCE.read_text()).body
         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
         and node.name in WANTED]
assert {node.name for node in nodes} == WANTED
namespace = {"asyncio": asyncio, "Path": Path, "time": time,
             "WORLD": Path("/tmp/canary-lifecycle-qa-world.otbm")}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), namespace)
short_status_options = namespace["short_status_options"]
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
