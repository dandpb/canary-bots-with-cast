# systems

## Overview
Package implementation for `data/scripts/systems`, providing component logic and data interfaces for systems.

## Interface
- `concoctionsOnLogin.onLogin` (`[concoctions.lua:concoctionsOnLogin.onLogin]`)
- `customMonsterLoot.onStartup` (`[custom_monster_loot.lua:customMonsterLoot.onStartup]`)
- `bossDeath.onDeath` (`[reward_chest.lua:bossDeath.onDeath]`)
- `bossParticipation.onHealthChange` (`[reward_chest.lua:bossParticipation.onHealthChange]`)
- `loginBossPlayer.onLogin` (`[reward_chest.lua:loginBossPlayer.onLogin]`)
- `bossThink.onThink` (`[reward_chest.lua:bossThink.onThink]`)

## Invariants
- None

## Side Effects
- None

## Verification
- See the [Lua regression guide](../../../tests/lua/README.md).
