# Interrupted recovery of a completed video pair

Follow-up to independent review 6652382979 on PR #21, baseline `188c7e5ca`.
The review's P1 was reproduced: terminate a recovery after its first unlink in
alphabetic order, then recover again. The old code deleted the final sidecar of
an already complete pair. This is a recovery-of-recovery failure, distinct from
the publisher cleanup case covered in the previous report.

## Correction

When recovery finds both final names linked but the journal still pending, it now
fsyncs final entries, writes committed via a temporary file, fsyncs that file,
replaces the journal and fsyncs staging before unlinking any payload. An already
committed journal is also synced before cleanup, covering a previous failed fsync.
An injected directory-sync failure verifies that staged inode evidence is retained
until that durability check succeeds.

Publication, rollback and recovery now share explicit journal-last cleanup instead
of TemporaryDirectory/rmtree. Staged payloads are unlinked first and their directory
synced; transaction.json is removed last, then the directory is synced/removed and
the parent synced. Recovery recognises the empty directory left by death after the
last journal unlink. Nonempty unrecognised staging is preserved for inspection.
The recovery decision is never inferred from directory enumeration order.

The committed write is outside partial-link rollback: failure to write its journal
after both links exist leaves the complete pair for recovery rather than starting
a new rollback of an already complete pair. A link collision in export_video is
now a ValueError handled by the export/CLI error path; foreign output is preserved.

## Directed tests

`tests/test_publication_recovery.py` creates an actual interrupted publisher and
then kills the recovering process at each unlink. Both SIGKILL and SIGTERM and
forward/reverse alphabetical directory iteration are injected through actual
child processes. The tests use production publication/recovery, with no encoder,
server or provider required.

- Complete pending pair: 3 unlink cuts x 2 orders x 2 signals = 12 cases. The next
  recovery must preserve both final files byte-for-byte and remove staging.
- Partial pair: 4 cuts (including final rollback) x 2 orders x 2 signals = 16 cases.
  A later publication must recover, retry successfully and remove staging.
- Durability failure: no staged payload may be removed before directory fsync
  succeeds; retry preserves the final pair and completes cleanup.

Validation on final code, using Python 3.12 in Windows/WSL:

```sh
python -m pytest -q                         # 140 passed in 77.19 s, includes real encoder
python -m ruff check src tests              # passed
python -m ruff format --check src tests     # 39 files formatted
python -m mypy src/canary_brain --no-incremental  # 18 modules passed
git diff --check                           # passed
```

The same 29 directed cases also ran with fresh pytest basetemp directories on
`/dev/shm` (tmpfs) and `/mnt/e/Development/tibia/.scratch` (Windows volume via WSL).
Both passed. Directory order is forced in both directions on each filesystem,
independent of its native enumeration behavior. The default full suite uses /tmp.
Final tmpfs run: 29 passed in 21.18 s; final Windows-volume run: 29 passed in 27.90 s.

The existing WAL, foreign replacement, active publisher, hash-contract, caught-write
failure and real codec tests remain included. Prior artifact/identity contracts
are unchanged. These tests establish signal-death recovery and syscall failure
behavior, not physical power-loss or storage-controller guarantees. Native Windows
signal behavior was not tested. Persistent destination lock files remain intentional.

All work occurred in the isolated video-review clone. No shared server/database,
paid provider, production deployment or main-branch merge was used.
