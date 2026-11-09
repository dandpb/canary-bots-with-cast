#!/usr/bin/env python3
"""Offline import controls for live lifecycle drivers; never contacts Docker/SQL."""
from contextlib import ExitStack
from pathlib import Path
import runpy
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent

class ImportSafety(unittest.TestCase):
    def inspect(self, name, remove_guard=False):
        calls=[]
        def blocked(*args, **kwargs):
            calls.append("operation")
            raise RuntimeError("blocked operational call")
        qa=types.ModuleType("lifecycle_qa")
        qa.PREFIX="offline-import-probe"
        qa.__getattr__=lambda name: blocked
        with ExitStack() as stack:
            stack.enter_context(patch.dict(sys.modules,{"lifecycle_qa":qa}))
            for namepart in ["run","check_output","Popen"]:
                stack.enter_context(patch.object(subprocess,namepart,blocked))
            if remove_guard:
                source=(ROOT/name).read_text()
                guard='if __name__ == "__main__":\n'
                self.assertIn(guard,source)
                source=source.replace(guard,'if True:\n',1)
                with self.assertRaisesRegex(RuntimeError,"blocked operational call"):
                    exec(compile(source,str(ROOT/name),"exec"),{"__name__":"import_probe","__file__":str(ROOT/name)})
                self.assertTrue(calls,"removing guard must expose operational side effect")
            else:
                runpy.run_path(str(ROOT/name),run_name="import_probe")
                self.assertEqual(calls,[])

    def test_cast_import_is_inert(self):
        self.inspect("test_cast_lifecycle.py")
    def test_checkpoint_import_is_inert(self):
        self.inspect("test_checkpoint_overlap.py")
    def test_cast_guard_removal_is_rejected(self):
        self.inspect("test_cast_lifecycle.py",True)
    def test_checkpoint_guard_removal_is_rejected(self):
        self.inspect("test_checkpoint_overlap.py",True)

if __name__ == "__main__":
    unittest.main()
