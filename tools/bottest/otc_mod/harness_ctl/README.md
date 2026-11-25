# OTClient Harness Control Mod (`tools/bottest/otc_mod/harness_ctl`)

## Overview
Provides the OTClient test harness mod (`harness_ctl`) used by `tools/bottest/hub.py` to execute deterministic client verbs (`login`, `goto`, `walk`, `wait_see`, `wait_gone`, `view`, `self`, `perceive`) and stream low-level packet-tapped perception events over a loopback WebSocket.

## Interface
- `harness_ctl.otmod`: Unsandboxed OTClient module (`autoload: true`, `autoload-priority: 1500`) loading `ctl.lua` and `perceive.lua` and calling `HarnessCtl.init()` / `HarnessCtl.terminate()`.
- `HarnessCtl` (`[ctl.lua:HarnessCtl]`, `[ctl.lua:HarnessCtl.emit]`): Connects to `OTC_HARNESS_HUB` (`ws://127.0.0.1:<port>`), identifies via `OTC_HARNESS_INSTANCE`, handles `{t="cmd", id, verb, args}` and `{t="ping", id}`, and emits `{t="hello"|"ev"|"reply"|"pong"}` JSON frames stamped with `cms` (`g_clock.realMillis()`) and optional Windows `ems`.
- `HarnessPerceive` (`[perceive.lua:HarnessPerceive]`): Wraps `ProtocolGame.onOpcode` (returning `false` after peeking opcodes `0x83`, `0x84`, `0x85`, `0xB4`) and samples creature/self state to emit `see_effect`, `see_effect_end`, `see_missile`, `see_sound`, `see_text`, `see_creature`, `see_self`, `see_cooldown`, and `tap_error`, plus `view`/`self`/`perceive` snapshot verbs.

## Invariants
- Completely inert unless `OTC_HARNESS_HUB` is set in the environment (`[ctl.lua:hubUrl]`).
- Every hub verb replies exactly once (`OK <verb> ...` or `STUCK verb=<v> reason=<r> ...`) and never persists login credentials to disk (`[ctl.lua]`).
- The `ProtocolGame.onOpcode` tap restores read position by returning `false` so C++ packet parsing and rendering remain unaltered (`[perceive.lua]`).

## Side Effects
- Opens a WebSocket client connection to `OTC_HARNESS_HUB`, buffers up to 20,000 outbound messages while disconnected, and drives OTClient input/movement/login actions during automated tests (`[ctl.lua]`).

## Verification
- Driven end-to-end by `tools/bottest/runner.py` and `tools/bottest/hub.py` (see [`../../README.md`](../../README.md)).
