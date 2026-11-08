# Debugging Utilities (`data/libs/debugging`)

## Overview

Provides recursive table/value string formatting and debug logging helpers (`dump.lua`).

## Interface

- `[dump.lua:dumpLevel]`: `function dumpLevel(input, level)` — recursively formats Lua tables and primitive values into an indented string representation.
- `[dump.lua:dump]`: `function dump(input)` — returns `dumpLevel(input, 0)`.
- `[dump.lua:pdump]`: `function pdump(input)` — formats `input` via `dump(input)`, logs it with `logger.debug`, and returns the formatted string.
- `[dump.lua:tdump]`: `function tdump(title, input)` — formats `input` with a titled header/footer border, logs it with `logger.debug`, and returns the formatted string.

## Invariants

- `[dump.lua:tdump]`: `title` must support `:len()` and string concatenation (`..`).

## Side Effects

- `[dump.lua:dumpLevel]`, `[dump.lua:dump]`, `[dump.lua:pdump]`, `[dump.lua:tdump]`: Defines global functions `dumpLevel`, `dump`, `pdump`, and `tdump`.
- `[dump.lua:pdump]`, `[dump.lua:tdump]`: Emits debug log entries via `logger.debug`.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
