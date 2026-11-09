# movements

## Overview
Package implementation for `data/scripts/movements`, providing component logic and data interfaces for movements.

## Interface
- `bathtubEnter.onStepIn` (`[bath_tub.lua:bathtubEnter.onStepIn]`)
- `bathtubExit.onStepOut` (`[bath_tub.lua:bathtubExit.onStepOut]`)
- `cake.onAddItem` (`[cake.lua:cake.onAddItem]`)
- `clawOfTheNoxiousSpawn.onEquip` (`[claw_of_the_noxious_spawn.lua:clawOfTheNoxiousSpawn.onEquip]`)
- `closingDoor.onStepIn` (`[closing_door.lua:closingDoor.onStepIn]`)
- `closingDoor.onStepOut` (`[closing_door.lua:closingDoor.onStepOut]`)
- `decay.onStepIn` (`[decay_to.lua:decay.onStepIn]`)
- `dough.onAddItem` (`[dough.lua:dough.onAddItem]`)
- `drowning.onStepIn` (`[drowning.lua:drowning.onStepIn]`)
- `drowning.onStepOut` (`[drowning.lua:drowning.onStepOut]`)

## Invariants
- None

## Side Effects
- None

## Verification
- Run: `ctest --test-dir build --output-on-failure`
