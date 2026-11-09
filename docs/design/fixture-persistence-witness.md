# Prospective closed-fixture XP/level persistence contract

Status: offline implementation for independent technical review; NOT qualification.
Base worker/harness: 8730ff2bb4c8617c342144e69b27026fa8968c4f.
Native source remains c8b3878d3e576ff8ef1561cbb2614cb77532a349, unchanged.
No old attempt may opt into this contract after running. #72 remains open.

## Problem and choice

Failed a03 remains immutable. Its frozen window ended at XP100426, final SQL
was XP100433. Existing live Lua already observed the +7 (35.105 versus frozen
33.016); the gain was not wholly unobserved. Those old samples lack the bound
terminal identity/sequence/removal/save contract. They are diagnosis, never a
retrofitted witness. Exact final SQL equality remains required.

Use a separate game-owned journal: retain the actual Player userdata, snapshot
XP/level before synchronous shutdown, call Game.setGameState(SHUTDOWN), then
verify the retained object is removed, absent from Game.getPlayers(), and still
has exactly the same XP/level/death count. Write a linked post-removal seal.
After clean owned process exit, the host fsyncs journal and directory, writes a
complete sidecar, fsyncs its directory, and only then reads SQL. Final SQL must
match that independent terminal pair exactly. Neither SQL nor the worker supplies
the witness XP. Scoring still uses the frozen native horizon; no equality becomes
an inequality and no record is appended to the closed production recording.

```mermaid
sequenceDiagram
  participant W as Production supervisor
  participant H as Owned host adapter
  participant L as Fixture Lua / retained Player
  participant S as Save manager / SQL
  W->>W: B,t0,D0,O0 → >=1800 native seconds → fence → close → seal
  H->>W: Audit actual completed receipt and post-close seal
  H->>L: Exclusive run/nonce stop.request (no character data)
  L->>L: Independent pre_shutdown XP/level, sequence
  L->>S: Synchronous SHUTDOWN callbacks, removal, saveAll
  L->>L: Removed + roster absent + unchanged XP/level; linked post_remove
  H->>H: Clean game exit + save logs; fsync journal and complete sidecar
  H->>S: Read final character SQL with timing receipt
  H->>H: Exact terminal XP/level equality; frozen scoring unchanged
```

Bare onShutdown is too early; onLogout precedes removal/save. Keeping the
production recorder open through game shutdown would conflict with the existing
peer/durability checks and post-close seal. This implementation changes neither.

## Source justification at exact C8

* src/server/signals.cpp:65-101 queues SIGTERM work on dispatcher. Normal contract
  shutdown does not use SIGTERM; bounded failure cleanup can still stop owned resources.
* src/game/game.cpp:634-704 synchronously performs save callbacks, shutdown
  callbacks, player removal and saveAll, then queues actual Game.shutdown.
* src/game/game.cpp:1233-1290 removes roster/list and marks removed; later
  Game.shutdown at :8552 unloads the engine. The wrapper runs before that queued task.
* src/creatures/players/player.cpp:4289 runs logout callbacks before removal;
  :11518-11566 performs de-equip/login-position cleanup and queues bot saves.
* src/game/scheduling/save_manager.cpp:47-108 captures live snapshots and waits
  save futures; its bot savePlayer return alone is NOT a SQL durability ACK.
* src/io/iologindata.cpp:194 captures PlayerSaveSnapshot from live Player.
* src/lua/functions/core/game/game_functions.cpp:410-421 calls setGameState
  synchronously; its true return is NOT an SQL ACK. :772 uses OTSYS_TIME(true),
  hence UNIX epoch milliseconds despite the misleading Game.monotonicMs name.
* src/lua/functions/lua_functions_loader.hpp:255-279 retains shared Player
  userdata; player_functions.cpp:1374,1413 getters can read that retained object.
