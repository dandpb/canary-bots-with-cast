# Video publication recovery and render identities

Follow-up to independent review comment 6651597046 on PR #21. Work used an
isolated sparse clone; the main development checkout, game, database and web were
not modified. No provider calls or paid tests were made.

## Abrupt process death

Two new regressions first reproduced the blocked retry by terminating a child
publisher with actual SIGKILL/SIGTERM immediately after the MP4 hard link. They
failed against the prior implementation. A destination kernel lock now excludes
live publishers from recovery. A flushed journal identifies each transaction;
recovery rolls back incomplete final names only if their inodes still match its
staged files. A foreign replacement remains untouched.

Additional child-process cases cover death immediately after both links and death
after deleting the first staging file during cleanup. The latter exposed a new
partial-cleanup case during development and failed before the committed-journal
fix. A flushed, atomically replaced committed journal now retains complete pairs
even when staging cleanup was interrupted. Another test pauses a live publisher
after its first link: a second publisher is rejected without removing its file;
after killing the first, retry succeeds.

POSIX directory fsync occurs for staged entries and destination links, before
staging cleanup. This improves metadata durability but the tests do not simulate
physical power loss or storage-controller behavior. Unrecognised/legacy staging
without the transaction journal is preserved for manual inspection. Persistent
lock files are intentional: unlinking a lock can create concurrent lock inodes.

## Sidecar version 2

`source_evidence_sha256` is recomputable from `source_evidence`: displayed manifest
labels, synthetic flag, sample interval, status and renderer-consumed chronological
events through the chosen end time. Prefix events establish initial state, trail
and cost. Storage envelopes (row ID/key/segment, wall time), metadata update times
and events beyond the fixed window do not change this identity.

`render_input_sha256` is recomputable from `render_input`, adding start/end, FPS,
normalized requested speed, renderer version, frame count, dimensions, font and
codec settings. Tests vary start/FPS/speed/renderer version independently, mutate
visible XP, and alter only envelopes plus append a later sample. Each identity
changes or remains stable according to this contract. The older full snapshot
audit hash remains available and is explicitly not a deduplication/cache key.
`video_sha256` remains the identity of actual encoded bytes across toolchains.

## Validation

From `deployment/brain`, using the existing WSL Python 3.12 environment:

```sh
python -m pytest -q --tb=short                    # 110 passed, 36.54 s
python -m ruff check src tests                   # passed
python -m ruff format --check src tests          # 38 files formatted
python -m mypy src/canary_brain --no-incremental  # 18 modules passed
git diff --check                                # passed
```

The full suite includes the real ffmpeg/ffprobe test, WAL concurrency, caught
publication failures, actual child-process deaths and collision preservation.
Snapshot deadlines and encoder/probe subprocess failures are now converted into
the CLI's ordinary ValueError path; three new tests cover these cases.

An additional real export to the Windows E: volume through WSL verified directory
fsync and hard links on this output filesystem: synthetic demo, 4 frames at 2 FPS,
2.0 seconds, 1280x720, JSON sidecar equal to the returned evidence. Local artifact:
`.scratch/replay-qa/video-publication-v2.mp4` (not tracked).

```text
source_evidence_sha256 867156e1d86b983c5051e86d9744be85b1686d2a94eaf0baaa03ff88fcf61b7e
render_input_sha256    d6521205fae07f5e727f3fbe058f2a45a3af2f37f7cb4f7ee5145302b39c86ca
video_sha256           7d95c75f34f9d226dae05a5ad466c9536b5829f7383cd43addb1d450a0166f09
```

The snapshot still copies the bounded whole recording database into the system
temporary directory, with a ten-second deadline. This is a retained capacity
limit, not evidence of arbitrary-size/slow-disk support. Windows-native locking is
implemented; the signal-death/directory-fsync evidence above is Linux/WSL evidence.
