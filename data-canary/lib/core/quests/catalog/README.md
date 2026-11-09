# Quest Catalog Definitions (`data-canary/lib/core/quests/catalog`)

## Overview
Defines the quest log catalog entries and module list for the minimal `data-canary` datapack.

## Interface
- `[init.lua:questModules]` — Ordered table of quest catalog module names (`{ "001_example" }`) passed to `catalog.build(DATA_DIRECTORY .. ".lib.core.quests.catalog", questModules)`.
- `[001_example.lua:quest]` — Quest table defining quest `"Example"` (`startStorageId = Storage.Quest.ExampleQuest.Example`, `startStorageValue = 1`) and mission `[1]` (`"The Hidden Seal"`).

## Invariants
- `[init.lua:5]` requires `CORE_DIRECTORY .. "/lib/core/quests/catalog.lua"` and `Storage.Quest.ExampleQuest.Example` (`[001_example.lua:3]`) to be loaded before building the quest catalog.

## Side Effects
- `[init.lua:5]` executes `dofile(CORE_DIRECTORY .. "/lib/core/quests/catalog.lua")` and loads each module listed in `questModules`.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
