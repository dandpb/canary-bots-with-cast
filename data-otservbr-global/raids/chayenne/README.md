# Chayenne

## Overview
Component package under `raids/chayenne` containing 1 files (`chayenne.xml`..`chayenne.xml`).

## Interface
- `<announce>` raid broadcast tags (3 messages) [chayenne.xml:announce]
- `<singlespawn name="Chayenne">` boss/creature spawn [chayenne.xml:singlespawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [chayenne.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [chayenne.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
