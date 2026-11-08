# Ferumbras Ascension

## Overview
Provides 5 direct files (`damned_soul.lua`..`rage_of_mazoran.lua`) and 4 subdirectories under `monster/quests/ferumbras_ascension`.

## Interface
- `Game.createMonsterType("Damned Soul")` and `mType:register(monster)` [damned_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Desperate Soul")` and `mType:register(monster)` [desperate_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Disgusting Ooze")` and `mType:register(monster)` [disgusting_ooze.lua:Game.createMonsterType]
- `Game.createMonsterType("Ferumbras Essence")` and `mType:register(monster)` [ferumbras_essence.lua:Game.createMonsterType]
- `Game.createMonsterType("Rage of Mazoran")` and `mType:register(monster)` [rage_of_mazoran.lua:Game.createMonsterType]
- [bosses](./bosses/README.md) - Component package under `monster/quests/ferumbras_ascension/bosses` containing 19 files (`ascending_ferumbras.lua`..`zamulosh3.lua`).
- [lovely](./lovely/README.md) - Component package under `monster/quests/ferumbras_ascension/lovely` containing 8 files (`lovely_deer.lua`..`lovely_yielothax.lua`).
- [summons](./summons/README.md) - Component package under `monster/quests/ferumbras_ascension/summons` containing 3 files (`enthralled_demon.lua`..`rift_invader.lua`).
- [traps](./traps/README.md) - Component package under `monster/quests/ferumbras_ascension/traps` containing 6 files (`bone_capsule.lua`..`void.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [damned_soul.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [desperate_soul.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [disgusting_ooze.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ferumbras_essence.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [rage_of_mazoran.lua:monster.flags]

## Side Effects
- Registers monster type `Damned Soul` into the global `Game` engine registry via `mType:register(monster)` [damned_soul.lua:mType:register]
- Registers monster type `Desperate Soul` into the global `Game` engine registry via `mType:register(monster)` [desperate_soul.lua:mType:register]
- Registers monster type `Disgusting Ooze` into the global `Game` engine registry via `mType:register(monster)` [disgusting_ooze.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [disgusting_ooze.lua:monster.events]
- Registers monster type `Ferumbras Essence` into the global `Game` engine registry via `mType:register(monster)` [ferumbras_essence.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [ferumbras_essence.lua:monster.events]
- Registers monster type `Rage of Mazoran` into the global `Game` engine registry via `mType:register(monster)` [rage_of_mazoran.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
