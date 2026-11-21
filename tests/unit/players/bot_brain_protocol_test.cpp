#include <gtest/gtest.h>
#include "creatures/players/bot/bot_brain_protocol.hpp"

TEST(BotBrainProtocol, RejectsAnActionAfterFloorOrPartyAuthorityChanges) {
	using nlohmann::json;
	json offered = { { "world", "a" }, { "lease", "l" }, { "objective_generation", 2 }, { "sequence", 10 }, { "captured_ms", 1000 }, { "bot", { { "id", 7 }, { "position", { 100, 100, 7 } }, { "alive", true } } }, { "party", { { "leader_id", 9 } } }, { "actions", { { { "id", "follow" }, { "action", "follow" }, { "ttl_ms", 500 } } } } };
	json intent = { { "version", 1 }, { "type", "intent" }, { "world", "a" }, { "lease", "l" }, { "action_id", "one" }, { "bot_id", 7 }, { "objective_generation", 2 }, { "observation_sequence", 10 }, { "candidate_id", "follow" }, { "expires_ms", 1500 } };
	EXPECT_EQ(botbrain::validate(intent, offered, offered, 1100), "");
	auto changed = offered;
	changed["bot"]["position"][2] = 8;
	EXPECT_EQ(botbrain::validate(intent, offered, changed, 1100), "floor_changed");
	changed = offered;
	changed["party"]["leader_id"] = 10;
	EXPECT_EQ(botbrain::validate(intent, offered, changed, 1100), "authority_changed");
	EXPECT_EQ(botbrain::validate(intent, offered, offered, 1501), "expired");
	changed = offered;
	changed["world"] = "new-engine";
	EXPECT_EQ(botbrain::validate(intent, offered, changed, 1100), "obsolete_generation");
	changed = offered;
	changed["actions"] = json::array();
	EXPECT_EQ(botbrain::validate(intent, offered, changed, 1100), "candidate_no_longer_eligible");
	changed = intent;
	changed["expires_ms"] = 1501;
	EXPECT_EQ(botbrain::validate(changed, offered, offered, 1100), "extended_deadline");
	changed = intent;
	changed["admin_command"] = "teleport";
	EXPECT_EQ(botbrain::validate(changed, offered, offered, 1100), "invalid_contract");
	changed = offered;
	changed["party"] = nullptr;
	EXPECT_EQ(botbrain::validate(intent, offered, changed, 1100), "invalid_contract");
}

TEST(BotBrainProtocol, AutonomousActionsNeedNoPartyButCannotCrossAuthorityChanges) {
	using nlohmann::json;
	json offered = { { "world", "a" }, { "lease", "l" }, { "objective_generation", 2 }, { "sequence", 10 }, { "captured_ms", 1000 }, { "autonomous", true }, { "bot", { { "id", 7 }, { "position", { 100, 100, 7 } }, { "alive", true } } }, { "party", nullptr }, { "actions", { { { "id", "resupply" }, { "action", "resupply" }, { "ttl_ms", 500 } } } } };
	json intent = { { "version", 1 }, { "type", "intent" }, { "world", "a" }, { "lease", "l" }, { "action_id", "solo" }, { "bot_id", 7 }, { "objective_generation", 2 }, { "observation_sequence", 10 }, { "candidate_id", "resupply" }, { "expires_ms", 1500 } };
	EXPECT_EQ(botbrain::validate(intent, offered, offered, 1100), "");
	auto ordinary = offered;
	ordinary["autonomous"] = false;
	EXPECT_NE(botbrain::validate(intent, ordinary, ordinary, 1100), "");
	auto grouped = offered;
	grouped["party"] = { { "leader_id", 9 } };
	EXPECT_NE(botbrain::validate(intent, offered, grouped, 1100), "");
}

TEST(BotBrainProtocol, PrudentHuntRequiresHealthyOnlineMembersOnTheSameFloor) {
	using nlohmann::json;
	json members = { { { "id", 9 }, { "health", 100 }, { "online", true }, { "position", { 100, 101, 7 } } } };
	EXPECT_TRUE(botbrain::partyReady(members, { 100, 100, 7 }));
	members[0]["health"] = 7; // observed 20/260 HP human leader
	EXPECT_FALSE(botbrain::partyReady(members, { 100, 100, 7 }));
	members[0]["health"] = 100;
	members[0]["position"][2] = 8;
	EXPECT_FALSE(botbrain::partyReady(members, { 100, 100, 7 }));
	members[0]["position"] = { 110, 100, 7 };
	EXPECT_FALSE(botbrain::partyReady(members, { 100, 100, 7 }));
	members[0]["position"] = { 100, 101, 7 };
	members[0]["online"] = false;
	EXPECT_FALSE(botbrain::partyReady(members, { 100, 100, 7 }));
}

