# player

## Overview
Package implementation for `data/scripts/eventcallbacks/player`, providing component logic and data interfaces for player.

## Interface
- `callback.playerOnBrowseField` (`[on_browse_field.lua:callback.playerOnBrowseField]`)
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
- Run: `ctest --test-dir build --output-on-failure`
