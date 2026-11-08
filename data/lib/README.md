# Legacy Core Library (`data/lib`)

## Overview

Top-level blueprint for `data/lib/`, housing the core quest catalog loader under `./core/README.md`.

## Subdirectories & Boundaries

- [core](./core/README.md): Core quest catalog builder and custom Lua module loader (`./core/quests/README.md`).

## Interface

- [core](./core/README.md): Exposes `[catalog.lua:build]`, `[loader.lua:load]`, and global `[loader.lua:Quests]`.

## Invariants

- Enforces unique quest `startStorageId` and `missionId` invariants via [core](./core/README.md).

## Side Effects

- Mutates `package.searchers` / `package.loaders` and global `Quests` via [core](./core/README.md).

## Verification

- Run: `ctest --test-dir build --output-on-failure`
