# Bot engine reload: preparation and Player handoff (#12)

The executable owns the loader. Run its API and engine consumers on the game
dispatcher. Network status and login callbacks already dispatch their work there.

`Game.botPrepareReload()` returns `{ok, phase, message, ticket, native_handoff}`. It reserves a
private directory beside the canonical library, copies the candidate to a read-only
file, opens that snapshot with `RTLD_LOCAL`, checks the ABI tag before calling a
factory, and parses authored CSVs using the candidate's parser. The parsed containers
belong to the candidate. Preparation does not initialize world-derived tables,
register Players, start a worker or replace the active engine.

`BotSystem.executeReload` requires successful preparation before draining the engine.
`Game.botReload(ticket)` captures the roster and strong Player references, queues
complete checkpoints through #11, cancels pending engine dispatcher callbacks and
drains training/party sessions before destroying the old engine. It consumes that
exact candidate and initializes derived tables without rereading the CSVs, then
restores the same Players, hibernation pool, virtual positions, AI pause flags and
compatible hunt/travel progress. Both APIs return structured success/failure;
callers must inspect `ok`, never parse log wording. `Game.botCancelReload(ticket)`
releases an unconsumed candidate. A stale ticket cannot commit/cancel another request.
There is no fallback to loading a mutable source path. Lua stops after commit failure,
cancels an unused preparation and clears its reload guard so an operator can retry.
Recovery also works when the initial library load failed.

Logs identify the failure phase: snapshot/open, ABI, symbols, factory, data,
preparation, commit or initialization. Each module destroys its instance before
closing the handle, then removes its private snapshot. A failed preparation retains
the active instance. Initialization failure after commit leaves the engine unavailable
and reports failure; it does not claim to roll back world effects. The executable
retains the captured roster until an explicit retry restores it, even if SQL saves
fail. Bots without avatars remain registered without a synchronous DB load. A
normal reload never activates/equips/teleports a restored Player. `debugCount="off"`
is an explicit repair of missing registrations with bounded asynchronous retries.
Numeric debug selection deliberately activates selected bots and deactivates others.

The executable also owns native Player shared-pointer control blocks. Their final
release can occur on a save worker after the library that created the bot is gone.
Engine callbacks are cancelled on unregister, reload drain and destruction;
`Dispatcher::stopEvent` clears their functions immediately. Engine native code has
no background thread or asynchronous SQL completion callback to join. SQL closures
belong to the executable and carry Players/position values, not engine references.
The executable owns the single recurring tick; restarting it cancels its predecessor.
Shutdown explicitly unloads the module while its world/logging dependencies exist.

Combat, party membership, training and world-owned transient activity are cancelled
and can be selected anew. Raw POI/target/callback references never cross libraries.
Hunts whose IDs disappeared or conflict in the candidate are cancelled with a log.
This is preservation of character progression and compatible route progress, not a
byte-for-byte snapshot of every transient AI session.

## Build and deploy together

Rebuild the executable and `bot_engine` together, and ship the matching Lua bindings
and scripts. The ABI tag covers a contract revision, shared interface/Player/Creature/
Position/storage/save/database headers, compiler identity/version, common C++ flags and build type. It is
a compatibility gate for these builds, not a promise of compatibility with arbitrary
server versions or toolchains. The executable must export symbols in both the
test-enabled static-core and ordinary builds (`-rdynamic`). Advance the contract revision in
`src/creatures/CMakeLists.txt` when changing an exported contract not captured there.
Older libraries without the ABI/preparation exports are rejected before factories.

Use atomic replacement of the canonical library; never modify a mapped file in place.
The loader needs write permission in its parent directory for private snapshots.
GNU builds disable `GNU_UNIQUE` symbols on the library; the post-build symbol check
rejects artifacts retaining them. Do not introduce hidden visibility or DEEPBIND to
separate Asio service identities from the executable.

## Regression commands

With the development C++ toolchain and installed vcpkg includes:

```sh
BOT_TEST_INCLUDES="$VCPKG_INSTALLED_DIR/x64-linux/include" \
  python3 tools/bot_brain/test_engine_loader.py
luajit tools/bot_brain/test_reload.lua
luajit tools/bot_brain/test_reload_missing.lua
luajit tools/bot_brain/test_reload_failures.lua
```

The loader suite compiles the production loader and real `IBotEngine` interface with
logging and an empty-roster checkpoint hook replaced. Disposable libraries cover missing/invalid replacements,
ABI/export/factory/data failures, exceptions, snapshot-copy failure, initial recovery,
stale/cancelled tickets, source replacement after preparation and 50 reloads. ASan and
UBSan are enabled. Final checks reject leftover snapshot directories or mapped copies.
These tests are also registered with CTest on GNU/Linux when tests are enabled.

The original reproduction loaded a valid library, removed its canonical file, called
reload, then accessed the engine: `reload=0 loaded=0`; UBSan reported reference binding
to null in the original `bot_engine_loader.cpp:126`. With preparation before destruction,
the same missing replacement returns failure and retains the original instance.

## Disposable live regression

Use the labelled lifecycle stack described in `tests/lua/README.bot-progression.md`,
with `tests/fixture/lifecycle_bridge.cpp` compiled as a test-only Lua module against
the same headers. No native test bridge is shipped in a normal runtime.

```sh
python3 tools/bot_brain/test_stateful_reload.py --swaps 50
# Optional matching QA library: change only loadHuntData to throw
# std::runtime_error("isolated init failure") before its body; do not deploy it.
python3 tools/bot_brain/test_stateful_reload.py --swaps 50 --fault-library /tmp/fault.so
```

The live exercise verifies actual pending-callback cancellation, identical runtime
Player IDs for awake and hibernated entries, constant-XP inventory retention, missing
candidate rejection and optional post-commit failure/retry while MariaDB rejects
updates. Fifty real swaps retained one mapped module, one private snapshot and 16
file descriptors in the measured small fixture. The loader-only sanitized tests and
the live server are separate evidence; neither implies human party/cast acceptance.
Representative population overhead, connected cast continuity and missing-library
teleport/PM/XML/binary-status exercises are recorded separately as they are completed.
