-- Run from the repository root: lua tools/bot_brain/test_reload.lua
-- Exercise the public reload lifecycle with an engine/player boundary fixture.
Position = function(x, y, z) return { x = x, y = y, z = z } end
local errors = {}
logger = {
	info = function() end,
	warn = function() end,
	error = function(message) errors[#errors + 1] = message end,
}
db = { query = function() return true end, storeQuery = function() return false end }
addEvent = function(callback) callback() end
Player = function() return nil end

local function actor(guid, removed, bot)
	return {
		getGuid = function() return guid end,
		getName = function() return "Companion" end,
		isRemoved = function() return removed end,
		isBotPlayer = function() return bot end,
	}
end
local stale = actor(51, true, true)
local current = actor(51, false, true)
local orphan = actor(52, true, true)
local recoveredOrphan = false
local human = actor(9, false, false)
Game = {
	botCommand = function() return "OK fixture" end,
	botIsActive = function(guid) return guid ~= 52 or recoveredOrphan end,
	botRecoverOrphanForReload = function(guid, player)
		assert(guid == 52 and player == orphan)
		recoveredOrphan = true
		return true
	end,
	getBotHibernationStates = function() return { { guid = 51, name = "Companion", hibernated = true } } end,
	loadBotPlayer = function() return current end,
	botForceDeactivateForReload = function() end,
	botReactivateForReload = function() return true end,
	botReload = function() return "Reloaded" end,
	botStartTickLoop = function() end,
	botReregisterAll = function() return 1 end,
	getPlayers = function() return { current, human } end,
}

dofile(arg[1] or "data/scripts/lib/bot_system.lua")
BotPlayers[51] = stale
BotPlayers[52] = orphan
BotSystem.executeReload({ source = "test" })
assert(#errors == 0, table.concat(errors, "; "))
assert(BotPlayers[51] == current, "reload must replace removed userdata with the current player")
assert(recoveredOrphan, "reload must retain unmatched references for orphan recovery")
assert(BotPlayers[9] == nil, "humans must not enter the bot hibernation cache")
assert(not BotSystem._reloadInProgress, "reload must finish")
print("PASS: reload refreshes the cache used by no-anchor hibernation")
