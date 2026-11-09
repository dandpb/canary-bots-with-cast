# Forgotten Knowledge

## Overview
Provides 31 direct files (`animated_sword.lua`..`unbound_demon_outcast.lua`) and 1 subdirectories under `monster/quests/forgotten_knowledge`.

## Interface
- Defines 31 script/configuration files (`animated_sword.lua` through `unbound_demon_outcast.lua`) [animated_sword.lua]
- `Game.createMonsterType("Animated Sword")` and `mType:register(monster)` [animated_sword.lua:Game.createMonsterType]
- `Game.createMonsterType("Baby Dragon")` and `mType:register(monster)` [baby_dragon.lua:Game.createMonsterType]
- `Game.createMonsterType("Bound Astral Power")` and `mType:register(monster)` [bound_astral_power.lua:Game.createMonsterType]
- `Game.createMonsterType("Corrupted Soul")` and `mType:register(monster)` [corrupted_soul.lua:Game.createMonsterType]
- `Game.createMonsterType("Cosmic Energy Prism A")` and `mType:register(monster)` [cosmic_energy_prism_a.lua:Game.createMonsterType]
- `Game.createMonsterType("Cosmic Energy Prism A Invu")` and `mType:register(monster)` [cosmic_energy_prism_a_invu.lua:Game.createMonsterType]
- `Game.createMonsterType("Cosmic Energy Prism B")` and `mType:register(monster)` [cosmic_energy_prism_b.lua:Game.createMonsterType]
- `Game.createMonsterType("Cosmic Energy Prism B Invu")` and `mType:register(monster)` [cosmic_energy_prism_b_invu.lua:Game.createMonsterType]
- `Game.createMonsterType("Cosmic Energy Prism C")` and `mType:register(monster)` [cosmic_energy_prism_c.lua:Game.createMonsterType]
- `Game.createMonsterType("Cosmic Energy Prism C Invu")` and `mType:register(monster)` [cosmic_energy_prism_c_invu.lua:Game.createMonsterType]
- `Game.createMonsterType("Cosmic Energy Prism D")` and `mType:register(monster)` [cosmic_energy_prism_d.lua:Game.createMonsterType]
- `Game.createMonsterType("Cosmic Energy Prism D Invu")` and `mType:register(monster)` [cosmic_energy_prism_d_invu.lua:Game.createMonsterType]
- `Game.createMonsterType("Dragon Egg")` and `mType:register(monster)` [dragon_egg.lua:Game.createMonsterType]
- `Game.createMonsterType("Dragon Servant")` and `mType:register(monster)` [dragon_servant.lua:Game.createMonsterType]
- `Game.createMonsterType("Frozen Man")` and `mType:register(monster)` [frozen_man.lua:Game.createMonsterType]
- `Game.createMonsterType("Frozen Minion")` and `mType:register(monster)` [frozen_minion.lua:Game.createMonsterType]
- `Game.createMonsterType("Icicle")` and `mType:register(monster)` [icicle.lua:Game.createMonsterType]
- `Game.createMonsterType("Lost Time")` and `mType:register(monster)` [lost_time.lua:Game.createMonsterType]
- `Game.createMonsterType("Possessed Tree")` and `mType:register(monster)` [possessed_tree.lua:Game.createMonsterType]
- `Game.createMonsterType("Shadow Fiend")` and `mType:register(monster)` [shadow_fiend.lua:Game.createMonsterType]
- `Game.createMonsterType("Shadow Tentacle")` and `mType:register(monster)` [shadow_tentacle.lua:Game.createMonsterType]
- `Game.createMonsterType("Soulcatcher")` and `mType:register(monster)` [soulcatcher.lua:Game.createMonsterType]
- `Game.createMonsterType("Sword of Vengeance")` and `mType:register(monster)` [sword_of_vengeance.lua:Game.createMonsterType]
- `Game.createMonsterType("The Distorted Astral Source")` and `mType:register(monster)` [the_distorted_astral_source.lua:Game.createMonsterType]
- [bosses](./bosses/README.md) - Component package under `monster/quests/forgotten_knowledge/bosses` containing 14 files (`dragonking_zyrtarch.lua`..`thorn_steed.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [animated_sword.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [baby_dragon.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bound_astral_power.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [corrupted_soul.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cosmic_energy_prism_a.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cosmic_energy_prism_a_invu.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cosmic_energy_prism_b.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cosmic_energy_prism_b_invu.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cosmic_energy_prism_c.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cosmic_energy_prism_c_invu.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cosmic_energy_prism_d.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [cosmic_energy_prism_d_invu.lua:monster.flags]

## Side Effects
- Registers monster type `Animated Sword` into the global `Game` engine registry via `mType:register(monster)` [animated_sword.lua:mType:register]
- Registers monster type `Baby Dragon` into the global `Game` engine registry via `mType:register(monster)` [baby_dragon.lua:mType:register]
- Registers monster type `Bound Astral Power` into the global `Game` engine registry via `mType:register(monster)` [bound_astral_power.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [bound_astral_power.lua:monster.events]
- Registers monster type `Corrupted Soul` into the global `Game` engine registry via `mType:register(monster)` [corrupted_soul.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [corrupted_soul.lua:monster.events]
- Registers monster type `Cosmic Energy Prism A` into the global `Game` engine registry via `mType:register(monster)` [cosmic_energy_prism_a.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [cosmic_energy_prism_a.lua:monster.events]
- Registers monster type `Cosmic Energy Prism A Invu` into the global `Game` engine registry via `mType:register(monster)` [cosmic_energy_prism_a_invu.lua:mType:register]
- Registers monster type `Cosmic Energy Prism B` into the global `Game` engine registry via `mType:register(monster)` [cosmic_energy_prism_b.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [cosmic_energy_prism_b.lua:monster.events]
- Registers monster type `Cosmic Energy Prism B Invu` into the global `Game` engine registry via `mType:register(monster)` [cosmic_energy_prism_b_invu.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
