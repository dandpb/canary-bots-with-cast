# Venore

## Overview
Component package under `raids/venore` containing 9 files (`dharalion.xml`..`water_buffalo.xml`).

## Interface
- `<announce>` raid broadcast tags (1 messages) [dharalion.xml:announce]
- `<singlespawn name="Dharalion">` boss/creature spawn [dharalion.xml:singlespawn]
- `<announce>` raid broadcast tags (3 messages) [elves.xml:announce]
- `<areaspawn>` monster `elf` (amount=4) [elves.xml:areaspawn]
- `<areaspawn>` monster `elf scout` (amount=4) [elves.xml:areaspawn]
- `<areaspawn>` monster `elf arcanist` (amount=3) [elves.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [fernfang.xml:announce]
- `<singlespawn name="Fernfang">` boss/creature spawn [fernfang.xml:singlespawn]
- `<singlespawn name="War Wolf">` boss/creature spawn [fernfang.xml:singlespawn]
- `<announce>` raid broadcast tags (1 messages) [feverish_citizen.xml:announce]
- `<areaspawn>` monster `feverish citizen` (amount=120) [feverish_citizen.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [hunter.xml:announce]
- `<areaspawn>` monster `Hunter` (amount=15) [hunter.xml:areaspawn]
- `<areaspawn>` monster `Orc Sambackpack` (amount=1) [orc_backpack.xml:areaspawn]
- `<announce>` raid broadcast tags (2 messages) [the_old_widow.xml:announce]
- `<singlespawn name="The Old Widow">` boss/creature spawn [the_old_widow.xml:singlespawn]
- `<areaspawn>` monster `Giant Spider` (amount=10) [the_old_widow.xml:areaspawn]
- `<announce>` raid broadcast tags (3 messages) [undead.xml:announce]
- `<areaspawn>` monster `Skeleton` (amount=35) [undead.xml:areaspawn]
- `<areaspawn>` monster `Banshee` (amount=12) [undead.xml:areaspawn]
- `<areaspawn>` monster `ghoul` (amount=22) [undead.xml:areaspawn]
- `<areaspawn>` monster `demon skeleton` (amount=18) [undead.xml:areaspawn]
- `<areaspawn>` monster `Vampire` (amount=15) [undead.xml:areaspawn]
- `<areaspawn>` monster `water buffalo` (amount=4) [water_buffalo.xml:areaspawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [dharalion.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [elves.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [fernfang.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [feverish_citizen.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [hunter.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [orc_backpack.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [the_old_widow.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [undead.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [water_buffalo.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [dharalion.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [elves.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [fernfang.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [feverish_citizen.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [hunter.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [orc_backpack.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [the_old_widow.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [undead.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [water_buffalo.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
