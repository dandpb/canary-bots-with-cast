# bot

## Overview
Package implementation for `data/scripts/creaturescripts/bot`, providing component logic and data interfaces for bot.

## Interface
- `botDeath.onDeath` (`[bot_death.lua:botDeath.onDeath]`)
- `botControlOpcode.onExtendedOpcode`, `botControlOpcodeLogin.onLogin` (`[bot_control_opcode.lua:botControlOpcode.onExtendedOpcode]`): Relays OTClient `game_botcontrol` requests on ExtendedOpcode `120` (`list` / `cmd <verb text>`) to `Game.botCommand("_global", "verb opcode ...")` for non-bot players.

## Invariants
- `botControlOpcode.onExtendedOpcode` drops payloads from bot players, empty strings, and payloads longer than `MAX_REQUEST` (`512` bytes), flattening newlines before forwarding (`[bot_control_opcode.lua]`).

## Side Effects
- None

## Verification
- See the [Lua regression guide](../../../../tests/lua/README.md).
