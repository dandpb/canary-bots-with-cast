local storeCoin = Action()

function storeCoin.onUse(player, item, fromPosition, target, toPosition, isHotkey)
	local count = player:redeemStoreCoin(item)
	if count == nil then
		player:sendCancelMessage("Your Store Coins could not be redeemed. Check that the token is in your own inventory or depot, and check your balance before trying again.")
		return true
	end

	if count == 0 then return true end

	local message = "You have added " .. count .. " tibia coins to your balance."
	local balance = player:getTransferableCoins()
	if balance ~= nil then
		message = message .. " Your total is now " .. balance .. "."
	end
	player:sendTextMessage(MESSAGE_EVENT_ADVANCE, message)
	player:getPosition():sendMagicEffect(CONST_ME_MAGIC_GREEN)

	logger.warn("[StoreCoinScript - ITEM_STORE_COIN] The player {} used the item to store Tibia Coins.", player:getName())
	return true
end

storeCoin:id(ITEM_STORE_COIN)
storeCoin:register()
