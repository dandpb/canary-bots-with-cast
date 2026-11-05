-- Public Lua reload boundary: preparation failures must not deactivate bots;
-- commit failures must not issue commands/ticks/restoration into a missing engine.
Position = function(x, y, z) return { x = x, y = y, z = z } end
logger = { info = function() end, warn = function() end, error = function() end }
db = { query = function() return true end, storeQuery = function() return false end }
Player = function() return nil end
addEvent = function(callback) callback() end
Game = {}
dofile(arg[1] or "data/scripts/lib/bot_system.lua")

local prepared, committed, cancelled, restored, commands, ticks
local mode, touched
local function fixture()
	prepared, committed, cancelled, restored, commands, ticks = 0, 0, 0, 0, 0, 0
	touched = false
	Game = {
		botPrepareReload = function()
			prepared = prepared + 1
			if mode == "prepare-throw" then error("invalid library") end
			if mode == "prepare-fail" then return { ok = false, phase = "data", message = "bad CSV" } end
			return { ok = true, ticket = 41 }
		end,
		botCancelReload = function(ticket) assert(ticket == 41); cancelled = cancelled + 1 end,
		getPlayers = function()
			assert(prepared == 1, "must prepare before inspecting/changing population")
			if mode == "prefix-throw" then error("snapshot failure") end
			return {}
		end,
		getBotHibernationStates = function() return {} end,
		botCommand = function(_, command)
			assert(not (mode == "commit-fail" and committed > 0), "command after failed commit")
			commands = commands + 1
			return command == "schedule status" and "Scheduler: OFF" or "OK"
		end,
		botForceDeactivateForReload = function() touched = true end,
		botReload = function(ticket)
			assert(ticket == 41)
			committed = committed + 1
			return { ok = mode ~= "commit-fail", message = "fixture commit result" }
		end,
		botStartTickLoop = function() ticks = ticks + 1; return true end,
		botReregisterAll = function() restored = restored + 1; return 0 end,
	}
end

for _, failure in ipairs({ "prepare-fail", "prepare-throw" }) do
	mode = failure; fixture()
	local outcome = BotSystem.executeReload({ source = failure })
	assert(not outcome.ok and not touched and committed == 0 and commands == 0 and ticks == 0 and restored == 0)
	assert(not BotSystem._reloadInProgress, "preparation failure must allow retry")
end
mode = "prefix-throw"; fixture()
assert(not BotSystem.executeReload({ source = mode }).ok)
assert(cancelled == 1 and committed == 0 and not BotSystem._reloadInProgress)
mode = "commit-fail"; fixture()
assert(not BotSystem.executeReload({ source = mode }).ok)
assert(committed == 1 and cancelled == 1 and ticks == 0 and restored == 0 and not BotSystem._reloadInProgress)
mode = "success"; fixture()
BotSystem.executeReload({ source = "retry" })
assert(committed == 1 and restored == 1 and ticks == 1 and not BotSystem._reloadInProgress)
print("PASS: preparation/commit failures stop safely, release reload state and permit retry")
