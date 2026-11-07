# Local stage validation

Base: `f72ddc0477931b8f797b493ec181309114f10d77`.
Branch: `stage/72-native-admission` (isolated scratch clone).
Design and test commit: `7db9977b` (expected RED without implementation).

Tests were written before implementation. Native RED compilation reports missing
`Session::admit`; Python RED collection reports missing `native_admission` module.
Logs are retained next to the checkout under the session TMPDIR.

GREEN on final source:

- 65 Python tests: `test_native_admission.py`, `test_telemetry_delivery.py`,
  `test_protocol.py`, `test_benchmark_stops.py` in deployment/brain/tests.
- 7 native tests: new admission suite plus existing brain protocol suite,
  compiled directly with C++20, `-Wall -Wextra -Werror`, system nlohmann JSON
  and system GoogleTest. The real Channel test uses a procfs fd alias for an
  actual TMPDIR directory to fit sockaddr_un without writing outside scratch.
- Ruff lint/format on changed Python files; strict mypy on native_admission
  (import dependencies followed silently); git diff --check.

Tests cover dropped B, missing terminal sequence, immutable lost-reply retries,
FIFO ordering across admission/death through real AF_UNIX, enqueue overflow,
source/nonce/world/bot mismatch, death during reply delay, duplicate mutation,
regressing native capture/deaths, dirty source, terminal loss, reload identity,
native observation horizon, and SIGKILL after a synthetic reply. Python crash
coverage demonstrates verifier behavior, not a supervised worker crash/recovery
integration test. Native dispatcher integration is inspected, not game-compiled.

A broader attempt including `test_benchmark_horizon.py`,
`test_benchmark_abort.py` and `test_benchmark_finalize.py` yielded 63 passes and
20 failures at configuration construction: `experiment output path is too long
for a private Unix socket`. These are blocked harness checks, not passes; no
helpers/path checks were edited to bypass them. The subsequent focused command
above passes all 65 tests. No Docker/provider/service access was performed.

The full server/engine, loader/reload and durable recording integration were
not built or exercised. This is an admission primitive plus standalone verifier,
not an active supervised completion fix. All remaining gates are in
[native-admission-stage.md](native-admission-stage.md). No changes to #82 files,
tests/fixture QA helpers, accounting implementation or FIFO transport algorithm.

## Review fixes after 55b2adce

Three P2 findings reproduced before edits: 9 RED cases (five pre-horizon
watermark faults, three conflicting observation retransmissions, and absent
CMake metadata generation); 26 existing cases still passed in that command.
The RED output is retained as `q72-review-red.log` under session TMPDIR.

Fixes:

- Validate status schema, world/bot and producer loss counters before checking
  horizon eligibility, making pre-horizon faults sticky.
- Retain canonical SHA-256 fingerprints for O0 and subsequent observations
  (8192 entries maximum). Compare the full validated payload on retransmission;
  exact older retransmissions remain idempotent, conflicts fail. An unknown
  older sequence within the admitted interval fails closed.
- Root CMake registers SourceMetadata.cmake; both core and bot_engine depend on
  its always-run generation target and receive its header include directory.
  WriteSourceMetadata.cmake generates the existing gitmetadata.h template,
  refreshes HEAD and tracked/untracked dirty state before compilation on each
  build, and uses unknown/dirty on Git failure. Unchanged content is not rewritten.
  This replaces the fallback in normal CMake builds without relying on the
  currently unused legacy git_watcher.cmake. Fallback remains fail-closed for
  standalone builds without generated metadata.

GREEN evidence:

- 74 focused Python tests passed (the previous four suites plus the nine new
  validator regressions): `q72-review-focused.log`.
- 35 admission/metadata tests passed together: `q72-review-green.log`. This
  overlaps the focused run. The metadata test configures one isolated Ninja
  project, compiles the real Session admission method using generated identity,
  then rebuilds without reconfiguration for clean, untracked-dirty, restored,
  new-commit and unavailable-Git states. Clean yields the exact fixture HEAD
  and no fault; dirty/missing-Git yield source_unqualified.
- The unchanged seven native tests were rerun: `q72-review-native.log`.
- Ruff lint/format, strict mypy on native_admission and whitespace checks passed.

Full server/engine CMake dependency configuration and gameplay compilation were
not run; the metadata compile probe validates the shared generator/target helper,
not the whole game. Prior harness path-length limitations and all stage-1
integration gates above remain. B/t0/D0/O0 and the FIFO implementation are
unchanged by this review delta. No live services or prohibited resources accessed.
