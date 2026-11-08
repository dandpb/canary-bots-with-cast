# Burning Hatred

## Overview
Component package under `monster/quests/soul_war/normal_monsters/burning_hatred` containing 5 files (`ashes_of_burning_hatred.lua`..`symbol_of_hatred.lua`).

## Interface
- `Game.createMonsterType("Ashes of Burning Hatred")` and `mType:register(monster)` [ashes_of_burning_hatred.lua:Game.createMonsterType]
- `Game.createMonsterType("Blaze of Burning Hatred")` and `mType:register(monster)` [blaze_of_burning_hatred.lua:Game.createMonsterType]
- `Game.createMonsterType("Flame of Burning Hatred")` and `mType:register(monster)` [flame_of_burning_hatred.lua:Game.createMonsterType]
- `Game.createMonsterType("Spark of Burning Hatred")` and `mType:register(monster)` [spark_of_burning_hatred.lua:Game.createMonsterType]
- `Game.createMonsterType("Symbol of Hatred")` and `mType:register(monster)` [symbol_of_hatred.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [symbol_of_hatred.lua:mType.onThink]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ashes_of_burning_hatred.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [blaze_of_burning_hatred.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [flame_of_burning_hatred.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [spark_of_burning_hatred.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [symbol_of_hatred.lua:monster.flags]

## Side Effects
- Registers monster type `Ashes of Burning Hatred` into the global `Game` engine registry via `mType:register(monster)` [ashes_of_burning_hatred.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [ashes_of_burning_hatred.lua:monster.events]
- Registers monster type `Blaze of Burning Hatred` into the global `Game` engine registry via `mType:register(monster)` [blaze_of_burning_hatred.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [blaze_of_burning_hatred.lua:monster.events]
- Registers monster type `Flame of Burning Hatred` into the global `Game` engine registry via `mType:register(monster)` [flame_of_burning_hatred.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [flame_of_burning_hatred.lua:monster.events]
- Registers monster type `Spark of Burning Hatred` into the global `Game` engine registry via `mType:register(monster)` [spark_of_burning_hatred.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [spark_of_burning_hatred.lua:monster.events]
- Registers monster type `Symbol of Hatred` into the global `Game` engine registry via `mType:register(monster)` [symbol_of_hatred.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