TEST(BotBrainProtocol, SelectRetreatRoutePrefersLastHuntAndRejectsNonTownLoops) {
	const botbrain::RetreatWaypoint pos { 32704, 32282, 7 };
	const botbrain::RetreatWaypoint home { 32958, 32077, 7 }; // Venore temple

	botbrain::RetreatRouteCandidate nonTownLoop {
		1258,
		false,
		"hunt",
		{ { 32770, 32342, 7 }, { 32709, 32279, 7 }, { 32770, 32342, 7 } }
	};
	botbrain::RetreatRouteCandidate scriptSeven {
		7,
		false,
		"hunt",
		{ { 32615, 32426, 9 }, { 32693, 32281, 7 }, { 33014, 32053, 6 } }
	};
	botbrain::RetreatRouteCandidate closerValid {
		401,
		false,
		"hunt",
		{ { 32700, 32280, 7 }, { 32960, 32080, 7 } }
	};

	// Non-town loop (1258) is closer to pos (dist 5 vs 11), so it must be rejected in favor of script 7.
	const auto withoutPreferred = botbrain::selectRetreatRoute(pos, home, 0, { nonTownLoop, scriptSeven });
	ASSERT_TRUE(withoutPreferred.has_value());
	EXPECT_EQ(withoutPreferred->scriptId, 7U);
	EXPECT_EQ(withoutPreferred->waypointIndex, 1U);

	// Preferred lastHuntScript (7) wins over closerValid (401) when both end near home.
	const auto withPreferred = botbrain::selectRetreatRoute(pos, home, 7, { nonTownLoop, closerValid, scriptSeven });
	ASSERT_TRUE(withPreferred.has_value());
	EXPECT_EQ(withPreferred->scriptId, 7U);
	EXPECT_EQ(withPreferred->waypointIndex, 1U);

	// Returns nullopt when no waypoint on pos.z is within maxAttachDist (60 tiles).
	botbrain::RetreatRouteCandidate farOrWrongFloor {
		99,
		false,
		"hunt",
		{ { 32704, 32282, 8 }, { 32800, 32282, 7 }, { 32960, 32080, 7 } }
	};
	EXPECT_FALSE(botbrain::selectRetreatRoute(pos, home, 99, { farOrWrongFloor }).has_value());
}

TEST(BotBrainProtocol, FormatsHuntCatalogDescriptionWithDeterministicMetadata) {
	const auto sameFloor = botbrain::formatHuntDescription(
		"Venore East Coryms",
		60,
		240,
		45,
		6,
		6,
		{ "corym charlatan", "corym skirmisher", "corym charlatan", "corym vanguard", "little corym charlatan" }
	);
	EXPECT_EQ(
		sameFloor,
		"Guide a prudent party hunt: Venore East Coryms (lvl 60-240, dist 45, same floor, targets: corym charlatan, corym skirmisher, corym vanguard)"
	);

	const auto adjacentFloor = botbrain::formatHuntDescription("Venore Coryms", 60, 0, 52, 7, 6, {});
	EXPECT_EQ(adjacentFloor, "Guide a prudent party hunt: Venore Coryms (lvl 60+, dist 52, floor 7)");

	const auto openBounds = botbrain::formatHuntDescription("Thais Rats", 0, 0, -5, 7, 7, { "", "rat" });
	EXPECT_EQ(openBounds, "Guide a prudent party hunt: Thais Rats (any lvl, dist 0, same floor, targets: rat)");

	const auto maxBounded = botbrain::formatHuntDescription("Dawnport", 0, 20, 12, 7, 7, {});
	EXPECT_EQ(maxBounded, "Guide a prudent party hunt: Dawnport (lvl <=20, dist 12, same floor)");

	const auto truncated = botbrain::formatHuntDescription(
		std::string(140, 'X'),
		100,
		300,
		88,
		7,
		7,
		{ "very long monster alpha", "very long monster beta", "very long monster gamma" }
	);
	EXPECT_LE(truncated.size(), 180U);
	EXPECT_EQ(truncated.substr(truncated.size() - 3), "...");
}

