# No Rest For The Wicked

## Overview
Component package under `scripts/quests/no_rest_for_the_wicked` containing 1 files (`actions_arbaziloth_lever.lua`..`actions_arbaziloth_lever.lua`).

## Interface
- `BossLever(config)` assigned to `lever` [actions_arbaziloth_lever.lua:lever]
- `BossLever(config)` registration [actions_arbaziloth_lever.lua:BossLever]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [actions_arbaziloth_lever.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [actions_arbaziloth_lever.lua:Game]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
