# account

## Overview
Provides the domain model and persistence abstractions for player accounts, including authentication (session, Argon2, and legacy SHA-1 password verification), premium time calculation and loyalty tracking, character listing, and coin balance/transaction management.

## Interface
- `Account` (`[account.hpp:Account]`): High-level domain wrapper around `AccountInfo` supporting account loading/saving (`[account.hpp:Account::load]`, `[account.hpp:Account::reload]`, `[account.hpp:Account::save]`), coin operations (`[account.hpp:Account::getCoins]`, `[account.hpp:Account::addCoins]`, `[account.hpp:Account::removeCoins]`, `[account.hpp:Account::registerCoinTransaction]`), premium day management (`[account.hpp:Account::addPremiumDays]`, `[account.hpp:Account::setPremiumDays]`, `[account.hpp:Account::updatePremiumTime]`), character lookup (`[account.hpp:Account::getAccountPlayers]`), house bid tracking (`[account.hpp:Account::setHouseBidId]`, `[account.hpp:Account::getHouseBidId]`), and authentication (`[account.hpp:Account::authenticate]`, `[account.hpp:Account::authenticateSession]`, `[account.hpp:Account::authenticatePassword]`).
- `AccountInfo` (`[account_info.hpp:AccountInfo]`): Value struct holding raw account state (`id`, `premiumRemainingDays`, `premiumLastDay`, `accountType`, `players`, `oldProtocol`, `sessionExpires`, `premiumDaysPurchased`, `creationTime`, `houseBidId`).
- `AccountRepository` & `g_accountRepository` (`[account_repository.hpp:AccountRepository]`, `[account_repository.hpp:g_accountRepository]`): Abstract repository interface and DI-backed singleton accessor (`[account_repository.cpp:AccountRepository::getInstance]`) for loading and persisting account records, passwords, characters, and coins.
- `AccountRepositoryDB` (`[account_repository_db.hpp:AccountRepositoryDB]`): Concrete MySQL-backed implementation of `AccountRepository` mapping `CoinType` values to database columns (`[account_repository_db.cpp:AccountRepositoryDB::AccountRepositoryDB]`).

## Invariants
- `Account` operations requiring persistence or loaded state (`reload`, `save`, `getCoins`, `addCoins`, `removeCoins`, `registerCoinTransaction`, `getPassword`, `getAccountPlayers`) require `m_accLoaded == true` and return `AccountErrors_t::NotInitialized` (or empty/no-op) otherwise (`[account.cpp:Account::reload]`, `[account.cpp:Account::save]`, `[account.cpp:Account::getCoins]`, `[account.cpp:Account::addCoins]`, `[account.cpp:Account::removeCoins]`, `[account.cpp:Account::registerCoinTransaction]`, `[account.cpp:Account::getPassword]`, `[account.cpp:Account::getAccountPlayers]`).
- `Account::removeCoins` enforces `coins >= amount` before deduction, returning `AccountErrors_t::RemoveCoins` on insufficient balance (`[account.cpp:Account::removeCoins]`).
- `Account::setPremiumDays` clamps non-positive `days <= 0` to `premiumLastDay = 0` and `premiumRemainingDays = 0` (`[account.cpp:Account::setPremiumDays]`).
- `Account::authenticatePassword` never logs plaintext passwords or stored password hashes on failure to prevent credential exposure (`[account.cpp:Account::authenticatePassword]`).
- `AccountRepositoryDB::loadAccountPlayers` filters out soft-deleted characters where `deletion != 0` (`[account_repository_db.cpp:AccountRepositoryDB::loadAccountPlayers]`).
- `AccountRepositoryDB::setupLoyaltyInfo` ensures `premiumDaysPurchased >= premiumRemainingDays` and `creationTime != 0`, persisting normalized values when violated (`[account_repository_db.cpp:AccountRepositoryDB::setupLoyaltyInfo]`).

## Side Effects
- Executes synchronous SQL `SELECT`, `UPDATE`, and `INSERT` queries against `accounts`, `account_sessions`, `players`, and `coins_transactions` tables via `g_database()` (`[account_repository_db.cpp:AccountRepositoryDB::loadByID]`, `[account_repository_db.cpp:AccountRepositoryDB::loadByEmailOrName]`, `[account_repository_db.cpp:AccountRepositoryDB::loadBySession]`, `[account_repository_db.cpp:AccountRepositoryDB::save]`, `[account_repository_db.cpp:AccountRepositoryDB::getCharacterByAccountIdAndName]`, `[account_repository_db.cpp:AccountRepositoryDB::getPassword]`, `[account_repository_db.cpp:AccountRepositoryDB::getCoins]`, `[account_repository_db.cpp:AccountRepositoryDB::setCoins]`, `[account_repository_db.cpp:AccountRepositoryDB::registerCoinsTransaction]`, `[account_repository_db.cpp:AccountRepositoryDB::loadAccountPlayers]`).
- Mutates in-memory `AccountInfo` state and triggers database saves during `Account::updatePremiumTime` and `AccountRepositoryDB::setupLoyaltyInfo` (`[account.cpp:Account::updatePremiumTime]`, `[account_repository_db.cpp:AccountRepositoryDB::setupLoyaltyInfo]`).
- Emits diagnostic and error logs via `g_logger()` (`[account.cpp:Account::removeCoins]`, `[account.cpp:Account::registerCoinTransaction]`, `[account.cpp:Account::authenticateSession]`, `[account.cpp:Account::authenticatePassword]`, `[account_repository_db.cpp:AccountRepositoryDB::save]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
