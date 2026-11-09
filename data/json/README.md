# JSON Configurations

## Overview

Groups JSON-based configuration subsystems and associated scripts under `data/json/`.

## Subdirectories & Boundaries

- [eventscheduler](./eventscheduler/README.md): JSON calendar event scheduler (`events.json`) and associated startup event scripts (`./eventscheduler/scripts/README.md`).

## Interface

- [eventscheduler](./eventscheduler/README.md): Exposes `[events.json:events]` calendar definitions and `[example.lua:GlobalEvent("EventScheduleExample")]`.

## Invariants

- See [eventscheduler](./eventscheduler/README.md) for `events.json` schema and date format invariants.

## Side Effects

- Configures scheduled rate modifiers and registers `GlobalEvent` scripts via [eventscheduler](./eventscheduler/README.md).

## Verification

- Run: `ctest --test-dir build --output-on-failure`
