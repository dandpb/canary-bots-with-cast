local senders = require("gamestore.senders")
local purchases = {}

local sendStorePurchaseSuccessful = senders.sendStorePurchaseSuccessful
local sendRequestPurchaseData = senders.sendRequestPurchaseData
local sendUpdatedStoreBalances = senders.sendUpdatedStoreBalances
local sendStoreError = senders.sendStoreError

local function countIsValid(count)
	return type(count) == "number" and count > 0 and count <= 0xFFFF and count % 1 == 0
end

local function canReceiveItems(player, itemId, count)
	local itemType = ItemType(itemId)
	if not itemType or itemType:getId() == 0 or not countIsValid(count) or (itemType:isStackable() and itemType:getStackSize() <= 0) then
		return false, "This item offer is unavailable."
	end
	return player:canReceiveStoreItems(itemId, count)
end

local function isCaskItem(itemId)
	return (itemId >= ITEM_HEALTH_CASK_START and itemId <= ITEM_HEALTH_CASK_END) or (itemId >= ITEM_MANA_CASK_START and itemId <= ITEM_MANA_CASK_END) or (itemId >= ITEM_SPIRIT_CASK_START and itemId <= ITEM_SPIRIT_CASK_END)
end

local function getHouseOfferItems(offer)
	return type(offer.itemtype) == "table" and offer.itemtype or { offer.itemtype }
end

local function templeTeleportAllowed(player)
	return player:getTile():hasFlag(TILESTATE_PROTECTIONZONE) or not (player:isPzLocked() or player:getCondition(CONDITION_INFIGHT, CONDITIONID_DEFAULT))
end

local function preflightPurchase(player, offer)
	local types = GameStore.OfferTypes
	local kind = offer.type
	if kind == types.OFFER_TYPE_ITEM or kind == types.OFFER_TYPE_ITEM_UNIQUE then
		return canReceiveItems(player, offer.itemtype, offer.count or 1)
	elseif kind == types.OFFER_TYPE_CHARGES then
		local itemType = ItemType(offer.itemtype)
		if not itemType or itemType:getCharges() <= 0 or not countIsValid(offer.charges) then
			return false, "This charged item offer is unavailable."
		end
		return canReceiveItems(player, offer.itemtype, 1)
	elseif kind == types.OFFER_TYPE_STACKABLE then
		local itemType = ItemType(offer.itemtype)
		if not itemType or not itemType:isStackable() or itemType:getStackSize() <= 0 then
			return false, "This stackable item offer is unavailable."
		end
		return canReceiveItems(player, offer.itemtype, offer.count)
	elseif kind == types.OFFER_TYPE_HOUSE or kind == types.OFFER_TYPE_ITEM_BED then
		if not countIsValid(offer.count) then
			return false, "This house offer is unavailable."
		end
		local kitCount = 0
		for _, itemId in ipairs(getHouseOfferItems(offer)) do
			local itemType = ItemType(itemId)
			if not itemType or itemType:getId() == 0 then
				return false, "This house offer is unavailable."
			end
			kitCount = kitCount + (isCaskItem(itemId) and 1 or offer.count)
		end
		return canReceiveItems(player, ITEM_DECORATION_KIT, kitCount)
	elseif kind == types.OFFER_TYPE_BLESSINGS then
		if not countIsValid(offer.blessid) or offer.blessid > 10 or not countIsValid(offer.count) or player:getBlessingCount(offer.blessid) + offer.count > 5 then
			return false, "You cannot receive the full blessing amount in this offer."
		end
	elseif kind == types.OFFER_TYPE_INSTANT_REWARD_ACCESS and player:getCollectionTokens() + offer.count > GameStore.ItemLimit.INSTANT_REWARD_ACCESS then
		return false, "You cannot own more than " .. GameStore.ItemLimit.INSTANT_REWARD_ACCESS .. " reward tokens."
	elseif kind == types.OFFER_TYPE_PREYBONUS and player:getPreyCards() + offer.count > GameStore.ItemLimit.PREY_WILDCARD then
		return false, "You cannot own more than " .. GameStore.ItemLimit.PREY_WILDCARD .. " prey wildcards."
	elseif kind == types.OFFER_TYPE_TEMPLE and not templeTeleportAllowed(player) then
		return false, "You can't use temple teleport in fight!"
	elseif kind == types.OFFER_TYPE_HIRELING_SKILL or kind == types.OFFER_TYPE_HIRELING_OUTFIT then
		if player:getClient().version < 1200 then
			return false, "This offer requires client 12 or later."
		end
	elseif (kind == types.OFFER_TYPE_PREYSLOT and player:preyThirdSlot() == nil) or (kind == types.OFFER_TYPE_HUNTINGSLOT and player:taskHuntingThirdSlot() == nil) then
		return false, "This slot is unavailable."
	elseif kind == types.OFFER_TYPE_PREMIUM then
		local days = offer.id - 3000
		if not countIsValid(days) or player:getPremiumDays() + days > 0xFFFE or math.max(os.time(), player:getVipTime()) + days * 86400 > 0xFFFFFFFF then
			return false, "Your account cannot receive the full premium time in this offer."
		end
	end
	return true
