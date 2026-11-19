# Core Library Modules (`data/lib/core`)

## Overview

Intermediate grouping for core data library subsystems such as the modular quest catalog loader.

## Subdirectories & Boundaries

- [quests](./quests/README.md): Quest catalog builder (`[quests/catalog.lua:build]`) and custom Lua searcher (`[quests/loader.lua:load]`) populating the global `Quests` table.

## Interface

- [quests](./quests/README.md): Exposes `[quests/catalog.lua:build]`, `[quests/loader.lua:load]`, and global `[quests/loader.lua:Quests]`.

## Invariants

- Preserves unique quest `startStorageId` and per-quest `missionId` constraints enforced in [quests](./quests/README.md).

## Side Effects

- Registers custom Lua package searchers and populates global `Quests` via [quests](./quests/README.md).

## Verification

- See the [Lua regression guide](../../../tests/lua/README.md).
