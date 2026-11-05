"""Kill the recovery itself at every unlink, independent of directory order."""

import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest
from test_timelapse_export import crash_publisher

from canary_brain import timelapse

RECOVER_AND_DIE = r"""
import os, signal, sys
from contextlib import contextmanager
from pathlib import Path
from canary_brain.timelapse import publication_lock, recover_publications
reverse = sys.argv[2] == 'reverse'
scan, listing, unlink = os.scandir, os.listdir, os.unlink
@contextmanager
def ordered_scan(path):
    with scan(path) as entries:
        yield iter(sorted(entries, key=lambda e: e.name, reverse=reverse))
os.scandir = ordered_scan
os.listdir = lambda path: sorted(listing(path), reverse=reverse)
calls = 0
def interrupted_unlink(path, *args, **kwargs):
    global calls
    unlink(path, *args, **kwargs)
    calls += 1
    if calls == int(sys.argv[3]):
        os.kill(os.getpid(), getattr(signal, sys.argv[4]))
os.unlink = interrupted_unlink
output = Path(sys.argv[1])
with publication_lock(output):
    recover_publications(output)
"""


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-death regression")
@pytest.mark.parametrize("termination", ["SIGKILL", "SIGTERM"])
@pytest.mark.parametrize("order", ["forward", "reverse"])
@pytest.mark.parametrize("cut", [1, 2, 3])
def test_recovery_of_complete_pending_pair_survives_each_unlink(
    tmp_path, termination, order, cut
):
    video = crash_publisher(tmp_path, "SIGKILL", after_link=2)
    sidecar = video.with_suffix(".mp4.json")
    original = video.read_bytes(), sidecar.read_bytes()
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            RECOVER_AND_DIE,
            str(video),
            order,
            str(cut),
            termination,
        ],
        env={**os.environ, "PYTHONPATH": str(Path(timelapse.__file__).parents[1])},
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == -getattr(signal, termination), result.stderr
    with timelapse.publication_lock(video):
        timelapse.recover_publications(video)
    assert (video.read_bytes(), sidecar.read_bytes()) == original
    assert not list(tmp_path.glob(".canary-video-*"))


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-death regression")
def test_committed_decision_is_durable_before_removing_any_staged_evidence(
    tmp_path, monkeypatch
):
    video = crash_publisher(tmp_path, "SIGKILL", after_link=2)
    directory = next(tmp_path.glob(".canary-video-*"))
    journal = json.loads((directory / "transaction.json").read_text())
    timelapse.write_publication_journal(directory, {**journal, "committed": True})
    original = timelapse.sync_directory

    def fail_directory_sync(path):
        if path == directory:
            raise OSError("injected directory durability failure")
        return original(path)

    with monkeypatch.context() as fault:
        fault.setattr(timelapse, "sync_directory", fail_directory_sync)
        with (
            timelapse.publication_lock(video),
            pytest.raises(OSError, match="durability"),
        ):
            timelapse.recover_publications(video)
    assert (directory / video.name).exists()
    assert (directory / video.with_suffix(".mp4.json").name).exists()
    with timelapse.publication_lock(video):
        timelapse.recover_publications(video)
    assert video.exists() and video.with_suffix(".mp4.json").exists()
    assert not list(tmp_path.glob(".canary-video-*"))


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-death regression")
@pytest.mark.parametrize("termination", ["SIGKILL", "SIGTERM"])
@pytest.mark.parametrize("order", ["forward", "reverse"])
@pytest.mark.parametrize("cut", [1, 2, 3, 4])
def test_recovery_of_partial_pair_can_die_at_each_unlink_and_retry(
    tmp_path, termination, order, cut
):
    video = crash_publisher(tmp_path, "SIGKILL", after_link=1)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            RECOVER_AND_DIE,
            str(video),
            order,
            str(cut),
            termination,
        ],
        env={**os.environ, "PYTHONPATH": str(Path(timelapse.__file__).parents[1])},
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == -getattr(signal, termination), result.stderr
    timelapse.publish_video(tmp_path / "encoded.bin", video, {"retry": True})
    assert video.read_bytes() == b"complete encoded bytes"
    assert not list(tmp_path.glob(".canary-video-*"))
