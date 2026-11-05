-- Test-only adapter. The harness injects it into a disposable server, never production.
assert(configManager.getString(configKeys.SERVER_NAME) == "Canary lifecycle QA", "isolated QA server required")
BOT_CONFIG.MASTER_DISABLE = true
local qa = {}
local storage = 987654

-- The game Lua state has no JSON module. Keep this fixture's response format local.
function qa.encode(value)
	local kind = type(value)
	if kind == "nil" then return "null" end
	if kind == "boolean" or kind == "number" then return tostring(value) end
	if kind == "string" then
		local out = { string.char(34) }
		for i = 1, #value do
			local byte = value:byte(i)
			if byte == 34 or byte == 92 then out[#out + 1] = string.char(92, byte)
			elseif byte < 32 then out[#out + 1] = string.char(92) .. "u" .. string.format("%04x", byte)
			else out[#out + 1] = string.char(byte) end
		end
		out[#out + 1] = string.char(34)
		return table.concat(out)
	end
	assert(kind == "table")
	local out = {}
	if #value > 0 then
		for _, item in ipairs(value) do out[#out + 1] = qa.encode(item) end
		return "[" .. table.concat(out, ",") .. "]"
	end
	for key, item in pairs(value) do out[#out + 1] = qa.encode(tostring(key)) .. ":" .. qa.encode(item) end
	return "{" .. table.concat(out, ",") .. "}"
end

local function snapshot(player, weaponId)
	local weapon = player:getItemById(weaponId or 28540, true)
	return {
		guid = player:getGuid(), name = player:getName(), xp = player:getExperience(),
		skill = player:getSkillLevel(SKILL_SWORD), tries = player:getSkillTries(SKILL_SWORD),
		magic = player:getMagicLevel(), spent = player:getManaSpent(),
		storage = player:getStorageValue(storage),
		charges = weapon and weapon:getAttribute(ITEM_ATTRIBUTE_CHARGES) or -1,
	}
end

function qa.run(command)
	local name = command.name or "Grizzle Alyronia"
	if command.action == "brain" then
		local operation = command.operation or "status"
		assert(operation == "status" or operation == "reload" or operation == "disable")
		return Game.botCommand("_global", "brain " .. operation)
	end
	if command.action == "party" then
		local leader = assert(Player("Lifecycle Human"))
		if leader:getParty() then leader:getParty():disband() end
		for _, botName in ipairs({ "Grizzle Alyronia", "Sever Heartspear", "Galdon Whitehoof" }) do
			local player = assert(Player(botName))
			Game.botSetAIPaused(player:getGuid(), false)
		end
		qa.native = qa.native or assert(package.loadlib("/qa/lifecycle_bridge.so", "luaopen_lifecycle_bridge"))()
		qa.native.cast("invite")
		return { invited = 3 }
	end
	if command.action == "population" then
		local start = assert(tonumber(command.start))
		local limit = assert(tonumber(command.limit))
		assert(limit > 0 and limit <= 25 and start >= 65000)
		Game.botCommand("_global", "schedule off")
		local cursor = db.storeQuery("SELECT id,name FROM players WHERE account_id=65000 AND id>=" .. start .. " ORDER BY id LIMIT " .. limit)
		local names, last = {}, start
		if cursor then
			repeat names[#names + 1] = result.getString(cursor, "name"); last = result.getNumber(cursor, "id") until not result.next(cursor)
			result.free(cursor)
		end
		for _, botName in ipairs(names) do
			local player = assert(Game.loadBotPlayer(botName))
			Game.botActivate(player:getGuid())
			Game.botSetAIPaused(player:getGuid(), true)
			Game.botHibernate(player:getGuid())
		end
		return { count = #names, last = last }
	end
	if command.action == "dbprobe" then
		local cursor = assert(db.storeQuery("SELECT 1 AS value"))
		result.free(cursor)
		return { completed = true }
	end
	if command.action == "cast" then
		qa.native = qa.native or assert(package.loadlib("/qa/lifecycle_bridge.so", "luaopen_lifecycle_bridge"))()
		return qa.native.cast(command.operation or "status", command.text or "")
	end
	if command.action == "optional" then
		assert(Game.loadBotPlayer(name) == nil)
		assert(Game.botCountActive() == 0)
		assert(Game.botActivate(65001) == false)
		assert(Game.botHibernate(65001) == false)
		assert(Game.botGetState(65001) == -1)
		assert(Game.botCommand("_global", "schedule status"):find("unavailable"))
		assert(Game.botReregisterAll() == 0)
		return { safe = true }
	end
	if command.action == "config" then
		assert(Game.reload(RELOAD_TYPE_CONFIG))
		return { showBots = configManager.getBoolean(configKeys.BOT_PLAYERS_SHOW_AS_ONLINE) }
	end
	if command.action == "death" then
		local player = assert(Player("Lifecycle Human"))
		player:addHealth(-player:getHealth())
		return { health = player:getHealth() }
	end
	if command.action == "virtual" or command.action == "unregister" or command.action == "pending"
		or command.action == "arm" or command.action == "counts" or command.action == "roster" then
		qa.native = qa.native or assert(package.loadlib("/qa/lifecycle_bridge.so", "luaopen_lifecycle_bridge"))()
		local guid = command.guid or 65001
		if command.action == "roster" then return qa.native.roster() end
		if command.action == "virtual" then
			qa.native.setVirtual(guid, command.x, command.y, command.z)
			saveServer()
			return { x = command.x, y = command.y, z = command.z }
		elseif command.action == "unregister" then
			qa.native.unregister(guid)
			return { registered = Game.botGetState(guid) >= 0, pending = qa.native.pending(guid) }
		elseif command.action == "pending" then return { pending = qa.native.pending(guid) }
		elseif command.action == "arm" then qa.native.armPause(guid, command.delay or 2000) end
		local fired, destroyed = qa.native.counts()
		return { fired = fired, destroyed = destroyed }
	end
	if command.action == "load" then
		Game.botCommand("_global", "schedule off")
		local player = assert(Game.loadBotPlayer(name), "fixture load failed")
		Game.botActivate(player:getGuid())
		Game.botSetAIPaused(player:getGuid(), true)
		local temple = Town(1):getTemplePosition()
		if player:getPosition() ~= temple then
			assert(player:teleportTo(temple), "fixture needs a temple tile")
		end
		return snapshot(player, command.weapon)
	end
	if command.action == "save" then saveServer(); return { scheduled = true } end
	if command.action == "reload" then return BotSystem.executeReload({ source = "isolated QA" }) end
	if command.action == "shutdown" then Game.setGameState(GAME_STATE_SHUTDOWN); return { shutdown = true } end
	if command.action == "wake" then
		Game.botCommand(name, "wake")
		return snapshot(assert(Player(name), "wake failed"), command.weapon)
	end
	local player = assert(Player(name), "awake fixture required")
	local guid = player:getGuid()
	if command.action == "mutate" then
		local xp = player:getExperience()
		player:addSkillTries(SKILL_SWORD, 17)
		player:addManaSpent(23)
		player:setStorageValue(storage, command.value or 123)
		local weaponId = command.weapon or 28540
		local weapon = player:getItemById(weaponId, true) or assert(player:addItem(weaponId, 1))
		weapon:setAttribute(ITEM_ATTRIBUTE_CHARGES, command.charges or 10)
		assert(player:getExperience() == xp, "fixture must not award XP")
	elseif command.action == "train" then
		local nativeAction = Action
		local action = { id = function() end, allowFarUse = function() end, register = function() end }
		Action = function() return action end
		local ok, failure = pcall(dofile, "data/scripts/actions/items/exercise_training_weapons.lua")
		Action = nativeAction
		assert(ok, failure)
		local dummyId = assert(next(Game.getDummies()), "no dummy definitions")
		local dummy = assert(Game.createItem(dummyId, 1, player:getPosition()), "dummy creation failed")
		local weapon = assert(player:getItemById(command.weapon or 28540, true))
		assert(action.onUse(player, weapon, player:getPosition(), dummy, player:getPosition(), false), "training action refused")
		qa.dummy = dummy
	elseif command.action == "stop" then
		player:setTraining(false)
		if _G.OnExerciseTraining[ player:getId() ] then
			stopEvent(_G.OnExerciseTraining[ player:getId() ].event)
			_G.OnExerciseTraining[ player:getId() ] = nil
		end
		if qa.dummy then qa.dummy:remove(); qa.dummy = nil end
	elseif command.action == "hibernate" then
		local before = snapshot(player, command.weapon)
		assert(Game.botHibernate(guid), "hibernate refused")
		return before
	elseif command.action == "deactivate" then
		assert(Game.botDeactivate(guid), "deactivate refused")
		assert(Game.botActivate(guid), "reactivation refused")
		player = assert(Player(name))
	elseif command.action == "force" then
		Game.botForceDeactivate(guid)
		assert(Game.botActivate(guid), "reactivation refused")
		player = assert(Player(name))
	elseif command.action == "wake" then
		Game.botCommand(name, "wake")
	elseif command.action ~= "inspect" then error("unknown QA action") end
	return snapshot(player, command.weapon)
end

return qa
