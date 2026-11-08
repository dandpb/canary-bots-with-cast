# Events Scripts

## Overview

Legacy XML-bound event handler scripts for `Creature`, `Party`, and `Player` entities (`creature.lua`, `monster.lua`, `party.lua`, `player.lua`), invoked by the C++ engine according to `../events.xml`.

## Interface

- `[creature.lua:Creature:onTargetCombat]`: `function Creature:onTargetCombat(target)` — validates PvP/summon/party/secure-mode targeting rules and triggers event stamina.
- `[creature.lua:Creature:onChangeOutfit]`: `function Creature:onChangeOutfit(outfit)` — synchronizes familiar summon lookType when a player changes outfit.
- `[creature.lua:Creature:onDrainHealth]`: `function Creature:onDrainHealth(attacker, typePrimary, damagePrimary, typeSecondary, damageSecondary, colorPrimary, colorSecondary)` — hook for health drain adjustments.
- `[party.lua:Party:onJoin]`: `function Party:onJoin(player)` — schedules `party:refreshHazard()` via `addEvent`.
- `[party.lua:Party:onLeave]`: `function Party:onLeave(player)` — schedules `party:refreshHazard()` and `player:updateHazard()` via `addEvent`.
- `[party.lua:Party:onDisband]`: `function Party:onDisband()` — schedules hazard refresh for disbanded members.
- `[party.lua:Party:onShareExperience]`: `function Party:onShareExperience(exp)` — computes shared party experience multiplier based on unique vocation count and party size.
- `[player.lua:Player:onLookInBattleList]`: `function Player:onLookInBattleList(creature, distance)` — formats battle list inspection text (including GM/God extended diagnostic info).
- `[player.lua:Player:onMoveItem]`: `function Player:onMoveItem(item, count, fromPosition, toPosition, fromCylinder, toCylinder)` — enforces item movement constraints, anti-push rate limits, container/tile restrictions, and two-handed/shield equipment swapping.
- `[player.lua:Player:onItemMoved]`: `function Player:onItemMoved(item, count, fromPosition, toPosition, fromCylinder, toCylinder)` — handles Secret Library quest tile/boss triggers on item move.
- `[player.lua:Player:onMoveCreature]`: `function Player:onMoveCreature(creature, fromPosition, toPosition)` — blocks pushing players currently in `_G.OnExerciseTraining`.
- `[player.lua:Player:onReportRuleViolation]`: `function Player:onReportRuleViolation(targetName, reportType, reportReason, comment, translation)` — writes rule violation reports to disk.
- `[player.lua:Player:onReportBug]`: `function Player:onReportBug(message, position, category)` — writes player bug reports to disk.
- `[player.lua:Player:onTurn]`: `function Player:onTurn(direction)` — teleports access-group players one tile forward when turning in their current facing direction.
- `[player.lua:Player:onTradeRequest]`: `function Player:onTradeRequest(target, item)` — blocks trading items with `IMMOVABLE_ACTION_ID` or store item IDs (`storeItemID`).
- `[player.lua:Player:onGainExperience]`: `function Player:onGainExperience(source, exp, rawExp)` — applies charm, soulpit, stamina, XP boost, concoction, VIP, hazard, and stage multipliers to gained experience.
- `[player.lua:Player:onLoseExperience]`: `function Player:onLoseExperience(exp)` — hook for experience loss adjustment.
- `[player.lua:Player:onGainSkillTries]`: `function Player:onGainSkillTries(skill, tries)` — applies global datapack skill growth limits, VIP skill bonus, and skill stage multipliers.
- `[player.lua:Player:onCombat]`: `function Player:onCombat(target, item, primaryDamage, primaryType, secondaryDamage, secondaryType)` — applies elemental amplification/resilience and charm/tier combat modifiers.
- `[player.lua:Player:onChangeZone]`: `function Player:onChangeZone(zone)` — manages protection-zone stamina regeneration timers (`staminaBonus.eventsPz`).
- `[player.lua:Player:onInventoryUpdate]`: `function Player:onInventoryUpdate(item, slot, equip)` — triggers inventory update callbacks.

## Invariants

- `[creature.lua:Creature:onTargetCombat]`: Summons and their player masters cannot attack each other (`RETURNVALUE_YOUMAYNOTATTACKTHISCREATURE`); party members cannot attack each other when `not IsRetroPVP()` or `PARTY_PROTECTION ~= 0`; secure-mode players cannot attack `SKULL_NONE` players when `not IsRetroPVP()` or `ADVANCED_SECURE_MODE ~= 0`.
- `[party.lua:Party:onShareExperience]`: Shared experience multiplier equals `0.1 * uniqueVocationsCount^2 - 0.2 * uniqueVocationsCount + 1.3`, reduced by `0.1` when `partySize >= 4`.
- `[player.lua:Player:onMoveItem]`: Rejects moving items with `IMMOVABLE_ACTION_ID`, onto teleports (`blockTeleportTrashing`), onto tiles exceeding `20` items (`tilelimit`), into reward chests/boss corpses (`ITEM_ATTRIBUTE_CORPSEOWNER == 2^31 - 1`), or exceeding anti-push rate limits (`maxItemsPerSeconds = 1`, `exhaustTime = 2000`); enforces a `2000` ms exhaust on equipping `ITEM_STONE_SKIN_AMULET` into `CONST_SLOT_NECKLACE`.
- `[player.lua:Player:onMoveCreature]`: Players registered in `_G.OnExerciseTraining[creature:getId()]` cannot be pushed unless the mover has `PlayerFlag_CanPushAllCreatures`.
- `[player.lua:Player:onTradeRequest]`: Rejects trading items with `item:getActionId() == IMMOVABLE_ACTION_ID` or listed in `storeItemID`.
- `[player.lua:Player:onGainExperience]`, `[player.lua:Player:onGainSkillTries]`: VIP experience and skill bonuses are capped at `100`%; skill tries return `0` when `IsRunningGlobalDatapack()` and `isSkillGrowthLimited(self, skill)` is true.

## Side Effects

- `[party.lua:Party:onJoin]`, `[party.lua:Party:onLeave]`, `[party.lua:Party:onDisband]`: Schedules asynchronous `addEvent` (`100` ms) calls to `party:refreshHazard()` and `player:updateHazard()`.
- `[player.lua:Player:onGainExperience]`: Mutates global tables `_G.NextUseStaminaTime`, `_G.NextUseXpStamina`, `_G.NextUseConcoctionTime`, player KV `"daily-reward-xp-boost"`, player stamina/XP boost timers, and calls `Concoction.experienceTick`.
- `[player.lua:Player:onMoveItem]`, `[player.lua:Player:onItemMoved]`: Moves conflicting two-handed/off-hand items into parent containers, mutates quest storage `Storage.Quest.U11_80.TheSecretLibrary.SmallIslands`, and transforms `The Remorseless Corruptor` into `The Corruptor of Souls`.
- `[player.lua:Player:onReportRuleViolation]`, `[player.lua:Player:onReportBug]`: Creates report directories via `FS.mkdir_p` and writes report files under `reports/players/` and `reports/bugs/`.
- `[player.lua:Player:onChangeZone]`: Schedules and cancels recurring `addStamina` events in `staminaBonus.eventsPz[playerId]`.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