end

local function processItemPurchase(player, offerId, offerCount, movable, setOwner)
	if ItemType(offerId):isStackable() then
		return player:addItemStoreInbox(offerId, offerCount, movable, setOwner) ~= nil
	end
	for _ = 1, offerCount do
		if not player:addItemStoreInbox(offerId, 1, movable, setOwner) then
			return false
		end
	end
	return true
end

local function processChargesPurchase(player, offerId, name, charges, movable, setOwner)
	return player:addItemStoreInbox(offerId, charges, movable, setOwner) ~= nil
end

local function processSingleBlessingPurchase(player, blessId, count)
	return player:addBlessing(blessId, count) == true
end

local function processAllBlessingsPurchase(player, count)
	local twistOfFateCount = player:getBlessingCount(1)
	local twistOfFateToAdd = twistOfFateCount == 0 and count or 5 - twistOfFateCount
	if twistOfFateToAdd > 0 and not processSingleBlessingPurchase(player, 1, twistOfFateToAdd) then
		return false
	end

	for i = 2, 8 do
		local currentCount = player:getBlessingCount(i)
		if currentCount < 5 and not processSingleBlessingPurchase(player, i, math.min(count, 5 - currentCount)) then
			return false
		end
	end
end

local function processInstantRewardAccess(player, offerCount)
	local expected = player:getCollectionTokens() + offerCount
	player:setCollectionTokens(expected)
	return player:getCollectionTokens() == expected
end

local function processCharmsPurchase(player)
	return player:charmExpansion(true) == true
end

local function processPremiumPurchase(player, offerId)
	local days = offerId - 3000
	if player:addPremiumDays(days, true) ~= true then
		return false
	end
	if configManager.getBoolean(configKeys.VIP_SYSTEM_ENABLED) then
		player:onAddVip(days, true)
		return function()
			player:sendTextMessage(MESSAGE_EVENT_ADVANCE, string.format("You have been granted %s days of VIP status.", days))
		end
	end
end

local function processStackablePurchase(player, offerId, offerCount, offerName, movable, setOwner)
	local inbox = player:getStoreInbox()
	local stackSize = ItemType(offerId):getStackSize()
	if not inbox or stackSize <= 0 then
		return false
	end
	local remainingCount = offerCount
	while remainingCount > 0 do
		local countToAdd = math.min(remainingCount, stackSize)
		local item = Game.createItem(offerId, countToAdd)
		if not item or (not movable and not item:setAttribute(ITEM_ATTRIBUTE_STORE, systemTime())) or inbox:addItemEx(item) ~= RETURNVALUE_NOERROR then
			return false
		end
		remainingCount = remainingCount - countToAdd
	end
	return true
end

local function processHouseRelatedPurchase(player, offer)
	local inbox = player:getStoreInbox()
	if not inbox then
		return false
	end
	for _, itemId in ipairs(getHouseOfferItems(offer)) do
		local cask = isCaskItem(itemId)
		local description = "You bought this item in the Store.\nUnwrap it in your own house to create a <" .. ItemType(itemId):getName() .. ">."
		for _ = 1, cask and 1 or offer.count do
			local decoKit = Game.createItem(ITEM_DECORATION_KIT, 1)
			if
				not decoKit
				or not decoKit:setAttribute(ITEM_ATTRIBUTE_DESCRIPTION, description)
				or not decoKit:setCustomAttribute("unWrapId", itemId)
				or (cask and not decoKit:setAttribute(ITEM_ATTRIBUTE_DATE, offer.count))
				or (not offer.movable and not decoKit:setAttribute(ITEM_ATTRIBUTE_STORE, systemTime()))
				or inbox:addItemEx(decoKit) ~= RETURNVALUE_NOERROR
			then
				return false
			end
		end
	end
	player:sendUpdateContainer(inbox)
	return true
end

