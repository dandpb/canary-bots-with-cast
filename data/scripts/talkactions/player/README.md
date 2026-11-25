# player

## Overview
Package implementation for `data/scripts/talkactions/player`, providing component logic and data interfaces for player.

## Interface
- `aol.onSay` (`[aol.lua:aol.onSay]`)
- `feature.onSay` (`[auto_loot.lua:feature.onSay]`)
- `balance.onSay` (`[bank.lua:balance.onSay]`)
- `deposit.onSay` (`[bank.lua:deposit.onSay]`)
- `withdraw.onSay` (`[bank.lua:withdraw.onSay]`)
- `transfer.onSay` (`[bank.lua:transfer.onSay]`)
- `bless.onSay` (`[bless.lua:bless.onSay]`)
- `houseCmd.onSay` (`[bot_house.lua:houseCmd.onSay]`)
- `botParty.onSay` (`[bot_party.lua:botParty.onSay]`)
- `talk.onSay` (`[brain.lua:talk.onSay]`)
- `!livestream` (`[livestream_system.lua]`): Player livestream management talkaction (`on`, `off`, `desc`, `password`, `kick`, `ban`, `unban`, `bans`, `mute`, `unmute`, `mutes`, `show`, `status`).

## Invariants
- None

## Side Effects
- None

## Verification
- See the [Lua regression guide](../../../../tests/lua/README.md).
