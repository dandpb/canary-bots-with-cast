# Traps

## Overview
Component package under `monster/quests/ferumbras_ascension/traps` containing 6 files (`bone_capsule.lua`..`void.lua`).

## Interface
- `Game.createMonsterType("Bone Capsule")` and `mType:register(monster)` [bone_capsule.lua:Game.createMonsterType]
- `Game.createMonsterType("Despair")` and `mType:register(monster)` [despair.lua:Game.createMonsterType]
- `Game.createMonsterType("Electric Sparks")` and `mType:register(monster)` [electric_sparks.lua:Game.createMonsterType]
- `Game.createMonsterType("Eruption of Destruction")` and `mType:register(monster)` [eruption_of_destruction.lua:Game.createMonsterType]
- `Game.createMonsterType("Guilt")` and `mType:register(monster)` [guilt.lua:Game.createMonsterType]
- `Game.createMonsterType("Void")` and `mType:register(monster)` [void.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bone_capsule.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [despair.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [electric_sparks.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [eruption_of_destruction.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [guilt.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [void.lua:monster.flags]

## Side Effects
- Registers monster type `Bone Capsule` into the global `Game` engine registry via `mType:register(monster)` [bone_capsule.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [bone_capsule.lua:monster.events]
- Registers monster type `Despair` into the global `Game` engine registry via `mType:register(monster)` [despair.lua:mType:register]
- Registers monster type `Electric Sparks` into the global `Game` engine registry via `mType:register(monster)` [electric_sparks.lua:mType:register]
- Registers monster type `Eruption of Destruction` into the global `Game` engine registry via `mType:register(monster)` [eruption_of_destruction.lua:mType:register]
- Registers monster type `Guilt` into the global `Game` engine registry via `mType:register(monster)` [guilt.lua:mType:register]
- Registers monster type `Void` into the global `Game` engine registry via `mType:register(monster)` [void.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
