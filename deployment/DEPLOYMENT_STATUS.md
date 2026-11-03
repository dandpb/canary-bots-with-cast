# Deployed fixes tracked by the fork

The intelligent companion controller and autonomous explorer were merged into
`dandpb/canary-bots-with-cast:main` in [PR #2](https://github.com/dandpb/canary-bots-with-cast/pull/2).
The deployment follow-up also versions the two earlier VPS adjustments:

- Startup loads bots serially in batches of 50, with a 35-second pause between
  batches and at most three attempts per failed load. Processing continues after
  an exhausted failure. Final logs report actual successful registrations.
  Online-row synchronization respects `botPlayersShowAsOnline`.
- Ordinary players can reach `/cavebot party`, `claim` and `release` handlers.
  The existing access check still blocks administrative operations. `/party`
  remains the dedicated ordinary-player party command.

The startup change was separately submitted to the original repository as
[upstream PR #3](https://github.com/1LineAtaTime/canary-bots-with-cast/pull/3).
An upstream merge is independent of the fork's main branch.

## Verification

Run from the repository root with Lua and repeat with LuaJIT:

```sh
lua tools/bot_brain/test_startup_batches.lua
lua tools/bot_brain/test_startup_batches.lua data/scripts/globalevents/bot_manager.lua online
lua tools/bot_brain/test_player_commands.lua
lua tools/bot_brain/test_reload.lua
lua tools/bot_brain/test_reload_missing.lua
```

The startup fixture uses a virtual event loop and 101 bot rows. It verifies batch
pauses, transient exception/nil retries, continued registration after a failure,
bounded final failure and enabled/disabled online visibility. The player fixture
exercises public registration and routing, then checks that ordinary players
cannot reach reload, status, teleport or brain administration through this action.
Both new fixtures fail against the previous main branch and pass with the fixes.

The same 50/35-second startup policy already restored all 997 bots on the VPS.
The existing running server uses these player permissions. This source-parity
follow-up does not require a game restart; no new cold-start acceptance is claimed.

Host-specific configuration, credentials, account entitlements, databases and
generated binaries remain deployment state. The worker and native library sources
are versioned; credentials and player data must not be copied into Git.

Remaining gameplay/performance acceptance is recorded in
[the companion evaluation](brain/EVALUATION.md) and
[issue #1](https://github.com/dandpb/canary-bots-with-cast/issues/1):
human party survival/usefulness, failed navigation routes, and bridge tuning above
the initial 2 ms target. Source merge completion does not close those checks.
