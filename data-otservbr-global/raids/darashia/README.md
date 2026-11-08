# Darashia

## Overview
Component package under `raids/darashia` containing 9 files (`arachir_the_ancient_one.xml`..`white_pale.xml`).

## Interface
- `<announce>` raid broadcast tags (1 messages) [arachir_the_ancient_one.xml:announce]
- `<singlespawn name="Arachir the Ancient One">` boss/creature spawn [arachir_the_ancient_one.xml:singlespawn]
- `<announce>` raid broadcast tags (3 messages) [lions.xml:announce]
- `<areaspawn>` monster `Lion` (amount=10) [lions.xml:areaspawn]
- `<areaspawn>` monster `Lion` (amount=5) [lions.xml:areaspawn]
- `<areaspawn>` monster `Zomba` (amount=1) [lions.xml:areaspawn]
- `<announce>` raid broadcast tags (3 messages) [minotaurs.xml:announce]
- `<areaspawn>` monster `Minotaur` (amount=10) [minotaurs.xml:areaspawn]
- `<areaspawn>` monster `Minotaur Guard` (amount=10) [minotaurs.xml:areaspawn]
- `<areaspawn>` monster `Minotaur Mage` (amount=10) [minotaurs.xml:areaspawn]
- `<areaspawn>` monster `Minotaur` (amount=20) [minotaurs.xml:areaspawn]
- `<areaspawn>` monster `Minotaur Guard` (amount=15) [minotaurs.xml:areaspawn]
- `<areaspawn>` monster `Minotaur Mage` (amount=20) [minotaurs.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [necropharus.xml:announce]
- `<singlespawn name="Necropharus">` boss/creature spawn [necropharus.xml:singlespawn]
- `<announce>` raid broadcast tags (1 messages) [pirates.xml:announce]
- `<areaspawn>` monster `Pirate Buccaneer` (amount=20) [pirates.xml:areaspawn]
- `<areaspawn>` monster `Pirate Cutthroat` (amount=15) [pirates.xml:areaspawn]
- `<areaspawn>` monster `Pirate Marauder` (amount=15) [pirates.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [priestesses.xml:announce]
- `<areaspawn>` monster `Priestess` (amount=25) [priestesses.xml:areaspawn]
- `<singlespawn name="The Pale Count">` boss/creature spawn [the_pale_count.xml:singlespawn]
- `<announce>` raid broadcast tags (2 messages) [undead_darashia.xml:announce]
- `<areaspawn>` monster `Vampire` (amount=25) [undead_darashia.xml:areaspawn]
- `<areaspawn>` monster `Stalker` (amount=30) [undead_darashia.xml:areaspawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [arachir_the_ancient_one.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [lions.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [minotaurs.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [necropharus.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [pirates.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [priestesses.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [the_pale_count.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [undead_darashia.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [white_pale.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [arachir_the_ancient_one.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [lions.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [minotaurs.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [necropharus.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [pirates.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [priestesses.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [the_pale_count.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [undead_darashia.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [white_pale.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
