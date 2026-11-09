# Fey

## Overview
Component package under `monster/fey` containing 19 files (`angry_sugar_fairy.lua`..`wisp.lua`).

## Interface
- `Game.createMonsterType("Angry Sugar Fairy")` and `mType:register(monster)` [angry_sugar_fairy.lua:Game.createMonsterType]
- `Game.createMonsterType("Arctic Faun")` and `mType:register(monster)` [arctic_faun.lua:Game.createMonsterType]
- `Game.createMonsterType("Boogy")` and `mType:register(monster)` [boogy.lua:Game.createMonsterType]
- `Game.createMonsterType("Cream Blob")` and `mType:register(monster)` [cream_blob.lua:Game.createMonsterType]
- `Game.createMonsterType("Dark Faun")` and `mType:register(monster)` [dark_faun.lua:Game.createMonsterType]
- `Game.createMonsterType("Dryad")` and `mType:register(monster)` [dryad.lua:Game.createMonsterType]
- `Game.createMonsterType("Faun")` and `mType:register(monster)` [faun.lua:Game.createMonsterType]
- `Game.createMonsterType("Fruit Drop")` and `mType:register(monster)` [fruit_drop.lua:Game.createMonsterType]
- `Game.createMonsterType("Nymph")` and `mType:register(monster)` [nymph.lua:Game.createMonsterType]
- `Game.createMonsterType("Pixie")` and `mType:register(monster)` [pixie.lua:Game.createMonsterType]
- `Game.createMonsterType("Pooka")` and `mType:register(monster)` [pooka.lua:Game.createMonsterType]
- `Game.createMonsterType("Sugar Cube")` and `mType:register(monster)` [sugar_cube.lua:Game.createMonsterType]
- `Game.createMonsterType("Sugar Cube Worker")` and `mType:register(monster)` [sugar_cube_worker.lua:Game.createMonsterType]
- `Game.createMonsterType("Swan Maiden")` and `mType:register(monster)` [swan_maiden.lua:Game.createMonsterType]
- `Game.createMonsterType("Tainted Soul")` and `mType:register(monster)` [tainted_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Truffle")` and `mType:register(monster)` [truffle.lua:Game.createMonsterType]
- `Game.createMonsterType("Truffle Cook")` and `mType:register(monster)` [truffle_cook.lua:Game.createMonsterType]
- `Game.createMonsterType("Twisted Pooka")` and `mType:register(monster)` [twisted_pooka.lua:Game.createMonsterType]
- `Game.createMonsterType("Wisp")` and `mType:register(monster)` [wisp.lua:Game.createMonsterType]

## Invariants
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [angry_sugar_fairy.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [angry_sugar_fairy.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [arctic_faun.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [arctic_faun.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [boogy.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [boogy.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [cream_blob.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cream_blob.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [dark_faun.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dark_faun.lua:monster.flags]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [dryad.lua:monster.Bestiary]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dryad.lua:monster.flags]

## Side Effects
- Registers monster type `Angry Sugar Fairy` into the global `Game` engine registry via `mType:register(monster)` [angry_sugar_fairy.lua:mType:register]
- Registers monster type `Arctic Faun` into the global `Game` engine registry via `mType:register(monster)` [arctic_faun.lua:mType:register]
- Registers monster type `Boogy` into the global `Game` engine registry via `mType:register(monster)` [boogy.lua:mType:register]
- Registers monster type `Cream Blob` into the global `Game` engine registry via `mType:register(monster)` [cream_blob.lua:mType:register]
- Registers monster type `Dark Faun` into the global `Game` engine registry via `mType:register(monster)` [dark_faun.lua:mType:register]
- Registers monster type `Dryad` into the global `Game` engine registry via `mType:register(monster)` [dryad.lua:mType:register]
- Registers monster type `Faun` into the global `Game` engine registry via `mType:register(monster)` [faun.lua:mType:register]
- Registers monster type `Fruit Drop` into the global `Game` engine registry via `mType:register(monster)` [fruit_drop.lua:mType:register]
- Registers monster type `Nymph` into the global `Game` engine registry via `mType:register(monster)` [nymph.lua:mType:register]
- Registers monster type `Pixie` into the global `Game` engine registry via `mType:register(monster)` [pixie.lua:mType:register]
- Registers monster type `Pooka` into the global `Game` engine registry via `mType:register(monster)` [pooka.lua:mType:register]
- Registers monster type `Sugar Cube` into the global `Game` engine registry via `mType:register(monster)` [sugar_cube.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
