# Interactions

## Overview
Manages in-game chat channels (`ChatChannel`, `PrivateChatChannel`, and the `Chat` manager singleton), supporting normal XML-configured channels, guild channels, party channels, and player-owned private channels with Lua event hooks.

## Interface
- `ChatChannel` (`[chat.hpp:ChatChannel]`): Represents a public or normal chat channel (`addUser`, `removeUser`, `hasUser`, `talk`, `sendToAll`, `executeOnJoinEvent`, `executeCanJoinEvent`, `executeOnLeaveEvent`, `executeOnSpeakEvent`).
- `PrivateChatChannel` (`[chat.hpp:PrivateChatChannel]`): Extends `ChatChannel` with ownership and invitation management (`getOwner`, `setOwner`, `isInvited`, `invitePlayer`, `excludePlayer`, `removeInvite`, `closeChannel`).
- `Chat` (`[chat.hpp:Chat]`, `[chat.hpp:g_chat]`): Singleton managing channel lifecycles (`load`, `createChannel`, `deleteChannel`, `addUserToChannel`, `removeUserFromChannel`, `removeUserFromAllChannels`, `talkToChannel`, `getChannelList`, `getChannel`, `getChannelById`, `getGuildChannelById`, `getPrivateChannel`, `getScriptInterface`).

## Invariants
- Only premium players (`player->isPremium()`) without an existing private channel may create a `CHANNEL_PRIVATE`, allocated from IDs `100` to `9999` (`[chat.cpp:Chat::createChannel]`).
- A player can only `talk` in a channel if their ID is present in `users` (`[chat.cpp:ChatChannel::talk]`).
- Removing the owner of a channel via `removeUserFromChannel` or `removeUserFromAllChannels` closes and deletes that private channel (`[chat.cpp:Chat::removeUserFromChannel]`, `[chat.cpp:Chat::removeUserFromAllChannels]`).

## Side Effects
- `Chat::load` (`[chat.cpp:Chat::load]`): Reads `<CORE_DIRECTORY>/chatchannels/chatchannels.xml` and loads Lua channel scripts from `<CORE_DIRECTORY>/chatchannels/scripts/` into `scriptInterface`.
- `ChatChannel::addUser` (`[chat.cpp:ChatChannel::addUser]`): Schedules `Game::sendGuildMotd` via `g_dispatcher().scheduleEvent` when joining `CHANNEL_GUILD`, and broadcasts channel join/leave/message packets to connected players.
- `ChatChannel::execute*Event` (`[chat.cpp:ChatChannel::executeCanJoinEvent]`, `[chat.cpp:ChatChannel::executeOnJoinEvent]`, `[chat.cpp:ChatChannel::executeOnLeaveEvent]`, `[chat.cpp:ChatChannel::executeOnSpeakEvent]`): Executes Lua callbacks (`canJoin`, `onJoin`, `onLeave`, `onSpeak`) on `Chat::scriptInterface`.

## Verification
- Run: `ctest --test-dir build --output-on-failure`
