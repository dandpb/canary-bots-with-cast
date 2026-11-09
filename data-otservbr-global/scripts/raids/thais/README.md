# Thais

## Overview
Component package under `scripts/raids/thais` containing 2 files (`rats.lua`..`wild_horses.lua`).

## Interface
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
- `Zone("thais.rats")` assigned to `zone` [rats.lua:zone]
- `Zone("thais.rats")` registration [rats.lua:Zone]
- `Raid("thais.wild-horses", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 0,
	initialChance = 30,
	targetChancePerDay = 50,
	maxChancePerCheck = 50,
	maxChecksPerDay = 2,
	minGapBetween = "23h",
})` assigned to `raid` [wild_horses.lua:raid]
- `Raid("thais.wild-horses", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 0,
	initialChance = 30,
	targetChancePerDay = 50,
	maxChancePerCheck = 50,
	maxChecksPerDay = 2,
	minGapBetween = "23h",
})` registration [wild_horses.lua:Raid]
- `Zone("thais.wild-horses")` assigned to `zone` [wild_horses.lua:zone]
- `Zone("thais.wild-horses")` registration [wild_horses.lua:Zone]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [rats.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [wild_horses.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
