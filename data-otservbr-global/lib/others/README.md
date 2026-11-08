# Others

## Overview
Component package under `lib/others` containing 3 files (`dawnport.lua`..`soulpit.lua`).

## Interface
- `Player.changeVocation(self, newVocationId)` [dawnport.lua:Player.changeVocation]
- `isSkillGrowthLimited(player, skillId)` [dawnport.lua:isSkillGrowthLimited]
- `removeMainlandSmugglingItems(player)` [dawnport.lua:removeMainlandSmugglingItems]
- Global symbol `Dawnport` [dawnport.lua:Dawnport]
- `dofile(CORE_DIRECTORY .. "/libs/functions/vocation.lua")` module loader [dawnport.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/lib/others/dawnport.lua")` module loader [load.lua:dofile]
- `dofile(DATA_DIRECTORY .. "/lib/others/soulpit.lua")` module loader [load.lua:dofile]
- `Zone("soulpit")` assigned to `zone` [soulpit.lua:zone]
- `Zone("soulpit")` registration [soulpit.lua:Zone]
- Global symbol `SoulPit` [soulpit.lua:SoulPit]

## Invariants
- None

## Side Effects
- Loads and executes `CORE_DIRECTORY .. "/libs/functions/vocation.lua"` via `dofile` [dawnport.lua:dofile]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [dawnport.lua:transform]
- Loads and executes `DATA_DIRECTORY .. "/lib/others/dawnport.lua"` via `dofile` [load.lua:dofile]
- Loads and executes `DATA_DIRECTORY .. "/lib/others/soulpit.lua"` via `dofile` [load.lua:dofile]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [soulpit.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
