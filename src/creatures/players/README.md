# Players Subsystem

## Overview
Implements the `Player` entity (`Player`, inheriting `Creature`, `Cylinder`, and `Bankable`) and coordinates all player-owned subsystems, including inventory/container management, combat/skill/experience progression, Monk harmony/virtue/mantra mechanics, stash and depot search, prey/task-hunting/bestiary/bosstiary tracking, Exaltation Forge actions, live cast broadcasting, and autonomous native bots.

## Interface
- `Player`, `Player::PlayerLock`, `Player::SkullTimeInfo`, `Player::AddItemBatchOptions`, `CharmInfo`, `OpenContainer` (`[player.hpp:Player]`, `[player.hpp:Player::PlayerLock]`, `[player.hpp:CharmInfo]`, `[player.hpp:OpenContainer]`, `[player.cpp:Player]`): Core player entity managing lifecycle (`createNativeBot`, `setID`, `addList`, `removeList`, `removePlayer`, `spawn`, `despawn`, `death`), combat and skills (`blockHit`, `doAttacking`, `drainHealth`, `drainMana`, `addManaSpent`, `addSkillAdvance`, `calculateFlatDamageHealing`, `getMitigation`), Monk mechanics (`getVirtue`, `setVirtue`, `setSerene`, `buildHarmony`, `spendHarmony`, `getHarmonyDamage`, `getMantra`), inventory/stash/depot cylinders (`queryAdd`, `addItemBatch`, `stowItem`, `withdrawItem`, `requestDepotItems`, `retrieveAllItemsFromDepotSearch`), Exaltation Forge (`forgeFuseItems`, `forgeTransferItemTier`, `forgeResourceConversion`), cast viewer fan-out (`setCastBroadcasting`, `addCastViewer`, `removeCastViewer`, `forwardToCastViewers`, `getCastViewerCount`, `setSyntheticCastViewers`), and component accessors (`wheel()`, `achiev()`, `badge()`, `title()`, `cyclopedia()`, `forgeHistory()`, `vip()`, `animusMastery()`, `attachedEffects()`, `storage()`).
- `HighscoreCategory` (`[highscore_category.hpp:HighscoreCategory]`): Name and ID pair representing a highscore leaderboard category.
- `ItemsTierKey`, `ItemsTierCountList`, `TierCountPairHash` (`[stash_definitions.hpp:ItemsTierKey]`, `[stash_definitions.hpp:ItemsTierCountList]`, `[stash_definitions.hpp:TierCountPairHash]`): Hash map types keying item counts by `(itemId, tier)` for depot, inbox, and stash summaries.
- [account](./account/README.md): Process-local per-account concurrency guard (`AccountLocker`, `AccountLock`).
- [animus_mastery](./animus_mastery/README.md): Monster soul/animus mastery tracking and experience bonus calculation (`AnimusMastery`).
- [bot](./bot/README.md): Autonomous player bot engine (`IBotEngine`, `BotEngine`, `BotEngineLoader`), pathfinding (`botnav`), and pilot brain IPC (`botbrain`).
- [cast](./cast/README.md): Abstract viewer session sink (`CastViewerSink`) for live player and bot cast streams.
- [components](./components/README.md): Modular player feature components (`PlayerAchievement`, `PlayerAttachedEffects`, `PlayerBadge`, `PlayerCyclopedia`, `PlayerForgeHistory`, `PlayerStorage`, `PlayerTitle`, `PlayerVIP`, and `./components/wheel`).
- [grouping](./grouping/README.md): Social, permission, and companion groupings (`Familiars`, `Groups`, `Guild`, `Party`, `TeamFinder`).
- [imbuements](./imbuements/README.md): Item imbuement definitions, categories, and active decay tracking (`Imbuements`, `Imbuement`, `ImbuementDecay`).
- [storages](./storages/README.md): XML loader and validator for symbolic player storage keys (`Storages`).
- [vocations](./vocations/README.md): Player vocation definitions, combat/skill multipliers, and XML configuration loading (`Vocation`, `Vocations`).

## Invariants
- `Player` is non-copyable and uniquely identified in-world by `id` in the range `[playerFirstID, playerLastID)` and persistently by `guid` (`[player.hpp:Player]`, `[player.hpp:Player::getFirstID]`, `[player.hpp:Player::getGUID]`).
- `Player::PlayerLock` acquires the per-player `std::mutex mutex` via RAII (`[player.hpp:Player::PlayerLock]`), and quick-loot operations serialize container mutations with `quickLootMutex` (`[player.hpp:Player::quickLootMutex]`).
- Step speed is clamped between `PLAYER_MIN_SPEED` (`10`) and `PLAYER_MAX_SPEED` (or `PLAYER_MAX_STAFF_SPEED` `8000` when `PlayerFlags_t::SetMaxSpeed` is set) (`[player.hpp:Player::getStepSpeed]`).
- `botAllowFcPos` is a transient single-tile whitelist: A* pathfinding for a bot player may only step onto a floor-change or teleport tile when its position matches `botAllowFcPos` (`[player.hpp:Player::isBotAllowFcPos]`, `[player.hpp:Player::botAllowFcPos]`).
- `getCastViewerCount()` returns real connected cast viewers plus `syntheticCastViewers` (used by performance probes), whereas `getRealCastViewerCount()` counts only live `ProtocolGame` viewer sessions (`[player.hpp:Player::getCastViewerCount]`, `[player.hpp:Player::getRealCastViewerCount]`).

## Side Effects
- Mutates world, tile, cylinder, container, party, guild, and market state via `g_game()`, `Map`, and `Cylinder` notifications (`[player.hpp:Player::postAddNotification]`, `[player.hpp:Player::postRemoveNotification]`, `[player.hpp:Player::onCreatureMove]`).
- Sends network packets to the owning `ProtocolGame` client and fans them out to attached `castViewers` (`[player.hpp:Player::forwardToCastViewers]`, `[player.hpp:Player::sendNetworkMessage]`).
- Schedules delayed movement, action, potion, and imbuement tracker tasks on `g_dispatcher()` (`[player.hpp:Player::createPlayerTask]`, `[player.hpp:Player::setNextWalkActionTask]`, `[player.hpp:Player::setNextActionTask]`).
- Invokes Lua creature, player, party, and storage events/callbacks (`Events`, `EventsCallbacks`) and triggers database/KV persistence via `IOLoginData`, `SaveManager`, and player components.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
