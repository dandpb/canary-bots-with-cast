# Legacy Core Library (`data/lib`)

## Overview

Top-level blueprint for `data/lib/`, housing the core quest catalog loader under `./core/README.md`.

## Subdirectories & Boundaries

- [core](./core/README.md): Core quest catalog builder and custom Lua module loader (`./core/quests/README.md`).

## Interface

- [core](./core/README.md): Exposes `[core/quests/catalog.lua:build]`, `[core/quests/loader.lua:load]`, and global `[core/quests/loader.lua:Quests]`.

## Invariants

- Enforces unique quest `startStorageId` and `missionId` invariants via [core](./core/README.md).

## Side Effects

- Mutates `package.searchers` / `package.loaders` and global `Quests` via [core](./core/README.md).

## Verification

- See the [Lua regression guide](../../tests/lua/README.md).
