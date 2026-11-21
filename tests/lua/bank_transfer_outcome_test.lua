-- Run from the repository root with Lua or LuaJIT.
local actions, messages, notifications, receipts = {}, {}, 0, 0
local success, pending = false, true
local sameOutcome = function() return success, pending end

Bank = { transfer = sameOutcome, transferToGuild = sameOutcome, hasBalance = function() return true end }
Player = setmetatable({}, { __call = function(_, target)
	if type(target) == "table" then return target end
	return { sendTextMessage = function() notifications = notifications + 1 end }
end })
TalkAction = function(name)
	local action = { separator = function() end, groupType = function() end, register = function() end }
	actions[name] = action
	return action
end
Game = {
	getNormalizedPlayerName = function(name) return name end,
	getNormalizedGuildName = function(name) return name end,
	createItem = function()
		receipts = receipts + 1
		return { setAttribute = function() end }
	end,
}
FormatNumber = tostring
MsgContains = function(message, word) return message:find(word, 1, true) ~= nil end
MsgFind = MsgContains
isValidMoney = function(amount) return amount > 0 end
getMoneyCount = tonumber
string.split = function(value) return { value:match("([^,]+),([^,]+)") } end
string.trim = function(value) return value:match("^%s*(.-)%s*$") end
string.titleCase = string.upper
logger = { info = function() end }
Npc = {}

local file = assert(io.open("data/libs/functions/player.lua"))
local source = file:read("*a")
file:close()
local transfer = assert(source:match("(function Player%.transferMoneyTo[^\n]*\n.-\nend)"))
assert((loadstring or load)(transfer))()
dofile("data/scripts/talkactions/player/bank.lua")
dofile("data/npclib/npc_system/bank_system.lua")

local guild = { getName = function() return "Sender Guild" end }
local player = setmetatable({
	getName = function() return "Sender" end,
	getGuild = function() return guild end,
	getInbox = function() return { addItemEx = function() end } end,
	sendTextMessage = function(_, _, message) messages[#messages + 1] = message end,
}, { __index = Player })

actions["!transfer"].onSay(player, "!transfer", "Receiver,10")
assert(messages[#messages]:find("before retrying", 1, true) and notifications == 0)
pending = false
actions["!transfer"].onSay(player, "!transfer", "Receiver,10")
assert(messages[#messages] == "The transfer could not be completed." and notifications == 0)
success = true
actions["!transfer"].onSay(player, "!transfer", "Receiver,10")
assert(messages[#messages]:find("You have transferred", 1, true) and notifications == 1)

local topic = 126
local handler = {
	getTopic = function() return topic end,
	setTopic = function(_, _, value) topic = value end,
	say = function(_, message) messages[#messages + 1] = message end,
}
local function guildTransfer()
	topic = 126
	Npc:parseGuildBank("10", nil, player, 1, handler)
	assert(topic == 127)
	Npc:parseGuildBank("Other Guild", nil, player, 1, handler)
	assert(topic == 128)
	Npc:parseGuildBank("yes", nil, player, 1, handler)
	assert(topic == 0)
end

success, pending = false, true
guildTransfer()
assert(messages[#messages]:find("Check your guild balance before retrying", 1, true) and receipts == 0)
pending = false
guildTransfer()
assert(receipts == 1)
success = true
guildTransfer()
assert(receipts == 2)

print("PASS: player and guild bank commands distinguish a pending transfer from a confirmed result")
