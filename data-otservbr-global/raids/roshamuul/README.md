# Roshamuul

## Overview
Component package under `raids/roshamuul` containing 2 files (`gaz_haragoth.xml`..`omrafir.xml`).

## Interface
- `<announce>` raid broadcast tags (4 messages) [gaz_haragoth.xml:announce]
- `<singlespawn name="Gaz'Haragoth">` boss/creature spawn [gaz_haragoth.xml:singlespawn]
- `<announce>` raid broadcast tags (2 messages) [omrafir.xml:announce]
- `<singlespawn name="Omrafir">` boss/creature spawn [omrafir.xml:singlespawn]

## Invariants
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [gaz_haragoth.xml:raid]
- Spawn coordinates (`x`, `y`, `z` / `fromx`..`toz`) and `delay` timestamps must correspond to valid map tiles and monster names [omrafir.xml:raid]

## Side Effects
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [gaz_haragoth.xml:raid]
- Broadcasts server-wide raid messages and spawns configured monsters when the raid executes [omrafir.xml:raid]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
