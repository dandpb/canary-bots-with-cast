# Player Login & Persistence Functions (`src/io/functions`)

## Overview

The `src/io/functions` component implements the granular player loading (`IOLoginDataLoad`), saving (`IOLoginDataSave`), and online-time calculation (`player_persistence::onlineSeconds`) helpers used by `IOLoginData`. It handles deserializing and serializing player attributes, skills, blessings, conditions, animus mastery, inventory/depot/inbox/reward/stash items, bestiary charms, bosstiary, prey/task-hunting slots, forge history, storage deltas, and Wheel of Destiny / virtue state.

## Interface

- `[iologindata_load_player.hpp:IOLoginDataLoad]` — Static player loader helper methods: `preLoadPlayer`, `loadPlayerBasicInfo`, `loadPlayerExperience`, `loadPlayerBlessings`, `loadPlayerConditions`, `loadPlayerAnimusMastery`, `loadPlayerDefaultOutfit`, `loadPlayerSkullSystem`, `loadPlayerSkill`, `loadPlayerKills`, `loadPlayerGuild`, `loadPlayerStashItems`, `loadPlayerBestiaryCharms`, `loadPlayerInstantSpellList`, `loadPlayerInventoryItems`, `loadPlayerStoreInbox`, `loadPlayerDepotItems`, `loadRewardItems`, `loadPlayerInboxItems`, `loadPlayerStorageMap`, `loadPlayerVip`, `loadPlayerPreyClass`, `loadPlayerTaskHuntingClass`, `loadPlayerForgeHistory`, `loadPlayerBosstiary`, `loadPlayerInitializeSystem`, `loadPlayerUpdateSystem`.
- `[iologindata_save_player.hpp:IOLoginDataSave]` — Static player persistence helper methods: `savePlayerFirst`, `savePlayerStash`, `savePlayerSpells`, `savePlayerKills`, `savePlayerBestiarySystem`, `savePlayerItem`, `savePlayerDepotItems`, `saveRewardItems`, `savePlayerInbox`, `savePlayerPreyClass`, `savePlayerTaskHuntingClass`, `savePlayerForgeHistory`, `savePlayerBosstiary`, `savePlayerStorage`, `savePlayerSystems`.
- `[player_online_time.hpp:player_persistence::onlineSeconds]` — Pure helper computing elapsed online seconds `(now - login)` while returning `0` when `login <= 0 || now <= login`.

## Invariants

- `[iologindata_load_player.cpp:IOLoginDataLoad::loadPlayerInitializeSystem]` — Skips `badge().checkAndUpdateNewBadges()`, `title().checkAndUpdateNewTitles()`, and `cyclopedia().loadSummaryData()` when `player->isBotPlayer()` is true, preventing expensive synchronous account-wide queries on shared bot accounts.
- `[player_online_time.hpp:player_persistence::onlineSeconds]` — Returns `0` whenever `login <= 0` or `now <= login` (such as headless bots that bypass normal login timestamp setup).
- `[iologindata_save_player.cpp:IOLoginDataSave::savePlayerFirst]` — Ensures `player->getHealth() > 0` before saving (clamping dead players to `1` HP via `player->changeHealth(1)`) and, when `!db.isCapturingStatements()` and the database `players.save` flag is `0`, only updates `lastlogin` and `lastip`.
- `[iologindata_save_player.cpp:IOLoginDataSave::savePlayerStorage]` — Calls `storage.prepareForPersist()` and writes `delta.deletions` and `delta.upserts` through `g_playerStorageRepository()`, outputting the uncommitted `delta` to `*persisted` so the caller can acknowledge it only after the enclosing SQL transaction commits.

## Side Effects

- `[iologindata_load_player.cpp:IOLoginDataLoad]` — Executes SQL `SELECT` (and default `INSERT INTO player_charms`) queries via `Database`, instantiates `Item`/`Container`/`Condition`/`Guild`/`PreySlot`/`TaskHuntingSlot` objects, starts item and imbuement decay timers (`item->startDecaying()`, `g_imbuementDecay().startImbuementDecay`), and mutates `Player` state and `KV` scopes.
- `[iologindata_save_player.cpp:IOLoginDataSave]` — Executes SQL `SELECT`, `UPDATE`, `DELETE`, and `DBInsert` queries across `players`, `player_stash`, `player_spells`, `player_kills`, `player_charms`, `player_items`, `player_depotitems`, `player_rewards`, `player_inboxitems`, `player_prey`, `player_taskhunt`, `player_bosstiary`, and `player_storage`, and updates `player->kv()->scoped("spells")` (`virtue`, `harmony`).

## Verification

- Run: `ctest --test-dir build --output-on-failure`
