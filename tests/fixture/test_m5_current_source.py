"""A clean driver tree must not attest modules imported from another checkout."""

import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import m5_current_qualification as driver


class ApplicationSourceTests(unittest.TestCase):
    def source_context(self, root, runtime_file, benchmark_file):
        stack = ExitStack()
        stack.enter_context(patch.object(driver, "ROOT", root))
        stack.enter_context(patch.object(driver.runtime, "__file__", runtime_file))
        stack.enter_context(patch.object(driver.benchmark, "__file__", benchmark_file))
        return stack

    def test_other_runtime_tree_is_rejected_before_git_attestation(self):
        for name in ["runtime", "benchmark"]:
            with self.subTest(module=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "driver-A"
                package = root / "deployment/brain/src/canary_brain"
                paths = {
                    "runtime": str(package / "runtime.py"),
                    "benchmark": str(package / "benchmark.py"),
                }
                paths[name] = str(Path(temporary) / "runtime-B" / (name + ".py"))
                with (
                    self.source_context(root, paths["runtime"], paths["benchmark"]),
                    patch.object(
                        driver.subprocess, "check_output", side_effect=["", "a" * 40]
                    ) as git,
                ):
                    with self.assertRaisesRegex(AssertionError, "imports"):
                        driver.current_revision()
                    git.assert_not_called()

    def test_module_without_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (
                self.source_context(root, None, None),
                patch.object(
                    driver.subprocess, "check_output", side_effect=["", "a" * 40]
                ) as git,
            ):
                with self.assertRaisesRegex(AssertionError, "imports"):
                    driver.current_revision()
                git.assert_not_called()

    def test_matching_imports_still_require_a_clean_git_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / "deployment/brain/src/canary_brain"
            with (
                self.source_context(
                    root, str(package / "runtime.py"), str(package / "benchmark.py")
                ),
                patch.object(
                    driver.subprocess, "check_output", side_effect=[" M runtime.py\n"]
                ),
                self.assertRaisesRegex(AssertionError, "clean"),
            ):
                driver.current_revision()

    def test_matching_clean_imports_attest_the_driver_revision(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / "deployment/brain/src/canary_brain"
            with (
                self.source_context(
                    root, str(package / "runtime.py"), str(package / "benchmark.py")
                ),
                patch.object(
                    driver.subprocess, "check_output", side_effect=["", "a" * 40 + "\n"]
                ),
            ):
                self.assertEqual(driver.current_revision(), "a" * 40)


if __name__ == "__main__":
    unittest.main()
