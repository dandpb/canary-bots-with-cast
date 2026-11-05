-- Integration test for a disposable server/database with a reduced population.
-- Wake loadedGuid first; excludedGuid must be a real bot outside the population.
-- dofile("tests/lua/bot_population_persistence_test.lua")(65045, 65999)
return function(loadedGuid, excludedGuid)
	assert(type(loadedGuid) == "number" and loadedGuid > 0 and loadedGuid % 1 == 0)
	assert(type(excludedGuid) == "number" and excludedGuid > 0 and excludedGuid % 1 == 0)
	assert(loadedGuid ~= excludedGuid, "fixtures must be distinct")
	local function hasState(guid)
		local resultId = db.storeQuery("SELECT `guid` FROM `bot_state_persistence` WHERE `guid` = " .. guid)
		if not resultId then return false end
		Result.free(resultId)
		return true
	end
	assert(db.query("INSERT INTO `bot_state_persistence` (`guid`, `name`, `ai_state`) " ..
		"SELECT `id`, `name`, 0 FROM `players` WHERE `id` IN (" .. loadedGuid .. "," .. excludedGuid .. ") " ..
		"ON DUPLICATE KEY UPDATE `ai_state`=0"), "could not seed restore fixtures")
	assert(hasState(loadedGuid) and hasState(excludedGuid), "fixtures must exist in the game database")
	Game.botRestoreStates()
	assert(not hasState(loadedGuid), "successfully restored state was not consumed")
	assert(hasState(excludedGuid), "unloaded bot lost its saved task")
	Game.botRestoreStates()
	assert(hasState(excludedGuid), "an empty restore erased the excluded bot's state")
	return "population persistence passed"
end
