# Threatened Dreams

## Overview
Component package under `scripts/quests/threatened_dreams` containing 12 files (`action_fairies_release.lua`..`nightmare_monsters_kills.lua`).

## Interface
- `revertFairy(toPosition, item)` [action_fairies_release.lua:revertFairy]
- `fairiesRelease.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_fairies_release.lua:fairiesRelease.onUse]
- `Action()` assigned to `fairiesRelease` [action_fairies_release.lua:fairiesRelease]
- `Action()` registration [action_fairies_release.lua:Action]
- `moonMirror.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_moon_mirror.lua:moonMirror.onUse]
- `Action()` assigned to `moonMirror` [action_moon_mirror.lua:moonMirror]
- `Action()` registration [action_moon_mirror.lua:Action]
- `poacherBook.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_poacher_book.lua:poacherBook.onUse]
- `Action()` assigned to `poacherBook` [action_poacher_book.lua:poacherBook]
- `Action()` registration [action_poacher_book.lua:Action]
- `poacherNotes.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_poacher_notes.lua:poacherNotes.onUse]
- `Action()` assigned to `poacherNotes` [action_poacher_notes.lua:poacherNotes]
- `Action()` registration [action_poacher_notes.lua:Action]
- `starlightVial.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_starlight_vial.lua:starlightVial.onUse]
- `Action()` assigned to `starlightVial` [action_starlight_vial.lua:starlightVial]
- `Action()` registration [action_starlight_vial.lua:Action]
- `sunCatcher.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_sun_catcher.lua:sunCatcher.onUse]
- `Action()` assigned to `sunCatcher` [action_sun_catcher.lua:sunCatcher]
- `Action()` registration [action_sun_catcher.lua:Action]
- `wolfFur.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [action_whelp_fur.lua:wolfFur.onUse]
- `Action()` assigned to `wolfFur` [action_whelp_fur.lua:wolfFur]
- `Action()` registration [action_whelp_fur.lua:Action]
- `createRavenHerb.onPeriodChange(period, light)` [event_raven_herb_bush.lua:createRavenHerb.onPeriodChange]
- `ravenHerb.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [event_raven_herb_bush.lua:ravenHerb.onUse]
- `Action()` assigned to `ravenHerb` [event_raven_herb_bush.lua:ravenHerb]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_fairies_release.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action_fairies_release.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_moon_mirror.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action_moon_mirror.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_poacher_book.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_poacher_notes.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_starlight_vial.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action_starlight_vial.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_sun_catcher.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [action_sun_catcher.lua:Tile]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [action_whelp_fur.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [event_raven_herb_bush.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_fairies_release.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_fairies_release.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_fairies_release.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [action_fairies_release.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_moon_mirror.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_moon_mirror.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_moon_mirror.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_poacher_book.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_poacher_book.lua:setStorageValue]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [action_poacher_book.lua:transform]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [action_poacher_notes.lua:register]
- Mutates player or global storage state via `setStorageValue` [action_poacher_notes.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
