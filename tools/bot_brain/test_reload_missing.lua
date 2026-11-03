-- Public reload regression: a registered bot can be between Player instances.
Position = function(x, y, z) return { x = x, y = y, z = z } end
local failures = {}
logger = { info = function() end, warn = function() end,
	error = function(message) failures[#failures + 1] = message end }
addEvent = function(callback) callback() end
local registered = { [51] = true, [53] = true, [54] = true }
local active = { [51] = true, [53] = true }
local scheduler = false
local world = {}
local function actor(guid, name)
	return { getGuid = function() return guid end, getName = function() return name end,
		isRemoved = function() return false end, isBotPlayer = function() return true end }
end
world[51] = actor(51, "Awake Companion")
local rows = { { id = 51, name = "Awake Companion" }, { id = 53, name = "Respawning Companion" }, { id = 54, name = "Inactive Companion" }, { id = 55, name = "Stale Registry Row" } }
db = {
	query = function() return true end,
	storeQuery = function(query)
		if query:find("bot_active_players", 1, true) then return { index = 1 } end
		return false
	end,
}
result = {
	getNumber = function(cursor) return rows[cursor.index].id end,
	getString = function(cursor) return rows[cursor.index].name end,
	next = function(cursor) cursor.index = cursor.index + 1; return rows[cursor.index] ~= nil end,
	free = function() end,
}
Player = function(name)
	for _, player in pairs(world) do if player:getName() == name then return player end end
end
Game = {
	botCommand = function(_, command)
		if command == "schedule status" then return scheduler and "Scheduler: ON" or "Scheduler: OFF" end
		if command == "schedule on" then scheduler = true end
		if command == "schedule off" then scheduler = false end
		return "OK fixture"
	end,
	botGetState = function(guid) return registered[guid] and 1 or -1 end,
	botIsActive = function(guid) return active[guid] == true end,
	getBotHibernationStates = function()
		return { { guid = 51, name = "Awake Companion", active = true, hibernated = false } }
	end,
	botForceDeactivateForReload = function(guid) active[guid] = false end,
	botReload = function() registered = {}; active = {}; scheduler = true; return "Reloaded" end,
	botStartTickLoop = function() end,
	loadBotPlayer = function(name)
		assert(not scheduler, "scheduler must pause while registrations are incomplete")
		local guid = name == "Respawning Companion" and 53 or 54
		assert(name ~= "Stale Registry Row")
		world[guid] = actor(guid, name)
		registered[guid] = true
		return world[guid]
	end,
	getPlayers = function()
		local list = {}; for _, player in pairs(world) do list[#list + 1] = player end; return list
	end,
	botReregisterAll = function()
		local count = 0
		for guid in pairs(world) do registered[guid] = true; count = count + 1 end
		return count
	end,
	botRecoverOrphanForReload = function(guid) return registered[guid] == true end,
	botReactivateForReload = function(guid)
		if not registered[guid] then return false end
		active[guid] = true; return true
	end,
	botActivate = function() return false end,
}
dofile(arg[1] or "data/scripts/lib/bot_system.lua")
BotPlayers[51] = world[51]
BotSystem.executeReload({ source = "test" })
assert(#failures == 0, table.concat(failures, "; "))
assert(Game.botGetState(53) ~= -1, "reload lost a registered bot outside the world and hibernation pool")
assert(Game.botIsActive(53), "reload must resume a previously active bot after rematerialization")
assert(Game.botIsActive(51), "reload must retain the awake bot")
assert(Game.botGetState(54) ~= -1 and not Game.botIsActive(54), "inactive registry member must stay inactive")
assert(not registered[55], "stale asynchronous registry rows must not create extra bots")
assert(not scheduler, "reload must preserve scheduler OFF")
assert(not BotSystem._reloadInProgress)
print("PASS: reload retains registered bots between Player instances")