local function processOutfitPurchase(player, offerSexIdTable, addon)
	local looktype, opposite
	local _addon = addon and addon or 0

	if player:getSex() == PLAYERSEX_MALE then
		looktype, opposite = offerSexIdTable.male, offerSexIdTable.female
	elseif player:getSex() == PLAYERSEX_FEMALE then
		looktype, opposite = offerSexIdTable.female, offerSexIdTable.male
	end

	if not looktype then
		return error({ code = 0, message = "This outfit seems not to suit your sex, we are sorry for that!" })
	elseif (not player:hasOutfit(looktype, 0)) and (_addon == 1 or _addon == 2) then
		return error({ code = 0, message = "You must own the outfit before you can buy its addon." })
	elseif player:hasOutfit(looktype, _addon) then
		return error({ code = 0, message = "You already own this outfit." })
	end
	if not player:addOutfitAddon(looktype, _addon) or not player:hasOutfit(looktype, _addon) then
		return false
	end
	return not opposite or player:addOutfitAddon(opposite, _addon) == true
end

local function processMountPurchase(player, offerId)
	if player:hasMount(offerId) then
		return error({ code = 0, message = "You already own this mount." })
	end

	return player:addMount(offerId) == true
end

local function processNameChangePurchase(player, offer, productType, newName)
	if productType == GameStore.ClientOfferTypes.CLIENT_STORE_OFFER_NAMECHANGE then
		local tile = Tile(player:getPosition())
		if tile then
			if not tile:hasFlag(TILESTATE_PROTECTIONZONE) then
				return error({ code = 1, message = "You can change name only in Protection Zone." })
			end
		end

		newName = newName:lower():trim():gsub("(%l)(%w*)", function(a, b)
			return string.upper(a) .. b
		end)

		local normalizedName = Game.getNormalizedPlayerName(newName, true)
		if normalizedName then
			return error({ code = 1, message = "This name is already used, please try again!" })
		end

		local result = GameStore.canChangeToName(newName)
		if not result.ability then
			return error({ code = 1, message = result.reason })
		end

		local namelockReason = player:kv():get("namelock")
		local price = namelockReason and 0 or offer.price
		local detail = player:getName() .. " to " .. newName
		if not GameStore.withPaidOrder(player, offer, price, function()
			return player:changeName(newName, true) == true
		end, detail) then
			return false
		end

		local message = namelockReason and "Your character has been renamed successfully." or string.format("You have purchased %s for %d coins.", offer.name, price)
		sendStorePurchaseSuccessful(player:getId(), message)
		player:remove()
	else
		return addPlayerEvent(sendRequestPurchaseData, 250, player:getId(), offer.id, GameStore.ClientOfferTypes.CLIENT_STORE_OFFER_NAMECHANGE)
	end
end

local function processSexChangePurchase(player)
	local oldSex = player:getSex()
	player:toggleSex()
	return player:getSex() ~= oldSex
end

local function processExpBoostPurchase(player)
	local currentXpBoostTime = player:getXpBoostTime()
	return player:setXpBoostPercent(50) == true and player:setXpBoostTime(currentXpBoostTime + 3600) == true
end

local function processPreyThirdSlot(player)
	if player:preyThirdSlot() then
		return error({ code = 1, message = "You already have unlocked all prey slots." })
	end
	return player:preyThirdSlot(true) == true
end

local function processTaskHuntingThirdSlot(player)
	if player:taskHuntingThirdSlot() then
		return error({ code = 1, message = "You already have unlocked all task hunting slots." })
	end
	return player:taskHuntingThirdSlot(true) == true
end

local function processPreyBonusReroll(player, offerCount)
	return player:addPreyCards(offerCount) == true
end

local function processTempleTeleportPurchase(player)
	if not templeTeleportAllowed(player) then
		return error({ code = 0, message = "You can't use temple teleport in fight!" })
	end

	if not player:teleportTo(player:getTown():getTemplePosition()) then
		return false
	end
	return function()
		player:getPosition():sendMagicEffect(CONST_ME_TELEPORT)
		player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "You have been teleported to your hometown.")
	end
end

