# Input/Output & Persistence (`src/io`)

## Overview

The `src/io` component implements Canary's binary file loaders (`OTB::Loader`, `FileStream`, `PropStream`, `PropWriteStream`), OTBM map and house persistence (`IOMap`, `IOMapSerialize`), player authentication and checkpoint/transactional persistence (`IOLoginData`), and subsystem data managers (`IOBestiary`, `IOBosstiary`, `IOGuild`, `IOMarket`, `IOPrey`, `IOWheel`, `IPlayerStorageRepository`).

## Interface

- `[fileloader.hpp:OTB::Loader]` / `[fileloader.hpp:OTB::Node]` / `[fileloader.hpp:PropStream]` / `[fileloader.hpp:PropWriteStream]` — Memory-mapped OTB tree parser (`mio::mmap_source`) and binary property read/write streams.
- `[filestream.hpp:FileStream]` — Byte buffer stream reader supporting OTB node navigation (`startNode`, `endNode`, `isProp`) and escaped primitive reads (`getU8`, `getU16`, `getU32`, `getU64`, `getString`).
- `[io_definitions.hpp:FILELOADER_ERRORS]` / `[io_definitions.hpp:OTBM_AttrTypes_t]` / `[io_definitions.hpp:OTBM_NodeTypes_t]` / `[io_definitions.hpp:OTBM_TileFlag_t]` / `[io_definitions.hpp:MarketStatistics]` — Shared OTBM format enums and market statistics struct.
- `[iomap.hpp:IOMap]` / `[iomap.hpp:IOMapException]` — OTBM map loader (`loadMap`) and XML loader helpers for monsters, zones, NPCs, and houses (`loadMonsters`, `loadZones`, `loadNpcs`, `loadHouses` and `*Custom` variants).
- `[iomapserialize.hpp:IOMapSerialize]` — House item and metadata persistence (`loadHouseItems`, `saveHouseItems`, `loadHouseInfo`, `saveHouseInfo`).
- `[iologindata.hpp:IOLoginData]` / `[iologindata.hpp:PlayerSaveSnapshot]` — Player authentication (`gameWorldAuthentication`), synchronous load/save (`loadPlayerById`, `loadPlayerByName`, `loadPlayer`, `savePlayer`), split dispatcher-capture / SQL-worker persistence (`capturePlayerSave`, `persistPlayerSave`, `acknowledgePlayerSave`), and VIP/bank helpers.
- `[iobestiary.hpp:IOBestiary]` / `[iobestiary.hpp:Charm]` / `[iobestiary.hpp:g_iobestiary]` — Bestiary kill tracking, charm rune unlocking/assignment, and charm combat parsing (`SoftSingleton` tracked).
- `[io_bosstiary.hpp:IOBosstiary]` / `[io_bosstiary.hpp:g_ioBosstiary]` — Bosstiary kill tracking, loot bonus calculations, and daily boosted boss selection (`loadBoostedBoss`).
- `[ioguild.hpp:IOGuild]` — Guild persistence and war list queries (`loadGuild`, `saveGuild`, `getGuildIdByName`, `getWarList`).
- `[iomarket.hpp:IOMarket]` — Market offer CRUD, expired offer processing (`checkExpiredOffers`, `processExpiredOffers`), and mutex-protected price statistics (`updateStatistics`, `getStatistics`).
- `[ioprey.hpp:IOPrey]` / `[ioprey.hpp:PreySlot]` / `[ioprey.hpp:TaskHuntingSlot]` / `[ioprey.hpp:TaskHuntingOption]` / `[ioprey.hpp:g_ioprey]` — Prey and Task Hunting slot state machines, rerolls, and reward options.
- `[io_wheel.hpp:IOWheel]` / `[io_wheel.hpp:IOWheelBonusData]` — Wheel of Destiny global spell/slot bonus initialization and per-slot vocation bonus functions.
- `[player_storage_repository.hpp:IPlayerStorageRepository]` / `[player_storage_repository_db.hpp:DbPlayerStorageRepository]` / `[player_storage_repository.hpp:g_playerStorageRepository]` — Player key-value storage repository interface and SQL implementation (`load`, `deleteKeys`, `upsert`).
- [functions](./functions/README.md): Granular player load (`IOLoginDataLoad`), save (`IOLoginDataSave`), and online-time (`player_persistence::onlineSeconds`) implementation helpers.

## Invariants

- `[fileloader.hpp:PropStream::read]` / `[fileloader.hpp:PropWriteStream::write]` / `[filestream.cpp:FileStream::read]` — Static assertion requires `std::is_trivially_copyable_v<T>`.
- `[iologindata.cpp:IOLoginData::capturePlayerSave]` / `[iologindata.cpp:IOLoginData::persistPlayerSave]` / `[iologindata.cpp:IOLoginData::acknowledgePlayerSave]` — `capturePlayerSave` must run on the dispatcher thread using a statement-capturing `Database::ScopedConnection` without touching the live SQL connection; `persistPlayerSave` executes the captured statements inside a `DBTransaction` on the SQL worker (retrying up to 5 times with exponential backoff only on InnoDB deadlock `db.canRetryDeadlock(connection)`); `acknowledgePlayerSave` commits the storage and forge deltas back to the in-memory `Player` only after persistence succeeds.
- `[iologindata.cpp:IOLoginData::saveOnlyDataForOnlinePlayer]` — Immediately returns without writing if `player->isOffline()`, preventing partial offline player loads from overwriting forge, bosstiary, wheel, or storage tables.
- `[iobestiary.cpp:IOBestiary::instanceTracker]` — Guarded by `SoftSingleton("IOBestiary")` and `SoftSingletonGuard` to warn if multiple instances are created.
- `[iomarket.cpp:IOMarket::updateStatistics]` / `[iomarket.cpp:IOMarket::getStatistics]` — Access to `purchaseStatistics` and `saleStatistics` is synchronized via `statisticsMutex`.

## Side Effects

- `[fileloader.cpp:OTB::Loader::Loader]` / `[iomap.cpp:IOMap::loadMap]` — Memory-maps OTB/OTBM files from disk via `mio::mmap_source` and populates `Map` tiles, towns, waypoints, houses, zones, and spawns.
- `[iologindata.cpp:IOLoginData]` / `[iomapserialize.cpp:IOMapSerialize]` / `[ioguild.cpp:IOGuild]` / `[iomarket.cpp:IOMarket]` / `[io_bosstiary.cpp:IOBosstiary::loadBoostedBoss]` / `[player_storage_repository_db.cpp:DbPlayerStorageRepository]` — Executes SQL queries and transactions against `accounts`, `players`, `account_viplist`, `account_vipgroups`, `account_vipgrouplist`, `houses`, `house_lists`, `tile_store`, `guilds`, `guild_ranks`, `guild_wars`, `market_offers`, `market_history`, `boosted_boss`, `player_bosstiary`, and `player_storage`.
- `[iomarket.cpp:IOMarket::checkExpiredOffers]` — Schedules asynchronous database tasks via `g_databaseTasks().store(...)` and recurring periodic events on `g_dispatcher()`.
- `[io_wheel.cpp:IOWheel::initializeGlobalData]` — Mutates global `InstantSpell` definitions in `g_spells()` with Wheel of Destiny grade boosts.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
