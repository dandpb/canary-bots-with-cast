# SQLite descriptor and diagnostic safety

## Confirmed defect, separate from the original incident

The original partial M5 execution persisted only `OperationalError`, without
the SQLite result code or operation. Its precise error cannot be reconstructed
from that class alone. A missing terminal does not establish whether a provider
returned trustworthy usage. Existing unknown reservations and the original
attempt remain unchanged; this patch performs no reconciliation or retries.

An independent synthetic reproduction did establish a defect in both
`Store.__init__` and `RecordingStore.__init__`: they raw-opened and closed the
database inode before connecting through SQLite. On Unix, closing another
descriptor for that inode can cancel locks held by existing SQLite connections
in the same process. SQLite documents this [POSIX locking hazard](https://www.sqlite.org/howtocorrupt.html).

With an idle WAL reader retained, the old Store constructor released its database
lock. A second process could then write, close and remove WAL/SHM despite that
reader. A 30-round control without reinitialization passed. Reinitializing the
old Store under the same schedule produced `SQLITE_CORRUPT` (11) and
`SQLITE_IOERR_SHORT_READ` (522, an `OperationalError`). This reproduced with both
host SQLite 3.45.1 and the common worker image's SQLite 3.46.1. These synthetic
codes are not asserted to be the original execution's unrecorded code.

An open reader alone was not sufficient to produce the fault: ordinary idle and
active read transactions allowed WAL writes. The problematic raw close and the
unnecessarily retained reader handles are addressed separately.

## File and connection changes

`sqlite_files.prepare_database` creates a private temporary inode in the same
directory with `O_EXCL|O_NOFOLLOW`, applies mode 0600, and closes it **before**
atomically publishing the final name through a hard link. Concurrent creators
can select the already-published inode. Only the owned temporary name is removed.
SQLite is never opened through that temporary alias. Existing databases use
`lstat` and chmod without following symlinks; they are never raw-opened by the
bootstrap. Both the financial Store and recording Store use this helper.

All four M5 ledger-reader sites now explicitly close their connections after
ending the transaction. RecordingStore also closes its connection if its setup
PRAGMA fails. No SQL retry, API retry, TTL, backoff schedule or provider mapping
is introduced or changed.

## Failure evidence

SQLite failures carry only allowlisted error type, numeric result code, symbolic
result name and operation stage. Exception messages, SQL, paths, provider headers
and credentials are not exported. Completed probe summaries enter the execution
result before financial reconciliation, so a failing read cannot discard them.
The primary failure and the separately failing ledger export retain their stages.

The provider captures the original exception, timeout origin and SQLite metadata
before writing auxiliary diagnostics. A failed diagnostic write is separately
identified and cannot replace the original usage/deadline/settlement exception.
The recorder receives a terminal attempt independently of that write. If the
recorder itself is unavailable, the original exception is still preserved.
`failure_elapsed_ms` describes the original failure; terminal `elapsed_ms` keeps
including bookkeeping time. Genuine-deadline provenance remains distinct.

A financial diagnostic failure blocks probe admission even when the original
outcome was a genuine timeout. Infrastructure failure must not be silently
accepted as deadline-only model performance. Reservations remain integral;
failed settlement never becomes a successful response.

## Verification boundary

The regression suite checks both Store facades with live reader locks, an active
read transaction and another writer process; concurrent creation; publication
only after raw descriptors close; symlink/private-mode behavior; owned-temporary
cleanup; and 30 rounds of reinitialization/external writes with stable WAL/SHM
inodes and successful integrity checks. Tests inspect live databases through
SQLite/stat only, never by raw hashing or copying their active inodes.

Failure tests use the real GatewayProvider, financial Store and Recorder with a
controlled SDK boundary and a synthetic competing writer. They exercise original
usage, deadline and settlement failures, a second failing diagnostic write,
terminal persistence, safe metadata and unreleased liabilities. M5 tests execute
both frozen fake provider blocks and final ledger export, checking that every RO
handle closes before the next model and that technical infrastructure failures
block the game boundary.

The common-image control uses
`sha256:dfd281ce86a6e9690e76003feea358514779455c7cd9f1e77c11538254d1c737`
with SQLite 3.46.1, read-only root filesystem, no network and only test source/test
dependencies mounted read-only. Synthetic databases live in its temporary
filesystem. The canonical volume, registered credentials, production services and
real providers are never mounted or accessed by these tests. Temporary containers
use `--rm`; their receipts confirm removal.

The final common-image run passed **84 tests and 8 subtests**. Receipt:
`/home/daniel/canary-maintenance/sqlite-fix-qualification-20261106T172838Z/common-image-receipt.json`,
SHA-256 `eb52fc849d9ddfab2269aa7111ce16464363e8b9421bc5300965610d57792b8f`.
Its Python source hashes match the final patch. Ruff lint/format for all nine
changed Python files, strict mypy for six application/tool modules and
`git diff --check` passed. The original lock test failed for both constructors
before the helper; all three handler regressions also failed before the fix.
