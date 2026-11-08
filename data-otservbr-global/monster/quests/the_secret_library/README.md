# The Secret Library

## Overview
Provides 47 direct files (`biting_cold.lua`..`yalahari_despoiler.lua`) and 1 subdirectories under `monster/quests/the_secret_library`.

## Interface
- Defines 47 script/configuration files (`biting_cold.lua` through `yalahari_despoiler.lua`) [biting_cold.lua]
- `Game.createMonsterType("Biting Cold")` and `mType:register(monster)` [biting_cold.lua:Game.createMonsterType]
- `Game.createMonsterType("Bone Jaw")` and `mType:register(monster)` [bone_jaw.lua:Game.createMonsterType]
- `Game.createMonsterType("Brother Chill")` and `mType:register(monster)` [brother_chill.lua:Game.createMonsterType]
- `Game.createMonsterType("Brother Freeze")` and `mType:register(monster)` [brother_freeze.lua:Game.createMonsterType]
- `Game.createMonsterType("Concentrated Death")` and `mType:register(monster)` [concentrated_death.lua:Game.createMonsterType]
- `Game.createMonsterType("Dark Knowledge")` and `mType:register(monster)` [dark_knowledge.lua:Game.createMonsterType]
- `Game.createMonsterType("Dazed Leaf Golem")` and `mType:register(monster)` [dazed_leaf_golem.lua:Game.createMonsterType]
- `Game.createMonsterType("Demon Blood")` and `mType:register(monster)` [demon_blood.lua:Game.createMonsterType]
- `Game.createMonsterType("Demon Slave")` and `mType:register(monster)` [demon_slave.lua:Game.createMonsterType]
- `Game.createMonsterType("Force Field")` and `mType:register(monster)` [force_field.lua:Game.createMonsterType]
- `Game.createMonsterType("Furious Scorpion")` and `mType:register(monster)` [furious_scorpion.lua:Game.createMonsterType]
- Lua script module `ghulosh'_deathgaze.lua` [ghulosh'_deathgaze.lua:module]
- `Game.createMonsterType("Imp Intruder")` and `mType:register(monster)` [imp_intruder.lua:Game.createMonsterType]
- `Game.createMonsterType("Invading Demon")` and `mType:register(monster)` [invading_demon.lua:Game.createMonsterType]
- `Game.createMonsterType("Jailer")` and `mType:register(monster)` [jailer.lua:Game.createMonsterType]
- `Game.createMonsterType("Knowledge Raider")` and `mType:register(monster)` [knowledge_raider.lua:Game.createMonsterType]
- `Game.createMonsterType("Librarian")` and `mType:register(monster)` [librarian.lua:Game.createMonsterType]
- `Game.createMonsterType("Lokathmor Stuck")` and `mType:register(monster)` [lokathmor_stuck.lua:Game.createMonsterType]
- `Game.createMonsterType("Malicious Minion")` and `mType:register(monster)` [malicious_minion.lua:Game.createMonsterType]
- `Game.createMonsterType("Mean Minion")` and `mType:register(monster)` [mean_minion.lua:Game.createMonsterType]
- `Game.createMonsterType("Neutral Deepling Warrior")` and `mType:register(monster)` [neutral_deepling_warrior.lua:Game.createMonsterType]
- Lua script module `oberons_bile.lua` [oberons_bile.lua:module]
- Lua script module `oberons_hate.lua` [oberons_hate.lua:module]
- Lua script module `oberons_ire.lua` [oberons_ire.lua:module]
- [bosses](./bosses/README.md) - Component package under `monster/quests/the_secret_library/bosses` containing 13 files (`brokul.lua`..`the_scourge_of_oblivion.lua`).

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [biting_cold.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [bone_jaw.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [brother_chill.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [brother_freeze.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [concentrated_death.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dark_knowledge.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [dazed_leaf_golem.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [demon_blood.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [demon_slave.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [force_field.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [furious_scorpion.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [imp_intruder.lua:monster.flags]

## Side Effects
- Registers monster type `Biting Cold` into the global `Game` engine registry via `mType:register(monster)` [biting_cold.lua:mType:register]
- Registers monster type `Bone Jaw` into the global `Game` engine registry via `mType:register(monster)` [bone_jaw.lua:mType:register]
- Registers monster type `Brother Chill` into the global `Game` engine registry via `mType:register(monster)` [brother_chill.lua:mType:register]
- Registers monster type `Brother Freeze` into the global `Game` engine registry via `mType:register(monster)` [brother_freeze.lua:mType:register]
- Registers monster type `Concentrated Death` into the global `Game` engine registry via `mType:register(monster)` [concentrated_death.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [concentrated_death.lua:monster.events]
- Registers monster type `Dark Knowledge` into the global `Game` engine registry via `mType:register(monster)` [dark_knowledge.lua:mType:register]
- Registers monster type `Dazed Leaf Golem` into the global `Game` engine registry via `mType:register(monster)` [dazed_leaf_golem.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [dazed_leaf_golem.lua:monster.events]
- Registers monster type `Demon Blood` into the global `Game` engine registry via `mType:register(monster)` [demon_blood.lua:mType:register]
- Registers monster type `Demon Slave` into the global `Game` engine registry via `mType:register(monster)` [demon_slave.lua:mType:register]
- Registers monster type `Force Field` into the global `Game` engine registry via `mType:register(monster)` [force_field.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
