# monster

## Overview
Package implementation for `data/scripts/creaturescripts/monster`, providing component logic and data interfaces for monster.

## Interface
- `onBossDeath.onDeath` (`[boss_lever_death.lua:onBossDeath.onDeath]`)
- `forgeKill.onDeath` (`[forge_kill.lua:forgeKill.onDeath]`)
- `creatureevent.onDeath` (`[giant_spider_wyda_death.lua:creatureevent.onDeath]`)
- `monsterDeath.onDeath` (`[spawn_system.lua:monsterDeath.onDeath]`)
- `monsterDeathBoss.onDeath` (`[spawn_system.lua:monsterDeathBoss.onDeath]`)
- `whiteDeerDeath.onDeath` (`[white_deer_death.lua:whiteDeerDeath.onDeath]`)
- `whiteDeerScoutsDeath.onDeath` (`[white_deer_scouts.lua:whiteDeerScoutsDeath.onDeath]`)

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[boss_lever_death.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
