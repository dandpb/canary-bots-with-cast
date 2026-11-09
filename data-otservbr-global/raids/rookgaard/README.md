# Rookgaard

## Overview
Component package under `raids/rookgaard` containing 6 files (`munster.xml`..`teleskor.xml`).

## Interface
- `<areaspawn>` monster `Munster` (amount=1) [munster.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [rats.xml:announce]
- `<areaspawn>` monster `Rat` (amount=20) [rats.xml:areaspawn]
- `<areaspawn>` monster `Cave Rat` (amount=10) [rats.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [rottie1.xml:announce]
- `<areaspawn>` monster `Rat` (amount=20) [rottie1.xml:areaspawn]
- `<areaspawn>` monster `Cave Rat` (amount=10) [rottie1.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [rottie2.xml:announce]
- `<areaspawn>` monster `Rottie The Rotworm` (amount=1) [rottie2.xml:areaspawn]
- `<areaspawn>` monster `Apprentice Sheng` (amount=1) [sheng.xml:areaspawn]
- `<areaspawn>` monster `Teleskor` (amount=1) [teleskor.xml:areaspawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [munster.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [rats.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [rottie1.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [rottie2.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [sheng.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [teleskor.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [munster.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [rats.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [rottie1.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [rottie2.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [sheng.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [teleskor.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
