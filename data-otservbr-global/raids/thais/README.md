# Thais

## Overview
Component package under `raids/thais` containing 4 files (`cyclops.xml`..`wild_horses.xml`).

## Interface
- `<announce>` raid broadcast tags (1 messages) [cyclops.xml:announce]
- `<areaspawn>` monster `Cyclops` (amount=5) [cyclops.xml:areaspawn]
- `<areaspawn>` monster `Cyclops Drone` (amount=5) [cyclops.xml:areaspawn]
- `<areaspawn>` monster `Cyclops Smith` (amount=3) [cyclops.xml:areaspawn]
- `<announce>` raid broadcast tags (2 messages) [orcs.xml:announce]
- `<singlespawn name="Orc Helmet">` boss/creature spawn [orcs.xml:singlespawn]
- `<singlespawn name="Orc Shield">` boss/creature spawn [orcs.xml:singlespawn]
- `<singlespawn name="Orc Armor">` boss/creature spawn [orcs.xml:singlespawn]
- `<areaspawn>` monster `Orc Shaman` (amount=3) [orcs.xml:areaspawn]
- `<areaspawn>` monster `Orc Berserker` (amount=3) [orcs.xml:areaspawn]
- `<areaspawn>` monster `Orc Warlord` (amount=1) [orcs.xml:areaspawn]
- `<areaspawn>` monster `Orc Rider` (amount=5) [orcs.xml:areaspawn]
- `<areaspawn>` monster `Orc` (amount=3) [orcs.xml:areaspawn]
- `<areaspawn>` monster `Orc Rider` (amount=3) [orcs.xml:areaspawn]
- `<areaspawn>` monster `Orc Berserker` (amount=2) [orcs.xml:areaspawn]
- `<areaspawn>` monster `Orc Shaman` (amount=4) [orcs.xml:areaspawn]
- `<areaspawn>` monster `Orc Warlord` (amount=3) [orcs.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [rats.xml:announce]
- `<areaspawn>` monster `rat` (amount=20) [rats.xml:areaspawn]
- `<areaspawn>` monster `cave rat` (amount=20) [rats.xml:areaspawn]
- `<areaspawn>` monster `Wild Horse` (amount=1) [wild_horses.xml:areaspawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [cyclops.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [orcs.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [rats.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [wild_horses.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [cyclops.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [orcs.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [rats.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [wild_horses.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