local function processHirelingPurchase(player, offer, productType, hirelingName, chosenSex)
	if player:getClient().version < 1200 then
		return error({ code = 1, message = "You cannot buy hirelings on client 10, please relog on client 12 and try again." })
	end
	if player:getHirelingsCount() >= GameStore.ItemLimit.HIRELING then
		return error({ code = 1, message = "You cannot have more than " .. GameStore.ItemLimit.HIRELING .. " hirelings." })
	end

	if productType == GameStore.ClientOfferTypes.CLIENT_STORE_OFFER_HIRELING then
		local result = GameStore.canUseHirelingName(hirelingName)
		if not result.ability then
			return error({ code = 1, message = result.reason })
		end

		hirelingName = hirelingName:lower():gsub("(%l)(%w*)", function(a, b)
			return string.upper(a) .. b
		end)

		local canReceive, errorMsg = player:canReceiveStoreItems(HIRELING_LAMP, 1)
		if not canReceive then
			return error({ code = 1, message = errorMsg })
		end

		local sex = chosenSex == HIRELING_SEX.FEMALE and "female" or "male"
		if not GameStore.withPaidOrder(player, offer, offer.price, function()
			if not player:addNewHireling(hirelingName, chosenSex) then
				return false
			end
			player:createTransactionSummary(offer.type, 1)
		end, hirelingName .. ", " .. sex) then
			return false
		end
		local message = "You have successfully bought " .. hirelingName
		sendUpdatedStoreBalances(player:getId())
		return addPlayerEvent(sendStorePurchaseSuccessful, 650, player:getId(), message)
		-- If not, we ask him to do!
	else
		-- TODO: Use the correct dialog (byte 0xDB) on client 1205+
		-- for compatibility, request name using the change name dialog
		return addPlayerEvent(sendRequestPurchaseData, 250, player:getId(), offer.id, GameStore.ClientOfferTypes.CLIENT_STORE_OFFER_HIRELING)
	end
end

-- Hireling Helpers
local function HandleHirelingNameChange(playerId, offer, newHirelingName)
	local player = Player(playerId)
	if not player then
		return
	end

	local functionCallback = function(playerIdInFunction, data, hireling)
		local playerInFunction = Player(playerIdInFunction)
		if not playerInFunction then
			return
		end

		if not hireling then
			return playerInFunction:showInfoModal("Error", "You must select a hireling.")
		end

		if hireling.active > 0 then
			return playerInFunction:showInfoModal("Error", "Your hireling must be inside his/her lamp.")
		end

		local oldName = hireling.name
		local detail = string.format("Hireling %d: %s to %s", hireling:getId(), oldName, data.newHirelingName)
		if not GameStore.withPaidOrder(playerInFunction, data.offer, data.offer.price, function()
			hireling.name = data.newHirelingName
			if not hireling:save() then
				return false
			end
			local lamp = playerInFunction:findHirelingLamp(hireling:getId())
			if lamp then
				return lamp:setAttribute(ITEM_ATTRIBUTE_DESCRIPTION, "This mysterious lamp summons your very own personal hireling.\nThis item cannot be traded.\nThis magic lamp is the home of " .. hireling:getName() .. ".") == true
			end
		end, detail) then
			return false
		end

		sendUpdatedStoreBalances(playerIdInFunction)
		sendStorePurchaseSuccessful(playerIdInFunction, oldName .. " has been renamed to " .. hireling.name .. ".")
	end

	player:sendHirelingSelectionModal("Choose a Hireling", "Select a hireling below", functionCallback, { offer = offer, newHirelingName = newHirelingName })
end

local function processHirelingChangeNamePurchase(player, offer, productType, newHirelingName)
	if player:getClient().version < 1200 then
		return error({
			code = 1,
			message = "You cannot buy hireling change name on client 10, please relog on client 12 and try again.",
		})
	end

	if productType == GameStore.ClientOfferTypes.CLIENT_STORE_OFFER_NAMECHANGE then
		local result = GameStore.canUseHirelingName(newHirelingName)
		if not result.ability then
			return error({ code = 1, message = result.reason })
		end

		newHirelingName = newHirelingName:lower():gsub("(%l)(%w*)", function(a, b)
			return string.upper(a) .. b
		end)

		local message = "Close the store window to select which hireling should be renamed to " .. newHirelingName
		local playerId = player:getId()
		addPlayerEvent(sendStoreError, 200, playerId, GameStore.StoreErrors.STORE_ERROR_INFORMATION, message)
		addPlayerEvent(HandleHirelingNameChange, 550, playerId, offer, newHirelingName)
	else
		return addPlayerEvent(sendRequestPurchaseData, 250, player:getId(), offer.id, GameStore.ClientOfferTypes.CLIENT_STORE_OFFER_NAMECHANGE)
	end
end

