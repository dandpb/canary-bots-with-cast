# Liberty Bay

## Overview
Component package under `raids/liberty_bay` containing 10 files (`crustacea_gigantica_1.xml`..`undead_cavebear.xml`).

## Interface
- `<areaspawn>` monster `Crustacea Gigantica` (amount=1) [crustacea_gigantica_1.xml:areaspawn]
- `<areaspawn>` monster `Crustacea Gigantica` (amount=1) [crustacea_gigantica_2.xml:areaspawn]
- `<areaspawn>` monster `Crustacea Gigantica` (amount=1) [crustacea_gigantica_3.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [diblis_the_fair.xml:announce]
- `<singlespawn name="Diblis The Fair">` boss/creature spawn [diblis_the_fair.xml:singlespawn]
- `<announce>` raid broadcast tags (3 messages) [ferumbras.xml:announce]
- `<singlespawn name="Ferumbras">` boss/creature spawn [ferumbras.xml:singlespawn]
- `<announce>` raid broadcast tags (3 messages) [morgaroth.xml:announce]
- `<singlespawn name="Morgaroth">` boss/creature spawn [morgaroth.xml:singlespawn]
- `<announce>` raid broadcast tags (3 messages) [quaras.xml:announce]
- `<areaspawn>` monster `Quara Mantassin Scout` (amount=12) [quaras.xml:areaspawn]
- `<areaspawn>` monster `Quara Constrictor Scout` (amount=12) [quaras.xml:areaspawn]
- `<areaspawn>` monster `Quara Hydromancer Scout` (amount=12) [quaras.xml:areaspawn]
- `<areaspawn>` monster `Quara Pincher Scout` (amount=12) [quaras.xml:areaspawn]
- `<areaspawn>` monster `Quara Predator Scout` (amount=10) [quaras.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [tigers.xml:announce]
- `<areaspawn>` monster `Tiger` (amount=30) [tigers.xml:areaspawn]
- `<announce>` raid broadcast tags (1 messages) [tortoises.xml:announce]
- `<areaspawn>` monster `Tortoise` (amount=30) [tortoises.xml:areaspawn]
- `<areaspawn>` monster `Undead Cavebear` (amount=3) [undead_cavebear.xml:areaspawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [crustacea_gigantica_1.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [crustacea_gigantica_2.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [crustacea_gigantica_3.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [diblis_the_fair.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [ferumbras.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [morgaroth.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [quaras.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [tigers.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [tortoises.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [undead_cavebear.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [crustacea_gigantica_1.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [crustacea_gigantica_2.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [crustacea_gigantica_3.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [diblis_the_fair.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [ferumbras.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [morgaroth.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [quaras.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [tigers.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [tortoises.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [undead_cavebear.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
