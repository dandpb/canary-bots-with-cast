# Ancient Feud

## Overview
Component package under `monster/quests/ancient_feud` containing 4 files (`katex_blood_tongue.lua`..`yirkas_blue_scales.lua`).

## Interface
- `Game.createMonsterType("Katex Blood Tongue")` and `mType:register(monster)` [katex_blood_tongue.lua:Game.createMonsterType]
- `Game.createMonsterType("Srezz Yellow Eyes")` and `mType:register(monster)` [srezz_yellow_eyes.lua:Game.createMonsterType]
- `Game.createMonsterType("Utua Stone Sting")` and `mType:register(monster)` [utua_stone_sting.lua:Game.createMonsterType]
- `Game.createMonsterType("Yirkas Blue Scales")` and `mType:register(monster)` [yirkas_blue_scales.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [katex_blood_tongue.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [srezz_yellow_eyes.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [utua_stone_sting.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [yirkas_blue_scales.lua:monster.flags]

## Side Effects
- Registers monster type `Katex Blood Tongue` into the global `Game` engine registry via `mType:register(monster)` [katex_blood_tongue.lua:mType:register]
- Registers monster type `Srezz Yellow Eyes` into the global `Game` engine registry via `mType:register(monster)` [srezz_yellow_eyes.lua:mType:register]
- Registers monster type `Utua Stone Sting` into the global `Game` engine registry via `mType:register(monster)` [utua_stone_sting.lua:mType:register]
- Registers monster type `Yirkas Blue Scales` into the global `Game` engine registry via `mType:register(monster)` [yirkas_blue_scales.lua:mType:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
