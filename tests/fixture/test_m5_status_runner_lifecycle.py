"""Exercise the runner's async cleanup without importing its runtime stack."""

import ast
import asyncio
import datetime
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest


SOURCE = Path(__file__).with_name("m5_current_qualification.py")
tree = ast.parse(SOURCE.read_text())
function = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)
                and node.name == "run_with_status_observer")
namespace = {"asyncio": asyncio, "datetime": datetime, "json": json, "sys": sys}


class QualificationObserverError(RuntimeError):
    pass


namespace["QualificationObserverError"] = QualificationObserverError
exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), "exec"), namespace)
run_with_status_observer = namespace["run_with_status_observer"]


class RunnerLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_cleanup_error_after_worker_stop_rejects_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            configuration = SimpleNamespace(state_file=Path(directory) / "state")
            stopped = asyncio.Event()

            async def worker(_configuration, _stopped):
                return None

            async def observer(_configuration, stop_event):
                await stop_event.wait()
                raise OSError("sink fsync failed")

            with self.assertRaises(QualificationObserverError):
                await run_with_status_observer(configuration, stopped, worker,
                                               observer, strict_cleanup=True)
            marker = json.loads((Path(directory) / "observer-error.json").read_text())
            self.assertEqual(marker["error_type"], "OSError")

    async def test_clean_opt_in_observer_completes_after_worker_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            configuration = SimpleNamespace(state_file=Path(directory) / "state")
            stopped = asyncio.Event()

            async def worker(_configuration, _stopped):
                return None

            async def observer(_configuration, stop_event):
                await stop_event.wait()

            await run_with_status_observer(configuration, stopped, worker,
                                           observer, strict_cleanup=True)
            self.assertFalse((Path(directory) / "observer-error.json").exists())


if __name__ == "__main__":
    unittest.main()
