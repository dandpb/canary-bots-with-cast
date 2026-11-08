# God

## Overview
Component package under `scripts/talkactions/god` containing 3 files (`house_backfill.lua`..`house_ingest.lua`).

## Interface
- `loadConfig()` [house_backfill.lua:loadConfig]
- `buildBotPool()` [house_backfill.lua:buildBotPool]
- `pickBot(botsByTown, townId)` [house_backfill.lua:pickBot]
- `isBedItemId(itemId)` [house_backfill.lua:isBedItemId]
- `isStructuralItemId(itemId)` [house_backfill.lua:isStructuralItemId]
- `isStructuralTile(tile)` [house_backfill.lua:isStructuralTile]
- `materializeHouseTiles(house)` [house_backfill.lua:materializeHouseTiles]
- `countMovableTilesInHouse(house)` [house_backfill.lua:countMovableTilesInHouse]
- `isHouseBare(house, size)` [house_backfill.lua:isHouseBare]
- `loadTemplatesAndDumpedSet()` [house_backfill.lua:loadTemplatesAndDumpedSet]
- `shuffleN(arr, times)` [house_backfill.lua:shuffleN]
- `pickRandomInteriorTile(house)` [house_backfill.lua:pickRandomInteriorTile]
- `placeHireling(house, botGuid, usedNames)` [house_backfill.lua:placeHireling]
- `unlockAllBotKVs()` [house_backfill.lua:unlockAllBotKVs]
- `houseBackfill.onSay(player, words, param)` [house_backfill.lua:houseBackfill.onSay]
- `processOneHouse(state, house, houseIdx)` [house_backfill.lua:processOneHouse]
- `processBackfillChunk(state, startIdx)` [house_backfill.lua:processBackfillChunk]
- `processBarePassChunk(state, startIdx)` [house_backfill.lua:processBarePassChunk]
- `TalkAction("/housebackfill")` assigned to `houseBackfill` [house_backfill.lua:houseBackfill]
- `TalkAction("/housebackfill")` registration [house_backfill.lua:TalkAction]
- Global symbol `CHUNK_SIZE` [house_backfill.lua:CHUNK_SIZE]
- Global symbol `CHUNK_DELAY_MS` [house_backfill.lua:CHUNK_DELAY_MS]
- Exported Lua configuration table [house_backfill.lua:return]
- `passesSaveFilter(itemId)` [house_clear.lua:passesSaveFilter]
- `clearOne(house)` [house_clear.lua:clearOne]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [house_backfill.lua:Tile]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [house_backfill.lua:db.query]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [house_clear.lua:Tile]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [house_clear.lua:db.query]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [house_ingest.lua:Tile]
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [house_ingest.lua:db.query]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [house_backfill.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [house_backfill.lua:Game]
- Executes SQL DDL/DML statements against the database via `db.query` [house_backfill.lua:db.query]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [house_backfill.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [house_clear.lua:register]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [house_clear.lua:transform]
- Executes SQL DDL/DML statements against the database via `db.query` [house_clear.lua:db.query]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [house_clear.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [house_ingest.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [house_ingest.lua:Game]
- Executes SQL DDL/DML statements against the database via `db.query` [house_ingest.lua:db.query]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
