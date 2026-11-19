local orders = {}

local function storeError(player, message)
	sendStoreError(player:getId(), GameStore.StoreErrors.STORE_ERROR_PURCHASE, message)
end

local function pending(player, id)
	local label = id and ("Order " .. id) or "Your purchase"
	storeError(player, label .. " is pending reconciliation. Check the result before trying again.")
	return false
end

function orders.withPaidOrder(player, offer, price, deliver, detail, wireOfferId)
	local offerId = wireOfferId or offer.id
	local coinType = offer.coinType
	if type(price) ~= "number" or price < 0 or price % 1 ~= 0 or type(offerId) ~= "number"
		or (coinType ~= GameStore.CoinType.Coin and coinType ~= GameStore.CoinType.Transferable) then
		storeError(player, "This purchase is unavailable.")
		return false
	end

	detail = detail or offer.name
	local guid, account = player:getGuid(), player:getAccountId()
	local id, status = db.reserveStoreOrder(guid, account, offerId, coinType == GameStore.CoinType.Transferable, price, detail)
	if status == "pending" or status == "uncertain" then return pending(player, id) end
	if status ~= "reserved" or not id then
		storeError(player, "The order could not be started. No delivery was attempted.")
		return false
	end
	-- Claim the order durably before invoking any fulfillment handler.
	if not db.claimStoreOrder(id, guid) then return pending(player, id) end
	local ok, result = pcall(deliver)
	if not ok or result == false then
		logger.warn("[GameStore] Delivery of order {} needs reconciliation", id)
		return pending(player, id)
	end
	if not db.finishStoreOrder(id, guid) then return pending(player, id) end

	if price > 0 then
		local published = pcall(GameStore.insertHistory, account, GameStore.HistoryTypes.HISTORY_TYPE_NONE, detail, -price, coinType)
		if not published then logger.warn("[GameStore] Could not publish history for completed order {}", id) end
	end
	if type(result) == "function" and not pcall(result) then
		logger.warn("[GameStore] Could not notify the player about completed order {}", id)
	end
	return true
end

return orders
