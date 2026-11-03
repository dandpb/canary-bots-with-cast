-- Public startup lifecycle with a virtual event loop: no game/database required.
local events, pending, attempts, loaded, warnings, onlineQueries = {}, {}, {}, {}, {}, {}
local clock = 0
local count = 101
BOT_CONFIG = { MASTER_DISABLE = false, BOT_ACCOUNT_ID = 65000, TARGET_ONLINE = count, MANAGER_INTERVAL = 10000 }
BotPlayers = {}
Position = function(x, y, z) return { x = x, y = y, z = z } end
configKeys = { BOT_PLAYERS_SHOW_AS_ONLINE = "show_online" }
local showOnline = arg[2] == "online"
configManager = { getBoolean = function(key) return key == "show_online" and showOnline end }
logger = { info = function() end, error = function() end,
	warn = function(message) warnings[#warnings + 1] = message end }
GlobalEvent = function(name)
	local event = { register = function() end, interval = function() end }
	events[name] = event
	return event
end
addEvent = function(callback, delay)
	pending[#pending + 1] = { at = clock + delay, callback = callback }
end
db = { query = function() return true end, botAsyncQuery = function(query) onlineQueries[#onlineQueries + 1] = query; return true end,
	storeQuery = function() return { index = 1 } end }
Result = {
	getString = function(cursor) return "Bot " .. cursor.index end,
	next = function(cursor) cursor.index = cursor.index + 1; return cursor.index <= count end,
	free = function() end,
}
Game = {
	createTile = function() end,
	loadBotPlayer = function(name)
		local guid = tonumber(name:match("%d+"))
		attempts[guid] = (attempts[guid] or 0) + 1
		if guid == 2 and attempts[guid] == 1 then error("transient load exception") end
		if guid == 52 and attempts[guid] == 1 then return nil end
		if guid == count then return nil end
		loaded[guid] = clock
		return { getGuid = function() return guid end, registerEvent = function() end }
	end,
}
dofile(arg[1] or "data/scripts/globalevents/bot_manager.lua")
assert(events.BotStartup.onStartup())
local finalized = false
while #pending > 0 do
	table.sort(pending, function(a, b) return a.at < b.at end)
	local nextEvent = table.remove(pending, 1)
	-- The post-load quest/state-restore callback is outside this pacing fixture.
	if attempts[count] == 3 then
		assert(nextEvent.at >= clock + 2000, "startup completion must remain deferred")
		finalized = true
		break
	end
	clock = nextEvent.at
	nextEvent.callback()
end
assert(loaded[51] and loaded[50] and loaded[51] - loaded[50] >= 35000,
	"batch 51 must wait for the first 50 loads and their pause")
assert(loaded[100] and attempts[count] == 3, "final load failure must have bounded retries")
assert(attempts[2] == 2 and attempts[52] == 2, "transient exceptions/nil loads must retry")
local registered = 0
for _ in pairs(BotPlayers) do registered = registered + 1 end
assert(registered == 100, "one failed bot must not lose later registrations")
assert(#warnings == 1 and finalized, "failed final bot must warn and still schedule startup completion")
if showOnline then
	assert(#onlineQueries >= 3, "visible bots must synchronize online rows during loading")
else
	assert(#onlineQueries == 0, "hidden bots must not publish online rows during loading")
end
print("PASS: startup batches pause after 50, retry transient failures and finish after a final failure")
