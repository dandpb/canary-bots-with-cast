"""Exercise native build identity against real Git and CMake, without Docker."""

import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "build_source", HERE / "verify-build-source.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BuildSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.git("init", "-q")
        (self.source / "input.txt").write_text("original\n")
        self.git("add", ".")
        self.git(
            "-c",
            "user.name=QA",
            "-c",
            "user.email=qa@example.invalid",
            "commit",
            "-qm",
            "fixture",
        )
        self.revision = self.git("rev-parse", "HEAD").strip()

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-C", str(self.source), *args], text=True
        )

    def test_clean_exact_revision(self):
        self.assertEqual(
            MODULE.verify(self.source, self.revision)["source_revision"], self.revision
        )

    def test_wrong_revision_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "revision"):
            MODULE.verify(self.source, "0" * 40)

    def test_dirty_source_rejected(self):
        (self.source / "input.txt").write_text("changed\n")
        with self.assertRaisesRegex(RuntimeError, "clean"):
            MODULE.verify(self.source, self.revision)

    def test_untracked_source_rejected(self):
        (self.source / "untracked.txt").write_text("extra\n")
        with self.assertRaisesRegex(RuntimeError, "clean"):
            MODULE.verify(self.source, self.revision)

    def test_unknown_label_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "40"):
            MODULE.verify(self.source, "unknown")

    def test_missing_git_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        with self.assertRaises(RuntimeError):
            MODULE.verify(outside, self.revision)

    @unittest.skipUnless(shutil.which("cmake"), "CMake is required")
    def test_separate_readonly_git_context_feeds_real_native_metadata(self):
        # Model the Docker mounts: source tree has no .git, metadata is separate.
        metadata = self.root / "gitmeta"
        (self.source / ".git").rename(metadata)
        env = dict(os.environ, GIT_DIR=str(metadata), GIT_WORK_TREE=str(self.source))
        cmake = HERE.parents[1] / "cmake" / "WriteSourceMetadata.cmake"
        output = self.root / "header"
        subprocess.run(
            [
                "cmake",
                f"-DSOURCE_DIRECTORY={self.source}",
                f"-DOUTPUT_DIRECTORY={output}",
                "-P",
                str(cmake),
            ],
            env=env,
            check=True,
            capture_output=True,
        )
        header = (output / "gitmetadata.h").read_text()
        self.assertIn(f'#define GIT_HEAD_SHA1 "{self.revision}"', header)
        self.assertIn("#define GIT_RETRIEVED_STATE 1", header)
        self.assertIn("#define GIT_IS_DIRTY 0", header)


if __name__ == "__main__":
    unittest.main()
