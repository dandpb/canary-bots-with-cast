# Core Quests Loader & Catalog Builder

## Overview

Provides the quest catalog builder (`catalog.lua`) and custom Lua package searcher (`loader.lua`) used to load and validate modular quest definitions.

## Interface

- `[catalog.lua:build]`: `buildCatalog(namespace, questModules)` — loads each quest module in `questModules` under `namespace`, validates start storage IDs and mission IDs, and returns the ordered `quests` table.
- `[loader.lua:load]`: `loadQuestCatalog(dataDirectory)` — registers a custom `package.searchers` / `package.loaders` searcher for `<dataDirectory>.lib.core.quests.catalog` and loads the global `Quests` table.
- `[loader.lua:Quests]`: Global table populated with the loaded quest catalog.

## Invariants

- `[catalog.lua:validateMissionId]`: Raises an error if a duplicate `missionId` is found within the same quest (`Duplicate mission id %d found in quest "%s"`).
- `[catalog.lua:validateStartStorage]`: Raises an error if two distinct quests declare the same `startStorageId` (`Duplicate quest start storage %d found in quests "%s" and "%s"`).
- `[catalog.lua:buildCatalog]`: Raises an error if any required quest module does not return a table.
- `[loader.lua:ensureQuestCatalogLoader]`: Inserts `questCatalogLoader` into `package.searchers` (or `package.loaders`) at most once per namespace, guarded by `package.loaded[namespace .. ".loader"]`.
- `[loader.lua:loadQuestCatalog]`: Returns the cached global `Quests` table without reloading when `Quests` is non-nil and `currentNamespace == namespace`.

## Side Effects

- `[catalog.lua:buildCatalog]`: Dynamically loads quest modules via `require(namespace .. "." .. moduleName)`.
- `[loader.lua:ensureQuestCatalogLoader]`: Mutates `package.searchers` / `package.loaders` (inserting `questCatalogLoader` at index `1`) and sets `package.loaded[namespace .. ".loader"] = true`.
- `[loader.lua:questCatalogLoader]`: Reads Lua files from disk via `loadfile(filePath)`.
- `[loader.lua:loadQuestCatalog]`: Sets the global `Quests` variable and module upvalue `currentNamespace`.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
