# lib

## Overview
Package implementation for `data/scripts/lib`, providing component logic and data interfaces for lib.

## Interface
- `BotEquipmentData.loadAll` (`[bot_equipment_data.lua:BotEquipmentData.loadAll]`)
- `BotEquipmentData.getLoadout` (`[bot_equipment_data.lua:BotEquipmentData.getLoadout]`)
- `loadouts` (`[bot_equipment_data.lua:loadouts]`)
- `BotHouseClaim.isBotGuid` (`[bot_house_claim.lua:BotHouseClaim.isBotGuid]`)
- `BotHouseClaim.ensureSchema` (`[bot_house_claim.lua:BotHouseClaim.ensureSchema]`)
- `BotHouseClaim.materialize` (`[bot_house_claim.lua:BotHouseClaim.materialize]`)
- `BotHouseClaim.snapshotIfAbsent` (`[bot_house_claim.lua:BotHouseClaim.snapshotIfAbsent]`)
- `BotHouseClaim.restore` (`[bot_house_claim.lua:BotHouseClaim.restore]`)
- `BotHuntData.loadAll` (`[bot_hunting_data.lua:BotHuntData.loadAll]`)
- `BotHuntData._loadScripts` (`[bot_hunting_data.lua:BotHuntData._loadScripts]`)

## Invariants
- None

## Side Effects
- Executes SQL queries against game database (`[bot_equipment_data.lua]`)
- Executes SQL queries against game database (`[bot_house_claim.lua]`)
- Executes SQL queries against game database (`[bot_hunting_data.lua]`)
- Executes SQL queries against game database (`[bot_market_data.lua]`)
- Emits system diagnostic logs (`[register_achievements.lua]`)
- Executes SQL queries against game database (`[register_migrations.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
