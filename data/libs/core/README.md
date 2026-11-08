# Core Global Storage Definitions (`data/libs/core`)

## Overview

Defines the global `Global.Storage` table (`global_storage.lua`) mapping named keys to reserved global and TibiaDrome storage IDs.

## Interface

- `[global_storage.lua:Global]`: Global table containing `Global.Storage`.
- `[global_storage.lua:Global.Storage.FamiliarSummonEvent10]`: Storage key `30054`.
- `[global_storage.lua:Global.Storage.FamiliarSummonEvent60]`: Storage key `30055`.
- `[global_storage.lua:Global.Storage.CobraFlask]`: Storage key `30056`.
- `[global_storage.lua:Global.Storage.TibiaDrome]`: Nested storage key table (`64000`–`64039`) for Drome upgrades (`BestiaryBetterment`, `CharmUpgrade`, `KooldownAid`, `StaminaExtension`, `StrikeEnhancement`, `WealthDuplex`), elemental/physical resiliences (`FireResilience`, `IceResilience`, `EarthResilience`, `EnergyResilience`, `HolyResilience`, `DeathResilience`, `PhysicalResilience`), and elemental/physical amplifications (`FireAmplification`, `IceAmplification`, `EarthAmplification`, `EnergyAmplification`, `HolyAmplification`, `DeathAmplification`, `PhysicalAmplification`), each exposing `TimeLeft` and/or `LastActivatedAt` keys.

## Invariants

- `[global_storage.lua:Global.Storage.TibiaDrome]`: Storage range `64000`–`64099` is reserved for TibiaDrome (`64000`–`64039` allocated).
- `[global_storage.lua:Global]`: Documents engine-reserved player action/storage ranges (`10000000`–`20000000`, `1000`–`1500`, `2001`–`2011`, `100` unmovable/unusable, `101` pick floor, `102` well down, `103`–`120` and `303` keys, `1000 + level` level doors).

## Side Effects

- `[global_storage.lua:Global]`: Defines the global `Global` table in the Lua environment.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
