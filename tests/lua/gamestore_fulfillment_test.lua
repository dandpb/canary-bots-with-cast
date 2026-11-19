-- Run from the repository root with Lua or LuaJIT.
local stored, blocked, usedCapacity, premiumResult, vipGranted, vipUntil
local returns = { success = 0, refusal = 5 }
RETURNVALUE_NOERROR = returns.success
SERVER_NAME = "Tests"
ITEM_DECORATION_KIT = 4
ITEM_ATTRIBUTE_CHARGES = "charges"
ITEM_ATTRIBUTE_DATE = "date"
ITEM_HEALTH_CASK_START, ITEM_HEALTH_CASK_END = 5, 5
ITEM_MANA_CASK_START, ITEM_MANA_CASK_END = 6, 6
ITEM_SPIRIT_CASK_START, ITEM_SPIRIT_CASK_END = 7, 7

local types = { OFFER_TYPE_ITEM = 1, OFFER_TYPE_CHARGES = 2, OFFER_TYPE_STACKABLE = 3, OFFER_TYPE_HOUSE = 4, OFFER_TYPE_PREMIUM = 5, OFFER_TYPE_PREYBONUS = 6 }
GameStore = { OfferTypes = types, ItemLimit = { PREY_WILDCARD = 50 } }
Player = {}
configKeys = {}
configManager = { getBoolean = function()
	return true
end }

function Condition()
	return {}
end

function ItemType(id)
	return {
		getId = function()
			return id or 0
		end,
		getName = function()
			return "Test Item"
		end,
		isStackable = function()
			return id == 2
		end,
		getStackSize = function()
			return 100
		end,
		getCharges = function()
			return id == 3 and 500 or 0
		end,
	}
end

local function makeItem(id, count)
	return {
		id = id,
		count = count,
		setCustomAttribute = function(self, key, value)
			self[key] = value
			return true
		end,
		setAttribute = function(self, key, value)
			if key then self[key] = value end
			return true
		end,
	}
end
Game = { createItem = makeItem }

local inbox = {
	addItemEx = function(_, item)
		if #stored + 1 == blocked then
			return returns.refusal
		end
		stored[#stored + 1] = item
		return returns.success
	end,
}

function Player:getStoreInbox()
	return inbox
end

function Player:canReceiveStoreItems(id, count)
	usedCapacity = { id, count }
	return true
end

function Player:sendUpdateContainer() end

function Player:getPreyCards()
	return 48
end

function Player:addMount()
	return false
end

function Player:hasMount()
	return false
end

function Player:addPremiumDays(days, requireExact)
	assert(days == 30 and requireExact)
	return premiumResult
end

function Player:getPremiumDays()
	return 0
end

function Player:getVipTime()
	return vipUntil
end

function Player:onAddVip(days, silent)
	assert(days == 30 and silent)
	vipGranted = true
end

package.preload["gamestore.senders"] = function()
	return {}
end
dofile(arg[2] or "data/libs/functions/player.lua")
local purchases = dofile(arg[1] or "data/libs/gamestore/purchases.lua")

stored = {}
blocked = 2
assert(purchases.processItemPurchase(Player, 1, 3, true) == false, "native addItemEx refusal must fail the delivery")
assert(#stored == 1 and stored[1].count == 1)

stored = {}
blocked = nil
assert(purchases.processItemPurchase(Player, 1, 3, true))
assert(#stored == 3 and stored[3].count == 1)
assert(purchases.processChargesPurchase(Player, 3, "charged tool", 500, true))
assert(stored[4].id == 3 and stored[4].count == 1 and stored[4].charges == 500)

stored = {}
assert(purchases.processStackablePurchase(Player, 2, 250, "stack", true))
assert(#stored == 3 and stored[1].count == 100 and stored[2].count == 100 and stored[3].count == 50)
stored = {}
blocked = 2
assert(purchases.processStackablePurchase(Player, 2, 250, "stack", true) == false and #stored == 1)

local furniture = { type = types.OFFER_TYPE_HOUSE, itemtype = { 8, 9 }, count = 2, movable = true }
assert(purchases.preflightPurchase(Player, furniture))
assert(usedCapacity[1] == ITEM_DECORATION_KIT and usedCapacity[2] == 4)
stored = {}
assert(purchases.processHouseRelatedPurchase(Player, furniture) == false and #stored == 1)
stored = {}
blocked = nil
assert(purchases.processHouseRelatedPurchase(Player, furniture))
assert(#stored == 4 and stored[1].unWrapId == 8 and stored[4].unWrapId == 9)

local cask = { type = types.OFFER_TYPE_HOUSE, itemtype = 5, count = 1000, movable = true }
assert(purchases.preflightPurchase(Player, cask) and usedCapacity[2] == 1)
stored = {}
assert(purchases.processHouseRelatedPurchase(Player, cask))
assert(#stored == 1 and stored[1].unWrapId == 5 and stored[1].date == 1000)

assert(purchases.preflightPurchase(Player, { type = types.OFFER_TYPE_PREYBONUS, count = 3 }) == false)
assert(purchases.preflightPurchase(Player, { type = types.OFFER_TYPE_PREYBONUS, count = 2 }))
assert(purchases.processMountPurchase(Player, 12) == false)
local premium = { type = types.OFFER_TYPE_PREMIUM, id = 3030 }
vipUntil = 0xFFFFFFFF - 29 * 86400
assert(purchases.preflightPurchase(Player, premium) == false)
vipUntil = 0xFFFFFFFF - 30 * 86400
assert(purchases.preflightPurchase(Player, premium))
premiumResult = 30
assert(purchases.processPremiumPurchase(Player, 3030) == false and not vipGranted)
premiumResult = true
assert(type(purchases.processPremiumPurchase(Player, 3030)) == "function" and vipGranted)

print("Purchase delivery checks the actual persisted product outcomes and amounts")
