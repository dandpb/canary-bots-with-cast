-- Run from the repository root with Lua or LuaJIT.
local events, deferred, orderMode, selection
local player = {}
local offer = { name = "Configured offer", id = 70, price = 150, type = 1 }
local hireling = { id = 42, name = "Old Name", sex = 1, active = 0 }

local function record(event)
	events[#events + 1] = event
end

function addPlayerEvent(callback, _, ...)
	local args = { ... }
	local unpackArgs = table.unpack or unpack
	deferred[#deferred + 1] = function()
		callback(unpackArgs(args))
	end
end

local function flushEvents()
	for _, callback in ipairs(deferred) do
		callback()
	end
	deferred = {}
end

package.preload["gamestore.senders"] = function()
	return {
		sendStorePurchaseSuccessful = function()
			record("success")
		end,
		sendRequestPurchaseData = function()
			record("request")
		end,
		sendUpdatedStoreBalances = function() end,
		sendStoreError = function()
			record("information")
		end,
	}
end

function string.trim(s)
	return s:match("^%s*(.-)%s*$")
end

function Player(id)
	assert(id == 10)
	return player
end

function Tile()
	return { hasFlag = function()
		return true
	end }
end

Game = { getNormalizedPlayerName = function() end }
GameStore = {
	ClientOfferTypes = { CLIENT_STORE_OFFER_NAMECHANGE = 1, CLIENT_STORE_OFFER_HIRELING = 2 },
	ItemLimit = { HIRELING = 10 },
	StoreErrors = { STORE_ERROR_INFORMATION = 4 },
	canUseHirelingName = function()
		return { ability = true }
	end,
	canChangeToName = function()
		return { ability = true }
	end,
	withPaidOrder = function(actor, product, price, deliver, detail)
		assert(actor == player and product == offer and price == (player.namelock and 0 or 150) and detail)
		record("order")
		if orderMode == "declined" then
			return false
		end
		local ok, result = pcall(deliver)
		assert((ok and result ~= false) == (orderMode ~= "delivery error"))
		if orderMode ~= "committed" then
			return false
		end
		record("durable")
		return true
	end,
}
HIRELING_SEX = { MALE = 1, FEMALE = 2 }
HIRELING_OUTFIT_DEFAULT = { male = 128, female = 136 }
HIRELING_LAMP = 29432

function player:getId()
	return 10
end

function player:getName()
	return "Old Name"
end

function player:getClient()
	return { version = 1200 }
end

function player:getPosition()
	return { sendMagicEffect = function()
		record("effect")
	end }
end

function player:kv()
	return { get = function()
		return player.namelock
	end }
end

function player:changeName(name, deferDisconnect)
	assert(name == "New Name" and deferDisconnect == true)
	record("rename character")
	return true
end

function player:remove()
	record("disconnect")
end

function player:getHirelingsCount()
	return 1
end

function player:canReceiveStoreItems(itemType, amount)
	assert(itemType == HIRELING_LAMP and amount == 1)
	return true
end

function player:makeCoinTransaction()
	error("configured purchase must reserve a durable order")
end

function player:addNewHireling(name, sex)
	assert(name == "New Name" and sex == 2)
	record("hireling lamp")
	return orderMode ~= "delivery error"
end

function player:createTransactionSummary()
	record("summary")
end

function player:findHirelingLamp(id)
	assert(id == 42)
	return nil
end

function player:sendHirelingSelectionModal(_, _, callback, data)
	selection = function()
		callback(self:getId(), data, hireling)
	end
end

function hireling:getId()
	return self.id
end

function hireling:getName()
	return self.name
end

function hireling:save()
	record("save hireling")
	return orderMode ~= "delivery error"
end

logger = { debug = function() end }

local purchases = dofile(arg[1] or "data/libs/gamestore/purchases.lua")

local function check(mode, run, expected)
	events, deferred, selection, orderMode = {}, {}, nil, mode
	run()
	flushEvents()
	assert(table.concat(events, ", ") == expected, table.concat(events, ", "))
end

check("declined", function()
	purchases.processNameChangePurchase(player, offer, 0, "")
	purchases.processHirelingPurchase(player, offer, 0, "", 0)
	purchases.processHirelingChangeNamePurchase(player, offer, 0, "")
end, "request, request, request")

local function renameCharacter()
	purchases.processNameChangePurchase(player, offer, 1, "new name")
end
check("declined", renameCharacter, "order")
check("pending", renameCharacter, "order, rename character")
check("committed", renameCharacter, "order, rename character, durable, success, disconnect")
player.namelock = true
check("committed", renameCharacter, "order, rename character, durable, success, disconnect")
player.namelock = nil

local function buyHireling()
	purchases.processHirelingPurchase(player, offer, 2, "new name", 2)
end
check("declined", buyHireling, "order")
check("delivery error", buyHireling, "order, hireling lamp")
check("committed", buyHireling, "order, hireling lamp, summary, durable, success")

local function renameHireling()
	purchases.processHirelingChangeNamePurchase(player, offer, 1, "new name")
	flushEvents()
	assert(selection and #events == 1 and events[1] == "information")
	selection()
end
check("declined", renameHireling, "information, order")
assert(hireling.name == "Old Name")
check("committed", renameHireling, "information, order, save hireling, durable, success")
assert(hireling.name == "New Name")

local function changeHirelingSex()
	purchases.processHirelingChangeSexPurchase(player, offer)
	flushEvents()
	assert(selection and #events == 1 and events[1] == "information")
	selection()
end
check("declined", changeHirelingSex, "information, order")
assert(hireling.sex == 1)
check("committed", changeHirelingSex, "information, order, save hireling, durable, success")
assert(hireling.sex == 2)

player.getTile = Tile
function player:isPzLocked()
	return false
end

function player:getCondition()
	return nil
end

function player:getTown()
	return { getTemplePosition = function()
		return 17
	end }
end

function player:teleportTo(position)
	assert(position == 17)
	record("teleport")
	return orderMode ~= "delivery error"
end

function player:sendTextMessage()
	record("notice")
end

function GetHirelingSkillNameById(id)
	assert(id == offer.id)
	return "banker"
end

function GetHirelingOutfitNameById(id)
	assert(id == offer.id)
	return "dragon"
end

function player:enableHirelingSkill(skill)
	assert(skill == "banker")
	record("skill")
end

function player:hasHirelingSkill()
	return true
end

function player:enableHirelingOutfit(outfit)
	assert(outfit == "dragon")
	record("outfit")
end

function player:hasHirelingOutfit()
	return true
end

for _, delivery in ipairs({
	{ handler = purchases.processTempleTeleportPurchase, action = "teleport" },
	{ handler = purchases.processHirelingSkillPurchase, action = "skill" },
	{ handler = purchases.processHirelingOutfitPurchase, action = "outfit" },
}) do
	local function deliver()
		local notice = delivery.handler(player, offer)
		assert(type(notice) == "function", "purchase notification must wait for confirmation")
		if orderMode == "committed" then
			record("durable")
			notice()
		end
	end
	check("pending", deliver, delivery.action)
	check("committed", deliver, delivery.action .. ", durable, effect, notice")
end

check("delivery error", function()
	assert(purchases.processTempleTeleportPurchase(player) == false)
end, "teleport")

print("GameStore purchase handlers passed")