* Game.loadBotPlayer at game_functions.cpp:840-940 bypasses login callbacks.
  Therefore render_fixture injects attach directly after BotDeath registration
  in generated bot_manager.lua, before quest preparation and native activation.
* src/creatures/players/bot/bot_brain.cpp:143-191 provides read-only brain status:
  actual world, mode and roster. Only that introspection command is used; no
  synthetic packets or gameplay commands are used to manufacture progress.

No native observer barrier appears necessary from these source semantics. Actual
embedded Lua execution is still required to confirm this conclusion; mocks do
not prove the server integration. If retained userdata/API behavior or lifecycle
ordering fails there, fail closed and propose a separately reviewed observer
barrier. Do not modify frozen C8 to make this fixture pass.

## Schema, producer and consumer

Profile `fixture_shutdown_v1`, version 1. Every raw JSON line has the exact binding
(run_id, 256-bit stop_nonce, GUID bot_id, native_source, worker_source,
fixture_sha256, canary_sha256, engine_sha256), runtime_id, contiguous sequence,
explicit `clock=unix_epoch_ms`, epoch_ms, actual XP/level, independent deaths,
and removed flag. Non-initial lines include the game-produced native status JSON.
The first line is attached, middle lines heartbeat, last two pre_shutdown and
post_remove. Post carries raw-pre-line SHA256 including newline and sequence.
Runtime identity must stay fixed; world, one-GUID native roster and shadow mode
must agree with actual native admission. Game.getPlayers absence is separate
from the engine's configured roster, which persists until engine unload.

The game creates audit.jsonl exclusively (0600, NOFOLLOW), writes exact raw bytes
using Linux ARM64 libc, hashes with OpenSSL SHA256 via LuaJIT FFI using the
pinned runtime SONAME libcrypto.so.3, and never reopens or truncates evidence.
The descriptor remains open until process exit so unexpected late audit/death
records poison an otherwise complete terminal pair. Host caps journal
at 4 MiB/8192 records; game caps each record at 16 KiB. The one-second audit rejects
coverage gaps >5 seconds and a shutdown pair >210 seconds. The host wait is bounded
at 210 seconds. A request is exclusive, fsynced and atomically published, bound
to the run and unique stop nonce. No request contains witness XP or SQL values.

The independent death event is attached before activation and starts at zero.
It latches a private sticky fault and increments before identity checks, encoding,
writing or throwing, including during stopping/sealed phases. All audit entrypoints
catch failures internally, latch before best-effort poison/rethrow, and check the
private latch before seal; clearing an exposed diagnostic field cannot clear it.
C8 may swallow callback errors, so propagation through setGameState is never
relied upon. Host closed-log checks reject C8 Lua errors/stack overflow globally,
including errors after post marker if a poisoned-record write itself fails.
This deliberately supports only a zero-death fixture;
any death, nonzero native
D0, reset, reattachment, identity change or missing coverage rejects it. Death
qualification needs a separately specified cumulative/death-reset contract; this
patch does not claim it. The opt-in consumer also reconciles the FULL native
counter stream against this independent audit, including post_horizon_telemetry
and diagnostic observations, never just the scored window. Any positive native
death count or contradictory dead/unavailable/hibernated phase rejects the
zero-death profile even when D0, window deaths, terminal journal deaths and final
SQL all appear zero/consistent. Malformed counter/identity/clock values, capture
or arrival regressions, sequence gaps/resets and duplicate-frame conflicts fail
closed without sorting away the evidence. Recorder telemetry omits bot_id and
sequence from its JSON; consumer uses the actual native:world:GUID:sequence key
and reconciles any explicitly supplied fields. This adds no waiver to the
independent audit requirement and never changes a legacy attempt's interpretation. Attach epoch precedes the host admission receipt. Native
captured_ms remains the native steady-clock domain and is NEVER compared with
Lua epoch_ms. Host request/publish/exit/durable/SQL monotonic brackets enforce
operation order; epoch brackets bind Lua samples to host stop request/exit. Wall
clock regression or contradictory clock evidence rejects the attempt.

