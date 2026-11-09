# Chat Channels Scripts

## Overview

Lua callback scripts implementing join access checks (`canJoin`) and message processing/moderation (`onSpeak`) for in-game chat channels configured in `../chatchannels.xml`.

## Interface

- `[advertising-rook.lua:canJoin]`: `function canJoin(player)` — restricts Rookgaard advertising channel join to `VOCATION_NONE` or group `>= GROUP_TYPE_SENIORTUTOR`.
- `[advertising-rook.lua:onSpeak]`: `function onSpeak(player, type, message)` — enforces level and 2-minute mute cooldown (`CHANNEL_ADVERTISING_ROOK = 6`) and normalizes channel talk types.
- `[advertising.lua:canJoin]`: `function canJoin(player)` — restricts mainland advertising channel join to `~= VOCATION_NONE` or group `>= GROUP_TYPE_SENIORTUTOR`.
- `[advertising.lua:onSpeak]`: `function onSpeak(player, type, message)` — enforces level `>= 20` or premium status and 2-minute mute cooldown (`CHANNEL_ADVERTISING = 5`).
- `[english_chat.lua:onSpeak]`: `function onSpeak(player, type, message)` — enforces level `>= 20` or premium status and normalizes talk types by group/flags.
- `[gamemaster.lua:canJoin]`: `function canJoin(player)` — restricts Gamemaster channel join to `accountType >= ACCOUNT_TYPE_GAMEMASTER`.
- `[gamemaster.lua:onSpeak]`: `function onSpeak(player, type, message)` — normalizes talk types based on `ACCOUNT_TYPE_GOD` and `PlayerFlag_CanTalkRedChannel`.
- `[guild_leaders.lua:canJoin]`: `function canJoin(player)` — restricts Guild Leaders channel join to `guildLevel == 3` or staff access (`player:getGroup():getAccess()`).
- `[guild_leaders.lua:onSpeak]`: `function onSpeak(player, type, message)` — formats messages with `[Staff]` and/or guild name tags and broadcasts to channel `11`.
- `[help.lua:onSpeak]`: `function onSpeak(player, type, message)` — handles Help channel (`CHANNEL_HELP = 7`) speaking rules and `!mute ` / `!unmute ` moderation commands.
- `[tutor.lua:canJoin]`: `function canJoin(player)` — restricts Tutor channel join to group `>= GROUP_TYPE_TUTOR`.
- `[tutor.lua:onSpeak]`: `function onSpeak(player, type, message)` — normalizes talk types based on `GROUP_TYPE_SENIORTUTOR`, `GROUP_TYPE_GAMEMASTER`, and `PlayerFlag_CanTalkRedChannel`.
- `[world_chat.lua:onSpeak]`: `function onSpeak(player, type, message)` — blocks level 1 non-GM players and normalizes talk types.

## Invariants

- `[advertising-rook.lua:canJoin]`: Joining Rookgaard Advertising requires `player:getVocation():getId() == VOCATION_NONE` or `player:getGroup():getId() >= GROUP_TYPE_SENIORTUTOR`.
- `[advertising-rook.lua:onSpeak]`: Non-GM players (`group < GROUP_TYPE_GAMEMASTER`) cannot speak at level 1 or while `CONDITION_CHANNELMUTEDTICKS` (subid `6`, `120000` ms) is active.
- `[advertising.lua:canJoin]`: Joining mainland Advertising requires `player:getVocation():getId() ~= VOCATION_NONE` or `player:getGroup():getId() >= GROUP_TYPE_SENIORTUTOR`.
- `[advertising.lua:onSpeak]`: Non-GM players must have `level >= 20` or `player:isPremium()`, and must not have `CONDITION_CHANNELMUTEDTICKS` (subid `5`, `120000` ms).
- `[english_chat.lua:onSpeak]`: Speaking requires `player:getLevel() >= 20` or `player:isPremium()`.
- `[gamemaster.lua:canJoin]`: Joining requires `player:getAccountType() >= ACCOUNT_TYPE_GAMEMASTER`.
- `[guild_leaders.lua:canJoin]`: Joining requires `player:getGuildLevel() == 3` or `player:getGroup():getAccess()`.
- `[help.lua:onSpeak]`: Normal group (`GROUP_TYPE_NORMAL`) players at level 1 and players with `player:kv():get("channel-help-exhaustion") > os.time()` cannot speak; `!mute ` and `!unmute ` require `playerGroupType >= GROUP_TYPE_TUTOR` and `playerGroupType > target:getAccountType()`.
- `[tutor.lua:canJoin]`: Joining requires `player:getGroup():getId() >= GROUP_TYPE_TUTOR`.
- `[world_chat.lua:onSpeak]`: Players with `level == 1` and `playerGroupType < GROUP_TYPE_GAMEMASTER` cannot speak.

## Side Effects

- `[advertising-rook.lua:onSpeak]`, `[advertising.lua:onSpeak]`: Adds `CONDITION_CHANNELMUTEDTICKS` (`120000` ms, subid `6` or `5`) to the speaking player and sends cancel messages on violation.
- `[guild_leaders.lua:onSpeak]`: Broadcasts custom formatted message to channel `11` via `sendChannelMessage` and returns `false` to suppress default channel output.
- `[help.lua:onSpeak]`: Applies or removes `CONDITION_CHANNELMUTEDTICKS` (`3600000` ms, subid `7`) on target player, sets or removes target KV key `"channel-help-exhaustion"` (`os.time() + 180`), and broadcasts moderation notices to channel `7` via `sendChannelMessage`.

## Verification

- Run: `ctest --test-dir build --output-on-failure`
