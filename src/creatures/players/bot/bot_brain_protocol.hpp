/**
 * Canary - A free and open-source MMORPG server emulator
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 */
#pragma once

#include <nlohmann/json.hpp>
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <string>
#include <vector>

namespace botbrain {
	struct RetreatWaypoint {
		uint16_t x = 0;
		uint16_t y = 0;
		uint8_t z = 0;
	};

	struct RetreatRouteCandidate {
		uint32_t scriptId = 0;
		bool isQuest = false;
		std::string category;
		std::vector<RetreatWaypoint> travelFrom;
	};

	struct RetreatRouteSelection {
		uint32_t scriptId = 0;
		size_t waypointIndex = 0;
	};

	/** Pick the nearest authored hunt travel_from route that ends close to home. */
	inline std::optional<RetreatRouteSelection> selectRetreatRoute(
		const RetreatWaypoint &pos,
		const RetreatWaypoint &home,
		uint32_t preferredScriptId,
		const std::vector<RetreatRouteCandidate> &candidates,
		int32_t maxAttachDist = 60,
		int32_t maxTownEndDist = 120
	) {
		auto cheb = [](const RetreatWaypoint &a, const RetreatWaypoint &b) -> int32_t {
			return std::max(
				std::abs(static_cast<int32_t>(a.x) - static_cast<int32_t>(b.x)),
				std::abs(static_cast<int32_t>(a.y) - static_cast<int32_t>(b.y))
			);
		};
		const int32_t currentHomeDist = cheb(pos, home);
		bool hasBest = false;
		bool bestPreferred = false;
		int32_t bestAttachDist = std::numeric_limits<int32_t>::max();
		int32_t bestEndHomeDist = std::numeric_limits<int32_t>::max();
		RetreatRouteSelection best {};

		for (const auto &candidate : candidates) {
			if (candidate.scriptId == 0 || candidate.isQuest || candidate.category != "hunt" || candidate.travelFrom.empty()) {
				continue;
			}
			const auto &end = candidate.travelFrom.back();
			const int32_t endHomeDist = cheb(end, home);
			if (endHomeDist > maxTownEndDist || !(endHomeDist < currentHomeDist || (pos.z != home.z && end.z == home.z))) {
				continue;
			}
			int32_t nearestDist = std::numeric_limits<int32_t>::max();
			size_t nearestIdx = 0;
			for (size_t i = 0; i < candidate.travelFrom.size(); ++i) {
				if (candidate.travelFrom[i].z != pos.z) {
					continue;
				}
				const int32_t d = cheb(candidate.travelFrom[i], pos);
				if (d < nearestDist) {
					nearestDist = d;
					nearestIdx = i;
				}
			}
			if (nearestDist > maxAttachDist) {
				continue;
			}
			const bool isPreferred = preferredScriptId != 0 && candidate.scriptId == preferredScriptId;
			const bool better = !hasBest
				|| (isPreferred != bestPreferred
					? isPreferred
					: (nearestDist != bestAttachDist
						? nearestDist < bestAttachDist
						: (endHomeDist != bestEndHomeDist ? endHomeDist < bestEndHomeDist : candidate.scriptId < best.scriptId)));
			if (better) {
				hasBest = true;
				bestPreferred = isPreferred;
				bestAttachDist = nearestDist;
				bestEndHomeDist = endHomeDist;
				best = { candidate.scriptId, nearestIdx };
			}
		}
		if (!hasBest) {
			return std::nullopt;
		}
		return best;
	}

	inline nlohmann::json telemetry(const std::string &world, uint32_t guid, uint64_t sequence, int64_t captured, uint64_t deaths, const std::string &phase, bool owned = false) {
		return { { "version", 1 }, { "type", "telemetry" }, { "world", world }, { "bot_id", guid },
		         { "sequence", sequence }, { "captured_ms", captured }, { "deaths", deaths }, { "phase", phase }, { "model_owned", owned } };
	}

	inline nlohmann::json telemetryStatus(const std::string &world, uint32_t guid, int64_t captured, uint64_t issued, uint64_t accepted, uint64_t pendingFrames, uint64_t pendingBytes, uint64_t overflowFrames, uint64_t discardedFrames) {
		return { { "version", 1 }, { "type", "telemetry_status" }, { "world", world }, { "bot_id", guid },
		         { "captured_ms", captured }, { "issued_sequence", issued }, { "accepted_sequence", accepted },
		         { "pending_frames", pendingFrames }, { "pending_bytes", pendingBytes },
		         { "overflow_frames", overflowFrames }, { "discarded_frames", discardedFrames } };
	}

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
