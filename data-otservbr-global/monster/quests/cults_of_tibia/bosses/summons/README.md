# Summons

## Overview
Component package under `monster/quests/cults_of_tibia/bosses/summons` containing 13 files (`dark_soul.lua`..`voidshard.lua`).

## Interface
- `Game.createMonsterType("Dark Soul")` and `mType:register(monster)` [dark_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Dread Minion")` and `mType:register(monster)` [dread_minion.lua:Game.createMonsterType]
- `Game.createMonsterType("Enraged Sand Brood")` and `mType:register(monster)` [enraged_sand_brood.lua:Game.createMonsterType]
- `Game.createMonsterType("Freed Soul")` and `mType:register(monster)` [freed_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Liquor Spirit")` and `mType:register(monster)` [liquor_spirit.lua:Game.createMonsterType]
- `Game.createMonsterType("Sand Brood")` and `mType:register(monster)` [sand_brood.lua:Game.createMonsterType]
- `Game.createMonsterType("Sand Vortex")` and `mType:register(monster)` [sand_vortex.lua:Game.createMonsterType]
- `Game.createMonsterType("Security Golem")` and `mType:register(monster)` [security_golem.lua:Game.createMonsterType]
- `Game.createMonsterType("Soul Reaper")` and `mType:register(monster)` [soul_reaper.lua:Game.createMonsterType]
- `Game.createMonsterType("Sphere of Wrath")` and `mType:register(monster)` [sphere_of_wrath.lua:Game.createMonsterType]
- `Game.createMonsterType("Stolen Soul")` and `mType:register(monster)` [stolen_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Vermin Swarm")` and `mType:register(monster)` [vermin_swarm.lua:Game.createMonsterType]
- `Game.createMonsterType("Voidshard")` and `mType:register(monster)` [voidshard.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dark_soul.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dread_minion.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [enraged_sand_brood.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [freed_soul.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [liquor_spirit.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [sand_brood.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [sand_vortex.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [security_golem.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [soul_reaper.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [sphere_of_wrath.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [stolen_soul.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [vermin_swarm.lua:monster.flags]

## Side Effects
- Registers monster type `Dark Soul` into the global `Game` engine registry via `mType:register(monster)` [dark_soul.lua:mType:register]
- Registers monster type `Dread Minion` into the global `Game` engine registry via `mType:register(monster)` [dread_minion.lua:mType:register]
- Registers monster type `Enraged Sand Brood` into the global `Game` engine registry via `mType:register(monster)` [enraged_sand_brood.lua:mType:register]
- Registers monster type `Freed Soul` into the global `Game` engine registry via `mType:register(monster)` [freed_soul.lua:mType:register]
- Registers monster type `Liquor Spirit` into the global `Game` engine registry via `mType:register(monster)` [liquor_spirit.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [liquor_spirit.lua:monster.events]
- Registers monster type `Sand Brood` into the global `Game` engine registry via `mType:register(monster)` [sand_brood.lua:mType:register]
- Registers monster type `Sand Vortex` into the global `Game` engine registry via `mType:register(monster)` [sand_vortex.lua:mType:register]
- Registers monster type `Security Golem` into the global `Game` engine registry via `mType:register(monster)` [security_golem.lua:mType:register]
- Registers monster type `Soul Reaper` into the global `Game` engine registry via `mType:register(monster)` [soul_reaper.lua:mType:register]
- Registers monster type `Sphere of Wrath` into the global `Game` engine registry via `mType:register(monster)` [sphere_of_wrath.lua:mType:register]
- Registers monster type `Stolen Soul` into the global `Game` engine registry via `mType:register(monster)` [stolen_soul.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
