# OTClient Bot Control Module (`otclient/modules/game_botcontrol`)

## Overview
Provides an OTClient Redemption (`4.2+`) MultiBot-style UI panel (`game_botcontrol`) that polls nearby/party bots and dispatches player bot-control commands over ExtendedOpcode `120`.

## Interface
- `game_botcontrol` module manifest (`[game_botcontrol.otmod]`): Autoloaded, sandboxed OTClient module (`autoload-priority: 1200`) binding `@onLoad: init()` and `@onUnload: terminate()`.
- `init`, `terminate`, `onOpcode`, `send`, `requestList`, `updateList`, `showResult` (`[botcontrol.lua]`): Registers ExtendedOpcode `120` handler, polls `"list"` every `POLL_MS = 2000` ms while visible, renders `{t="list", ...}` bot rows, and sends `"cmd <verb text>"` payloads (`@all follow`, `@Some_Bot invite`, `summon ...`).
- `botcontrol.otui`: OTUI window and `BotRow` widget definitions for the control panel.

## Invariants
- The client module never enforces permissions locally; every command is built as plain `"cmd <verb text>"` text and validated server-side by `data/scripts/creaturescripts/bot/bot_control_opcode.lua` (`[botcontrol.lua]`).
- Background polling (`pollEvent`) stops automatically when the window is hidden or unloaded (`[botcontrol.lua:stopPoll]`, `[botcontrol.lua:poll]`).

## Side Effects
- Sends and receives ExtendedOpcode `120` network messages with `g_game.getProtocolGame()` and creates/destroys OTClient UI widgets (`[botcontrol.lua]`).

## Verification
- Load `game_botcontrol` in OTClient 4.2+ against a running Canary server with `bot_control_opcode.lua` active and toggle the bot control panel.
