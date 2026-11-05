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
	if command.action == "virtual" or command.action == "unregister" or command.action == "pending"
		or command.action == "arm" or command.action == "counts" then
		qa.native = qa.native or assert(package.loadlib("/qa/lifecycle_bridge.so", "luaopen_lifecycle_bridge"))()
		local guid = command.guid or 65001
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
