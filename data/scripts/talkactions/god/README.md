# god

## Overview
Package implementation for `data/scripts/talkactions/god`, providing component logic and data interfaces for god.

## Interface
- `addAchievement.onSay` (`[achievement_functions.lua:addAchievement.onSay]`)
- `removeAchievement.onSay` (`[achievement_functions.lua:removeAchievement.onSay]`)
- `checkAchievements.onSay` (`[achievement_functions.lua:checkAchievements.onSay]`)
- `addaddon.onSay` (`[add_addon.lua:addaddon.onSay]`)
- `talkaction.onSay` (`[add_bosstiary_kills.lua:talkaction.onSay]`)
- `talkaction.onSay` (`[add_condition.lua:talkaction.onSay]`)
- `addMoney.onSay` (`[add_money.lua:addMoney.onSay]`)
- `addmount.onSay` (`[add_mount.lua:addmount.onSay]`)
- `addSkill.onSay` (`[add_skill.lua:addSkill.onSay]`)
- `attributes.onSay` (`[attributes.lua:attributes.onSay]`)

## Invariants
- None

## Side Effects
- Executes SQL queries against game database (`[bot_cavebot.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[bot_cavebot.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[icons_functions.lua]`)
- Executes SQL queries against game database (`[ip_ban.lua]`)
- Schedules timed tasks or dispatcher callbacks (`[save.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
