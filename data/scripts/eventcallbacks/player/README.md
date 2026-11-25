# player

## Overview
Package implementation for `data/scripts/eventcallbacks/player`, providing component logic and data interfaces for player.

## Interface
- `callback.playerOnBrowseField` (`[on_browse_field.lua:callback.playerOnBrowseField]`)
- `callback.playerOnKill` (`[on_kill_taskboard.lua:callback.playerOnKill]`): Forwards eligible non-bot, non-reward-boss, bestiary-raced monster kills to `Taskboard`.
- `callback.playerOnLoginComplete` (`[on_login_complete_taskboard.lua:callback.playerOnLoginComplete]`): Pushes initial `Taskboard` bounty and weekly windows on login for supported, eligible players.
- `callback.playerOnLook` (`[on_look.lua:callback.playerOnLook]`)
- `battleListCallback.playerOnLookInBattleList` (`[on_look.lua:battleListCallback.playerOnLookInBattleList]`)
- `callback.playerOnLookInShop` (`[on_look_in_shop.lua:callback.playerOnLookInShop]`)
- `callback.playerOnLookInTrade` (`[on_look_in_trade.lua:callback.playerOnLookInTrade]`)
- `callback.playerOnRemoveCount` (`[on_remove_count.lua:callback.playerOnRemoveCount]`)
- `callback.playerOnRequestQuestLine` (`[on_request_quest_line.lua:callback.playerOnRequestQuestLine]`)
- `callback.playerOnRequestQuestLog` (`[on_request_quest_log.lua:callback.playerOnRequestQuestLog]`)
- `callback.playerOnRotateItem` (`[on_rotate_item.lua:callback.playerOnRotateItem]`)
- `callback.playerOnStorageUpdate` (`[on_storage_update.lua:callback.playerOnStorageUpdate]`)

## Invariants
- None

## Side Effects
- None

## Verification
- See the [Lua regression guide](../../../../tests/lua/README.md).
