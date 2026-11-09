# The Primal Ordeal

## Overview
Component package under `scripts/quests/the_primal_ordeal` containing 2 files (`creaturescripts_magma_bubble_death.lua`..`creaturescripts_the_primal_menace_killed.lua`).

## Interface
- `hasOutfit(player)` [creaturescripts_magma_bubble_death.lua:hasOutfit]
- `magmaBubbleDeath.onDeath(creature, corpse, killer, mostDamage, unjustified, mostDamage_unjustified)` [creaturescripts_magma_bubble_death.lua:magmaBubbleDeath.onDeath]
- `CreatureEvent("MagmaBubbleDeath")` assigned to `magmaBubbleDeath` [creaturescripts_magma_bubble_death.lua:magmaBubbleDeath]
- `CreatureEvent("MagmaBubbleDeath")` registration [creaturescripts_magma_bubble_death.lua:CreatureEvent]
- `thePrimalMenaceDeath.onDeath(creature)` [creaturescripts_the_primal_menace_killed.lua:thePrimalMenaceDeath.onDeath]
- `CreatureEvent("ThePrimalMenaceDeath")` assigned to `thePrimalMenaceDeath` [creaturescripts_the_primal_menace_killed.lua:thePrimalMenaceDeath]
- `CreatureEvent("ThePrimalMenaceDeath")` registration [creaturescripts_the_primal_menace_killed.lua:CreatureEvent]

## Invariants
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_magma_bubble_death.lua:getStorageValue]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [creaturescripts_the_primal_menace_killed.lua:getStorageValue]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_magma_bubble_death.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_magma_bubble_death.lua:setStorageValue]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [creaturescripts_the_primal_menace_killed.lua:register]
- Mutates player or global storage state via `setStorageValue` [creaturescripts_the_primal_menace_killed.lua:setStorageValue]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
