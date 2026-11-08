# Adventures Of Galthen

## Overview
Component package under `scripts/quests/adventures_of_galthen` containing 10 files (`actions_ahau.lua`..`actions_yselda_shortcut.lua`).

## Interface
- `BossLever(config)` assigned to `lever` [actions_ahau.lua:lever]
- `BossLever(config)` registration [actions_ahau.lua:BossLever]
- `galthensTree.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_galthens_tree.lua:galthensTree.onUse]
- `Action()` assigned to `galthensTree` [actions_galthens_tree.lua:galthensTree]
- `Action()` registration [actions_galthens_tree.lua:Action]
- `idol.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_idol_of_tukh.lua:idol.onUse]
- `Action()` assigned to `idol` [actions_idol_of_tukh.lua:idol]
- `Action()` registration [actions_idol_of_tukh.lua:Action]
- `entrance.onUse(creature, item, position, fromPosition)` [actions_iksupan_entrance.lua:entrance.onUse]
- `Action()` assigned to `entrance` [actions_iksupan_entrance.lua:entrance]
- `Action()` registration [actions_iksupan_entrance.lua:Action]
- `exit.onStepIn(creature, item, position, fromPosition)` [actions_iksupan_exit.lua:exit.onStepIn]
- `MoveEvent()` assigned to `exit` [actions_iksupan_exit.lua:exit]
- `MoveEvent()` registration [actions_iksupan_exit.lua:MoveEvent]
- `BossLever(config)` assigned to `lever` [actions_megasylvan_yselda.lua:lever]
- `BossLever(config)` registration [actions_megasylvan_yselda.lua:BossLever]
- `BossLever(config)` assigned to `lever` [actions_mitmah_vanguard.lua:lever]
- `BossLever(config)` registration [actions_mitmah_vanguard.lua:BossLever]
- `mitmahVanguardExit.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_mitmah_vanguard_exit.lua:mitmahVanguardExit.onUse]
- `Action()` assigned to `mitmahVanguardExit` [actions_mitmah_vanguard_exit.lua:mitmahVanguardExit]
- `Action()` registration [actions_mitmah_vanguard_exit.lua:Action]
- `forestOfLife.onStepIn(creature, item, position, fromPosition)` [actions_yselda_entrances.lua:forestOfLife.onStepIn]
- `MoveEvent()` assigned to `forestOfLife` [actions_yselda_entrances.lua:forestOfLife]
- `MoveEvent()` registration [actions_yselda_entrances.lua:MoveEvent]
- `entranceYselda.onUse(creature, item, position, fromPosition)` [actions_yselda_shortcut.lua:entranceYselda.onUse]

## Invariants
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_iksupan_entrance.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_iksupan_exit.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_yselda_entrances.lua:getPlayer]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [actions_yselda_shortcut.lua:getPlayer]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_ahau.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_galthens_tree.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_galthens_tree.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_galthens_tree.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_idol_of_tukh.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_idol_of_tukh.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_iksupan_entrance.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_iksupan_entrance.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_iksupan_exit.lua:register]
- Teleports creatures/players across map coordinates via `teleportTo` [actions_iksupan_exit.lua:teleportTo]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_megasylvan_yselda.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_mitmah_vanguard.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
