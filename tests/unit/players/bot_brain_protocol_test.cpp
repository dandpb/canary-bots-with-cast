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
