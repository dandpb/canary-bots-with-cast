-- Run from the repository root with Lua or LuaJIT.
local actionPath = arg and arg[1] or "data/scripts/actions/items/store_coins.lua"
local paymentPath = arg and arg[2] or "data/libs/gamestore/player.lua"
local action = { id = function() end, register = function() end }
local refused, messages, effects, redemptions = 0, 0, 0, 0
local approval, approve, publishedBalance
local token = {}

Action = function() return action end
logger = { warn = function() end, error = function() end }
local actor = {
	redeemStoreCoin = function(_, requested)
		assert(requested == token)
		redemptions = redemptions + 1
		return approval
	end,
	getTransferableCoins = function() return publishedBalance end,
	getName = function() return "Fixture" end,
	sendCancelMessage = function() refused = refused + 1 end,
	sendTextMessage = function() messages = messages + 1 end,
	getPosition = function()
		return { sendMagicEffect = function() effects = effects + 1 end }
	end,
}
dofile(actionPath)
assert(action.onUse(actor, token))
assert(refused == 1 and redemptions == 1 and messages == 0 and effects == 0, "an unconfirmed redemption cannot report success")

approval, publishedBalance = 25, nil
assert(action.onUse(actor, token))
assert(redemptions == 2 and messages == 1 and effects == 1, "a failed balance refresh cannot hide a confirmed redemption")

approval = 0
assert(action.onUse(actor, token))
assert(redemptions == 3 and messages == 1 and effects == 1, "removal of an already credited token cannot report another credit")

local balances, history, boostCount, charged, reportedBalance = 0, {}, 2, nil, 100
package.preload["gamestore.senders"] = function()
	return { sendStoreBalanceUpdating = function() balances = balances + 1 end }
end
GameStore = {
	OfferTypes = { OFFER_TYPE_EXPBOOST = 8 },
	CoinType = { Coin = 1, Transferable = 2 },
	Kv = { expBoostCount = "xp" },
	ExpBoostValues = { 15, 20 },
	HistoryTypes = { HISTORY_TYPE_NONE = 0 },
	insertHistory = function(_, _, _, price) table.insert(history, price) end,
}
local methods = dofile(paymentPath)
local buyer = setmetatable({
	getTibiaCoins = function() return reportedBalance end,
	getTransferableCoins = function() return reportedBalance end,
	getId = function() return 5 end,
	getAccountId = function() return 42 end,
	removeTibiaCoins = function(_, amount)
		charged = amount
		return approve
	end,
	removeTransferableCoins = function() return approve end,
	addTibiaCoins = function() return approve end,
	addTransferableCoins = function() return approve end,
	kv = function()
		return { get = function() return boostCount end, set = function(_, _, value) boostCount = value end }
	end,
}, { __index = methods })
local offer = { price = 8, name = "Fixture", type = GameStore.OfferTypes.OFFER_TYPE_EXPBOOST, coinType = GameStore.CoinType.Coin }
approve = false
assert(not buyer:removeCoinsBalance(15) and not buyer:removeTransferableCoinsBalance(15))
assert(not buyer:addCoinsBalance(15, true) and not buyer:addTransferableCoinsBalance(15, true))
assert(not buyer:makeCoinTransaction(offer))
assert(balances == 0 and #history == 0 and boostCount == 2 and offer.price == 8, "refused payment cannot report success or advance price")

reportedBalance = nil
assert(not buyer:canRemoveCoins(15) and not buyer:canRemoveTransferableCoins(15), "balance read failures must refuse payment validation")
reportedBalance = 100
approve = true
assert(buyer:makeCoinTransaction(offer))
assert(balances == 1 and history[1] == -20 and boostCount == 3 and charged == 20 and offer.price == 8)

print("PASS: Store Coins retain refused tokens and propagate actual payment results")
