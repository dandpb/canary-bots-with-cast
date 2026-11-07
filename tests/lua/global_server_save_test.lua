-- Run from the repository root: lua tests/lua/global_server_save_test.lua
-- Exercise the real daily global save event with fake engine globals for each close/shutdown combination.
local scriptPath = arg and arg[1] or "data/scripts/globalevents/global_server_save.lua"
local passed = 0

local function run(shutdown, close)
	local calls = { states = {}, saves = 0 }
	local config = { shutdown = shutdown, close = close, clean = false, notify = false }
	local event = {}
	configKeys = {
		GLOBAL_SERVER_SAVE_SHUTDOWN = "shutdown",
		GLOBAL_SERVER_SAVE_CLOSE = "close",
		GLOBAL_SERVER_SAVE_CLEAN_MAP = "clean",
		GLOBAL_SERVER_SAVE_NOTIFY_MESSAGE = "notify",
		GLOBAL_SERVER_SAVE_NOTIFY_DURATION = "duration",
		GLOBAL_SERVER_SAVE_TIME = "time",
	}
	configManager = {
		getBoolean = function(key)
			return config[key]
		end,
		getNumber = function()
			return 5
		end,
		getString = function()
			return "06:00:00"
		end,
	}
	GAME_STATE_CLOSED, GAME_STATE_SHUTDOWN = "closed", "shutdown"
	Game = {
		setGameState = function(state)
			table.insert(calls.states, state)
		end,
		broadcastMessage = function() end,
	}
	saveServer = function()
		calls.saves = calls.saves + 1
	end
	cleanMap = function() end
	addEvent = function(callback, _, ...)
		callback(...)
	end -- run at once: warnings, then the save
	DailyReward = { storages = { lastServerSave = 1 } }
	UpdateDailyRewardGlobalStorage = function() end
	Raid = { registry = {} }
	GlobalEvent = function()
		return setmetatable(event, { __index = { time = function() end, register = function() end } })
	end
	dofile(scriptPath)
	calls.keep = event.onTime(0)
	return calls
end

local function test(name, shutdown, close, states, saves)
	local calls = run(shutdown, close)
	assert(table.concat(calls.states, ",") == states, name .. ": states " .. table.concat(calls.states, ","))
	assert(calls.saves == saves, name .. ": saveServer called " .. calls.saves .. " times")
	assert(calls.keep == not shutdown, name .. ": onTime must keep the event unless it shuts down")
	passed = passed + 1
	print("ok " .. passed .. " - " .. name)
end

test("default shutdown saves through GAME_STATE_SHUTDOWN only", true, false, "shutdown", 0)
test("close without shutdown saves through GAME_STATE_CLOSED only", false, true, "closed", 0)
test("close and shutdown keep both states", true, true, "closed,shutdown", 0)
test("no close and no shutdown still saves the world", false, false, "", 1)
print(passed .. " global server save tests passed")
