# Bosses

## Overview
Component package under `scripts/raids/bosses` containing 13 files (`arachir_the_ancient_one.lua`..`white_pale.lua`).

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
- `Zone("drefia.arachir")` assigned to `zone` [arachir_the_ancient_one.lua:zone]
- `Zone("drefia.arachir")` registration [arachir_the_ancient_one.lua:Zone]
- `Raid("muggy_plains.battlemaster_zunzu", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.8,
})` assigned to `raid` [battlemaster_zunzu.lua:raid]
- `Raid("muggy_plains.battlemaster_zunzu", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.8,
})` registration [battlemaster_zunzu.lua:Raid]
- `Zone("muggy_plains.battlemaster_zunzu")` assigned to `zone` [battlemaster_zunzu.lua:zone]
- `Zone("muggy_plains.battlemaster_zunzu")` registration [battlemaster_zunzu.lua:Zone]
- `Raid("nargor.diblis", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.8,
})` assigned to `raid` [diblis_the_fair.lua:raid]
- `Raid("nargor.diblis", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.8,
})` registration [diblis_the_fair.lua:Raid]
- `Zone("nargor.diblis")` assigned to `zone` [diblis_the_fair.lua:zone]
- `Zone("nargor.diblis")` registration [diblis_the_fair.lua:Zone]
- `Raid("fury-gates.furiosa", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.01,
	targetChancePerDay = 0.01,
	maxChancePerCheck = 0.6,
})` assigned to `raid` [furyosa.lua:raid]
- `Raid("fury-gates.furiosa", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.01,
	targetChancePerDay = 0.01,
	maxChancePerCheck = 0.6,
})` registration [furyosa.lua:Raid]
- `Zone("fury-gates.furiosa")` assigned to `zone` [furyosa.lua:zone]
- `Zone("fury-gates.furiosa")` registration [furyosa.lua:Zone]
- `Raid("svargrond.hirintror", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.8,
})` assigned to `raid` [hirintror.lua:raid]
- `Raid("svargrond.hirintror", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.8,
})` registration [hirintror.lua:Raid]
- `Zone("svargrond.hirintror")` assigned to `zone` [hirintror.lua:zone]
- `Zone("svargrond.hirintror")` registration [hirintror.lua:Zone]
- `Raid("roshamuul.mawhawk", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 2,
	initialChance = 0.04,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.4,
})` assigned to `raid` [mawhawk.lua:raid]
- `Raid("roshamuul.mawhawk", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 2,
	initialChance = 0.04,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.4,
})` registration [mawhawk.lua:Raid]
- `Zone("roshamuul.mawhawk")` assigned to `zone` [mawhawk.lua:zone]
- `Zone("roshamuul.mawhawk")` registration [mawhawk.lua:Zone]
- `Raid("edron.valorcrest", {
	zone = zone,
	allowedDays = { "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" },
	minActivePlayers = 3,
	initialChance = 0.02,
	targetChancePerDay = 0.02,
	maxChancePerCheck = 0.8,
})` assigned to `raid` [sir_valorcrest.lua:raid]

## Invariants
- None

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [arachir_the_ancient_one.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [battlemaster_zunzu.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [diblis_the_fair.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [furyosa.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [hirintror.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [mawhawk.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [sir_valorcrest.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [the_old_widow.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [the_pale_count.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [the_welter.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [tyrn.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [weakened_shlorg.lua:register]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
