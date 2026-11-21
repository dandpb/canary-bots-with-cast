-- Run from the repository root with Lua or LuaJIT.
local scriptPath = arg and arg[1] or "data/scripts/globalevents/bot_house_reclaim.lua"
local event = { interval = function() end, register = function() end }
local state, reads, freed, restores, pending = 0, 0, 0, 0, nil
local deferred
local unpackValues = table.unpack or unpack

GAME_STATE_SHUTDOWN = 1
Game = { getGameState = function() return state end }
GlobalEvent = function() return event end
BotHouseClaim = {
	ensureSchema = function() end,
	isBotGuid = function() return true end,
	restore = function()
		restores = restores + 1
		return 1
	end,
}
db = { botAsyncStoreQuery = function(_, callback)
	reads = reads + 1
	pending = callback
end }
Result = {
	getNumber = function(result, key) return key == "hid" and result.index or 65000 end,
	next = function(result)
		result.index = result.index + 1
		return result.index <= result.size
	end,
	free = function() freed = freed + 1 end,
}
House = function() return { getOwnerGuid = function() return 0 end } end
logger = { info = function() end, error = error }
addEvent = function(callback, _, ...)
	local arguments = { ... }
	deferred = function() return callback(unpackValues(arguments)) end
end

dofile(scriptPath)

state = GAME_STATE_SHUTDOWN
assert(event.onThink(0) and reads == 0, "shutdown must not poll vacancies")

state = 0
assert(event.onThink(0) and reads == 1)
state = GAME_STATE_SHUTDOWN
pending({ index = 1, size = 1 })
assert(freed == 1 and restores == 0, "late query results must be freed without restoring houses")

state = 0
assert(event.onThink(0) and reads == 2)
pending({ index = 1, size = 6 })
assert(freed == 2 and restores == 5 and deferred, "normal work must restore a chunk and schedule the remainder")
state = GAME_STATE_SHUTDOWN
deferred()
assert(restores == 5, "a chunk queued before shutdown must not restore houses")

print("PASS: house reclaim stops polling and mutating during shutdown")
