-- Disposable in-game fixtures only: ordinary native bots on nearby safe,
-- walkable tiles outside protection zones. Call the returned check after a tick.
return function(bot, member)
	assert(bot and not bot:getParty(), "requires a solo native bot fixture")
	local pos = bot:getPosition()
	assert(not Tile(pos):hasFlag(TILESTATE_PROTECTIONZONE), "fixture is in a protection zone")
	local before = bot:getExperience()
	local memberBefore, party
	if member then
		assert(not member:getParty(), "party fixture must start solo")
		memberBefore = member:getExperience()
		party = assert(Party(bot), "party creation failed")
		party:addInvite(member)
		assert(party:addMember(member), "party join failed")
		assert(party:setSharedExperience(true), "shared XP activation failed")
	end
	-- Never force a creature onto a wall: combat would correctly reject the hit.
	local monster = Game.createMonster("Wolf", Position(pos.x + 1, pos.y, pos.z), true, false)
	if not monster then
		if party then party:disband() end
		error("no walkable monster spawn beside the fixture")
	end
	if member then
		-- Both actors participate before checking the ordinary shared-XP rules.
		doTargetCombatHealth(bot, monster, COMBAT_PHYSICALDAMAGE, -2, -2, CONST_ME_NONE)
		doTargetCombatHealth(member, monster, COMBAT_PHYSICALDAMAGE, -2, -2, CONST_ME_NONE)
		if not party:isSharedExperienceEnabled() then
			monster:remove()
			party:disband()
			error("fixtures are not eligible for shared XP after participating")
		end
	end
	doTargetCombatHealth(bot, monster, COMBAT_PHYSICALDAMAGE, -500, -500, CONST_ME_NONE)
	if monster:getHealth() > 0 then
		monster:remove()
		if party then party:disband() end
		error("fixture attack was blocked; no monster kill occurred")
	end
	return function()
		local after = bot:getExperience()
		local memberAfter = member and member:getExperience()
		if party then party:disband() end
		assert(after > before, "monster kill did not award native bot XP")
		if member then
			assert(memberAfter > memberBefore, "eligible native party member did not receive shared XP")
		end
		return { before = before, after = after, memberBefore = memberBefore, memberAfter = memberAfter }
	end
end