The host requires owned game exit 0 and C8 save-batch success strictly between
unique pre/post log markers, rejects known save failures, then fsyncs the journal
and directory. It exclusively publishes durable-complete.json and fsyncs the
directory before any SQL read. io.close and Game.setGameState true alone are not
durability claims. This is a post-clean-exit durability proof, NOT crash-safe
pre-save witness durability. The raw complete sidecar and journal must be retained
with immutable external manifests. Consumers verify raw line hash linkage,
sidecar hash/size/binding, actual native clean-source admission, >=1800 horizon,
fence and after-flush completed seal, fixture/replay identity and #81 stop/SQL
receipts. Final SQL id/experience/level must equal the terminal witness exactly.
Malformed, missing or contradictory evidence fails closed and leaves other
report diagnostics available. Legacy attempts keep their old strict comparison.

## Closed-fixture trust boundary and activation prerequisites

This is an opt-in helper contract, not a new general production guarantee. The
external immutable-input attestation must pin the actual generated scripts and
all loaded save/shutdown/logout/death/de-equip callbacks, fixture/map, config,
worker source and native binary hashes. Those hash fields are bindings to that
external attestation, not game-computed self-attestation. Native admission independently
checks the native source/world/GUID; replay consumer supplies run and fixture identity.
No reload, resurrection, another player, script replacement, or deferred character
mutation after seal is allowed. Audit all callbacks and dispatcher shutdown path
for that closed fixture. Pre/post equality cannot detect a transient mutate-then-
restore, nor prove arbitrary unreviewed asynchronous code harmless. Save success
logs plus clean exit and exact SQL are additional checks, not a generic callback audit.
Only XP/level persistence is claimed; equipment, inventory, health, mana and position serialization
are explicitly outside this contract.

A new reviewed plan must copy fresh generated scripts, call render_fixture on
that copy BEFORE image creation, hash the actual mounted output and callback set,
and mount a fresh private `attempt/persistence` at `/qa-persistence` game-only.
Keep it OUTSIDE the worker's writable /qa run mount. Pin the Linux ARM64 ABI and
verify actual embedded LuaJIT FFI/OpenSSL availability without relaxing gates.
Do not change native source pin; worker/helper source pin must name the prospective
reviewed commit, distinct from frozen 8730. No credentials/provider/real ledger
access is added by these helpers.

The harness adapter is opt-in through stop_and_read_character(..., terminal={
'directory': private_path, 'binding': binding, 'world': actual_world,
'require_native_receipt': partial(production_receipt_check, configuration)}).
The owned harness must implement wait_game(timeout), shutdown_logs()->bytes,
and character()->actual SQL. production_receipt_check reuses the existing
m5_worker.require_final_receipt on actual private state; do not supply a simulated
verdict in real execution. All failure paths retain primary errors/raw journal
and use the existing outer bounded owned-resource cleanup; the adapter neither
starts resources nor retries. A failed wait/save/fsync skips SQL consumption and
cannot claim success. Offline report diagnostics can run after failure, without
upgrading that outcome. Fixture overlay generation does not auto-activate a run.

Before another long attempt: publish/review this helper-contract PR, independently
review its new plan/mount/identity/callback wiring, verify actual short embedded
Lua lifecycle/retained-userdata/save behavior and cleanup, then separately obtain
technical GO for any fresh qualification. No retry is authorized by this patch.

## Queued callback closure remains a separate activation HOLD

