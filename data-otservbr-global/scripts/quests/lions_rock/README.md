# Lions Rock

## Overview
Component package under `scripts/quests/lions_rock` containing 2 files (`actions_lions_rock.lua`..`movements_lions_rock.lua`).

## Interface
- `lionsRockSacrificesTest.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lions_rock.lua:lionsRockSacrificesTest.onUse]
- `reset(setting)` [actions_lions_rock.lua:reset]
- `lionsGetLionsMane.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lions_rock.lua:lionsGetLionsMane.onUse]
- `lionsGetHolyWater.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lions_rock.lua:lionsGetHolyWater.onUse]
- `lionsRockFountain.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [actions_lions_rock.lua:lionsRockFountain.onUse]
- `Action()` assigned to `lionsRockSacrificesTest` [actions_lions_rock.lua:lionsRockSacrificesTest]
- `Action()` assigned to `lionsGetLionsMane` [actions_lions_rock.lua:lionsGetLionsMane]
- `Action()` assigned to `lionsGetHolyWater` [actions_lions_rock.lua:lionsGetHolyWater]
- `Action()` assigned to `lionsRockFountain` [actions_lions_rock.lua:lionsRockFountain]
- `Action()` registration [actions_lions_rock.lua:Action]
- `lionsRockEntrance.onStepIn(creature, item, position, fromPosition)` [movements_lions_rock.lua:lionsRockEntrance.onStepIn]
- `lionsRockTranslationScroll.onStepIn(creature, item, position, fromPosition)` [movements_lions_rock.lua:lionsRockTranslationScroll.onStepIn]
- `reset()` [movements_lions_rock.lua:reset]
- `lionsRockSigns.onStepIn(creature, item, position, fromPosition)` [movements_lions_rock.lua:lionsRockSigns.onStepIn]
- `lionsRockMessage.onStepIn(creature, item, position, fromPosition)` [movements_lions_rock.lua:lionsRockMessage.onStepIn]
- `MoveEvent()` assigned to `lionsRockEntrance` [movements_lions_rock.lua:lionsRockEntrance]
- `MoveEvent()` assigned to `lionsRockTranslationScroll` [movements_lions_rock.lua:lionsRockTranslationScroll]
- `MoveEvent()` assigned to `lionsRockSigns` [movements_lions_rock.lua:lionsRockSigns]
- `MoveEvent()` assigned to `lionsRockMessage` [movements_lions_rock.lua:lionsRockMessage]
- `MoveEvent()` registration [movements_lions_rock.lua:MoveEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [actions_lions_rock.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [actions_lions_rock.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [movements_lions_rock.lua:getStorageValue]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [movements_lions_rock.lua:getPlayer]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [movements_lions_rock.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_lions_rock.lua:register]
- Mutates player or global storage state via `setStorageValue` [actions_lions_rock.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [actions_lions_rock.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [actions_lions_rock.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [movements_lions_rock.lua:register]
- Mutates player or global storage state via `setStorageValue` [movements_lions_rock.lua:setStorageValue]
- Teleports creatures/players across map coordinates via `teleportTo` [movements_lions_rock.lua:teleportTo]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [movements_lions_rock.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [movements_lions_rock.lua:addEvent]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
