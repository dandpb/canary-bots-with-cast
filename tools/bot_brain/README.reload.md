# Bot engine reload: preparation and failure handling (#12/A)

The executable owns the loader. Run its API and engine consumers on the game
dispatcher. Network status and login callbacks already dispatch their work there.

`Game.botPrepareReload()` returns `{ok, phase, message, ticket}`. It reserves a
private directory beside the canonical library, copies the candidate to a read-only
file, opens that snapshot with `RTLD_LOCAL`, checks the ABI tag before calling a
factory, and parses authored CSVs using the candidate's parser. The parsed containers
belong to the candidate. Preparation does not initialize world-derived tables,
register Players, start a worker or replace the active engine.

`BotSystem.executeReload` requires successful preparation before force-deactivation.
`Game.botReload(ticket)` consumes that exact candidate and initializes its derived
tables without rereading the CSVs. Both APIs return structured success/failure;
callers must inspect `ok`, never parse log wording. `Game.botCancelReload(ticket)`
releases an unconsumed candidate. A stale ticket cannot commit/cancel another request.
There is no fallback to loading a mutable source path. Lua stops after commit failure,
cancels an unused preparation and clears its reload guard so an operator can retry.
Recovery also works when the initial library load failed.

Logs identify the failure phase: snapshot/open, ABI, symbols, factory, data,
preparation, commit or initialization. Each module destroys its instance before
closing the handle, then removes its private snapshot. A failed preparation retains
the active instance. Initialization failure after commit leaves the engine unavailable
and reports failure; it does not claim to roll back world effects.

## Build and deploy together

Rebuild the executable and `bot_engine` together, and ship the matching Lua bindings
and scripts. The ABI tag covers a contract revision, shared interface/Player/Creature/
Position headers, compiler identity/version, common C++ flags and build type. It is
a compatibility gate for these builds, not a promise of compatibility with arbitrary
server versions or toolchains. Advance the contract revision in
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
only logging replaced. Disposable libraries cover missing/invalid replacements,
ABI/export/factory/data failures, exceptions, snapshot-copy failure, initial recovery,
stale/cancelled tickets, source replacement after preparation and 50 reloads. ASan and
UBSan are enabled. Final checks reject leftover snapshot directories or mapped copies.
These tests are also registered with CTest on GNU/Linux when tests are enabled.

The original reproduction loaded a valid library, removed its canonical file, called
reload, then accessed the engine: `reload=0 loaded=0`; UBSan reported reference binding
to null in the original `bot_engine_loader.cpp:126`. With preparation before destruction,
the same missing replacement returns failure and retains the original instance.

## Remaining acceptance

This is the first delivery of #12. Complete Player checkpoint/retention belongs to
#11 and must be integrated before #12/B can establish the full state-preserving swap.
Still validate real active/hibernated bots, skills/items at constant XP, save failures,
cast continuity, pending callbacks, threads, and one tick cycle in a disposable server
and database. The isolated loader's 50 swaps do not prove actual gameplay acceptance.
The guarded teleport/PM/status/cast/Lua paths still require that integrated exercise
with a missing library, including XML and binary status with population reporting on/off.
