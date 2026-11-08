# Core Datapack Library (`data-canary/lib/core`)

## Overview
Initializes global storage key tables (`Storage`, `GlobalStorage`) and loads the quest catalog for the `data-canary` datapack.

## Interface
- `[load.lua:1]` — Entry script executing `dofile(DATA_DIRECTORY .. "/lib/core/storages.lua")` and `require("data-canary.lib.core.quests")`.
- `[storages.lua:Storage]` — Global table defining `Storage.Quest.Key.ID1000` (`103`), `Storage.Quest.ExampleQuest.Example` (`9000`), `Storage.Quest.ExampleQuest.Door` (`9001`), `Storage.DelayLargeSeaShell` (`30002`), and `Storage.Imbuement` (`30004`).
- `[storages.lua:GlobalStorage]` — Global table defining `GlobalStorage.ExampleQuest.Example` (`60000`).
- `[quests.lua:1]` — Delegates quest catalog loading to `require("data.lib.core.quests.loader").load(DATA_DIRECTORY)`.
- Subdirectories:
  - `quests`: [`./quests/README.md`](./quests/README.md) — Quest catalog module definitions.

## Invariants
- `[load.lua:1]` loads `storages.lua` prior to `require("data-canary.lib.core.quests")` so `Storage` keys are defined when quest catalog modules evaluate.
- `[storages.lua:5]` avoids reserved engine player storage key ranges (`[10000000 - 20000000]`, `[1000 - 1500]`, `[2001 - 2011]`).

## Side Effects
- `[storages.lua:24]` populates global Lua tables `Storage` and `GlobalStorage`.
- `[load.lua:1]` and `[quests.lua:1]` load `storages.lua` and `data-canary` quest catalog modules into the Lua state.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
