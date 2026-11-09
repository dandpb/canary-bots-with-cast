# Fury Gate

## Overview
Component package under `raids/fury_gate` containing 1 files (`furyosa.xml`..`furyosa.xml`).

## Interface
- `<singlespawn name="Furyosa">` boss/creature spawn [furyosa.xml:singlespawn]
- `<areaspawn>` monster `Demon` (amount=30) [furyosa.xml:areaspawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [furyosa.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [furyosa.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