TEST(BotBrainProtocol, RoutesPartyBrainChatToGroupOrTargetByNameOrVocation) {
	const std::vector<botbrain::PartyChatMember> members {
		{ 65001, "Grizzle Alyronia", 4 },
		{ 65002, "Aegis Stone", 2 },
		{ 65003, "Lyra Swift", 3 },
		{ 65004, "Ignis Ember", 2 },
	};

	const auto broadcast = botbrain::routePartyBrainChat("compra pocoes", members);
	EXPECT_FALSE(broadcast.targeted);
	EXPECT_EQ(broadcast.message, "compra pocoes");
	EXPECT_EQ(broadcast.recipients, (std::vector<uint32_t> { 65001, 65002, 65003, 65004 }));

	const auto explicitGroup = botbrain::routePartyBrainChat("todos recua", members);
	EXPECT_FALSE(explicitGroup.targeted);
	EXPECT_EQ(explicitGroup.message, "recua");
	EXPECT_EQ(explicitGroup.recipients, (std::vector<uint32_t> { 65001, 65002, 65003, 65004 }));

	const auto druidTarget = botbrain::routePartyBrainChat("druid espera", members);
	EXPECT_TRUE(druidTarget.targeted);
	EXPECT_EQ(druidTarget.message, "espera");
	EXPECT_EQ(druidTarget.recipients, (std::vector<uint32_t> { 65002, 65004 }));

	const auto ekColonTarget = botbrain::routePartyBrainChat("ek: compra pots", members);
	EXPECT_TRUE(ekColonTarget.targeted);
	EXPECT_EQ(ekColonTarget.message, "compra pots");
	EXPECT_EQ(ekColonTarget.recipients, (std::vector<uint32_t> { 65001 }));

	const auto rpAtTarget = botbrain::routePartyBrainChat("@rp recua", members);
	EXPECT_TRUE(rpAtTarget.targeted);
	EXPECT_EQ(rpAtTarget.message, "recua");
	EXPECT_EQ(rpAtTarget.recipients, (std::vector<uint32_t> { 65003 }));

	const auto missingSorc = botbrain::routePartyBrainChat("ms foca", members);
	EXPECT_TRUE(missingSorc.targeted);
	EXPECT_EQ(missingSorc.message, "foca");
	EXPECT_TRUE(missingSorc.recipients.empty());

	const auto fullNameTarget = botbrain::routePartyBrainChat("Grizzle Alyronia recua", members);
	EXPECT_TRUE(fullNameTarget.targeted);
	EXPECT_EQ(fullNameTarget.message, "recua");
	EXPECT_EQ(fullNameTarget.recipients, (std::vector<uint32_t> { 65001 }));

	const auto firstNameColon = botbrain::routePartyBrainChat("grizzle: espera", members);
	EXPECT_TRUE(firstNameColon.targeted);
	EXPECT_EQ(firstNameColon.message, "espera");
	EXPECT_EQ(firstNameColon.recipients, (std::vector<uint32_t> { 65001 }));

	const auto firstNameAt = botbrain::routePartyBrainChat("@Aegis compra pots", members);
	EXPECT_TRUE(firstNameAt.targeted);
	EXPECT_EQ(firstNameAt.message, "compra pots");
	EXPECT_EQ(firstNameAt.recipients, (std::vector<uint32_t> { 65002 }));

	const auto bareToken = botbrain::routePartyBrainChat("druid", members);
	EXPECT_FALSE(bareToken.targeted);
	EXPECT_EQ(bareToken.message, "druid");
	EXPECT_EQ(bareToken.recipients, (std::vector<uint32_t> { 65001, 65002, 65003, 65004 }));
}

TEST(BotBrainProtocol, SelectsDynamicPartyPilotsDeterministicallyUpToCap) {
	std::vector<botbrain::DynamicPartyCandidate> candidates {
		{ 65001, 10, true, false },
		{ 65010, 10, false, false },
		{ 65020, 10, false, true },
	};
	for (uint32_t guid = 65101; guid <= 65112; ++guid) {
		candidates.push_back({ guid, 10, false, false });
	}
	candidates.push_back({ 65200, 20, false, false });

	const auto selected = botbrain::selectDynamicPartyPilots(candidates, 10, 10);
	EXPECT_EQ(selected.size(), 10U);
	// Previously dynamic 65020 comes before lower GUIDs 65010 and 65101..
	EXPECT_EQ(selected.front(), 65020U);
	// Static 65001 already occupies 1 of party 10's 10 slots, so only 9 dynamic slots remain for leader 10; 10th goes to leader 20.
	EXPECT_EQ(std::count(selected.begin(), selected.end(), 65001U), 0);
	EXPECT_EQ(std::count(selected.begin(), selected.end(), 65200U), 1);
	EXPECT_EQ(std::count(selected.begin(), selected.end(), 65010U), 1);
	EXPECT_EQ(std::count(selected.begin(), selected.end(), 65107U), 1);
	EXPECT_EQ(std::count(selected.begin(), selected.end(), 65108U), 0);
}

TEST(BotBrainProtocol, TranscodesUtf8AndLatin1ForTibiaChat) {
	const std::string utf8Sample = "Vou seguir voc\xC3\xAA; j\xC3\xA1 chegamos, n\xC3\xA3o h\xC3\xA1 n\xC3\xADvel \xE2\x80\x94 tudo certo\xE2\x80\xA6";
	const std::string latin1 = botbrain::utf8ToLatin1(utf8Sample);
	EXPECT_EQ(latin1, "Vou seguir voc\xEA; j\xE1 chegamos, n\xE3o h\xE1 n\xEDvel - tudo certo...");
	EXPECT_EQ(latin1.find("\xC3"), std::string::npos);

	const std::string rawLatin1In = "compra po\xE7\xF5" "es";
	const std::string decodedUtf8 = botbrain::latin1ToUtf8(rawLatin1In);
	EXPECT_EQ(decodedUtf8, "compra po\xC3\xA7\xC3\xB5" "es");
	// Valid UTF-8 input passes through unchanged and serializes cleanly via nlohmann::json.
	EXPECT_EQ(botbrain::latin1ToUtf8(utf8Sample), utf8Sample);
	const nlohmann::json payload = { { "text", decodedUtf8 } };
	EXPECT_NO_THROW((void)payload.dump());
}
