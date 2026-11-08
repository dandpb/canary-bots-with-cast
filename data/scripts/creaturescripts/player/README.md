# player

## Overview
Package implementation for `data/scripts/creaturescripts/player`, providing component logic and data interfaces for player.

## Interface
- `adventurerBlessingLogin.onLogin` (`[adventure_blessing.lua:adventurerBlessingLogin.onLogin]`)
- `playerDeath.onDeath` (`[death.lua:playerDeath.onDeath]`)
- `playerLoginGlobal.onLogin` (`[login.lua:playerLoginGlobal.onLogin]`)
- `playerLogout.onLogout` (`[logout.lua:playerLogout.onLogout]`)
- `CheckNamelock` (`[name_lock.lua:CheckNamelock]`)
- `playerLogin.onLogin` (`[name_lock.lua:playerLogin.onLogin]`)
- `offlineTraining.onLogin` (`[offline_training.lua:offlineTraining.onLogin]`)
- `regenerateStamina.onLogin` (`[regenerate_stamina.lua:regenerateStamina.onLogin]`)
- `sendFirstItems.onLogin` (`[send_first_items.lua:sendFirstItems.onLogin]`)
- `updatePlayerOnAdvancedLevel.onAdvance` (`[update_player_on_advanced_level.lua:updatePlayerOnAdvancedLevel.onAdvance]`)

## Invariants
- None

## Side Effects
- Executes SQL queries against game database (`[death.lua]`)
- Executes SQL queries against game database (`[login.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
