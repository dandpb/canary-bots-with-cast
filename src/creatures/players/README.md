# Players Subsystem

## Overview
Implements the `Player` entity (`Player`, inheriting `Creature`, `Cylinder`, and `Bankable`) and coordinates all player-owned subsystems, including inventory/container management, combat/skill/experience progression, Monk harmony/virtue/mantra mechanics, stash and depot search, prey/task-hunting/bestiary/bosstiary tracking, Exaltation Forge actions, live cast broadcasting, and autonomous native bots.

## Interface
- `Player`, `Player::PlayerLock`, `Player::SkullTimeInfo`, `Player::AddItemBatchOptions`, `SkillsEquipment`, `BaseCritical`, `ExivaRestrictions`, `CharmInfo`, `OpenContainer` (`[player.hpp:Player]`, `[player.hpp:Player::PlayerLock]`, `[player.hpp:CharmInfo]`, `[player.hpp:OpenContainer]`, `[player.cpp:Player]`): Core player entity managing lifecycle (`createNativeBot`, `setID`, `addList`, `removeList`, `removePlayer`, `spawn`, `despawn`, `death`), combat and skills (`blockHit`, `doAttacking`, `drainHealth`, `drainMana`, `addManaSpent`, `addSkillAdvance`, `calculateFlatDamageHealing`, `getMitigation`, `setPvpMode`, `getPvpMode`), Monk mechanics (`getVirtue`, `setVirtue`, `setSerene`, `buildHarmony`, `spendHarmony`, `getHarmonyDamage`, `getMantra`), inventory/stash/depot cylinders and batched container updates (`queryAdd`, `addItemBatch`, `addItemBatchToPaginedContainer`, `beginBatchUpdate`, `endBatchUpdate`, `sendBatchUpdateContainer`, `isBatching`, `stowItem`, `withdrawItem`, `requestDepotItems`, `retrieveAllItemsFromDepotSearch`), Exaltation Forge (`forgeFuseItems`, `forgeTransferItemTier`, `forgeResourceConversion`), cast viewer & visual replay fan-out (`setCastBroadcasting`, `addCastViewer`, `removeCastViewer`, `forwardToCastViewers`, `getCastViewerCount`, `setSyntheticCastViewers`, `visualReplayEncoder`, `hasVisualReplayOutput`, `stopVisualReplay`), and component accessors (`wheel()`, `achiev()`, `badge()`, `title()`, `cyclopedia()`, `forgeHistory()`, `vip()`, `animusMastery()`, `attachedEffects()`, `storage()`, `weaponProficiency()`, `m_pvpPlayer`).
- `HighscoreCategory` (`[highscore_category.hpp:HighscoreCategory]`): Name and ID pair representing a highscore leaderboard category.
- `ItemsTierKey`, `ItemsTierCountList`, `TierCountPairHash` (`[stash_definitions.hpp:ItemsTierKey]`, `[stash_definitions.hpp:ItemsTierCountList]`, `[stash_definitions.hpp:TierCountPairHash]`): Hash map types keying item counts by `(itemId, tier)` for depot, inbox, and stash summaries.
- [account](../../account/README.md): Authentication, account records, and character lists.
- [account (local pointer)](./account/README.md): Cross-reference stub linking account management and protocol admission.
- [animus_mastery](./animus_mastery/README.md): Monster soul/animus mastery tracking and experience bonus calculation (`AnimusMastery`).
- [bot](./bot/README.md): Autonomous player bot engine (`IBotEngine`, `BotEngine`, `BotEngineLoader`), pathfinding (`botnav`), and pilot brain IPC (`botbrain`).
- [cast](./cast/README.md): Asynchronous per-GUID human caster `cast_broadcasters` SQL publisher (`CastPublisher`, `g_castPublisher`).
- [components](./components/README.md): Modular player feature components (`PlayerAchievement`, `PlayerAttachedEffects`, `PlayerBadge`, `PlayerCyclopedia`, `PlayerForgeHistory`, `PlayerStorage`, `PlayerTitle`, `PlayerVIP`, `WeaponProficiency`, `./components/pvp`, and `./components/wheel`).
- [grouping](./grouping/README.md): Social, permission, and companion groupings (`Familiars`, `Groups`, `Guild`, `Party`, `TeamFinder`).
- [imbuements](./imbuements/README.md): Item imbuement definitions, categories, and active decay tracking (`Imbuements`, `Imbuement`, `ImbuementDecay`).
- [livestream](./livestream/README.md): Built-in player livestream manager (`LivestreamManager`, `g_livestream`).
- [management](./management/README.md): Banishment and IP-ban helpers (`IOBan`).
- [storages](./storages/README.md): XML loader and validator for symbolic player storage keys (`Storages`).
- [vocations](./vocations/README.md): Player vocation definitions, combat/skill multipliers, and XML configuration loading (`Vocation`, `Vocations`).

## Invariants
- `Player` is non-copyable and uniquely identified in-world by `id` in the range `[playerFirstID, playerLastID)` and persistently by `guid` (`[player.hpp:Player]`, `[player.hpp:Player::getFirstID]`, `[player.hpp:Player::getGUID]`).
- `Player::PlayerLock` acquires the per-player `std::mutex mutex` via RAII (`[player.hpp:Player::PlayerLock]`), and quick-loot operations serialize container mutations with `quickLootMutex` (`[player.hpp:Player::quickLootMutex]`).
- Step speed is clamped between `PLAYER_MIN_SPEED` (`10`) and `PLAYER_MAX_SPEED` (or `PLAYER_MAX_STAFF_SPEED` `65535` when `PlayerFlags_t::SetMaxSpeed` is set) (`[player.hpp:Player::getStepSpeed]`, `[player.hpp:Player::PLAYER_MAX_STAFF_SPEED]`).
- `botAllowFcPos` is a transient single-tile whitelist: A* pathfinding for a bot player may only step onto a floor-change or teleport tile when its position matches `botAllowFcPos` (`[player.hpp:Player::isBotAllowFcPos]`, `[player.hpp:Player::botAllowFcPos]`).
- `getCastViewerCount()` returns real connected cast viewers plus `syntheticCastViewers` (used by performance probes), whereas `getRealCastViewerCount()` counts only live `ProtocolGame` viewer sessions (`[player.hpp:Player::getCastViewerCount]`, `[player.hpp:Player::getRealCastViewerCount]`).

## Side Effects
- Mutates world, tile, cylinder, container, party, guild, and market state via `g_game()`, `Map`, and `Cylinder` notifications (`[player.hpp:Player::postAddNotification]`, `[player.hpp:Player::postRemoveNotification]`, `[player.hpp:Player::onCreatureMove]`).
- Sends network packets to the owning `ProtocolGame` client and fans them out to attached `castViewers` (`[player.hpp:Player::forwardToCastViewers]`, `[player.hpp:Player::sendNetworkMessage]`).
- Schedules delayed movement, action, potion, and imbuement tracker tasks on `g_dispatcher()` (`[player.hpp:Player::createPlayerTask]`, `[player.hpp:Player::setNextWalkActionTask]`, `[player.hpp:Player::setNextActionTask]`).
- Invokes Lua creature, player, party, and storage events/callbacks (`Events`, `EventsCallbacks`) and triggers database/KV persistence via `IOLoginData`, `SaveManager`, and player components.

## Verification
- See the [C++ build and test guide](../../../tests/README.md#running-tests).
