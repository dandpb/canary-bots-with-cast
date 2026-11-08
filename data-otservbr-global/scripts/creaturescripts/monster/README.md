# Monster

## Overview
Component package under `scripts/creaturescripts/monster` containing 18 files (`gaz_haragoth_heal.lua`..`zavarash_hide.lua`).

## Interface
- `gazHaragothHeal.onThink(creature)` [gaz_haragoth_heal.lua:gazHaragothHeal.onThink]
- `CreatureEvent("GazHaragothHeal")` assigned to `gazHaragothHeal` [gaz_haragoth_heal.lua:gazHaragothHeal]
- `CreatureEvent("GazHaragothHeal")` registration [gaz_haragoth_heal.lua:CreatureEvent]
- `grandMasterOberonImmunity.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType, origin)` [grand_master_oberon_immunity.lua:grandMasterOberonImmunity.onHealthChange]
- `CreatureEvent("OberonImmunity")` assigned to `grandMasterOberonImmunity` [grand_master_oberon_immunity.lua:grandMasterOberonImmunity]
- `CreatureEvent("OberonImmunity")` registration [grand_master_oberon_immunity.lua:CreatureEvent]
- `greaterMinion.onThink(creature)` [greater_minion.lua:greaterMinion.onThink]
- `CreatureEvent("GreaterMinion")` assigned to `greaterMinion` [greater_minion.lua:greaterMinion]
- `CreatureEvent("GreaterMinion")` registration [greater_minion.lua:CreatureEvent]
- `hirintrorHeal.onPrepareDeath(creature, lastHitKiller, mostDamageKiller)` [hirintror_heal.lua:hirintrorHeal.onPrepareDeath]
- `CreatureEvent("HirintrorHeal")` assigned to `hirintrorHeal` [hirintror_heal.lua:hirintrorHeal]
- `CreatureEvent("HirintrorHeal")` registration [hirintror_heal.lua:CreatureEvent]
- `invulnerable.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType)` [invulnerable.lua:invulnerable.onHealthChange]
- `Monster:setInvulnerable()` [invulnerable.lua:Monster:setInvulnerable]
- `Monster:removeInvulnerable()` [invulnerable.lua:Monster:removeInvulnerable]
- `CreatureEvent("monster.invulnerable")` assigned to `invulnerable` [invulnerable.lua:invulnerable]
- `CreatureEvent("monster.invulnerable")` registration [invulnerable.lua:CreatureEvent]
- `removeTeleport(position)` [minion_gaz_haragoth_vortex.lua:removeTeleport]
- `minionDeath.onDeath(creature, corpse, killer, mostDamageKiller, unjustified, mostDamageUnjustified)` [minion_gaz_haragoth_vortex.lua:minionDeath.onDeath]
- `CreatureEvent("MinionGazDeath")` assigned to `minionDeath` [minion_gaz_haragoth_vortex.lua:minionDeath]
- `CreatureEvent("MinionGazDeath")` registration [minion_gaz_haragoth_vortex.lua:CreatureEvent]
- `mirrorImageTransform.onHealthChange(creature, attacker, primaryDamage, primaryType, secondaryDamage, secondaryType)` [mirror_image_transform.lua:mirrorImageTransform.onHealthChange]
- `CreatureEvent("MirrorImageTransform")` assigned to `mirrorImageTransform` [mirror_image_transform.lua:mirrorImageTransform]
- `CreatureEvent("MirrorImageTransform")` registration [mirror_image_transform.lua:CreatureEvent]
- `necromanticMinion.onThink(creature)` [necromantic_minion.lua:necromanticMinion.onThink]

## Invariants
- World position operations verify `Tile(...)` existence before manipulating items or creatures [minion_gaz_haragoth_vortex.lua:Tile]
- Callbacks validate that the triggering creature is a valid `Player` instance (`getPlayer()`) before proceeding [mirror_image_transform.lua:getPlayer]
- Execution paths are gated by quest/player storage state checks via `getStorageValue` [omrafir_explode.lua:getStorageValue]
- World position operations verify `Tile(...)` existence before manipulating items or creatures [shargon_growth_check.lua:Tile]

## Side Effects
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [gaz_haragoth_heal.lua:register]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [gaz_haragoth_heal.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [grand_master_oberon_immunity.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [greater_minion.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [greater_minion.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [greater_minion.lua:transform]
- Schedules asynchronous delayed callbacks on the server dispatcher via `addEvent` [greater_minion.lua:addEvent]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [hirintror_heal.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [invulnerable.lua:register]
- Registers RevScript event/spell/type handlers into the server engine via `:register()` [minion_gaz_haragoth_vortex.lua:register]
- Spawns items, monsters, or NPCs in the game world via `Game.createItem` / `Game.createMonster` / `Game.createNpc` [minion_gaz_haragoth_vortex.lua:Game]
- Mutates player inventory or map tile items (`addItem`, `removeItem`, `transform`, `remove`) [minion_gaz_haragoth_vortex.lua:transform]

## Verification
- Run: `ctest --test-dir build --output-on-failure`
