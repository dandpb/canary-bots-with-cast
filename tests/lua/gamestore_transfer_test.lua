-- Run from the repository root with Lua or LuaJIT.
local state
local player = {}

function player:getName()
	return "Sender"
end

function player:getAccountId()
	return 4
end

function player:getTransferableCoins()
	return 100
end

function player:transferTransferableCoins(accountId, amount)
	assert(accountId == 12 and amount == 8, "transfer must use the resolved account and requested amount")
	state.transfers = state.transfers + 1
	return state.success, state.reason
end

function player:updateUIExhausted()
	state.exhaustion = true
end

function Player(id)
	assert(id == 1)
	return player
end

local senders = {
	openStore = function()
		state.opened = true
	end,
	sendStoreError = function(_, _, message)
		state.error = message
	end,
	sendStorePurchaseSuccessful = function()
		state.notice = true
	end,
}
package.preload["gamestore.helpers"] = function()
	return {}
end
package.preload["gamestore.senders"] = function()
	return senders
end

function addPlayerEvent(callback, _, ...)
	callback(...)
end

db = {
	escapeString = function(value)
		assert(value == "receiver")
		return "'receiver'"
	end,
	storeQuery = function()
		return 7
	end,
	query = function()
		error("transfer must not update account balances through raw Lua SQL")
	end,
}

Result = {
	getNumber = function(id, key)
		assert(id == 7 and key == "account_id")
		return state.accountId
	end,
	free = function(id)
		assert(id == 7 and not state.freed)
		state.freed = true
	end,
}

GameStore = {
	StoreErrors = { STORE_ERROR_TRANSFER = 1 },
	HistoryTypes = { HISTORY_TYPE_NONE = 0 },
	CoinType = { Transferable = 1 },
	insertHistory = function(accountId, mode, _, amount, coinType)
		assert(mode == 0 and coinType == 1)
		state.history[accountId] = amount
	end,
}

local packet = {
	getString = function()
		return "Receiver"
	end,
	getU32 = function()
		return 8
	end,
}
local parser = dofile(arg[1] or "data/libs/gamestore/parsers.lua")

local function transfer(success, reason, recipientAccount)
	state = { success = success, reason = reason, accountId = recipientAccount or 12, transfers = 0, history = {} }
	parser.parseTransferableCoins(1, packet)
	assert(state.freed, "character-to-account lookup must release its result")
	assert(state.transfers == (state.accountId == 4 and 0 or 1))
	if success then
		assert(state.notice and state.opened and state.exhaustion and not state.error)
		assert(state.history[4] == -8 and state.history[12] == 8)
	else
		assert(state.error and not state.notice and not state.opened and not state.exhaustion)
		assert(next(state.history) == nil)
	end
end

transfer(false, "insufficient")
assert(state.error:find("don't have", 1, true))
transfer(false, "uncertain")
assert(state.error:find("before trying again", 1, true))
transfer(false)
transfer(false, nil, 4)
assert(state.error:find("same account", 1, true))
transfer(true)

print("GameStore transfer outcomes passed")
