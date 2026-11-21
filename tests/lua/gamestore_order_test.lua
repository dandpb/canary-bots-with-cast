local orders = dofile(arg[1] or "data/libs/gamestore/orders.lua")
local calls, messages, deliveries = {}, {}, 0
local reserveStatus, claim, finish = "reserved", true, true
local offer = { id = 17, name = "Test outfit", coinType = 0 }
local player = { getId = function() return 9 end, getGuid = function() return 42 end, getAccountId = function() return 7 end }
GameStore = {
	StoreErrors = { STORE_ERROR_PURCHASE = 0 }, CoinType = { Coin = 0, Transferable = 1 },
	HistoryTypes = { HISTORY_TYPE_NONE = 0 }, insertHistory = function() calls[#calls + 1] = "history" end,
}
sendStoreError = function(_, _, message) messages[#messages + 1] = message end
logger = { warn = function() end }
db = {
	reserveStoreOrder = function(guid, account, id, _, amount)
		assert(guid == 42 and account == 7 and id == 17 and amount >= 0)
		calls[#calls + 1] = "reserve"
		if reserveStatus == "refused" then return nil, reserveStatus end
		return "9007199254740993", reserveStatus
	end,
	claimStoreOrder = function(id, guid)
		assert(id == "9007199254740993" and guid == 42)
		calls[#calls + 1] = "claim"
		return claim
	end,
	finishStoreOrder = function(id, guid)
		assert(id == "9007199254740993" and guid == 42)
		calls[#calls + 1] = "finish"
		return finish
	end,
}
local function deliver()
	deliveries = deliveries + 1
	calls[#calls + 1] = "deliver"
end

reserveStatus = "refused"
assert(not orders.withPaidOrder(player, offer, 10, deliver) and deliveries == 0)
reserveStatus = "uncertain"
assert(not orders.withPaidOrder(player, offer, 10, deliver) and deliveries == 0)
reserveStatus, claim = "reserved", false
assert(not orders.withPaidOrder(player, offer, 10, deliver) and deliveries == 0)
claim, finish = true, false
assert(not orders.withPaidOrder(player, offer, 10, deliver) and deliveries == 1)
reserveStatus = "pending"
assert(not orders.withPaidOrder(player, offer, 10, deliver) and deliveries == 1)
assert(messages[#messages]:find("9007199254740993", 1, true))
reserveStatus, finish = "reserved", true
calls = {}
assert(orders.withPaidOrder(player, offer, 10, deliver))
assert(table.concat(calls, ",") == "reserve,claim,deliver,finish,history")
calls = {}
assert(orders.withPaidOrder(player, offer, 0, deliver))
assert(table.concat(calls, ",") == "reserve,claim,deliver,finish")
calls = {}
assert(not orders.withPaidOrder(player, offer, 10, function() return false end))
assert(table.concat(calls, ",") == "reserve,claim")
local function deliverWithNotification()
	deliver()
	return function() calls[#calls + 1] = "notify" end
end
calls, finish = {}, false
assert(not orders.withPaidOrder(player, offer, 10, deliverWithNotification))
assert(table.concat(calls, ",") == "reserve,claim,deliver,finish")
calls, finish = {}, true
assert(orders.withPaidOrder(player, offer, 10, deliverWithNotification))
assert(table.concat(calls, ",") == "reserve,claim,deliver,finish,history,notify")
print("PASS: durable store orders do not deliver on failed funding/claim or repeat pending fulfillment")
