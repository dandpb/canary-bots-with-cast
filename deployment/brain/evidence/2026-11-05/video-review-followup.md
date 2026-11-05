# Timelapse review follow-up — 2026-11-05

PR #21 review identified source WAL retention during encoding, incomplete output
publication after write failure, and an events-only source hash. These were
reproduced against the reviewed implementation before their fixes.

## Live recorder isolation

The regression uses the real Recorder/SQLite path with a 1 MiB limit. At the
encoder boundary it appends 120 samples, flushes every sample, and requests WAL
checkpoints between batches. The old implementation persisted only 48 of 121
samples, including the initial sample, and exposed `storage_limit`. This excludes
queue overload: every enqueue succeeds and every write batch is drained.

Commit `513ab5205` takes a private SQLite backup and closes the live source before
rendering, encoding or probing. Copying has a ten-second progress deadline; private
files are cleaned on exit. The same regression now persists all 121 samples, with
no storage-limit gap, and truncates the source WAL while export remains active.
A separate test mutates/deletes live metadata/events after the copy and verifies
that the isolated export still reads its original consistent history.

The source-evidence digest now includes the captured run metadata and the digest
of the chronological event prefix through the selected ending time. Changing
only manifest/status changes `source_snapshot_sha256`; unchanged events retain
their `source_events_sha256`. The sidecar exposes enough information to reproduce
that combined digest. This does not hash unused future events or SQLite file bytes.

## Publication and retry

Before `910d587b5`, injected partial MP4 copying, sidecar-write failure and a sidecar
created by another writer left an orphan MP4 and blocked retry. The fix writes and
flushes both files into a private staging directory on the destination filesystem.
Exclusive hard links publish complete files without replacing existing paths.
Caught errors/interruption roll back only names whose inode matches this export.

Tests cover partial copying, sidecar write failure, destination collisions and
interruptions immediately after either final name is created. Failed writes leave
neither final file, a subsequent export succeeds, and concurrent foreign artifacts
remain intact. The MP4 and JSON are separate sequential publications; consumers
must require both files. This does not claim an atomic two-file transaction across
process death or power failure. Hard-link support is required at the destination.

## Validation

- 12 video tests passed, including the actual ffmpeg/ffprobe encoder test; fault
  tests stub only the codec to isolate recorder and filesystem behavior.
- Full integrated Python suite: **95 passed**. Ruff passed; strict mypy passed in
  18 source modules. No native code changed in this follow-up.
- A new export to the Windows workspace through WSL verified publication on that
  filesystem. It again produced 213 frames, 24 fps, 8.875 seconds, 1280×720, from
  an 88.365-second real native-party recording with explicitly simulated inference.
- MP4 SHA-256 remains
  `817d6bc77470b6c7a4981ecf8f8e445368f3cc222e3a274099f0db8bb2f2d53a`;
  the rendered video is byte-identical to the previously inspected artifact.
- Its new source-evidence digest is
  `a388e989cd03a251badb671c9cf287b2e0a5745676529a150e6cf7352c4fd7f1`;
  event-prefix digest is
  `e2138913a225be7ee5bf9b271c8cbc2f3b6118204c51ec0ce4feb2c47239b57a`.

Reproduce with `python -m pytest -q tests/test_timelapse.py tests/test_timelapse_export.py`
from `deployment/brain`. No paid inference or production deployment occurred.
