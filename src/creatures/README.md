# creatures

## Overview
Package implementation for `src/creatures`, providing component logic and data interfaces for creatures.

## Interface
- `measure` (`[creature.cpp:measure]`)
- `BotEngine` (`[creature.hpp:BotEngine]`)
- `CreatureEvent` (`[creature.hpp:CreatureEvent]`)
- `Condition` (`[creature.hpp:Condition]`)
- `Map` (`[creature.hpp:Map]`)
- `Container` (`[creature.hpp:Container]`)
- `Player` (`[creature.hpp:Player]`)
- `Monster` (`[creature.hpp:Monster]`)
- `Npc` (`[creature.hpp:Npc]`)
- `MonkData_t` (`[creatures_definitions.hpp:MonkData_t]`)
- Subdirectory [`./appearance/README.md`](./appearance/README.md) - Sub-package for appearance
- Subdirectory [`./combat/README.md`](./combat/README.md) - Sub-package for combat
- Subdirectory [`./interactions/README.md`](./interactions/README.md) - Sub-package for interactions
- Subdirectory [`./monsters/README.md`](./monsters/README.md) - Sub-package for monsters
- Subdirectory [`./npcs/README.md`](./npcs/README.md) - Sub-package for npcs
- Subdirectory [`./players/README.md`](./players/README.md) - Sub-package for players

## Invariants
- None

## Side Effects
- Emits system diagnostic logs (`[creature.cpp]`)
- Schedules timed tasks or dispatcher callbacks (`[creature.cpp]`)
- Schedules timed tasks or dispatcher callbacks (`[creature.hpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
