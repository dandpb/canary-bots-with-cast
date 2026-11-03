-- Orders use the caller's real creature id; text cannot become an operator command.
local talk = TalkAction("/brain")

function talk.onSay(player, words, param)
	if param == "" then
		player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "Use /brain <mensagem> ou envie uma mensagem privada ao bot. O lider da party define os objetivos.")
		return true
	end
	local reply = Game.botCommand("_global", "brain chat " .. player:getId() .. " " .. param)
	player:sendTextMessage(MESSAGE_EVENT_ADVANCE, reply or "Companheiro indisponivel.")
	return true
end

talk:separator(" ")
talk:groupType("normal")
talk:register()
