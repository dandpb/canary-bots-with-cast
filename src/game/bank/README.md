# Game Bank System (`src/game/bank`)

## Overview
Implements the financial transaction abstraction (`Bank` and `Bankable`) for players and guilds, supporting balance queries, credits, debits, physical gold deposits/withdrawals, and inter-account bank transfers with town-restriction and sample-character checks.

## Interface
- `Bankable` (`[bank.hpp:Bankable]`): Abstract interface implemented by entities that hold a bank balance (`setBankBalance`, `getBankBalance`, `getPlayer`, `isGuild`, `setOnline`, `isOnline`).
- `Bank` (`[bank.hpp:Bank]`): Transaction controller wrapping a `std::shared_ptr<Bankable>` (`credit`, `debit`, `balance`, `hasBalance`, `transferTo`, `withdraw`, `deposit`).

## Invariants
- `Bank::debit` and `Bank::withdraw` require `hasBalance(amount)` (`balance() >= amount`) to succeed before deducting funds (`[bank.cpp:Bank::debit]`, `[bank.cpp:Bank::withdraw]`).
- `Bank::transferTo` rejects transfers to sample/system character names in `deniedNames` (`accountmanager`, `rooksample`, `druidsample`, `sorcerersample`, `knightsample`, `paladinsample`) (`[bank.cpp:deniedNames]`, `[bank.cpp:Bank::transferTo]`).
- `Bank::transferTo` forbids cross-tier town transfers where one player's town ID is below `MIN_TOWN_ID_TO_BANK_TRANSFER_FROM_MAIN` (e.g., Dawnport/Rookgaard) and the other's is at or above it (`[bank.cpp:Bank::transferTo]`).

## Side Effects
- Mutates `Bankable` balances via `setBankBalance` and adds/removes physical currency items on players via `g_game().addMoney` and `g_game().removeMoney` (`[bank.cpp:Bank::balance]`, `[bank.cpp:Bank::withdraw]`, `[bank.cpp:Bank::deposit]`).
- Persists offline `Player` or offline `Guild` state via `g_saveManager().savePlayer` / `g_saveManager().saveGuild` when the `Bank` instance is destroyed (`[bank.cpp:Bank::~Bank]`).
- Emits `balance_increase` and `balance_decrease` counters to `g_metrics()` on transfers, withdrawals, and deposits (`[bank.cpp:Bank::transferTo]`, `[bank.cpp:Bank::withdraw]`, `[bank.cpp:Bank::deposit]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