local function HandleHirelingSexChange(playerId, offer)
	local player = Player(playerId)
	if not player then
		return
	end

	local functionCallback = function(playerIdInFunction, data, hireling)
		local playerInFunction = Player(playerIdInFunction)
		if not playerInFunction then
			return
		end

		if not hireling then
			return playerInFunction:showInfoModal("Error", "You must select a hireling.")
		end

		if hireling.active > 0 then
			return playerInFunction:showInfoModal("Error", "Your hireling must be inside his/her lamp.")
		end

		local changeTo, sexString, lookType
		if hireling.sex == HIRELING_SEX.FEMALE then
			changeTo = HIRELING_SEX.MALE
			sexString = "male"
			lookType = HIRELING_OUTFIT_DEFAULT.male
		else
			changeTo = HIRELING_SEX.FEMALE
			sexString = "female"
			lookType = HIRELING_OUTFIT_DEFAULT.female
		end

		local detail = string.format("Hireling %d: %s to %s", hireling:getId(), hireling:getName(), sexString)
		if not GameStore.withPaidOrder(playerInFunction, data.offer, data.offer.price, function()
			hireling.sex = changeTo
			hireling.looktype = lookType
			return hireling:save() == true
		end, detail) then
			return false
		end

		sendUpdatedStoreBalances(playerIdInFunction)
		sendStorePurchaseSuccessful(playerIdInFunction, hireling:getName() .. " is now " .. sexString .. ".")
	end

	player:sendHirelingSelectionModal("Choose a Hireling", "Select a hireling below", functionCallback, { offer = offer })
end

local function processHirelingChangeSexPurchase(player, offer)
	if player:getClient().version < 1200 then
		return error({
			code = 1,
			message = "You cannot buy hireling change sex on client 10, please relog on client 12 and try again.",
		})
	end

	local message = "Close the store window to select which hireling should have the sex changed."
	local playerId = player:getId()
	addPlayerEvent(sendStoreError, 200, playerId, GameStore.StoreErrors.STORE_ERROR_INFORMATION, message)
	addPlayerEvent(HandleHirelingSexChange, 550, playerId, offer)
end

local function processHirelingSkillPurchase(player, offer)
	if player:getClient().version < 1200 then
		return error({
			code = 1,
			message = "You cannot buy hireling skill on client 10, please relog on client 12 and try again.",
		})
	end

	local skill = GetHirelingSkillNameById(offer.id)
	if not skill then
		return false
	end
	player:enableHirelingSkill(skill)
	if not player:hasHirelingSkill(skill) then
		return false
	end
	return function()
		player:getPosition():sendMagicEffect(CONST_ME_MAGIC_BLUE)
		player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "A new hireling skill has been added to all your hirelings")
	end
end

local function processHirelingOutfitPurchase(player, offer)
	if player:getClient().version < 1200 then
		return error({
			code = 1,
			message = "You cannot buy hireling outfit on client 10, please relog on client 12 and try again.",
		})
	end

	local outfitName = GetHirelingOutfitNameById(offer.id)
	if not outfitName then
		return false
	end
	logger.debug("Processing hireling outfit purchase name {}", outfitName)
	player:enableHirelingOutfit(outfitName)
	if not player:hasHirelingOutfit(outfitName) then
		return false
	end
	return function()
		player:getPosition():sendMagicEffect(CONST_ME_MAGIC_GREEN)
		player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "A new hireling outfit has been added to all your hirelings")
	end
end

purchases.preflightPurchase = preflightPurchase
purchases.processItemPurchase = processItemPurchase
purchases.processChargesPurchase = processChargesPurchase
purchases.processSingleBlessingPurchase = processSingleBlessingPurchase
purchases.processAllBlessingsPurchase = processAllBlessingsPurchase
purchases.processInstantRewardAccess = processInstantRewardAccess
purchases.processCharmsPurchase = processCharmsPurchase
purchases.processPremiumPurchase = processPremiumPurchase
purchases.processStackablePurchase = processStackablePurchase
purchases.processHouseRelatedPurchase = processHouseRelatedPurchase
purchases.processOutfitPurchase = processOutfitPurchase
purchases.processMountPurchase = processMountPurchase
purchases.processNameChangePurchase = processNameChangePurchase
purchases.processSexChangePurchase = processSexChangePurchase
purchases.processExpBoostPurchase = processExpBoostPurchase
purchases.processPreyThirdSlot = processPreyThirdSlot
purchases.processTaskHuntingThirdSlot = processTaskHuntingThirdSlot
purchases.processPreyBonusReroll = processPreyBonusReroll
purchases.processTempleTeleportPurchase = processTempleTeleportPurchase
purchases.processHirelingPurchase = processHirelingPurchase
purchases.processHirelingChangeNamePurchase = processHirelingChangeNamePurchase
purchases.processHirelingChangeSexPurchase = processHirelingChangeSexPurchase
purchases.processHirelingSkillPurchase = processHirelingSkillPurchase
purchases.processHirelingOutfitPurchase = processHirelingOutfitPurchase

return purchases
