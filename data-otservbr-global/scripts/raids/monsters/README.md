# Monsters

## Overview
Component package under `scripts/raids/monsters` containing 6 files (`draptor.lua`..`yeti.lua`).

## Interface
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
- `Zone("farmine.draptor")` assigned to `zone` [draptor.lua:zone]
- `Zone("farmine.draptor")` registration [draptor.lua:Zone]
- `Raid("tiquanda.midnight-panther", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.03,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.9,
})` assigned to `raid` [midnight_panther.lua:raid]
- `Raid("tiquanda.midnight-panther", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.03,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.9,
})` registration [midnight_panther.lua:Raid]
- `Zone("tiquanda.midnight-panther")` assigned to `zone` [midnight_panther.lua:zone]
- `Zone("tiquanda.midnight-panther")` registration [midnight_panther.lua:Zone]
- `Raid("thais.rats", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 2,
	initialChance = 0.04,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.4,
	minGapBetween = "36h",
})` assigned to `raid` [rats.lua:raid]
- `Raid("thais.rats", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 2,
	initialChance = 0.04,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.4,
	minGapBetween = "36h",
})` registration [rats.lua:Raid]
- `Zone("thais.rats")` assigned to `zone` [rats.lua:zone]
- `Zone("thais.rats")` registration [rats.lua:Zone]
- `Raid("farmine.draptor", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 2,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.6,
	minGapBetween = "12h",
})` assigned to `raid` [undead_cavebear.lua:raid]
- `Raid("farmine.draptor", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 2,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.6,
	minGapBetween = "12h",
})` registration [undead_cavebear.lua:Raid]
- `Zone("farmine.draptor")` assigned to `zone` [undead_cavebear.lua:zone]
- `Zone("farmine.draptor")` registration [undead_cavebear.lua:Zone]
- `Raid("thais.wild-horses", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 30,
	targetChancePerDay = 50,
	maxChancePerCheck = 50,
	maxChecksPerDay = 2,
	minGapBetween = "12h",
})` assigned to `raid` [wild_horses.lua:raid]
- `Raid("thais.wild-horses", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 30,
	targetChancePerDay = 50,
	maxChancePerCheck = 50,
	maxChecksPerDay = 2,
	minGapBetween = "12h",
})` registration [wild_horses.lua:Raid]
- `Zone("thais.wild-horses")` assigned to `zone` [wild_horses.lua:zone]
- `Zone("thais.wild-horses")` registration [wild_horses.lua:Zone]
- `Raid("folda.yeti", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 2,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.6,
	minGapBetween = "48h",
})` assigned to `raid` [yeti.lua:raid]
- `Raid("folda.yeti", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 2,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.6,
	minGapBetween = "48h",
})` registration [yeti.lua:Raid]
- `Zone("folda.yeti")` assigned to `zone` [yeti.lua:zone]
- `Zone("folda.yeti")` registration [yeti.lua:Zone]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [draptor.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [midnight_panther.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [rats.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [undead_cavebear.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [wild_horses.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [yeti.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
