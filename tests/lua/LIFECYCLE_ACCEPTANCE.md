# Lifecycle acceptance — 2026-11-05

This records disposable development evidence for #11/#12/#13 and the integrated
#1/#10 stack. It does not authorize merge or deployment. The original local stash
and production containers were preserved. Tests used x86_64 WSL/Docker, a private
internal network, separate MariaDB data and no published ports or paid providers.
Native test bridges and fault libraries are never shipped in runtime images.

## Persistence (#18, over #17)

- Real exercise-dummy training consumed a charge (10 → 9), added skill tries and
  mana spent with XP fixed at 4200. Hibernate → normal shutdown (exit 0) → a new
  server process retained skills, charges, storage and XP.
- Deactivate/force/unregister, virtual position, overlapping generations, failed
  SQL and later full-save retry were exercised. Pending authoritative Players are
  reused rather than replaced by older database state; existing backpacks survive.
- Review found that retaining Player alone did not make serialization safe.
  A real five-second SQL barrier reproduced old skills with newly mutated charges
  in one committed save. The immutable-checkpoint fix captures every statement and
  its exact acknowledgement delta on the dispatcher; SQL workers never traverse
  live inventory, skills or other mutable Player fields. The database `save` flag
  is checked by the worker. Binary/text literals require no live DB connection
  during capture. Unexpected reads during serialization fail closed.
- The deterministic test now persists the coherent pre-barrier skills and 77
  charges despite a concurrent wake/mutation to 66. A following checkpoint persists
  the new state. Five consecutive variants also reloaded the library while SQL was
  blocked, mutated to 55 charges, retained runtime identities and persisted the
  latest state afterward. XP remained 4200. These are barrier tests, not TSAN runs.
- The first immutable-checkpoint build exposed dispatcher producer-slot exhaustion
  when dedicated workers posted acknowledgements directly. GDB identified
  `SaveManager::runBotSave → Dispatcher::addEvent → pthread_mutex_lock`. The final
  implementation relays only acknowledgements through the registered general pool;
  SQL remains on its four dedicated connections. All five reload/barrier repetitions
  passed after this correction, followed by the population save/reload below.
- A later UPDATE failure trigger covered the final implementation: wake/mutation
  and a 996-bot reload retained the same Player with unsaved charges; removing the
  trigger and requesting a full save recovered the newest charges (22), XP 4200.
- Storage acknowledges only written values after COMMIT. Forge additions remain
  pending until dispatcher acknowledgement and are idempotent across overlapping
  captured batches. Human storage fixtures remain covered; ordinary human saves
  retain their existing configuration/implementation.

### Representative population

The public SQL seed supplied 996 bots, loaded and hibernated in bounded batches.
The comparison baseline (#17 guard-only) reported global player-save time
0.005–0.006 ms because it omitted these hibernated Players; this is missing work,
not an equivalent faster implementation.

The final immutable-checkpoint implementation (`81ac51592` plus matching library)
measured three asynchronous full saves:

| Trial | Capturing 996 stable checkpoints ms | SQL/save completion ms | Save control round trip ms | Concurrent SELECT probe ms | Game / DB CPU-seconds |
|---|---:|---:|---:|---:|---:|
| 1 | 59.705 | 2240.837 | 413.688 | 425.612 | 1.976 / 3.594 |
| 2 | 50.496 | 2465.955 | 438.971 | 268.646 | 2.102 / 4.019 |
| 3 | 43.576 | 2374.370 | 421.509 | 262.933 | 2.016 / 3.797 |

Control/probe measurements include Docker execution and the 200 ms QA poll.
CPU windows were 2.69–2.87 seconds and include control work. The capture time is
dispatcher work; SQL completion is asynchronous when configured. Earlier 1–2 ms
capture results only retained references and are superseded by these stable-state
measurements. Explicit synchronous/shutdown saves still wait for durability; the
earlier full-state implementation measured 3.31–3.33 seconds with async disabled.
No claim of nonblocking synchronous saves or measured queue saturation is made.
The per-GUID queue coalesces pending generations; exact peak backlog was not sampled.

A final full reload preserved all 996 runtime identities and hibernated states;
its control-inclusive duration was 420.759 ms. See
[raw population measurements](immutable-population-evidence.json).

## Safe reload (#17 → #18 → #19)

- Missing/invalid ELF, ABI/export/factory/data errors, copy failure and exceptions
  leave the prepared active engine intact; production-loader ASan/UBSan regression
  tests include 50 swaps and verify mapping/temporary-file cleanup.
- Actual unregister/reload cancels the pending native callback and destroys its
  function before dlclose. A real 50-swap fixture retained one mapped module, one
  private snapshot directory and 16 file descriptors. Engine code has no native
  background thread to join; executable-owned SQL work survives independently.
- A matching fault library throwing during initialization after commit retained
  awake/hibernated Players for explicit retry while UPDATE was unavailable.
- Initial missing-library startup exercised ordinary human teleport/speech, offline
  PM and admin bot methods, real TCP character-list serialization, cast/viewers,
  XML and binary status, including bot count visibility on/off. Restoring the
  library allowed recovery without restarting the server.
- A connected viewer selected a hibernated bot, woke the same Player and remained
  attached across successful reload. One executable-owned tick is retained.
- Full integrated Release server/library/unit build passed; the library exported
  zero GNU_UNIQUE symbols. Final immutable/relay build passed 32 selected native
  tests, four loader/Lua CTests and 16 Lua startup tests.

## Cast publication (#16 + #20)

The integrated fixture exercises a separate ordinary human account and the actual
ProtocolGame login/release, connected loopback transport, Connection.close, viewer
teardown, late old release after replacement, /cast off, logout, death and repeated
stop. Real HTTP listing converges with MariaDB; native TCP character-list bytes
are delivered over the loopback connection. This is not full OTClient authentication.
Delayed DELETE and rapid reconnect preserve the newest publication. A prolonged
SQL failure recovers without discarding the current desired state. Startup cleanup
also runs when bots are disabled.

The first shared-connection implementation blocked a dispatcher SELECT behind a
two-second DELETE (2049 ms). Two private cast DB workers reduced the same
control-inclusive probe to 201–204 ms. Hibernated bot listings/wake were also
exercised. Standalone #16+#20 build/runtime evidence is recorded separately; the
integrated result alone is not claimed as proof of branch independence.

## Replay/party and remaining gates

See [benchmark evidence](../../deployment/brain/evidence/2026-11-05/README.md) for
four real independent native baseline trials, orchestrator crash recovery,
recorder/viewer overhead, a native party/Portuguese hold fixture with fake inference,
and verified offline video. PRs #15/#21 provide M1–M4/M6 implementation and evidence.
Real-model M5 requires explicit model/provider selection and paid opt-in/caps.
Human party hunt/resupply, usefulness, survival and variety acceptance for #1
remains external; automated safe fixtures do not substitute for it.

Reproduce the live SQL overlap with `tools/bot_brain/test_checkpoint_overlap.py`
and `--reload`, only against the labelled disposable stack. The runbook also
documents `test_stateful_reload.py` and `test_cast_lifecycle.py`. Issues remain
open pending review and their remaining acceptance gates.
