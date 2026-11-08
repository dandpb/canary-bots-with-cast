# data

## Overview
Package implementation for `data`, providing component logic and data interfaces for data.

## Interface
- `IsRunningGlobalDatapack` (`[global.lua:IsRunningGlobalDatapack]`)
- `IsRetroPVP` (`[global.lua:IsRetroPVP]`)
- `IsTravelFree` (`[global.lua:IsTravelFree]`)
- `addStamina` (`[global.lua:addStamina]`)
- `BotPlayers` (`[global.lua:BotPlayers]`)
- `eventsTrainer` (`[global.lua:eventsTrainer]`)
- `eventsPz` (`[global.lua:eventsPz]`)
- Subdirectory [`./chatchannels/README.md`](./chatchannels/README.md) - Sub-package for chatchannels
- Subdirectory [`./events/README.md`](./events/README.md) - Sub-package for events
- Subdirectory [`./json/README.md`](./json/README.md) - Sub-package for json
- Subdirectory [`./lib/README.md`](./lib/README.md) - Sub-package for lib
- Subdirectory [`./libs/README.md`](./libs/README.md) - Sub-package for libs
- Subdirectory [`./modules/README.md`](./modules/README.md) - Sub-package for modules
- Subdirectory [`./npclib/README.md`](./npclib/README.md) - Sub-package for npclib
- Subdirectory [`./scripts/README.md`](./scripts/README.md) - Sub-package for scripts

## Invariants
- None

## Side Effects
- Schedules timed tasks or dispatcher callbacks (`[global.lua]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
