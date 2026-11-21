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
