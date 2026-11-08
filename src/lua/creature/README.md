# Lua Creature Events & Actions (`src/lua/creature`)

## Overview
Implements Lua-scripted gameplay interactions and lifecycle hooks tied to creatures, players, items, and world tiles. This package encompasses item use actions (`Actions`), creature lifecycle events (`CreatureEvents`), global class-method event hooks (`Events`), tile/equipment movement triggers (`MoveEvents`), XML-configured monster raids (`Raids`), and player chat commands (`TalkActions`).

## Interface
- `Action` & `Actions` / `g_actions` (`[actions.hpp:Action]`, `[actions.hpp:Actions]`, `[actions.hpp:g_actions]`): Item usage handlers supporting item ID, unique ID, action ID, and map position bindings (`useItem`, `useItemEx`, `canUse`, `canUseFar`, `registerLuaEvent`, `clear`).
- `CreatureEvent` & `CreatureEvents` / `g_creatureEvents` (`[creatureevent.hpp:CreatureEvent]`, `[creatureevent.hpp:CreatureEvents]`, `[creatureevent.hpp:g_creatureEvents]`): Per-creature and global player lifecycle hooks (`playerLogin`, `playerLogout`, `playerAdvance`, `executeOnThink`, `executeOnPrepareDeath`, `executeOnDeath`, `executeOnKill`, `executeHealthChange`, `executeManaChange`, `executeModalWindow`, `executeTextEdit`, `executeExtendedOpcode`).
- `Events` / `g_events` (`[events.hpp:Events]`, `[events.hpp:g_events]`): XML-configured (`events.xml`) class method callbacks for `Creature`, `Party`, `Player`, and `Monster` (`loadFromXml`, `eventCreatureOn*`, `eventPartyOn*`, `eventPlayerOn*`, `eventMonsterOnDropLoot`).
- `MoveEvent` & `MoveEvents` / `g_moveEvents` (`[movement.hpp:MoveEvent]`, `[movement.hpp:MoveEvents]`, `[movement.hpp:g_moveEvents]`): Step-in/step-out, tile item add/remove, and player equipment slot handlers (`onCreatureMove`, `onPlayerEquip`, `onPlayerDeEquip`, `onItemMove`, `EquipItem`, `DeEquipItem`, `StepInField`, `AddItemField`).
- `Raids`, `Raid`, `RaidEvent`, `AnnounceEvent`, `SingleSpawnEvent`, `AreaSpawnEvent`, `ScriptEvent` (`[raids.hpp:Raids]`, `[raids.hpp:Raid]`, `[raids.hpp:RaidEvent]`): Legacy XML raid loader and scheduler (`loadFromXml`, `startup`, `checkRaids`, `startRaid`, `executeRaidEvent`).
- `TalkAction` & `TalkActions` / `g_talkActions` (`[talkaction.hpp:TalkAction]`, `[talkaction.hpp:TalkActions]`, `[talkaction.hpp:g_talkActions]`): Chat-triggered command registration and permission-checked dispatch (`checkPlayerCanSayTalkAction`, `checkWord`, `executeSay`, `registerLuaEvent`).

## Invariants
- All Lua script executions across `Action`, `CreatureEvent`, `Events`, `MoveEvent`, `ScriptEvent`, and `TalkAction` must first acquire a script environment slot via `LuaScriptInterface::reserveScriptEnv()` and release it via `callFunction`/`callVoidFunction` or `resetScriptEnv()` (`[actions.cpp:Action::executeUse]`, `[creatureevent.cpp:CreatureEvent::executeHealthChange]`, `[events.cpp:Events::eventCreatureOnAreaCombat]`).
- `Actions` and `MoveEvents` reject duplicate registrations for the same item ID, unique ID, action ID (and equipment slot for `MoveEvents`), or map position (`[actions.cpp:Actions::registerLuaItemEvent]`, `[movement.cpp:MoveEvents::registerEvent]`).
- `MoveEvent::executeStep` prevents infinite self-teleport loops when stepping onto a teleport item whose destination equals `fromPosition` by redirecting the player to their temple position (`[movement.cpp:MoveEvent::executeStep]`).
- `Raids::loadFromXml` and `Raids::startup` are no-ops if `DISABLE_LEGACY_RAIDS` is enabled in config; individual raid events enforce a minimum delay of `RAID_MINTICKS` (1000 ms) and sort ascending by delay (`[raids.cpp:Raids::loadFromXml]`, `[raids.cpp:Raid::loadFromXml]`, `[raids.cpp:RaidEvent::configureRaidEvent]`).
- `TalkActions::checkWord` enforces account-to-group permission levels before executing a command unless the player has `ACCOUNT_TYPE_GOD` (`[talkaction.cpp:TalkActions::checkWord]`).

## Side Effects
- Mutates game world, creature, player, and item state: transforms items, opens/closes containers and depots, applies/removes equipment conditions, skills, stats, speed, and imbuement decay, and spawns raid monsters on the map (`[actions.cpp:Actions::internalUseItem]`, `[movement.cpp:MoveEvent::EquipItem]`, `[movement.cpp:MoveEvent::DeEquipItem]`, `[raids.cpp:SingleSpawnEvent::executeEvent]`, `[raids.cpp:AreaSpawnEvent::executeEvent]`).
- Mutates `ItemType` wield requirements (`wieldInfo`, `minReqLevel`, `minReqMagicLevel`, `vocationString`) globally when registering `MOVE_EVENT_EQUIP` item events (`[movement.cpp:MoveEvents::registerLuaItemEvent]`).
- Schedules and cancels asynchronous timer tasks on `g_dispatcher()` for periodic raid checks and sequential raid event execution (`[raids.cpp:Raids::startup]`, `[raids.cpp:Raid::startRaid]`, `[raids.cpp:Raids::clear]`).
- Reads XML configuration and Lua script files from disk (`events.xml`, `raids.xml`, raid scripts) and dispatches raid announcement messages to connected players and `g_webhook()` (`[events.cpp:Events::loadFromXml]`, `[raids.cpp:Raids::loadFromXml]`, `[raids.cpp:AnnounceEvent::executeEvent]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
