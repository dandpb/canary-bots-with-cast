# Appearance

## Overview
Intermediate blueprint grouping creature visual appearance subsystems: attached cosmetic effects (auras, wings, shaders, effects), mounts, and player outfits.

## Subdirectories & Boundaries
- [attached_effects](./attached_effects/README.md): Cosmetic visual attachments (`Aura`, `Shader`, `Effect`, `Wing`) loaded from `attachedeffects.xml`.
- [mounts](./mounts/README.md): Creature mount definitions (`Mount`, `Mounts`) loaded from `mounts.xml`.
- [outfit](./outfit/README.md): Player outfit definitions (`Outfit`, `OutfitEntry`, `ProtocolOutfit`, `Outfits`) loaded from `outfits.xml`.

## Interface
- `AttachedEffects`, `Aura`, `Shader`, `Effect`, `Wing` (`[attached_effects/attached_effects.hpp:AttachedEffects]`): Attachment registry and data structs.
- `Mounts`, `Mount` (`[mounts/mounts.hpp:Mounts]`, `[mounts/mounts.hpp:Mount]`): Mount registry and metadata.
- `Outfits`, `Outfit`, `OutfitEntry`, `ProtocolOutfit` (`[outfit/outfit.hpp:Outfits]`, `[outfit/outfit.hpp:Outfit]`): Sex-indexed outfit registry and protocol helpers.

## Invariants
- Unregistered lookTypes for mounts and outfits are rejected during XML loading when `WARN_UNSAFE_SCRIPTS` is enabled (`[mounts/mounts.cpp:Mounts::loadFromXml]`, `[outfit/outfit.cpp:Outfits::loadFromXml]`).
- Outfit lookups by lookType require valid player sex (`PLAYERSEX_FEMALE` or `PLAYERSEX_MALE`) (`[outfit/outfit.cpp:Outfits::getOutfitByLookType]`).

## Side Effects
- Reads XML configuration files (`attachedeffects.xml`, `mounts.xml`, `outfits.xml`) from `<CORE_DIRECTORY>/XML/`, mutates in-memory registries (`AttachedEffects`, `Mounts`, `outfits`), and logs diagnostics via `g_logger()` (`[attached_effects/attached_effects.cpp:AttachedEffects::loadFromXml]`, `[mounts/mounts.cpp:Mounts::loadFromXml]`, `[outfit/outfit.cpp:Outfits::loadFromXml]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
