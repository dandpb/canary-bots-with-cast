-- Integration test: run inside a disposable server with a level-8, 4200-XP
-- character, no party, no equipment/stat bonuses, and a standard vocation.
-- dofile("tests/lua/bot_progression_test.lua")(Player("Fixture Name"))
-- The same assertions apply to native bots and ordinary players.
return function(player)
	assert(player and player:getLevel() == 8 and player:getExperience() == 4200,
		"requires a disposable level-8 character with exactly 4200 XP")
	assert(not player:getParty(), "fixture must be solo")
	local gains = {
		[1] = { hp = 5, mana = 30, cap = 10 },
		[2] = { hp = 5, mana = 30, cap = 10 },
		[3] = { hp = 10, mana = 15, cap = 20 },
		[4] = { hp = 15, mana = 5, cap = 25 },
	}
	local gain = assert(gains[player:getVocation():getBaseId()], "unsupported fixture vocation")
	local hp, mana, capacity = player:getMaxHealth(), player:getMaxMana(), player:getCapacity()

	player:addExperience(0)
	assert(player:getExperience() == 4200 and player:getLevel() == 8, "zero XP changed progression")

	player:addExperience(100)
	assert(player:getExperience() == 4300, "earned XP was discarded")
	assert(player:getLevel() == 8, "advanced before the level threshold")
	assert(player:getMaxHealth() == hp and player:getMaxMana() == mana, "stats changed without a level")

	-- Tibia's standard thresholds: level 8 = 4200, 9 = 6400, 11 = 13000.
	player:addExperience(2100, true)
	assert(player:getExperience() == 6400 and player:getLevel() == 9, "exact threshold did not advance")
	assert(player:getMaxHealth() == hp + gain.hp, "incorrect vocation health gain")
	assert(player:getMaxMana() == mana + gain.mana, "incorrect vocation mana gain")
	assert(player:getCapacity() == capacity + gain.cap, "incorrect vocation capacity gain")
	assert(player:getHealth() == player:getMaxHealth(), "level-up did not restore health")
	assert(player:getMana() == player:getMaxMana(), "level-up did not restore mana")

	player:addExperience(6600)
	assert(player:getExperience() == 13000 and player:getLevel() == 11, "multiple level-ups were lost")
	assert(player:getMaxHealth() == hp + 3 * gain.hp, "multiple health gains were lost")
	assert(player:getMaxMana() == mana + 3 * gain.mana, "multiple mana gains were lost")
	assert(player:getCapacity() == capacity + 3 * gain.cap, "multiple capacity gains were lost")
	return { name = player:getName(), experience = 13000, level = 11 }
end
