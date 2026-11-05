# Shared quests and quest roles across reload (#19)

Follow-up to independent review 6652802900, baseline `f35db9ba3`. Work used the
labelled disposable lifecycle game/MariaDB stack, an internal network, private
database, no published ports and no provider calls. The main checkout was preserved.

## Before the correction

The native admin command assigned enabled quest 38, Market Thais Example, to two
Players (65001/65003). Before reload, both ran it with separate waypoint cursors
1/2 and kill counters 5/7; whohunts reported zero exclusive reservations. Reload
reserved the quest for the first Player and cancelled the second (huntId=0, IDLE,
cursor/kills lost). Both also lost isQuestBot. At the controlled completion boundary,
the real finishResupplyAndReroll/tryStartHunt path chose a common hunt (script 8 in
the final red run) rather than a quest.

## Correction

Restore uses the candidate script's existing botScriptIsQuest classification:
isQuest or category quest. These activities can be restored concurrently and never
insert an exclusive activeHunts_/activeSpawnGroups_ entry. Ordinary hunts retain
their exclusive ownership. No extra classification flag is duplicated in the DTO.

Quest-role eligibility is derived from GUID and the current configured percentage
by one local helper shared by activation and restore. This follows activation's
existing policy, including clamp 0..100, without inferring a bot's permanent role
from its currently forced activity. The documented module-local quest-start cooldown
reset on reload remains unchanged; restored activities are not stamped as new starts.
This follow-up changes no public DTO layout; the earlier #19 ABI extension still
requires deployment of the matching executable and library together.

## Directed regression

Prepare the matching test bridge/Lua adapter described in README.bot-progression.md.
The private game's config uses only these QA overrides:

```lua
botQuestBotPct = 4
botResupplyRehuntPct = 100
```

The fixture's three public seed characters have GUID suffixes 1, 3 and 4: the first
two get quest roles, and the third is a regular-role control. A guaranteed re-hunt
roll makes the production next-selection path deterministic as a policy decision;
the particular eligible script is still selected by the native RNG/catalogue.

```sh
python3 tools/bot_brain/test_reload_quests.py
python3 tools/bot_brain/test_reload_progress.py
```

The first test performs two real swaps and verifies:

- Both quest runners retain GUID/runtime ID, HUNTING, quest ID, phase, waypoint,
  kills and their quest roles; whohunts has no exclusive reservation for the quest.
- The third Player retains its regular role and runtime identity.
- At the seeded completion/resupply boundary, production tick invokes the normal
  next-selector. The selected script is classified from the actual private runtime
  CSV as a quest and has no exclusive reservation. No next script ID is forced.
- An intentionally conflicting ordinary hunt still restores exactly one owner.

The second test repeats the seven previous phase/deadline/debug-selection swaps.
Both passed with the corrected library. These are controlled state boundaries,
not full quest navigation, reward/XP acceptance or a client playtest.

An initial green assertion accepted only two possible next quest IDs. The native
selector correctly chose enabled quest 1286, so the assertion was corrected to
classify the actual runtime catalogue. It does not restrict valid RNG choices or
fabricate completion of the route. Raw red/green evidence and artifact hashes are
in RELOAD_QUEST_EVIDENCE.json.

## Build and scope

Release targets canary/bot_engine/canary_ut completed with -j2. The incremental
build recompiled bot_engine.cpp and linked the library; the matching executable
remained current. All 155 native unit tests and four CTests (production loader with
ASan/UBSan plus three Lua reload tests) passed. Post-build inspection reported zero
GNU_UNIQUE dynamic symbols. Ruff passed for the new Python regression.

The private game and database exited 0 after validation. Their previous paired
artifacts, Lua adapter and config were restored while stopped. No shared server,
paid inference, main-branch merge or production deployment was used.