At exact C8 dispatcher.cpp:210-239 executes the remaining serial task vector;
:158-162 executes serial then scheduled tasks before mergeEvents. setGameState
queues Game.shutdown, but does not itself set Dispatcher::shuttingDown. The
scheduled-task guard at :325-345 only becomes effective when actual Game.shutdown
starts (game.cpp:8552 onwards), calls dispatcher.shutdown, then unloads the engine.
Consequently pre/post equality does NOT by itself close the pending dispatcher
interval. Native review identified BotEngine::tick restoring MANA before the
processBot removed-player guard. Removal/seal therefore demonstrably is NOT
full-character quiescence. No reachable ordinary removed-player XP/level mutation
was demonstrated by that review, which is narrower than proving none exists. Do not claim it does. Late audit death/fault records now invalidate the
journal, but arbitrary uninstrumented mutations still require source closure.

Inspected BotShutdown only saves bot-state metadata/restore flag; HirelingSave
calls SaveHirelings; PlayerLogout cleans training/stamina/cast state, and GodAfkLogout
removes AFK tracking. The one-bot loader also queues initial load and delayed
state-restore callbacks. A fresh DB must have no prior restore flag/states and
loader setup must be complete before stopping. This is not an exhaustive closure
proof for all registered callbacks, de-equip handlers, pending native tasks or
indirect helpers. Pin and independently audit the actual loaded callback graph
and all queued relevant mutations before activation; any unresolved path blocks
it. If that cannot establish no post-seal progression mutation, a separately
reviewed native observer/barrier is required. This helper patch does not install
one, suppress queued callbacks, or alter frozen C8.

The next fresh short-probe plan must provide concrete observations for each
closed-fixture invariant, not a list of assertions: hash every mounted generated
script, loaded callback/item-handler and source image; enumerate and independently
review their actual registration/indirect progression paths; map only Rat actors
with no active quest/encounter progression; retain fresh seed queries showing no
restorable bot states/restore flag plus actual loader/restore-complete logs before
request; establish empty command/walk queues using actual available runtime
receipts and producer/consumer accounting. A read-only brain status alone is NOT
a generic command-queue observer. If the required queue invariant is not observable,
report that missing prerequisite and do not fabricate it. Enforce exclusive private
mount ownership, no external writer mounts/ports/providers, one GUID/actor roster,
no reload/reactivation/resurrection paths or additional actors; retain actual
admission, API/hash probe, exit, journal/fsync and exact SQL receipts. Evidence
must distinguish what configuration prevents from what live observers verify.
No change to C8 is approved here; a broad guarantee still requires a native barrier.

Actual runtime activation must probe loading libcrypto.so.3 and SHA256 inside the
embedded server, before issuing any stop request, and compare a known hash vector
with independently computed expected bytes. Host LuaJIT passing alone is insufficient.
The separate short-probe plan remains HOLD and its old b0 overlay is superseded;
regenerate only after both native/Python reviews and review its new exact hashes.

## External final manifest ordering

Old a03 FINAL remains unchanged with its known stdout self-hash mismatch; its
accepted additive FAILURE receipt binds the completed log and original FINAL.
Prospectively an external coordinator waits for collection to exit and closes its
redirected stdout, then calls finalize_manifest on an explicit quiescent artifact
set. The manifest refuses its own path, symlinks, its process's open stdout/stderr
and changes during hashing. It is published exclusively, fsynced, and its hash is
returned outside the inputs. The caller must stop all other writers first: a
stable read cannot prove no future writes. No additive replacement is presented
as repairing the original attempt.

## Offline validation versus remaining proof

Tests execute the actual Lua writer/SHA/raw journal under host LuaJIT with mocked
Game/Player APIs, and a real fresh SQLite replay/report consumer. They inject
mutation/death, malformed or contradictory evidence, SQL ±1, timing/source/world/
identity/coverage/clock errors, missing seal, wait/fsync/save failures, old-file
collisions, and verify actual generated loader output. Adapter ordering requires
production completion before request and durability before SQL. Manifest tests
wait for a real child collector to close stdout before hashing and reject self
references. These are offline regressions, not actual server startup, 30-minute
qualification, callback closure proof, crash/death/reload/fault qualification or
full-world/comparative campaign equivalence. All previous failures remain failed.
