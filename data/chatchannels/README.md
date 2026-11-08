# Chat Channels

## Overview

Defines the server's in-game chat channel declarations (`chatchannels.xml`) and delegates channel join/speak callbacks to Lua scripts in `./scripts/README.md`.

## Subdirectories & Boundaries

- [scripts](./scripts/README.md): Lua channel callback scripts (`canJoin` and `onSpeak`) for Tutor, World Chat, English Chat, Advertising, Advertising-Rookgaard, Help, Gamemaster, and Guild Leaders channels.

## Interface

- `[chatchannels.xml:channels]`: Declares channel IDs `2` (`Tutor` -> `tutor.lua`), `3` (`World Chat` -> `world_chat.lua`), `4` (`English Chat` -> `english_chat.lua`), `5` (`Advertising` -> `advertising.lua`), `6` (`Advertising-Rookgaard` -> `advertising-rook.lua`), `7` (`Help` -> `help.lua`), `8` (`Gamemaster` -> `gamemaster.lua`), and `11` (`Guild Leaders` -> `guild_leaders.lua`).
- [scripts](./scripts/README.md): Exposes `canJoin(player)` and `onSpeak(player, type, message)` callbacks bound by `chatchannels.xml`.

## Invariants

- `[chatchannels.xml:channel]`: Each `<channel>` entry maps a unique integer `id` (`2`, `3`, `4`, `5`, `6`, `7`, `8`, `11`) and optional `public="1"` flag to a corresponding script in `./scripts/`.

## Side Effects

- Delegates runtime channel join validation, rate limiting (`CONDITION_CHANNELMUTEDTICKS`), and Help channel KV moderation (`channel-help-exhaustion`) to `./scripts/README.md`.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
