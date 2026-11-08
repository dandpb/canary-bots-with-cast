# Game Force Exit Module (`game_forceexit`)

## Overview

OTClient module (`game_forceexit`) providing emergency keyboard shortcuts and console helpers to immediately force-logout or drop the active TCP game connection without waiting for server logout blocks.

## Interface

- `[game_forceexit.otmod:Module]` — OTClient module definition `game_forceexit` (`autoload: true`, `sandboxed: true`, `scripts: [ forceexit ]`, `@onLoad: init()`, `@onUnload: terminate()`).
- `[forceexit.lua:init]` / `[forceexit.lua:terminate]` — Module lifecycle hooks that bind (`bindKeys()`) and unbind (`unbindKeys()`, `destroyConfirm()`) hotkeys and confirmation dialogs.
- `[forceexit.lua:force]` — `force()`: invokes `g_game.forceLogout()` when online, optionally prompting via `ask()`.
- `[forceexit.lua:drop]` — `drop()`: invokes `protocol:disconnect()` on `g_game.getProtocolGame()` via `pcall`, falling back to `g_game.forceLogout()` if unavailable, optionally prompting via `ask()`.
- `[forceexit.lua:status]` — `status()`: prints current `config.forceKey`, `config.dropKey`, `config.confirm`, and `g_game.isOnline()` state to the client terminal.
- `[forceexit.lua:set]` — `set(key, value)`: updates `config[key]` for valid keys (`forceKey`, `dropKey`, `confirm`) and rebinds hotkeys when key bindings change.

## Invariants

- `[forceexit.lua:force]` — Requires `g_game.isOnline()` to be true before calling `g_game.forceLogout()`; returns early with a terminal message if offline.
- `[forceexit.lua:drop]` — Requires `g_game.isOnline()` to be true before attempting socket disconnect; falls back to `g_game.forceLogout()` if `g_game.getProtocolGame()` returns `nil` or `protocol:disconnect()` errors under `pcall`.
- `[forceexit.lua:ask]` — When `config.confirm` is true, destroys any existing `confirmWindow` before creating a new `displayGeneralBox` dialog and only executes `yesCallback` upon confirmation.
- `[forceexit.lua:bindKeys]` — Always calls `unbindKeys()` before binding non-empty `config.forceKey` (default `'Ctrl+Shift+Q'`) and `config.dropKey` (default `'Ctrl+Shift+D'`).
- `[forceexit.lua:set]` — Rejects keys where `config[key] == nil` (only `forceKey`, `dropKey`, and `confirm` are accepted).

## Side Effects

- `[forceexit.lua:bindKeys]` / `[forceexit.lua:unbindKeys]` — Registers and removes global keyboard shortcuts via `g_keyboard.bindKeyDown` and `g_keyboard.unbindKeyDown`.
- `[forceexit.lua:ask]` / `[forceexit.lua:destroyConfirm]` — Spawns and destroys UI modal confirmation dialogs (`confirmWindow`) via `displayGeneralBox` and `confirmWindow:destroy()`.
- `[forceexit.lua:force]` — Sends a logout packet and tears down the local game session via `g_game.forceLogout()`.
- `[forceexit.lua:drop]` — Closes the active game TCP connection via `protocol:disconnect()` (or falls back to `g_game.forceLogout()`).
- `[forceexit.lua:status]` — Prints status, action notices, and configuration changes to client stdout/terminal via `print()`.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
