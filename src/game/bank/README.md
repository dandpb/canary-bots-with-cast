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
- A transfer commits both balances in one transaction before publishing either balance in memory. An uncertain commit fences both participants until the receipt can be checked. Lua retains its success boolean and returns a second pending boolean (`[bank.cpp:Bank::transferTo]`, `[bank_functions.cpp:BankFunctions::luaBankTransfer]`).

## Side Effects
- Mutates `Bankable` balances via `setBankBalance` and adds/removes physical currency items on players via `g_game().addMoney` and `g_game().removeMoney` (`[bank.cpp:Bank::balance]`, `[bank.cpp:Bank::withdraw]`, `[bank.cpp:Bank::deposit]`).
- Persists dirty offline handles through `SaveManager` on destruction. A committed transfer has already saved its balances (`[bank.cpp:Bank::~Bank]`).
- Emits `balance_increase` and `balance_decrease` counters to `g_metrics()` on transfers, withdrawals, and deposits (`[bank.cpp:Bank::transferTo]`, `[bank.cpp:Bank::withdraw]`, `[bank.cpp:Bank::deposit]`).

## Verification
- See the [C++ build and test guide](../../../tests/README.md#running-tests).
