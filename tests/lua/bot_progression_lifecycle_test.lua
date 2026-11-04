-- Run only in a disposable server after bot_progression_test.lua.
-- With the QA save queue blocked, "reconnect" must still preserve progression.
return function(name, mode)
	local player = assert(Player(name), "fixture must be awake")
	local guid = player:getGuid()
	local expected = {
		level = player:getLevel(), xp = player:getExperience(),
		hp = player:getMaxHealth(), mana = player:getMaxMana(), cap = player:getCapacity(),
	}
	Game.botCommand(name, "pin off")
	player = nil
	collectgarbage("collect")
	if mode == "hibernate" then
		assert(Game.botHibernate(guid), "hibernate refused")
		Game.botCommand(name, "wake")
	elseif mode == "reconnect" or mode == "force" or mode == "named" then
		if mode == "force" then
			Game.botForceDeactivate(guid)
		else
			assert(Game.botDeactivate(guid), "deactivation refused")
		end
		collectgarbage("collect")
		if mode == "named" then
			assert(Game.loadBotPlayer(name:lower()), "case-insensitive reload refused")
		end
		assert(Game.botActivate(guid), "reactivation refused")
	else
		error("expected hibernate, reconnect, force or named")
	end
	player = assert(Player(name), "fixture did not return")
	assert(player:getLevel() == expected.level and player:getExperience() == expected.xp,
		"lifecycle lost earned XP or levels")
	assert(player:getMaxHealth() == expected.hp and player:getMaxMana() == expected.mana,
		"lifecycle lost vocation stat gains")
	assert(player:getCapacity() == expected.cap, "lifecycle lost capacity gains")
	Game.botCommand(name, "pin on")
	return expected
end
