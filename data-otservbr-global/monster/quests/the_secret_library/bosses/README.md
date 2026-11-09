# Bosses

## Overview
Component package under `monster/quests/the_secret_library/bosses` containing 13 files (`brokul.lua`..`the_scourge_of_oblivion.lua`).

## Interface
- `Game.createMonsterType("Brokul")` and `mType:register(monster)` [brokul.lua:Game.createMonsterType]
- `Game.createMonsterType("Ghulosh")` and `mType:register(monster)` [ghulosh.lua:Game.createMonsterType]
- `Game.createMonsterType("Gorzindel")` and `mType:register(monster)` [gorzindel.lua:Game.createMonsterType]
- `Game.createMonsterType("Grand Canon Dominus")` and `mType:register(monster)` [grand_canon_dominus.lua:Game.createMonsterType]
- `Game.createMonsterType("Grand Chaplain Gaunder")` and `mType:register(monster)` [grand_chaplain_gaunder.lua:Game.createMonsterType]
- `Game.createMonsterType("Grand Commander Soeren")` and `mType:register(monster)` [grand_commander_soeren.lua:Game.createMonsterType]
- `Game.createMonsterType("Grand Master Oberon")` and `mType:register(monster)` [grand_master_oberon.lua:Game.createMonsterType]
- `mType.onThink` lifecycle callback [grand_master_oberon.lua:mType.onThink]
- `mType.onSay` lifecycle callback [grand_master_oberon.lua:mType.onSay]
- `healOberon(monster)` [grand_master_oberon_functions.lua:healOberon]
- `SendOberonAsking(monster)` [grand_master_oberon_functions.lua:SendOberonAsking]
- Global symbol `GrandMasterOberonAsking` [grand_master_oberon_functions.lua:GrandMasterOberonAsking]
- Global symbol `GrandMasterOberonResponses` [grand_master_oberon_functions.lua:GrandMasterOberonResponses]
- Global symbol `GrandMasterOberonConfig` [grand_master_oberon_functions.lua:GrandMasterOberonConfig]
- `Game.createMonsterType("Lokathmor")` and `mType:register(monster)` [lokathmor.lua:Game.createMonsterType]
- `Game.createMonsterType("Mazzinor")` and `mType:register(monster)` [mazzinor.lua:Game.createMonsterType]
- `Game.createMonsterType("Preceptor Lazare")` and `mType:register(monster)` [preceptor_lazare.lua:Game.createMonsterType]
- `Game.createMonsterType("Thawing Dragon Lord")` and `mType:register(monster)` [thawing_dragon_lord.lua:Game.createMonsterType]
- `Game.createMonsterType("The Scourge of Oblivion")` and `mType:register(monster)` [the_scourge_of_oblivion.lua:Game.createMonsterType]

## Invariants
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [brokul.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [ghulosh.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [gorzindel.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [grand_canon_dominus.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [grand_chaplain_gaunder.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [grand_commander_soeren.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [grand_master_oberon.lua:monster.flags]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [grand_master_oberon_functions.lua:getStorageValue]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [lokathmor.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [mazzinor.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [preceptor_lazare.lua:monster.flags]
- Combat and movement behavior is bounded by `monster.flags`, `monster.health`, `monster.elements`, and `monster.immunities` [thawing_dragon_lord.lua:monster.flags]

## Side Effects
- Registers monster type `Brokul` into the global `Game` engine registry via `mType:register(monster)` [brokul.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [brokul.lua:monster.events]
- Registers monster type `Ghulosh` into the global `Game` engine registry via `mType:register(monster)` [ghulosh.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [ghulosh.lua:monster.events]
- Registers monster type `Gorzindel` into the global `Game` engine registry via `mType:register(monster)` [gorzindel.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [gorzindel.lua:monster.events]
- Registers monster type `Grand Canon Dominus` into the global `Game` engine registry via `mType:register(monster)` [grand_canon_dominus.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [grand_canon_dominus.lua:monster.events]
- Registers monster type `Grand Chaplain Gaunder` into the global `Game` engine registry via `mType:register(monster)` [grand_chaplain_gaunder.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [grand_chaplain_gaunder.lua:monster.events]
- Registers monster type `Grand Commander Soeren` into the global `Game` engine registry via `mType:register(monster)` [grand_commander_soeren.lua:mType:register]
- Attaches creature event scripts defined in `monster.events` on spawn [grand_commander_soeren.lua:monster.events]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
