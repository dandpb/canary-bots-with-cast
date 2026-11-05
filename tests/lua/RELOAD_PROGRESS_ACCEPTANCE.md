# Reload phase-progress regression (#12/B, PR #19)

Independent review 6651888280 identified omitted state and invalid debug-selection
handling. The reproductions use the existing labelled disposable lifecycle stack,
an internal network, private MariaDB data and no published ports or provider calls.
The main development checkout was preserved. Test bridge code is not shipped in a
normal runtime.

## Before the fix

The real admin hunt command reserved script 1 for GUID 65001 and entered TRAVELING
with `pendingHuntAfterTravel=true`. Reload cleared that flag. Advancing the real
engine tick at the arrival boundary entered IDLE while keeping the reservation.

PREPARING and RESUPPLYING each lost the prepare start/wait clocks and step 1 during
reload. A due production tick treated the zero clock as expired: PREPARING moved
to TRAVEL_TO; RESUPPLYING finished/rerolled. DWELLING lost its future deadline and
entered IDLE at the first tick, several seconds before the original deadline.

With three active Players and scheduler ON, `debug,Unknown` completed the native
handoff, deactivated all three Players, then returned a Lua selection error with
scheduler OFF. The pure Lua regression also failed against the old implementation.

## Correction and regression

`BotReloadEntry` now captures the pending hunt intent and absolute dwell deadline,
plus preparation start/wait/step/target and resupply start/phase/reroll values.
Restore accepts the hunt before copying its pending intent and preparation values,
derives its town from the candidate script and never transfers an old BotState,
POI or callback pointer. A missing/conflicting hunt leaves pending intent clear.
The same-process deadline is neither refreshed nor reset to zero by the swap.

The Lua helper validates the complete explicit debug selection before scheduler,
tick-owner or debug-population changes. It rejects an unknown name even in a mixed
known/unknown list and rejects fractional counts. Validation uses the authoritative
roster returned by the native commit: it does not promise to avoid the native swap
or preserve cancelled transient sessions when the debug selection is invalid.
The caller can retry; the engine and roster remain available.

```sh
python3 tools/bot_brain/test_reload_progress.py
```

The labelled server must have the matching `tests/fixture/lifecycle_bridge.cpp`
compiled as `/qa/lifecycle_bridge.so` and the test Lua adapter installed as described
in README.bot-progression.md. Server/library must be rebuilt together: adding DTO
fields changes the automatically computed ABI tag.

The test covers seven actual library swaps:

- Cross-town pending hunt remains reserved through reload; arrival enters HUNTING /
  PREPARING, clears pending intent and retains the same runtime Player.
- PREPARING and RESUPPLYING retain start/wait/step/phase values and keep waiting at
  the next due tick, rather than timing out or skipping preparation.
- DWELLING retains its exact deadline, remains dwelling before it and enters IDLE
  after it. A separate already-expired deadline stays expired after another swap.
- Invalid debug selection returns failure with scheduler still ON and all three
  GUID/runtime/active/hibernated tuples unchanged. The fixture turns the scheduler
  back OFF only after recording that result, to keep QA frozen.
- An unavailable hunt ID is cancelled with IDLE / huntId=0 / pending=false and no
  reservation for that ID. Other bots' legitimate reservations are not required
  to disappear.

The bridge selects a stationary town with an authored boat and seeds arrival/wait
boundaries; production `tick()` performs the transitions. This is not a playtest of
the boat journey, navigation, full client authentication or successful hunting.

## Validation

Matching Release server, library and unit binary built with two parallel jobs in
the local Windows/WSL environment (not the Oracle host). All 155 native unit tests
passed. Four CTests passed: the production-loader ASan/UBSan regression and three
Lua reload scripts, including the new invalid-selection cases. The library's
post-build gate reported zero GNU_UNIQUE dynamic symbols. The current main was
then incorporated and the composed binaries/regressions checked again.

The first disposable startup attempt during regression development raced MariaDB
TCP readiness; it was not a product regression result. Subsequent runs explicitly
wait for a successful authenticated TCP SELECT before starting game. An initially
overbroad assertion that *all* hunt reservations disappear was narrowed to the
cancelled fixture ID, preserving other bots' legitimate state. Original red and
successful corrected evidence are retained in RELOAD_PROGRESS_EVIDENCE.json.
