# data-otservbr-global Blueprint

## Overview
Root global datapack (`data-otservbr-global`) containing libraries, database migrations, monsters, NPCs, raids, RevScripts, and startup tables.

## Subdirectories & Boundaries
- [lib](./lib/README.md) - Provides 1 direct files (`lib.lua`..`lib.lua`) and 5 subdirectories under `lib`.
- [migrations](./migrations/README.md) - Component package under `migrations` containing 57 files (`1.lua`..`9.lua`).
- [monster](./monster/README.md) - Intermediate blueprint grouping 30 subdirectories under `monster`.
- [npc](./npc/README.md) - Provides 1027 direct files (`....lua`..`zurak_arena.lua`) and 1 subdirectories under `npc`.
- [raids](./raids/README.md) - Provides 1 direct files (`raids.xml`..`raids.xml`) and 17 subdirectories under `raids`.
- [scripts](./scripts/README.md) - Intermediate blueprint grouping 14 subdirectories under `scripts`.
- [startup](./startup/README.md) - Provides 1 direct files (`startup.lua`..`startup.lua`) and 2 subdirectories under `startup`.

## Interface
- `dofile(DATA_DIRECTORY .. "/lib/core/load.lua")` module loader [lib.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/lib/others/load.lua")` module loader [lib.lua:dofile]
- Defines 57 script/configuration files (`1.lua` through `9.lua`) [1.lua]
- `onUpdateDatabase()` [1.lua:onUpdateDatabase]
- `Game.createMonsterType("Azure Frog")` and `mType:register(monster)` [azure_frog.lua:Game.createMonsterType]
- `Game.createMonsterType("Bog Frog")` and `mType:register(monster)` [bog_frog.lua:Game.createMonsterType]
- Defines 1027 script/configuration files (`....lua` through `zurak_arena.lua`) [....lua]
- `Game.createNpcType("...")` and `npcType:register(npcConfig)` [....lua:Game.createNpcType]
- `<raid name="Badger" file="abdendriel/badger.xml">` entry [raids.xml:raid]
- `<raid name="WarWolf" file="abdendriel/warwolf.xml">` entry [raids.xml:raid]
- `doNotTeleport(player)` [adventurers_stone.lua:doNotTeleport]
- `adventurersStone.onUse(player, item, fromPosition, target, toPosition, isHotkey)` [adventurers_stone.lua:adventurersStone.onUse]
- `dofile(DATA_DIRECTORY .. "/startup/tables/load.lua")` module loader [startup.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/startup/others/load.lua")` module loader [startup.lua:dofile]
- [lib](./lib/README.md) - Provides 1 direct files (`lib.lua`..`lib.lua`) and 5 subdirectories under `lib`.
- [migrations](./migrations/README.md) - Component package under `migrations` containing 57 files (`1.lua`..`9.lua`).
- [monster](./monster/README.md) - Intermediate blueprint grouping 30 subdirectories under `monster`.
- [npc](./npc/README.md) - Provides 1027 direct files (`....lua`..`zurak_arena.lua`) and 1 subdirectories under `npc`.
- [raids](./raids/README.md) - Provides 1 direct files (`raids.xml`..`raids.xml`) and 17 subdirectories under `raids`.
- [scripts](./scripts/README.md) - Intermediate blueprint grouping 14 subdirectories under `scripts`.
- [startup](./startup/README.md) - Provides 1 direct files (`startup.lua`..`startup.lua`) and 2 subdirectories under `startup`.

## Invariants
- Database queries require valid schema state and execute sequentially within `onUpdateDatabase` or startup hooks [1.lua:db.query]
- Bestiary configuration (`monster.Bestiary`) and `monster.raceId` must match unique creature race metadata [azure_frog.lua:monster.Bestiary]
- `npcConfig.flags.floorchange` and `npcConfig.health`/`npcConfig.maxHealth` bound NPC movement and vitals [....lua:npcConfig.flags]
- Each `<raid>` entry in `raids.xml` must reference a valid relative XML raid file path and define `interval2` and `margin` attributes [raids.xml:raid]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [adventurers_stone.lua:Tile]

## Side Effects
- Loads and executes `DATA_DIRECTORY .. "/lib/core/load.lua"` via `dofile` [lib.lua:dofile]
- Executes SQL DDL/DML statements against the database via `db.query` [1.lua:db.query]
- Registers monster type `Azure Frog` into the global `Game` engine registry via `mType:register(monster)` [azure_frog.lua:mType:register]
- Registers NPC `...` into the `Game` engine via `npcType:register(npcConfig)` [....lua:npcType:register]
- Registers raid schedule definitions loaded by the server raid manager [raids.xml:raids]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [adventurers_stone.lua:register]
- Loads and executes `DATA_DIRECTORY .. "/startup/tables/load.lua"` via `dofile` [startup.lua:dofile]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
