/**
 * Canary - A free and open-source MMORPG server emulator
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 */
#pragma once

#include <nlohmann/json.hpp>
#include <algorithm>
#include <string>

namespace botbrain {

	// Used by both the live candidate projector and the movement guard.
	inline bool partyReady(const nlohmann::json &members, const nlohmann::json &origin) {
		for (const auto &member : members) {
			const auto &position = member.at("position");
			if (!member.at("online").get<bool>() || member.at("health").get<int>() < 60
			    || position.at(2) != origin.at(2)
			    || std::abs(position.at(0).get<int>() - origin.at(0).get<int>()) > 6
			    || std::abs(position.at(1).get<int>() - origin.at(1).get<int>()) > 6) {
				return false;
			}
		}
		return true;
	}

	inline std::string validate(const nlohmann::json &intent, const nlohmann::json &offered, const nlohmann::json &current, int64_t now) {
		try {
			if (!intent.is_object() || intent.size() != 10 || intent.at("version") != 1 || intent.at("type") != "intent") {
				return "invalid_contract";
			}
			if (!intent.at("action_id").is_string() || intent.at("action_id").get<std::string>().empty()
			    || intent.at("action_id").get<std::string>().size() > 80) {
				return "invalid_action_id";
			}
			for (const auto* field : { "world", "lease", "objective_generation" }) {
				if (intent.at(field) != offered.at(field) || offered.at(field) != current.at(field)) {
					return "obsolete_generation";
				}
			}
			if (intent.at("bot_id") != offered.at("bot").at("id") || offered.at("bot").at("id") != current.at("bot").at("id")
			    || intent.at("observation_sequence") != offered.at("sequence")) {
				return "invalid_observation";
			}
			if (offered.at("party").is_null() || current.at("party").is_null()) {
				if (!offered.at("party").is_null() || !current.at("party").is_null()
				    || !offered.value("autonomous", false) || !current.value("autonomous", false)) {
					return "invalid_contract";
				}
			} else if (offered.at("party").at("leader_id") != current.at("party").at("leader_id")) {
				return "authority_changed";
			}
			if (!current.at("bot").at("alive").get<bool>()) {
				return "bot_unavailable";
			}
			if (offered.at("bot").at("position").at(2) != current.at("bot").at("position").at(2)) {
				return "floor_changed";
			}
			const auto &id = intent.at("candidate_id");
			const auto &actions = offered.at("actions");
			auto action = std::find_if(actions.begin(), actions.end(), [&](const auto &item) { return item.at("id") == id; });
			if (action == actions.end()) {
				return "unknown_candidate";
			}
			const auto &fresh = current.at("actions");
			if (std::none_of(fresh.begin(), fresh.end(), [&](const auto &item) { return item.at("id") == id; })) {
				return "candidate_no_longer_eligible";
			}
			const int64_t expiry = intent.at("expires_ms").get<int64_t>();
			if (expiry > offered.at("captured_ms").get<int64_t>() + action->at("ttl_ms").template get<int64_t>()) {
				return "extended_deadline";
			}
			if (now > expiry) {
				return "expired";
			}
			return "";
		} catch (const nlohmann::json::exception &) {
			return "invalid_contract";
		}
	}

} // namespace botbrain
