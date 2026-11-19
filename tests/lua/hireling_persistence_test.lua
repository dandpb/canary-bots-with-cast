-- Run from the repository root with Lua or LuaJIT.
local insertedId
local lampId
local inbox

db = {
	insert = function(sql)
		assert(sql:find("INSERT INTO `player_hirelings`", 1, true))
		return insertedId
	end,
	escapeString = function(name)
		return "'" .. name .. "'"
	end,
	query = function()
		return false
	end,
	storeQuery = function()
		return 1
	end,
}
Result = { getNumber = function()
	return 19 -- A preexisting orphan, unrelated to the new insert.
end }

Player = {}
function Player:getGuid()
	return 7
end

function Player:getName()
	return "Owner"
end

function Player:getFreeCapacity()
	return 10
end

function Player:getStoreInbox()
	return inbox
end

function Player:getPosition()
	return { sendMagicEffect = function() end }
end

function Player:sendTextMessage() end

function ItemType()
	return { getWeight = function()
		return 1
	end }
end

logger = { error = function() end }

dofile(arg[1] or "data/libs/systems/hireling.lua")

local hireling = Hireling:new({ name = "First", player_id = 7 })
assert(not PersistHireling(hireling), "a refused INSERT must not resolve to a historical row")
assert(hireling:getId() == -1)
assert(not Player:addNewHireling("No inbox", HIRELING_SEX.FEMALE))

inbox = {
	getItems = function()
		return {}
	end,
	getMaxCapacity = function()
		return 1
	end,
	addItem = function()
		return {
			setAttribute = function() end,
			setCustomAttribute = function(_, key, id)
				assert(key == "Hireling")
				lampId = id
			end,
		}
	end,
}
assert(not Player:addNewHireling("Database refusal", HIRELING_SEX.FEMALE))
assert(Player:getHirelingsCount() == 0 and not lampId)

insertedId = 27
local bought = Player:addNewHireling("Second", HIRELING_SEX.FEMALE)
assert(bought and bought:getId() == 27 and lampId == 27)
assert(Player:getHirelingsCount() == 1)

print("Hireling persistence uses only the confirmed INSERT id")
