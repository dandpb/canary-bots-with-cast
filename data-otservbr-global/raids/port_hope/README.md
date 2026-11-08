# Port Hope

## Overview
Component package under `raids/port_hope` containing 8 files (`kongras.xml`..`the_welter.xml`).

## Interface
- `<announce>` raid broadcast tags (2 messages) [kongras.xml:announce]
- `<areaspawn>` monster `Lizard Snakecharmer` (amount=5) [kongras.xml:areaspawn]
- `<areaspawn>` monster `Lizard Templar` (amount=10) [kongras.xml:areaspawn]
- `<areaspawn>` monster `Lizard Sentinel` (amount=5) [kongras.xml:areaspawn]
- `<areaspawn>` monster `Lizard Snakecharmer` (amount=10) [kongras.xml:areaspawn]
- `<areaspawn>` monster `Lizard Templar` (amount=5) [kongras.xml:areaspawn]
- `<announce>` raid broadcast tags (2 messages) [lizards.xml:announce]
- `<areaspawn>` monster `Lizard Snakecharmer` (amount=5) [lizards.xml:areaspawn]
- `<areaspawn>` monster `Lizard Templar` (amount=10) [lizards.xml:areaspawn]
- `<areaspawn>` monster `Lizard Sentinel` (amount=5) [lizards.xml:areaspawn]
- `<areaspawn>` monster `Lizard Snakecharmer` (amount=10) [lizards.xml:areaspawn]
- `<areaspawn>` monster `Lizard Templar` (amount=5) [lizards.xml:areaspawn]
- `<areaspawn>` monster `Midnight Panther` (amount=1) [midnight_panther_1.xml:areaspawn]
- `<areaspawn>` monster `Midnight Panther` (amount=1) [midnight_panther_2.xml:areaspawn]
- `<areaspawn>` monster `Midnight Panther` (amount=1) [midnight_panther_3.xml:areaspawn]
- `<announce>` raid broadcast tags (3 messages) [serpent_spawn.xml:announce]
- `<areaspawn>` monster `Serpent Spawn` (amount=15) [serpent_spawn.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [terrorbirds.xml:announce]
- `<areaspawn>` monster `Terror Bird` (amount=30) [terrorbirds.xml:areaspawn]
- `<singlespawn name="The Welter">` boss/creature spawn [the_welter.xml:singlespawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [kongras.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [lizards.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [midnight_panther_1.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [midnight_panther_2.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [midnight_panther_3.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [serpent_spawn.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [terrorbirds.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [the_welter.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [kongras.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [lizards.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [midnight_panther_1.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [midnight_panther_2.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [midnight_panther_3.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [serpent_spawn.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [terrorbirds.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [the_welter.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
