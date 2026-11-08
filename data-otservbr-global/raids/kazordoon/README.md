# Kazordoon

## Overview
Component package under `raids/kazordoon` containing 2 files (`goblins.xml`..`horned.xml`).

## Interface
- `<announce>` raid broadcast tags (3 messages) [goblins.xml:announce]
- `<singlespawn name="Goblin Leader">` boss/creature spawn [goblins.xml:singlespawn]
- `<areaspawn>` monster `Goblin` (amount=50) [goblins.xml:areaspawn]
- `<areaspawn>` monster `Goblin Scavenger` (amount=15) [goblins.xml:areaspawn]
- `<areaspawn>` monster `Goblin Assassin` (amount=10) [goblins.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [horned.xml:announce]
- `<singlespawn name="Minotaur mage">` boss/creature spawn [horned.xml:singlespawn]
- `<singlespawn name="the Horned Fox">` boss/creature spawn [horned.xml:singlespawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [goblins.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [horned.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [goblins.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [horned.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
