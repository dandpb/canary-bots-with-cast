# Player Grouping

## Overview
Manages social, permission, and companion groupings for players, including vocation familiars (`Familiars`), permission groups and flags (`Groups`), persistent guilds with bank balances (`Guild`), dynamic parties with shared experience, loot/supply/damage analyzers, and Monk mantra sharing (`Party`), and the team-assembly finder (`TeamFinder`).

## Interface
- `Familiars`, `Familiar`, `FamiliarEntry` (`[familiars.hpp:Familiars]`, `[familiars.hpp:Familiar]`, `[familiars.hpp:FamiliarEntry]`, `[familiars.cpp:Familiars]`): Singleton XML loader (`loadFromXml`, `reload`) and lookup service (`getFamiliars`, `getFamiliarByLookType`) for vocation familiars.
- `Groups`, `Group` (`[groups.hpp:Groups]`, `[groups.hpp:Group]`, `[groups.cpp:Groups]`): XML loader (`load`, `reload`) and lookup (`getGroup`, `getGroups`, `getFlagNumber`, `getFlagFromNumber`) for player permission groups and `PlayerFlags_t` bitsets.
- `Guild`, `GuildRank`, `GuildRank_ptr` (`[guild.hpp:Guild]`, `[guild.hpp:GuildRank]`, `[guild.cpp:Guild]`): `Bankable` guild entity managing online members (`addMember`, `removeMember`, `getMembersOnline`), ranks (`addRank`, `getRankById`, `getRankByName`, `getRankByLevel`), bank balance, and MOTD.
- `Party`, `SharedExpStatus_t` (`[party.hpp:Party]`, `[party.hpp:SharedExpStatus_t]`, `[party.cpp:Party]`): Party lifecycle (`create`, `invitePlayer`, `joinParty`, `leaveParty`, `passPartyLeadership`, `disband`), shared experience (`shareExperience`, `setSharedExperience`, `updateSharedExperience`, `canUseSharedExperience`), Monk Guiding Presence mantra buff sharing (`updateMantraHolder`, `applyGuidingPresence`), member status updates, and party tracker analyzer (`updateTrackerAnalyzer`, `addPlayerLoot`, `addPlayerSupply`, `addPlayerDamage`, `addPlayerHealing`).
- `TeamFinder` (`[team_finder.hpp:TeamFinder]`): Data model storing team-finder criteria (level range, vocation bitmask, slots, boss/hunt/quest IDs, leader GUID, and member status map).

## Invariants
- `Familiars::loadFromXml` rejects familiar entries whose `vocation > VOCATION_LAST` or that lack a `lookType` attribute (`[familiars.cpp:Familiars::loadFromXml]`).
- When the last online member is removed from a `Guild` via `Guild::removeMember`, the guild is removed from the active `Game` registry (`[guild.cpp:Guild::removeMember]`).
- Shared experience (`SHAREDEXP_OK`) requires a non-empty party where all members are within level range (`getMinLevel()` based on `PARTY_SHARE_RANGE_MULTIPLIER`), within `Position::areInRange<30, 30, 1>` of the leader, and active in combat within the last 2 minutes (`[party.cpp:Party::getMemberSharedExperienceStatus]`, `[party.cpp:Party::isPlayerActive]`).
- `Party::updateMantraHolder` selects the party member with `VOCATION_MONK_CIP` and `WheelInstant_t::GUIDING_PRESENCE` who has the highest mantra value, and `applyGuidingPresence` grants `100 + mantra / 2` to `BUFF_MANTRA` on all other party members (`[party.cpp:Party::updateMantraHolder]`, `[party.cpp:Party::applyGuidingPresence]`).

## Side Effects
- Loads `XML/familiars.xml` and `XML/groups.xml` from disk (`[familiars.cpp:Familiars::loadFromXml]`, `[groups.cpp:Groups::load]`).
- `Guild` and `Party` membership changes update player helpers, shields, skulls, party icons, and party channels across online players via `g_game()` and `Player` network methods, and invoke Lua party events/callbacks (`eventPartyOnJoin`, `eventPartyOnLeave`, `eventPartyOnDisband`, `eventPartyOnShareExperience`) (`[guild.cpp:Guild::addMember]`, `[party.cpp:Party::joinParty]`, `[party.cpp:Party::leaveParty]`, `[party.cpp:Party::disband]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
