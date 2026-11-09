# Carlin

## Overview
Component package under `raids/carlin` containing 2 files (`orc.xml`..`yeti.xml`).

## Interface
- `<announce>` raid broadcast tags (2 messages) [orc.xml:announce]
- `<areaspawn>` monster `Orc` (amount=50) [orc.xml:areaspawn]
- `<areaspawn>` monster `Orc Berserker` (amount=20) [orc.xml:areaspawn]
- `<areaspawn>` monster `Orc Leader` (amount=15) [orc.xml:areaspawn]
- `<areaspawn>` monster `Orc Shaman` (amount=15) [orc.xml:areaspawn]
- `<announce>` raid broadcast tags (3 messages) [yeti.xml:announce]
- `<areaspawn>` monster `Yeti` (amount=60) [yeti.xml:areaspawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [orc.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [yeti.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [orc.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [yeti.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
