# Attached Effects

## Overview
Manages cosmetic visual attachment definitions (`Aura`, `Shader`, `Effect`, `Wing`) loaded from the server's `attachedeffects.xml` configuration file, providing lookup by numeric ID or case-insensitive name.

## Interface
- `Aura` (`[attached_effects.hpp:Aura]`): Represents a visual aura attachment (`id`, `name`).
- `Shader` (`[attached_effects.hpp:Shader]`): Represents a visual shader attachment (`id`, `name`).
- `Effect` (`[attached_effects.hpp:Effect]`): Represents a visual effect attachment (`id`, `name`).
- `Wing` (`[attached_effects.hpp:Wing]`): Represents a visual wing attachment (`id`, `name`).
- `AttachedEffects::reload` (`[attached_effects.hpp:AttachedEffects::reload]`): Clears existing vectors and reloads definitions from XML.
- `AttachedEffects::loadFromXml` (`[attached_effects.hpp:AttachedEffects::loadFromXml]`): Parses `<CORE_DIRECTORY>/XML/attachedeffects.xml` and populates attachment vectors.
- `AttachedEffects::getAuraByID`, `getEffectByID`, `getWingByID`, `getShaderByID` (`[attached_effects.hpp:AttachedEffects::getAuraByID]`, `[attached_effects.hpp:AttachedEffects::getEffectByID]`, `[attached_effects.hpp:AttachedEffects::getWingByID]`, `[attached_effects.hpp:AttachedEffects::getShaderByID]`): Retrieves an attachment definition by numeric ID.
- `AttachedEffects::getAuraByName`, `getShaderByName`, `getEffectByName`, `getWingByName` (`[attached_effects.hpp:AttachedEffects::getAuraByName]`, `[attached_effects.hpp:AttachedEffects::getShaderByName]`, `[attached_effects.hpp:AttachedEffects::getEffectByName]`, `[attached_effects.hpp:AttachedEffects::getWingByName]`): Retrieves an attachment definition by case-insensitive name (`strcasecmp`).
- `AttachedEffects::getAuras`, `getShaders`, `getEffects`, `getWings` (`[attached_effects.hpp:AttachedEffects::getAuras]`, `[attached_effects.hpp:AttachedEffects::getShaders]`, `[attached_effects.hpp:AttachedEffects::getEffects]`, `[attached_effects.hpp:AttachedEffects::getWings]`): Read-only accessors to the loaded attachment vectors.

## Invariants
- Name lookups (`[attached_effects.cpp:AttachedEffects::getAuraByName]`, `[attached_effects.cpp:AttachedEffects::getShaderByName]`, `[attached_effects.cpp:AttachedEffects::getEffectByName]`, `[attached_effects.cpp:AttachedEffects::getWingByName]`) perform case-insensitive matching via `strcasecmp`.

## Side Effects
- `AttachedEffects::reload` (`[attached_effects.cpp:AttachedEffects::reload]`): Mutates in-memory vectors (`auras`, `shaders`, `effects`, `wings`) by clearing and reloading them.
- `AttachedEffects::loadFromXml` (`[attached_effects.cpp:AttachedEffects::loadFromXml]`): Reads `<CORE_DIRECTORY>/XML/attachedeffects.xml` from disk via `pugi::xml_document::load_file`, queries `g_configManager().getString(CORE_DIRECTORY)`, and logs parse failures via `printXMLError`.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
