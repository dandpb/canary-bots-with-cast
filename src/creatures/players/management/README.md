# management

## Overview
Package implementation for `src/creatures/players/management`, providing component logic and data interfaces for management.

## Interface
- `lockClass` (`[ban.cpp:lockClass]`)
- `BanInfo` (`[ban.hpp:BanInfo]`)
- `ConnectBlock` (`[ban.hpp:ConnectBlock]`)
- `Ban` (`[ban.hpp:Ban]`)
- `IOBan` (`[ban.hpp:IOBan]`)
- `acceptConnection` (`[ban.hpp:acceptConnection]`)
- `isAccountBanned` (`[ban.hpp:isAccountBanned]`)
- `isIpBanned` (`[ban.hpp:isIpBanned]`)
- `isPlayerNamelocked` (`[ban.hpp:isPlayerNamelocked]`)
- `Player` (`[waitlist.hpp:Player]`)

## Invariants
- None

## Side Effects
- Executes SQL queries against game database (`[ban.cpp]`)
- Emits system diagnostic logs (`[waitlist.cpp]`)

## Verification
- Run: `ctest --test-dir build --output-on-failure`
