# Outfit

## Overview
Manages player outfit definitions (`Outfit`, `OutfitEntry`, `ProtocolOutfit`) indexed by player sex (`PlayerSex_t`), loaded from `<CORE_DIRECTORY>/XML/outfits.xml`.

## Interface
- `OutfitEntry` (`[outfit.hpp:OutfitEntry]`): Lightweight struct pairing `lookType` and `addons` bitmask.
- `Outfit` (`[outfit.hpp:Outfit]`): Struct defining an outfit (`name`, `lookType`, `premium`, `unlocked`, `from`).
- `ProtocolOutfit` (`[outfit.hpp:ProtocolOutfit]`): Network serialization view of an outfit (`name`, `lookType`, `addons`).
- `Outfits::getInstance` (`[outfit.hpp:Outfits::getInstance]`): DI singleton accessor via `inject<Outfits>()`.
- `Outfits::reload` (`[outfit.hpp:Outfits::reload]`): Clears the global `outfits` arrays and reloads from XML.
- `Outfits::loadFromXml` (`[outfit.hpp:Outfits::loadFromXml]`): Loads outfit definitions from `<CORE_DIRECTORY>/XML/outfits.xml`.
- `Outfits::getOutfitByLookType` (`[outfit.hpp:Outfits::getOutfitByLookType]`): Looks up an outfit for a player's sex (or opposite sex when `isOppositeOutfit` is true) by `lookType`.
- `Outfits::getOutfits` (`[outfit.hpp:Outfits::getOutfits]`): Returns the vector of outfits for a given `PlayerSex_t`.
- `Outfits::getOutfitByName` (`[outfit.hpp:Outfits::getOutfitByName]`): Looks up an outfit by `PlayerSex_t` and exact `name`.

## Invariants
- Outfit `type` in XML must not exceed `PLAYERSEX_LAST` (`[outfit.cpp:Outfits::loadFromXml]`).
- `Outfits::getOutfitByLookType` (`[outfit.cpp:Outfits::getOutfitByLookType]`) requires a non-null `Player` whose sex is either `PLAYERSEX_FEMALE` or `PLAYERSEX_MALE`.
- When `WARN_UNSAFE_SCRIPTS` is enabled, `Outfits::loadFromXml` (`[outfit.cpp:Outfits::loadFromXml]`) ignores outfits whose non-zero `looktype` is not registered in `g_game().isLookTypeRegistered(lookType)`.

## Side Effects
- `Outfits::reload` and `Outfits::loadFromXml` (`[outfit.cpp:Outfits::reload]`, `[outfit.cpp:Outfits::loadFromXml]`): Mutate the module-scope `outfits[PLAYERSEX_LAST + 1]` vectors (`[outfit.cpp:outfits]`), read `<CORE_DIRECTORY>/XML/outfits.xml` from disk, and log warnings/errors via `g_logger()`.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
