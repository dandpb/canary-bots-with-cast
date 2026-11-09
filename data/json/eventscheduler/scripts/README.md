# Event Scheduler Scripts

## Overview

Contains Lua startup event scripts triggered by the JSON event scheduler (`../events.json`).

## Interface

- `[example.lua:GlobalEvent("EventScheduleExample")]`: Defines the `EventScheduleExample` `GlobalEvent` instance.
- `[example.lua:globalEvent.onStartup]`: `function globalEvent.onStartup()` — startup callback for the scheduled event example.

## Invariants

- None.

## Side Effects

- `[example.lua:globalEvent:register()]`: Registers the `EventScheduleExample` `GlobalEvent` with the engine upon script load.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
