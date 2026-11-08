# #72 free-QA harness handoff (for b25bbdb9)

Use the production supervised worker; do not duplicate its stop loop. This is an
interface description, not authorization to start a service or qualification run.
The P2 followup preserves main 3431b404's #82 recorder shutdown and #84 QA save.

## Activation

Prepare a clean native source/build containing admission and correlated fence
support. Pin the actual native build's full Git commit (40 lowercase hex chars),
not the prior main revision or the separate harness revision. CMake embeds HEAD
and dirty state. Unknown/dirty source is rejected; a commit string alone is not
binary/image attestation. Preserve external build/binary identity receipts.

The native `CANARY_BRAIN_CONFIG` JSON needs `mode: "shadow"`, `bots: [BOT_ID]`,
`autonomous_bot: BOT_ID`, `keep_awake: true`, and `socket_directory: PRIVATE_SOCKET_DIR`.
The bot must be activated/alive in the isolated QA world before admission. The
worker does not create or repair a bot. Use one private directory shared by native
peer and worker. The native directory must be an absolute path <=80 characters;
its server.sock/worker.sock pathnames must fit AF_UNIX (<108 encoded bytes).
Do not silently reuse production sockets or old run databases. The worker checks
sender pathname and socket device/inode/owner; replacement invalidates the run.

Example worker JSON (replace uppercase values before validation):

```json
{
  "provider": "native",
  "mode": "shadow",
  "bots": [65001],
  "socket_directory": "/PRIVATE_SHORT_PATH/ipc",
  "state_file": "/PRIVATE_PATH/run-state.sqlite3",
  "run_seconds": 1800,
  "benchmark_supervision": true,
  "native_source_revision": "NATIVE_BUILD_COMMIT_40_HEX",
  "learning": false,
  "memory_mode": "frozen",
  "recording": {
    "path": "/PRIVATE_PATH/replay.sqlite3",
    "namespace": "freeqa72",
    "sample_ms": 1000,
    "manifests": [{
      "run_id": "freeqa72:native:0",
      "bot_id": 65001,
      "lineage": "freeqa72:native:0",
      "provider": "native",
      "model": "none",
      "memory_mode": "frozen",
      "source_revision": "NATIVE_BUILD_COMMIT_40_HEX"
    }]
  }
}
```

No credential/gateway is needed. Omit operator_port and budget_file for the free
native worker; its private state Store is newly created, not a canonical ledger.
Use a unique run_id/namespace and files per attempt. If manifests are supplied,
the source pin and bot roster must match exactly. `experiment` is optional.
The worker also accepts the pin from the sole manifest when the explicit field
is omitted. Short run_seconds never bypasses the native minimum of 1800 seconds.

Launch the worker via the normal CLI in the installed worker environment:

```sh
PYTHONPATH="$QUALIFIED_SOURCE/deployment/brain/src" "$WORKER_PYTHON" \
  -m canary_brain.cli serve --config "$PRIVATE_CONFIG"
```

Or call `await runtime.run(Configuration.model_validate(config), stop_event)`.
The native peer must advertise lifecycle_telemetry=1, telemetry_delivery=1,
telemetry_admission=1, telemetry_fence=1, keep_awake=true. The production worker
owns admission nonce/retry, heartbeat, B delivery, clock opening, cutoff, model
closure, terminal request/retry, drain, recorder close, and final validation.
The harness must not generate its own admitted/fence packets or extend the drain.

## Durable admission schema

`Store(state_file).get("native_admission", RUN_ID)` returns this full private JSON
(after recorder commit, before model/intent admission). In SQLite it is the
`records` row with kind=`native_admission`, key=RUN_ID; `data` is JSON:

```text
version: 1
 type: "telemetry_admitted"
 world: native runtime generation string
 bot_id: BOT_ID
 nonce: opaque worker admission nonce
 begin_sequence: B (positive integer, allocated once)
 captured_ms: t0 (native monotonic milliseconds)
 deaths: D0 (cumulative native deaths at admission)
 observation: O0 (complete protocol.Observation, including private lease)
 source: actual native source commit (40 hex)
 source_dirty: false
 fault: ""
```

B/t0/D0/O0 are descriptive aliases, not additional JSON keys. O0.world/bot.id/
captured_ms must match world/bot_id/t0. O0 includes sequence, bot state/XP/level,
actions, etc. Lost replies retry the same nonce and preserve this exact boundary.
A restarted/reused attempt cannot silently readmit. Missing B is a failure even
if later telemetry and a terminal status arrive.

The replay has `event_key="native-admission"`, kind=`lifecycle`, data containing
`phase: "native_admitted"` plus the same admission fields. Replay public-data
filtering removes O0.lease and other private fields; do not deserialize that
public projection as a complete Admission. The first ordinary sample is O0
without lease/messages. The private state artifact retains the full admission.

## Terminal artifacts and harness responsibilities

The first observation with captured_ms-t0 >= max(1800, run_seconds)*1000 is the
score cutoff, stored as `event_key="horizon-final-sample"`. Use its XP/level and
D0-relative in-window deaths, not later diagnostic observations or final SQL.
Negative policy state at this cutoff (including stalled/proposal_timeout) is
frozen; later XP cannot turn it into completed. Late in-window deaths, peer/world
faults and transport/recording evidence still invalidate completion. Operator chat
shares persistent admission closure and bounded model-task shutdown.

`event_key="native-terminal-fence"` has kind=lifecycle and data:
`phase="native_terminal_fence"`, plus TelemetryStatus fields version/type/world/
bot_id/captured_ms/issued_sequence/accepted_sequence/pending_frames/pending_bytes/
overflow_frames/discarded_frames/fence_nonce/fault. The fence nonce differs from
the admission nonce and is generated by the worker. Periodic statuses do not
qualify. Committed native keys are `native:WORLD:BOT:SEQUENCE`; the worker verifies
both exact payloads and contiguous coverage from B through issued_sequence.

The authoritative stop is `Store(state_file).get("run_stop", "end")`:
- `native_finalizing` is NOT completion. A crash here remains incomplete.
- `completed` is published only after successful bounded recorder close and
  committed proof, with negative stop priorities checked again after that proof.
- Other reasons are failed/interrupted attempts; retain every attempt's artifacts.

A positive replay also has `event_key="supervisor-native-qualified"`,
kind=lifecycle, `phase="run_supervisor_stop"`, reason=completed, after_flush=true.
The stop details include elapsed_seconds (receipt watchdog clock) and
observed_seconds (first cutoff captured_ms minus t0, divided by 1000).
A zero CLI exit or an in-memory tail-confirmed event alone is insufficient.
Require the authoritative completed stop, positive final replay receipt, clean
recording, native duration >=1800s, pinned artifacts and real QA checks.

The harness may set the worker's stop event/send SIGTERM for an external stop or
its own conservative timeout. It must not manufacture completed, ignore negative
worker stops, overwrite B, or use SQL save results to move the scoring window.
`runtime.run` does not itself close a campaign manifest or compare final QA SQL;
those harness duties must preserve the worker's result and #81 window-vs-save
semantics. Keep exact commands, source/binary identity, replay, saves and resource
receipts. A synthetic captured-time jump is test evidence, not a real 30-min run.
#72 remains open until the free isolated native run and remaining review gates.
