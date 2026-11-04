# Native bot progression integration test

`bot_progression_test.lua` runs inside the game Lua environment against the real
`Player:addExperience` API. It changes a disposable character from level 8 to
level 11. Never run it on a player's account or on the production database.

Build the server and `libbot_engine.so` from this branch using the repository's
CMake configuration (C++23). Custom validation libraries must use the same C++
standard and dependency versions as the executable, including its thread pool. The XP and level-up
guards were in `Player::addExperience` in the executable, so replacing only the
bot library does not enable progression in an old server binary.

In an isolated database, prepare a solo character with level 8, experience 4200,
a standard vocation, and no equipment, wheel or condition stat bonuses. Load it
as a native bot using the usual bot account and pause autonomous actions during
the assertions. A party and LLM provider are unnecessary. Invoke from a temporary
QA script in that server:

```lua
local result = dofile("tests/lua/bot_progression_test.lua")(Player("Fixture Name"))
assert(result.level == 11 and result.experience == 13000)
```

Run with knight, paladin, druid and sorcerer fixtures. Repeat with an ordinary
player as a control. The test checks zero XP, accumulating XP below a threshold,
an exact level threshold, multiple levels in one grant, vocation health/mana/
capacity increments, and health/mana restoration on advance. On the old server,
a native bot fails with `earned XP was discarded` after the 100-XP grant.

Also check the lifecycle through the game API, checking both immediate reconnection and a fresh database load after saves
finish:

```lua
local check = dofile("tests/lua/bot_progression_lifecycle_test.lua")
check("Fixture Name", "hibernate")
check("Fixture Name", "reconnect")
check("Fixture Name", "force")
check("Fixture Name", "named")
```

1. Hibernate the progressed bot using `Game.botHibernate(guid)`, then wake it
   using the administrative `wake` bot command. Verify level 11 and XP 13000.
2. Deactivate it using `Game.botDeactivate(guid)`, release the QA script's player
   reference, then activate it again. Verify the same level, XP and maximum stats
   after a fresh database load. Repeat with `Game.botForceDeactivate(guid)`.
   Deliberately hold the isolated database save queue and repeat immediate
   deactivation/activation: the pending Player must be reused without losing XP.
3. Restart the isolated server after the bot hibernates and verify progression
   after activation. Repeat an engine reload after earning XP, before hibernating.
4. Fail a progression save in the isolated database, then reconnect without
   awarding more XP. Restore the database, hibernate again and verify the same
   progress is retried and saved. Offline pending bots must also be retried by
   the regular server save.
5. Keep an unchanged bot as a control: repeated wake/hibernate cycles should not
   add a full player save unless its experience changed.
6. Resume a solo bot in a real hunt and confirm a monster kill increases its XP.
   In an eligible party, confirm shared XP reaches both native bots and humans;
   ordinary party eligibility and XP multipliers must still apply.

`bot_progression_combat_test.lua` also provides a deterministic combat-credit
fixture. With native bots on adjacent walkable tiles outside a protection zone,
invoke it first without a member, then with an eligible native member:

```lua
local check = dofile("tests/lua/bot_progression_combat_test.lua")(bot, member)
addEvent(check, 1000)
```

It kills an ordinary Wolf through the combat API and checks actual kill XP;
it never grants experience directly. The optional member checks native shared
XP. Forced placement on a wall is deliberately avoided because combat correctly
rejects attacks against such a fixture.

The lifecycle checkpoint uses the existing player save manager and player
columns. It retains a queued bot until saving finishes, including a true logout
that releases the last game reference. Reconnection reuses pending state, and a
failed save keeps that state available for a later lifecycle or server-save retry. No progression is minted by the virtual
hibernation simulator, and no additional model requests are needed. As with
ordinary asynchronous saves, a process crash before the queued save completes
can lose the most recent unsaved progress.
