# Ankrahmun

## Overview
Component package under `raids/ankrahmun` containing 6 files (`bone_beast.xml`..`terramite.xml`).

## Interface
- `<announce>` raid broadcast tags (2 messages) [bone_beast.xml:announce]
- `<areaspawn>` monster `Bonebeast` (amount=15) [bone_beast.xml:areaspawn]
- `<announce>` raid broadcast tags (3 messages) [cobra.xml:announce]
- `<areaspawn>` monster `Cobra` (amount=25) [cobra.xml:areaspawn]
- `<announce>` raid broadcast tags (2 messages) [gargoyle.xml:announce]
- `<areaspawn>` monster `Gargoyle` (amount=15) [gargoyle.xml:areaspawn]
- `<announce>` raid broadcast tags (2 messages) [nomad.xml:announce]
- `<areaspawn>` monster `Nomad` (amount=160) [nomad.xml:areaspawn]
- `<announce>` raid broadcast tags (2 messages) [scarab.xml:announce]
- `<areaspawn>` monster `Larva` (amount=50) [scarab.xml:areaspawn]
- `<areaspawn>` monster `Scarab` (amount=30) [scarab.xml:areaspawn]
- `<areaspawn>` monster `Ancient Scarab` (amount=16) [scarab.xml:areaspawn]
- `<announce>` raid broadcast tags (2 messages) [terramite.xml:announce]
- `<areaspawn>` monster `Terramite` (amount=30) [terramite.xml:areaspawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [bone_beast.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [cobra.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [gargoyle.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [nomad.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [scarab.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [terramite.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [bone_beast.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [cobra.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [gargoyle.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [nomad.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [scarab.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [terramite.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
