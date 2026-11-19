local prefix = "data/libs/gamestore/"
local alerts, order, deliveries = {}, nil, 0
local sendStoreError = function(_, _, message) alerts[#alerts + 1] = message end
package.preload["gamestore.constants"] = function() return { OfferTypes = {}, ConfigureOffers = { SHOW_NORMAL = 0 } } end
package.preload["gamestore.helpers"] = function()
	local helpers = dofile(prefix .. "helpers.lua")
	helpers.useOfferConfigure = function() return 0 end
	return helpers
end
package.preload["gamestore.senders"] = function()
	return { sendStoreError = sendStoreError, sendUpdatedStoreBalances = function() end, sendStorePurchaseSuccessful = function() end }
end
function addPlayerEvent(callback, delay, ...)
	callback(...)
end
function table.contains(values, value)
	for _, candidate in pairs(values) do
		if candidate == value then return true end
	end
	return false
end

local stack = { id = { 101, 102 }, price = { 20, 35 }, coinType = 1, name = "Supply", type = 1, count = 5 }
local outfit = { id = { male = 201, female = 202 }, price = 70, coinType = 1, name = "Outfit", type = 2 }
local boost = { id = 301, price = 30, coinType = 1, name = "XP Boost", type = 3 }
local playerAvailable, purchaseReady = true, true
local boostTier
local actor = {
	kv = function()
		return {
			get = function(_, key) if key == "xp" then return boostTier end end,
			set = function(_, key, value) if key == "xp" then boostTier = value end end,
		}
	end,
	getVocation = function() return { getId = function() return 1 end } end,
	canBuyOffer = function() return { disabled = playerAvailable and 0 or 1, disabledReason = "Already owned." } end,
	canPayForOffer = function() return true end,
	createTransactionSummary = function() end,
}
Player = function() return actor end
GameStore = {
	Categories = { { offers = { stack, outfit, boost } } },
	OfferTypes = { OFFER_TYPE_STACKABLE = 1, OFFER_TYPE_OUTFIT = 2, OFFER_TYPE_EXPBOOST = 3 },
	ExpBoostValues = { 30, 45 }, ExpBoostValuesCustom = { 37, 80 },
	ConfigureOffers = { SHOW_CONFIGURE = 1 },
	StoreErrors = { STORE_ERROR_NETWORK = 1 }, Kv = { purchaseCooldown = "cooldown", expBoostCount = "xp" },
	preflightPurchase = function() return purchaseReady, "Insufficient inbox space." end,
	withPaidOrder = function(_, offer, price, deliver, _, wireId)
		order = { offer = offer, price = price, id = wireId }
		return deliver()
	end,
	processStackablePurchase = function() deliveries = deliveries + 1; return true end,
	processOutfitPurchase = function() deliveries = deliveries + 1; return true end,
	processExpBoostPurchase = function() deliveries = deliveries + 1; return true end,
}
GameStore.getOfferById = dofile(arg[1] or prefix .. "store.lua").getOfferById
local parser = dofile(prefix .. "parsers.lua")
local function buy(id)
	parser.parseBuyStoreOffer(1, { getU32 = function() return id end, getByte = function() return 0 end })
end

buy(102)
assert(order.id == 102 and order.price == 35 and deliveries == 1)
buy(101)
assert(order.id == 101 and order.price == 20 and deliveries == 2, "selecting a variant must preserve other variants")
assert(stack.id[1] == 101 and stack.id[2] == 102 and stack.price[1] == 20 and stack.price[2] == 35)
buy(202)
assert(order.id == 202 and order.price == 70 and deliveries == 3, "outfits must use the wire ID, even with a table of catalog IDs")

playerAvailable, order = false, nil
buy(202)
assert(not order and alerts[#alerts] == "Already owned.")
playerAvailable, purchaseReady = true, false
buy(101)
assert(not order and alerts[#alerts] == "Insufficient inbox space." and deliveries == 3)

purchaseReady = true
buy(301)
assert(order.price == 37 and boostTier == 2 and deliveries == 4)
buy(301)
assert(order.price == 80 and boostTier == 3 and deliveries == 5)
order = nil
buy(301)
assert(not order and alerts[#alerts] == "This offer is unavailable." and deliveries == 5)

print("PASS: catalog variants preserve prices/IDs and rejected offers never reserve an order")
