# Raids

## Overview
Intermediate blueprint grouping 3 subdirectories under `scripts/raids`.

## Subdirectories & Boundaries
- [bosses](./bosses/README.md) - Component package under `scripts/raids/bosses` containing 13 files (`arachir_the_ancient_one.lua`..`white_pale.lua`).
- [monsters](./monsters/README.md) - Component package under `scripts/raids/monsters` containing 6 files (`draptor.lua`..`yeti.lua`).
- [thais](./thais/README.md) - Component package under `scripts/raids/thais` containing 2 files (`rats.lua`..`wild_horses.lua`).

## Interface
- `Raid("drefia.arachir", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.8,
})` assigned to `raid` [arachir_the_ancient_one.lua:raid]
- `Raid("drefia.arachir", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.8,
})` registration [arachir_the_ancient_one.lua:Raid]
- `Raid("farmine.draptor", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 2,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.6,
	minGapBetween = "12h",
})` assigned to `raid` [draptor.lua:raid]
- `Raid("farmine.draptor", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 2,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.6,
	minGapBetween = "12h",
})` registration [draptor.lua:Raid]
- `Raid("thais.rats", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 0,
	targetChancePerDay = 30,
	maxChancePerCheck = 50,
	minGapBetween = "36h",
})` assigned to `raid` [rats.lua:raid]
- `Raid("thais.rats", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 0,
	targetChancePerDay = 30,
	maxChancePerCheck = 50,
	minGapBetween = "36h",
})` registration [rats.lua:Raid]
- [bosses](./bosses/README.md) - Component package under `scripts/raids/bosses` containing 13 files (`arachir_the_ancient_one.lua`..`white_pale.lua`).
- [monsters](./monsters/README.md) - Component package under `scripts/raids/monsters` containing 6 files (`draptor.lua`..`yeti.lua`).
- [thais](./thais/README.md) - Component package under `scripts/raids/thais` containing 2 files (`rats.lua`..`wild_horses.lua`).

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [arachir_the_ancient_one.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [draptor.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [rats.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
