# Globalevents

## Overview
Provides 2 direct files (`dawnport_magic_effect.lua`..`update.lua`) and 3 subdirectories under `scripts/globalevents`.

## Interface
- `dawnportMagicEffect.onThink(interval)` [dawnport_magic_effect.lua:dawnportMagicEffect.onThink]
- `GlobalEvent("DawnportMagicEffect")` assigned to `dawnportMagicEffect` [dawnport_magic_effect.lua:dawnportMagicEffect]
- `GlobalEvent("DawnportMagicEffect")` registration [dawnport_magic_effect.lua:GlobalEvent]
- `update.onStartup()` [update.lua:update.onStartup]
- `GlobalEvent("Update")` assigned to `update` [update.lua:update]
- `GlobalEvent("Update")` registration [update.lua:GlobalEvent]
- `dofile(fileToUpdate)` module loader [update.lua:dofile]
- [others](./others/README.md) - Component package under `scripts/globalevents/others` containing 3 files (`check_mount.lua`..`raids_schedule.lua`).
- [spawn](./spawn/README.md) - Component package under `scripts/globalevents/spawn` containing 1 files (`rashid.lua`..`rashid.lua`).
- [vip](./vip/README.md) - Component package under `scripts/globalevents/vip` containing 2 files (`online_coins.lua`..`online_tokens.lua`).

## Invariants
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [update.lua:db.query]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [dawnport_magic_effect.lua:register]
- Loads and executes `fileToUpdate` via `dofile` [update.lua:dofile]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [update.lua:register]
- Executes SQL DDL/DML statements against the database via `db.query` [update.lua:db.query]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
