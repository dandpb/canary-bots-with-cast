# Bosses

## Overview
Component package under `monster/bosses` containing 94 files (`alchemist_container.lua`..`zushuka.lua`).

## Interface
- Defines 94 script/configuration files (`alchemist_container.lua` through `zushuka.lua`) [alchemist_container.lua]
- `Game.createMonsterType("Alchemist Container")` and `mType:register(monster)` [alchemist_container.lua:Game.createMonsterType]
- `Game.createMonsterType("Antenna")` and `mType:register(monster)` [antenna.lua:Game.createMonsterType]
- `Game.createMonsterType("Apocalypse")` and `mType:register(monster)` [apocalypse.lua:Game.createMonsterType]
- `Game.createMonsterType("Apprentice Sheng")` and `mType:register(monster)` [apprentice_sheng.lua:Game.createMonsterType]
- `Game.createMonsterType("Armenius (Creature)")` and `mType:register(monster)` [armenius.lua:Game.createMonsterType]
- `Game.createMonsterType("Bakragore")` and `mType:register(monster)` [bakragore.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [bakragore.lua:mType.onThink]
- `mType.onAppear` lifecycle callback [bakragore.lua:mType.onAppear]
- `mType.onDisappear` lifecycle callback [bakragore.lua:mType.onDisappear]
- `mType.onMove` lifecycle callback [bakragore.lua:mType.onMove]
- `mType.onSay` lifecycle callback [bakragore.lua:mType.onSay]
- `Game.createMonsterType("Bazir")` and `mType:register(monster)` [bazir.lua:Game.createMonsterType]
- `Game.createMonsterType("Bibby Bloodbath")` and `mType:register(monster)` [bibby_bloodbath.lua:Game.createMonsterType]
- `Game.createMonsterType("Big Boss Trolliver")` and `mType:register(monster)` [big_boss_trolliver.lua:Game.createMonsterType]
- `Game.createMonsterType("Black Knight")` and `mType:register(monster)` [black_knight.lua:Game.createMonsterType]
- `Game.createMonsterType("Brain Head")` and `mType:register(monster)` [brain_head.lua:Game.createMonsterType]
- `Game.createMonsterType("Brain Parasite")` and `mType:register(monster)` [brain_parasite.lua:Game.createMonsterType]
- `Game.createMonsterType("Bullwark")` and `mType:register(monster)` [bullwark.lua:Game.createMonsterType]
- `Game.createMonsterType("Cerebellum")` and `mType:register(monster)` [cerebellum.lua:Game.createMonsterType]
- `Game.createMonsterType("Chagorz")` and `mType:register(monster)` [chagorz.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [chagorz.lua:mType.onThink]
- `mType.onAppear` lifecycle callback [chagorz.lua:mType.onAppear]
- `mType.onDisappear` lifecycle callback [chagorz.lua:mType.onDisappear]
- `mType.onMove` lifecycle callback [chagorz.lua:mType.onMove]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [alchemist_container.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [antenna.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [apocalypse.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [apprentice_sheng.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [armenius.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bakragore.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bazir.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bibby_bloodbath.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [big_boss_trolliver.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [black_knight.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [brain_head.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [brain_parasite.lua:monster.flags]

## Side Effects
- Registers monster type `Alchemist Container` into the global `Game` engine registry via `mType:register(monster)` [alchemist_container.lua:mType:register]
- Registers monster type `Antenna` into the global `Game` engine registry via `mType:register(monster)` [antenna.lua:mType:register]
- Registers monster type `Apocalypse` into the global `Game` engine registry via `mType:register(monster)` [apocalypse.lua:mType:register]
- Registers monster type `Apprentice Sheng` into the global `Game` engine registry via `mType:register(monster)` [apprentice_sheng.lua:mType:register]
- Registers monster type `Armenius (Creature)` into the global `Game` engine registry via `mType:register(monster)` [armenius.lua:mType:register]
- Registers monster type `Bakragore` into the global `Game` engine registry via `mType:register(monster)` [bakragore.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [bakragore.lua:monster.events]
- Registers monster type `Bazir` into the global `Game` engine registry via `mType:register(monster)` [bazir.lua:mType:register]
- Registers monster type `Bibby Bloodbath` into the global `Game` engine registry via `mType:register(monster)` [bibby_bloodbath.lua:mType:register]
- Registers monster type `Big Boss Trolliver` into the global `Game` engine registry via `mType:register(monster)` [big_boss_trolliver.lua:mType:register]
- Registers monster type `Black Knight` into the global `Game` engine registry via `mType:register(monster)` [black_knight.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [black_knight.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
