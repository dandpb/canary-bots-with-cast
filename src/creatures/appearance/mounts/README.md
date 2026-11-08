# Mounts

## Overview
Manages creature mount definitions (`Mount`) loaded from `<CORE_DIRECTORY>/XML/mounts.xml`, providing lookup by mount ID, client lookType ID, or case-insensitive name.

## Interface
- `Mount` (`[mounts.hpp:Mount]`): Struct storing mount metadata (`name`, `speed`, `clientId`, `id`, `premium`, `type`).
- `Mounts::reload` (`[mounts.hpp:Mounts::reload]`): Clears existing mounts and reloads from XML.
- `Mounts::loadFromXml` (`[mounts.hpp:Mounts::loadFromXml]`): Parses `<CORE_DIRECTORY>/XML/mounts.xml` and populates the mounts hash set.
- `Mounts::getMountByID` (`[mounts.hpp:Mounts::getMountByID]`): Finds a mount by internal `uint8_t` ID.
- `Mounts::getMountByName` (`[mounts.hpp:Mounts::getMountByName]`): Finds a mount by case-insensitive name (`strcasecmp`).
- `Mounts::getMountByClientID` (`[mounts.hpp:Mounts::getMountByClientID]`): Finds a mount by client lookType ID (`uint16_t`).
- `Mounts::getMounts` (`[mounts.hpp:Mounts::getMounts]`): Returns the underlying `phmap::parallel_flat_hash_set<std::shared_ptr<Mount>>`.

## Invariants
- When `WARN_UNSAFE_SCRIPTS` is enabled in `g_configManager()`, `Mounts::loadFromXml` (`[mounts.cpp:Mounts::loadFromXml]`) rejects mounts with a non-zero `clientid` that is not registered in `g_game().isLookTypeRegistered(lookType)` to prevent client crashes.

## Side Effects
- `Mounts::reload` (`[mounts.cpp:Mounts::reload]`): Clears and repopulates the `mounts` hash set.
- `Mounts::loadFromXml` (`[mounts.cpp:Mounts::loadFromXml]`): Reads `<CORE_DIRECTORY>/XML/mounts.xml` from disk, queries `g_configManager()` and `g_game()`, and logs warnings via `g_logger()` or `printXMLError`.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
