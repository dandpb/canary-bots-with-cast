# Grave Danger

## Overview
Provides 26 direct files (`azarams_soul.lua`..`vampiric_blood.lua`) and 1 subdirectories under `monster/quests/grave_danger`.

## Interface
- Defines 26 script/configuration files (`azarams_soul.lua` through `vampiric_blood.lua`) [azarams_soul.lua]
- Lua script module `azarams_soul.lua` [azarams_soul.lua:module]
- `Game.createMonsterType("Black Cobra")` and `mType:register(monster)` [black_cobra.lua:Game.createMonsterType]
- `Game.createMonsterType("Cart Packed with Gold")` and `mType:register(monster)` [cart_packed_with_gold.lua:Game.createMonsterType]
- `Game.createMonsterType("Condensed Sin")` and `mType:register(monster)` [condensed_sin.lua:Game.createMonsterType]
- `Game.createMonsterType("Condensed Sins")` and `mType:register(monster)` [condensed_sins.lua:Game.createMonsterType]
- `Game.createMonsterType("Dark Druid")` and `mType:register(monster)` [dark_druid.lua:Game.createMonsterType]
- `Game.createMonsterType("Dark Knight")` and `mType:register(monster)` [dark_knight.lua:Game.createMonsterType]
- `Game.createMonsterType("Dark Paladin")` and `mType:register(monster)` [dark_paladin.lua:Game.createMonsterType]
- `Game.createMonsterType("Dark Sorcerer")` and `mType:register(monster)` [dark_sorcerer.lua:Game.createMonsterType]
- `Game.createMonsterType("Fetter")` and `mType:register(monster)` [fetter.lua:Game.createMonsterType]
- `Game.createMonsterType("Frozen Soul")` and `mType:register(monster)` [frozen_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Magical Sphere")` and `mType:register(monster)` [magical_sphere.lua:Game.createMonsterType]
- `Game.createMonsterType("Magnor Mournbringer")` and `mType:register(monster)` [magnor_mournbringer.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [magnor_mournbringer.lua:mType.onThink]
- `mType.onAppear` lifecycle callback [magnor_mournbringer.lua:mType.onAppear]
- `mType.onDisappear` lifecycle callback [magnor_mournbringer.lua:mType.onDisappear]
- `mType.onMove` lifecycle callback [magnor_mournbringer.lua:mType.onMove]
- `mType.onSay` lifecycle callback [magnor_mournbringer.lua:mType.onSay]
- `Game.createMonsterType("Nargol The Impaler")` and `mType:register(monster)` [nargol_the_impaler.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [nargol_the_impaler.lua:mType.onThink]
- `mType.onAppear` lifecycle callback [nargol_the_impaler.lua:mType.onAppear]
- `mType.onDisappear` lifecycle callback [nargol_the_impaler.lua:mType.onDisappear]
- `mType.onMove` lifecycle callback [nargol_the_impaler.lua:mType.onMove]
- `mType.onSay` lifecycle callback [nargol_the_impaler.lua:mType.onSay]
- [bosses](./bosses/README.md) - Component package under `monster/quests/grave_danger/bosses` containing 8 files (`count_vlarkorth.lua`..`sir_nictros.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [black_cobra.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cart_packed_with_gold.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [condensed_sin.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [condensed_sins.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dark_druid.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dark_knight.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dark_paladin.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dark_sorcerer.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [fetter.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [frozen_soul.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [magical_sphere.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [magnor_mournbringer.lua:monster.flags]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [azarams_soul.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [azarams_soul.lua:Game]
- Registers monster type `Black Cobra` into the global `Game` engine registry via `mType:register(monster)` [black_cobra.lua:mType:register]
- Registers monster type `Cart Packed with Gold` into the global `Game` engine registry via `mType:register(monster)` [cart_packed_with_gold.lua:mType:register]
- Registers monster type `Condensed Sin` into the global `Game` engine registry via `mType:register(monster)` [condensed_sin.lua:mType:register]
- Registers monster type `Condensed Sins` into the global `Game` engine registry via `mType:register(monster)` [condensed_sins.lua:mType:register]
- Registers monster type `Dark Druid` into the global `Game` engine registry via `mType:register(monster)` [dark_druid.lua:mType:register]
- Registers monster type `Dark Knight` into the global `Game` engine registry via `mType:register(monster)` [dark_knight.lua:mType:register]
- Registers monster type `Dark Paladin` into the global `Game` engine registry via `mType:register(monster)` [dark_paladin.lua:mType:register]
- Registers monster type `Dark Sorcerer` into the global `Game` engine registry via `mType:register(monster)` [dark_sorcerer.lua:mType:register]
- Registers monster type `Fetter` into the global `Game` engine registry via `mType:register(monster)` [fetter.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [fetter.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
