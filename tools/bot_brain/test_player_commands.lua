-- Exercise registration and real /cavebot public command routing.
local action, calls, replies = nil, {}, {}
MESSAGE_STATUS = 1
TalkAction = function()
	action = { separator = function() end, register = function() end,
		groupType = function(self, group) self.group = group end }
	return action
end
Game = { botCommand = function(name, command)
	calls[#calls + 1] = { name, command }
	return "accepted fixture command"
end }
local player = {
	getId = function() return 321 end,
	getGroup = function() return { getAccess = function() return false end } end,
	sendTextMessage = function(_, kind, text)
		assert(kind == MESSAGE_STATUS and type(text) == "string")
		replies[#replies + 1] = text
	end,
}
dofile(arg[1] or "data/scripts/talkactions/god/bot_cavebot.lua")
assert(action.group == "normal", "ordinary players must reach the guarded public commands")
for _, case in ipairs({
	{ "party ek,ed", "*", "party create 321 ek,ed" },
	{ "party leave", "*", "party leave 321" },
	{ "claim", "_global", "claimspawn 321" },
	{ "release", "_global", "releasespawn 321" },
}) do
	assert(action.onSay(player, "/cavebot", case[1]))
	assert(calls[#calls][1] == case[2] and calls[#calls][2] == case[3])
end
local allowed = #calls
for _, command in ipairs({ "", "reload", "partyinfo", "status", "Tarshaw Steelheart teleport 1,2,3", "_global brain disable" }) do
	assert(action.onSay(player, "/cavebot", command))
	assert(#calls == allowed, "ordinary player reached administrative command: " .. command)
	assert(replies[#replies] == "You need God access to use /cavebot.")
end
print("PASS: ordinary party/spawn commands work while administrative commands remain denied")
