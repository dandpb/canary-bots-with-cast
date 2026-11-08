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

## Supervised integration on main 3431b404

Draft #83 head ba3e00a8 was rebased as dde8b9f3 before integration. Recorder,
runtime and replay_cli were identical to main immediately after that rebase,
preserving #82. #84's QA save changes were not edited. No tests/fixture helpers,
providers, live services, canonical ledgers or frozen evidence were accessed.

RED: `q72-integration-red.log` records 10 new supervised integration cases failing
because Controller had no native_source_revision/admission integration. Tests
were written before the integration implementation. Additional regressions cover
receipt TTL versus native capture, loss of B, lost reply/retry, cutoff versus
latest sample, pre-horizon world changes, altered duplicates, terminal deadline,
committed frame deletion/payload corruption, admission storage failure, peer
rebind, callback overflow and cancellation before a model task starts.

GREEN (logs next to the scratch checkout in session TMPDIR):

- `q72-broad-offline-final.log`: 130 tests across controller, supervision, runtime,
  recording/integration, native admission, telemetry delivery, stop policy,
  protocol, decision-fixtures and supervised admission.
- `q72-integration-final.log`: 19 supervised integration regressions, all included
  in the final broad run (including TTL/capture, admission commit failure and
  visible ingress overflow).
- `q72-mocked-harness.log`: 37 campaign horizon/abort/finalize/startup-interrupt
  checks. A session-only pytest fixture aliases actual TMPDIR directories via
  procfs fds to fit sockaddr_un; no production path checks were bypassed.
- `q72-worker-diagnose.log`: all 29 subprocess worker regressions, including fake
  and native no-inference paths, negative stop priority, #82 close=False/timeouts,
  post-confirmation failures and synthetic FIFO retry/backpressure. The fixture
  now implements admission/fence and uses an explicitly accelerated native clock
  for short tests; it is not 30-minute qualification evidence.
- `q72-worker-contract-final.log`: 9 real AF_UNIX supervised runtime cases:
  completion, dropped B, wrong nonce, reload, peer loss, missing capability,
  operator stop during close, close=False, and operator stop during awaited
  durable proof. Positive paths assert neither
  worker state nor replay publishes completed before close/final proof.
- `q72-accounting-mocks.log`: 14 provider/gateway unit tests using in-memory fake
  client methods and fresh synthetic SQLite files, including unknown liability.
  No actual provider request or canonical ledger was used.
- `q72-integrated-metadata.log`: 1 compiled clean/dirty/rebuild/Git-loss test.
- `q72-integrated-native.log`: 7 C++20 tests, -Wall -Wextra -Werror, real Channel
  FIFO plus immutable admission, correlated fence, wrong admission nonce and
  unavailable bot. No full game dependency build is represented by this command.
- `q72-types.log`: strict mypy over all eight changed Python implementation
  modules. Ruff lint/format and cumulative whitespace checks pass.

Total distinct Python cases across these commands: 220, plus seven native cases.
Earlier exploratory runs had Unix-path and startup-time failures while native
compilers were running concurrently; the above final focused runs pass after
using procfs aliases for scratch sockets, running timing-sensitive workers
without competing builds, and giving the unsupervised runtime fixture a bounded
10-second cold-start readiness wait with exit diagnostics. Production startup
and drain limits were not increased. This is synthetic offline validation, not game QA.

`q72-server-configure.log` records the offline full CMake attempt: configuration
stops at find_package(CURL CONFIG REQUIRED), missing CURLConfig.cmake. No Docker,
dependency downloads or native game/loader run was attempted to bypass it. See
native-admission-stage.md for the remaining integration/30-minute gates.

## Independent P2 followup (base e3657489)

Reviewer ce308d77 found a cutoff stalled/proposal_timeout that later XP could
clear, and an untracked Supervisor._chat model call after closure. Both were
reproduced before fixes: q72-p2-red.log contains six failing regression cases.
The cutoff is now evaluated once after the first qualifying observation and
frozen separately from receipt watchdogs and late fault/in-window-death evidence.
Operator chat guards admission at entry/before model/after response; its actual
request task is tracked (one per bot, at most three), cancelled and included in
the same bounded close. Controller closure remains permanent even if B arrives
later. An uncooperative chat rejects qualification instead of extending shutdown.

q72-p2-focused.log: 96 tests pass through actual runtime/chat paths, controller,
supervision, stop policy, admission/recording, #82 decision-fixture close gates,
and fake-client accounting tests. q72-p2-types.log: strict mypy passes five changed
or related implementation modules. Ruff lint/format and whitespace checks pass.
No actual provider calls or canonical ledger access occurred.

The runtime regressions retain a valid correlated fence and clean sealed replay
while requiring stalled/proposal_timeout to win over subsequent XP. Chat tests
exercise both cutoff and Controller.close, direct private guard, close-before-B,
concurrent request rejection, cooperative cancellation and cancellation-resistant
model shutdown. Existing slow-chat/newer-pause behavior is preserved.

See native-supervised-harness-interface.md for b25bbdb9's exact activation and
artifact contract. Native configure/build receipts are stored outside the repo
under session TMPDIR (q72-prefix-configure-final.log, q72-prefix-build-final.log);
they supersede the earlier missing-CURL configure attempt. No full-game build
success is implied here; consult the final build receipt. The prefix and existing
Release cache were read only; no existing build, production or services changed.
q72-p2-loader.log passes the real dlopen loader regression under ASan/UBSan with
disposable libraries; q72-p2-reload.log passes the three mocked LuaJIT reload
scripts. These do not establish live avatar handoff or 30-minute qualification.
