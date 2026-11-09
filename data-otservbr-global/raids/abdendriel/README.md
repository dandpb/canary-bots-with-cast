# Abdendriel

## Overview
Component package under `raids/abdendriel` containing 4 files (`badger.xml`..`wasp_bear.xml`).

## Interface
- `<areaspawn>` monster `Badger` (amount=100) [badger.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [dragons.xml:announce]
- `<singlespawn name="Dragon Lord">` boss/creature spawn [dragons.xml:singlespawn]
- `<areaspawn>` monster `Dragon` (amount=2) [dragons.xml:areaspawn]
- `<areaspawn>` monster `Dragon Hatchling` (amount=3) [dragons.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [warwolf.xml:announce]
- `<areaspawn>` monster `Wolf` (amount=55) [warwolf.xml:areaspawn]
- `<areaspawn>` monster `War Wolf` (amount=70) [warwolf.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [wasp_bear.xml:announce]
- `<areaspawn>` monster `Wasp` (amount=30) [wasp_bear.xml:areaspawn]
- `<areaspawn>` monster `Bear` (amount=30) [wasp_bear.xml:areaspawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [badger.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [dragons.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [warwolf.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [wasp_bear.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [badger.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [dragons.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [warwolf.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [wasp_bear.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
