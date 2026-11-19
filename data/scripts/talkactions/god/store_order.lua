local storeOrder = TalkAction("/storeorder")

function storeOrder.onSay(player, words, param)
	if not player:getGroup():getAccess() then return false end
	local id = param:match("^%s*(%d+)%s*$")
	local action
	if not id then
		id, action = param:match("^%s*(%d+)%s+(%a+)%s+verified%s*$")
	end
	if not id or (action and action ~= "complete" and action ~= "refund") then
		player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Use /storeorder <id> or /storeorder <id> complete|refund verified.")
		return false
	end
	local order = db.getStoreOrder(id)
	if not order then
		player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "The order could not be read.")
		return false
	end
	if not action then
		player:sendTextMessage(MESSAGE_EVENT_ADVANCE, string.format("Order %s is %s. Character %d, account %d, offer %d, amount %d (%s). %s",
			order.id, order.state, order.playerGuid, order.accountId, order.offerId, order.amount,
			order.transferable and "transferable coins" or "coins", order.detail))
		return false
	end
	local status = db.resolveStoreOrder(id, action)
	player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Store order " .. id .. ": " .. status .. ".")
	logger.info("[GameStore] {} reconciled order {} with action {} and result {}", player:getName(), id, action, status)
	return false
end

storeOrder:separator(" ")
storeOrder:groupType("god")
storeOrder:register()
