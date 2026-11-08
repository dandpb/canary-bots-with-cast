# OTClient Modules (`otclient_mods`)

## Overview

Collection of custom OTClient Redemption client-side Lua modules (`game_forceexit` and `game_hudclean`) and module autoload configuration (`client_mods/mods.otmod`) for session disconnect controls and extended-view HUD decluttering.

## Subdirectories & Boundaries

- `game_forceexit`: [`./game_forceexit/README.md`](./game_forceexit/README.md) — Emergency keyboard shortcuts and console functions (`force()`, `drop()`, `status()`, `set()`) to force-logout or drop the active TCP game connection.
- `game_hudclean`: [`./game_hudclean/README.md`](./game_hudclean/README.md) — Action-bar slot masking and extended-view (`mode == 2`) background chrome stripping module (`init()`, `terminate()`, `refresh()`, `status()`).
