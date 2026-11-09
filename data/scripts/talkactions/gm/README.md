# gm

## Overview
Package implementation for `data/scripts/talkactions/gm`, providing component logic and data interfaces for gm.

## Interface
- `afk.onSay` (`[afk.lua:afk.onSay]`)
- `afkEffect.onThink` (`[afk.lua:afkEffect.onThink]`)
- `callback.playerOnWalk` (`[afk.lua:callback.playerOnWalk]`)
- `godAfkLogout.onLogout` (`[afk.lua:godAfkLogout.onLogout]`)
- `playersAFKs` (`[afk.lua:playersAFKs]`)
- `ban.onSay` (`[ban.lua:ban.onSay]`)
- `blessStatus.onSay` (`[bless_status.lua:blessStatus.onSay]`)
- `Broadcast` (`[broadcast.lua:Broadcast]`)
- `broadcast.onSay` (`[broadcast.lua:broadcast.onSay]`)
- `clean.onSay` (`[clean.lua:clean.onSay]`)

## Invariants
- None

## Side Effects
- Executes SQL queries against game database (`[ban.lua]`)
- Executes SQL queries against game database (`[gold_highscore.lua]`)
- Executes SQL queries against game database (`[unban.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
