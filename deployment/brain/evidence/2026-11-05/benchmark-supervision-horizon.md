# Supervised benchmark horizon and stop integration

Date: 2026-11-05. Base: `83262d3e8dd8511f35e4f9aaad550a2bb76a9e8f`.
Isolated clone; no provider credentials, paid calls, native/ABI changes or deploy.
The ongoing real-game qualification in #25 retains its frozen source; this patch
was developed in a separate checkout and did not modify its workers.

## Reproduced problems

`test_benchmark_horizon.py` drives the actual campaign orchestrator with a mocked
private harness and controlled monotonic clock. The first observation arrives
two seconds after readiness. Before the fix, the configured ten-second run ended
after **eight observed seconds**, but was marked completed. Command:

```sh
cd deployment/brain
python -m pytest tests/test_benchmark_horizon.py -q
```

The original deadline was based on service readiness rather than the worker's
first observation. The worker's clock was correct; a second orchestrator deadline
ended it early. A second regression also rejected an early `completed` claim
without elapsed evidence; before that guard it incorrectly succeeded.

During stop-policy integration, injected critical gap markers exposed another
case: the recorder's persistent incomplete flag could be set while its transient
error/drop counters were clear. Both native/fake real CLI workers still ended as
completed. The two `recording_gap` regressions failed before the persistent-gap
check and passed afterward. They insert the same stored loss marker as a
storage-limit failure; they do not simulate physical disk exhaustion.

The real proposal-timeout test also exposed an attribution problem: `continue`
could be removed from the actual autonomous-work request but still exist in the
raw latest observation. An invalid fake choice was then marked `selected`, closing
the timeout window before intent validation failed. A regression reproduced that
marker; selection now validates against the filtered request before it can reset
the window. An eleven-case CLI IPC suite includes a real thirty-second window
with continuous observations and invalid choices, which stops correctly.

## Resulting behavior

Independent review of `07e1bb7` identified four further shutdown races, which
were not covered by the earlier 174-test pass. New regressions reproduce a gap
coincident with completion, a gap committed during recorder close, a budget marker
written just as the worker finishes, and SIGINT while the second trial provisions
its database. The first two and the observed-coverage test failed before the fixes.
The signal regression additionally caught asynchronous signal delivery starting
the second worker; campaign interruption now marks its event synchronously and
wakes the loop, then lets the current provisioning operation finish before
teardown. It never starts that second provider worker.

The campaign enables an opt-in single-bot policy in the production worker. Valid
observation/telemetry and locally validated choice events feed the same policy
logic exercised in the free qualification. Completion starts at the first valid
observation and requires fresh observations covering the full horizon. The final
actual observation is sampled explicitly. The orchestrator waits for `run_stop`
and verifies both observed elapsed time and first-to-last recorded sample span;
it no longer treats its own startup deadline as successful gameplay.

The policy bounds death, observation loss, lack of observed progress, model-choice
silence and generation changes. Persistent critical gaps and writer errors stop
the worker. Stop causes remain visible in state and recording lifecycle events.
Gameplay stops are failed trial outcomes; operator stop interrupts the campaign
and critical infrastructure stops abort it before a subsequent trial. No stop
releases an unknown financial liability or permits an automatic replacement run.

Recorder errors and persistent gaps override completion and ordinary gameplay
stops. A generation change remains a critical stop even if it also creates a gap.
After all worker/provider tasks and the recorder drain, both worker and runner
revalidate durable evidence. The runner rereads the financial marker at that
point before accepting completion. Unknown stop reasons abort rather than become
another failed gameplay trial. Campaign signals remain active during provisioning
and between trials; explicitly hosted workers do not replace those handlers.
Standalone worker handlers are removed/restored on exit. A bounded 30-second
shutdown allowance covers drain without being counted as observed gameplay.
Duplicate/out-of-order observations cannot refresh benchmark liveness or progress.
This filtering is confined to supervised benchmarks.

This does not change direct production-worker behavior by default. Supervision
requires an explicit flag, one recorded bot and a timed horizon. The existing
benchmark command supplies the flag. Its models, prices, gateway and monthly
ledger remain governed by the existing preflight and reservation controls.

## Validation and scope

The subsequent integrated review found two remaining startup/priority cases:
SIGINT during `character()` could still create a worker; a signal during socket
readiness or blocking `start_game()` did not reach that worker until the startup
await returned. It also reproduced a budget marker replacing a critical stale,
world-change or startup reason. Nine directed cases failed before correction.
The campaign now checks after character restoration and while waiting for the
socket, and relays operator interruption concurrently into the worker's stop
event while awaiting blocking startup. Cleanup waits for the owned startup
operation to return before closing its stack. Financial stop can replace only
completion or ordinary gameplay reasons, preserving critical infrastructure
causes. Twenty-six targeted startup, financial priority, abort and horizon cases
passed after the correction, including both SIGINT and SIGTERM. All use fake
harness/worker or native-only isolated SQLite; no paid/provider request occurs.

**182 Python tests passed in 168.72 s**, using a short owned pytest base directory
to respect Unix socket path limits. This includes twelve policy tests, two
orchestrator horizon cases, campaign-abort/shutdown race cases, a filtered-choice regression and eleven real supervised CLI
worker cases. The CLI cases use only a local synthetic Unix datagram peer and
native/fake providers: normal completion after a delayed first observation,
death limit, generation change, observation loss and critical recording gap.
They assert correct reason, worker exit, socket removal and zero request rows.

```sh
python -m pytest -q --basetemp=/tmp/m5-su-final-f
ruff check src/canary_brain/benchmark_stops.py src/canary_brain/controller.py \
  src/canary_brain/runtime.py src/canary_brain/benchmark.py \
  tests/test_benchmark_horizon.py tests/test_benchmark_stops.py \
  tests/test_benchmark_worker.py tests/test_benchmark_abort.py \
  tests/test_benchmark_choice_window.py tests/test_benchmark_finalize.py
mypy src
```

The long native/fake game runs belong to the separate #25 QA harness and image;
these IPC/orchestrator tests do not claim to be another long server playtest.
No human acceptance, production deployment, account access or paid opt-in is
established by these checks. M5 admission still requires the remaining fixture,
timing, supplies, account and spending decisions recorded in #10/#14.
