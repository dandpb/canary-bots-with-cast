/**
 * Canary - A free and open-source MMORPG server emulator
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 */
#pragma once

#include <nlohmann/json.hpp>
#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <string>
#include <unordered_map>
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

	/** Format a compact, deterministic hunt description with level band, distance, floor, and targets. */
	inline std::string formatHuntDescription(
		const std::string &name,
		uint32_t levelMin,
		uint32_t levelMax,
		int32_t distanceTiles,
		uint8_t entryFloor,
		uint8_t botFloor,
		const std::vector<std::string> &targetNames
	) {
		std::string desc = "Guide a prudent party hunt: " + name + " (";
		if (levelMin > 0 && levelMax > 0) {
			desc += "lvl " + std::to_string(levelMin) + "-" + std::to_string(levelMax);
		} else if (levelMin > 0) {
			desc += "lvl " + std::to_string(levelMin) + "+";
		} else if (levelMax > 0) {
			desc += "lvl <=" + std::to_string(levelMax);
		} else {
			desc += "any lvl";
		}
		desc += ", dist " + std::to_string(std::max<int32_t>(0, distanceTiles));
		desc += entryFloor == botFloor ? ", same floor" : (", floor " + std::to_string(entryFloor));
		std::vector<std::string> targets;
		for (const auto &target : targetNames) {
			if (target.empty()) {
				continue;
			}
			if (std::find(targets.begin(), targets.end(), target) == targets.end()) {
				targets.push_back(target);
				if (targets.size() >= 3) {
					break;
				}
			}
		}
		if (!targets.empty()) {
			desc += ", targets: ";
			for (size_t i = 0; i < targets.size(); ++i) {
				if (i > 0) {
					desc += ", ";
				}
				desc += targets[i];
			}
		}
		desc += ")";
		if (desc.size() > 180) {
			desc.resize(177);
			desc += "...";
		}
		return desc;
	}

	struct PartyChatMember {
		uint32_t guid = 0;
		std::string name;
		uint8_t baseVocation = 0;
	};

	struct PartyChatRoute {
		std::vector<uint32_t> recipients;
		std::string message;
		bool targeted = false;
	};

	/** Route a human leader `/brain` message to the whole party or targeted bots by name/vocation. */
	inline PartyChatRoute routePartyBrainChat(const std::string &rawText, const std::vector<PartyChatMember> &members) {
		auto isSpace = [](unsigned char ch) { return std::isspace(ch) != 0; };
		auto trimAscii = [&](const std::string &input) -> std::string {
			size_t start = 0;
			while (start < input.size() && isSpace(static_cast<unsigned char>(input[start]))) {
				++start;
			}
			size_t end = input.size();
			while (end > start && isSpace(static_cast<unsigned char>(input[end - 1]))) {
				--end;
			}
			return input.substr(start, end - start);
		};
		auto toLowerAscii = [](const std::string &input) -> std::string {
			std::string out = input;
			for (char &ch : out) {
				ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
			}
			return out;
		};
		auto stripTargetPunct = [](std::string token) -> std::string {
			if (!token.empty() && token.front() == '@') {
				token.erase(token.begin());
			}
			while (!token.empty() && (token.back() == ':' || token.back() == ',')) {
				token.pop_back();
			}
			return token;
		};

		const std::string trimmed = trimAscii(rawText);
		if (trimmed.empty() || members.empty()) {
			return {};
		}

		std::vector<uint32_t> allRecipients;
		allRecipients.reserve(members.size());
		for (const auto &member : members) {
			allRecipients.push_back(member.guid);
		}

		// Priority 1: match full bot name prefix (longest names first) + whitespace + message.
		const std::string body = (!trimmed.empty() && trimmed.front() == '@') ? trimAscii(trimmed.substr(1)) : trimmed;
		const std::string lowerBody = toLowerAscii(body);
		std::vector<const PartyChatMember*> byNameLength;
		byNameLength.reserve(members.size());
		for (const auto &member : members) {
			if (!member.name.empty()) {
				byNameLength.push_back(&member);
			}
		}
		std::sort(byNameLength.begin(), byNameLength.end(), [](const PartyChatMember* a, const PartyChatMember* b) {
			return a->name.size() > b->name.size();
		});
		for (const auto* member : byNameLength) {
			const std::string lowerName = toLowerAscii(trimAscii(member->name));
			if (lowerName.empty() || lowerBody.size() <= lowerName.size() || lowerBody.rfind(lowerName, 0) != 0) {
				continue;
			}
			size_t after = lowerName.size();
			if (after < body.size() && (body[after] == ':' || body[after] == ',')) {
				++after;
			}
			if (after >= body.size() || !isSpace(static_cast<unsigned char>(body[after]))) {
				continue;
			}
			const std::string rest = trimAscii(body.substr(after));
			if (rest.empty()) {
				continue;
			}
			std::vector<uint32_t> matched;
			for (const auto &candidate : members) {
				if (toLowerAscii(trimAscii(candidate.name)) == lowerName) {
					matched.push_back(candidate.guid);
				}
			}
			return { std::move(matched), rest, true };
		}

		// Priority 2: inspect first token when followed by a non-empty message.
		size_t ws = 0;
		while (ws < trimmed.size() && !isSpace(static_cast<unsigned char>(trimmed[ws]))) {
			++ws;
		}
		const std::string rest = ws < trimmed.size() ? trimAscii(trimmed.substr(ws)) : "";
		if (!rest.empty()) {
			const std::string token = stripTargetPunct(toLowerAscii(trimmed.substr(0, ws)));
			static constexpr std::array<const char*, 4> kGroupAliases { "all", "todos", "grupo", "party" };
			if (std::find(kGroupAliases.begin(), kGroupAliases.end(), token) != kGroupAliases.end()) {
				return { std::move(allRecipients), rest, false };
			}

			// 2b. First name of a bot in the party.
			std::vector<uint32_t> firstNameMatched;
			for (const auto &member : members) {
				const std::string lowerMemberName = toLowerAscii(trimAscii(member.name));
				size_t nameEnd = 0;
				while (nameEnd < lowerMemberName.size() && !isSpace(static_cast<unsigned char>(lowerMemberName[nameEnd]))) {
					++nameEnd;
				}
				if (nameEnd > 0 && lowerMemberName.substr(0, nameEnd) == token) {
					firstNameMatched.push_back(member.guid);
				}
			}
			if (!firstNameMatched.empty()) {
				return { std::move(firstNameMatched), rest, true };
			}

			// 2c. Base vocation aliases.
			uint8_t targetVocation = 0;
			static constexpr std::array<const char*, 6> kSorcAliases { "sorcerer", "sorcerers", "sorc", "sorcs", "ms", "mss" };
			static constexpr std::array<const char*, 8> kDruidAliases { "druid", "druids", "druida", "druidas", "ed", "eds", "healer", "healers" };
			static constexpr std::array<const char*, 8> kPaladinAliases { "paladin", "paladins", "paladino", "paladinos", "pally", "pala", "rp", "rps" };
			static constexpr std::array<const char*, 8> kKnightAliases { "knight", "knights", "kina", "kinas", "ek", "eks", "tank", "tanks" };
			if (std::find(kSorcAliases.begin(), kSorcAliases.end(), token) != kSorcAliases.end()) {
				targetVocation = 1;
			} else if (std::find(kDruidAliases.begin(), kDruidAliases.end(), token) != kDruidAliases.end()) {
				targetVocation = 2;
			} else if (std::find(kPaladinAliases.begin(), kPaladinAliases.end(), token) != kPaladinAliases.end()) {
				targetVocation = 3;
			} else if (std::find(kKnightAliases.begin(), kKnightAliases.end(), token) != kKnightAliases.end()) {
				targetVocation = 4;
			}
			if (targetVocation != 0) {
				std::vector<uint32_t> vocMatched;
				for (const auto &member : members) {
					if (member.baseVocation == targetVocation) {
						vocMatched.push_back(member.guid);
					}
				}
				return { std::move(vocMatched), rest, true };
			}
		}

		return { std::move(allRecipients), trimmed, false };
	}

	struct DynamicPartyCandidate {
		uint32_t guid = 0;
		uint32_t leaderGuid = 0;
		bool inStaticRoster = false;
		bool previouslyDynamic = false;
	};

	/** Deterministically select non-static human-party bots up to per-party and global caps. */
	inline std::vector<uint32_t> selectDynamicPartyPilots(
		const std::vector<DynamicPartyCandidate> &candidates,
		size_t maxBotsPerParty,
		size_t maxDynamicTotal
	) {
		std::unordered_map<uint32_t, size_t> partyCount;
		std::vector<DynamicPartyCandidate> dynamicPool;
		dynamicPool.reserve(candidates.size());

		for (const auto &candidate : candidates) {
			if (candidate.guid == 0 || candidate.leaderGuid == 0) {
				continue;
			}
			if (candidate.inStaticRoster) {
				++partyCount[candidate.leaderGuid];
			} else {
				dynamicPool.push_back(candidate);
			}
		}

		std::sort(dynamicPool.begin(), dynamicPool.end(), [](const DynamicPartyCandidate &a, const DynamicPartyCandidate &b) {
			if (a.previouslyDynamic != b.previouslyDynamic) {
				return a.previouslyDynamic > b.previouslyDynamic;
			}
			return a.guid < b.guid;
		});

		std::vector<uint32_t> selected;
		for (const auto &candidate : dynamicPool) {
			if (selected.size() >= maxDynamicTotal) {
				break;
			}
			auto &count = partyCount[candidate.leaderGuid];
			if (count >= maxBotsPerParty) {
				continue;
			}
			++count;
			selected.push_back(candidate.guid);
		}
		return selected;
	}

	/** Decode UTF-8 into ISO-8859-1 (Latin-1) with ASCII typography fallbacks for Tibia client text. */
	inline std::string utf8ToLatin1(const std::string &utf8) {
		std::string out;
		out.reserve(utf8.size());
		size_t i = 0;
		const size_t n = utf8.size();
		while (i < n) {
			const auto b0 = static_cast<unsigned char>(utf8[i]);
			if (b0 < 0x80) {
				out.push_back(static_cast<char>(b0));
				++i;
				continue;
			}
			uint32_t cp = 0;
			size_t len = 0;
			if (b0 >= 0xC2 && b0 <= 0xDF && i + 1 < n) {
				const auto b1 = static_cast<unsigned char>(utf8[i + 1]);
				if ((b1 & 0xC0) == 0x80) {
					cp = (static_cast<uint32_t>(b0 & 0x1F) << 6) | static_cast<uint32_t>(b1 & 0x3F);
					len = 2;
				}
			} else if (b0 >= 0xE0 && b0 <= 0xEF && i + 2 < n) {
				const auto b1 = static_cast<unsigned char>(utf8[i + 1]);
				const auto b2 = static_cast<unsigned char>(utf8[i + 2]);
				if ((b1 & 0xC0) == 0x80 && (b2 & 0xC0) == 0x80
				    && !(b0 == 0xE0 && b1 < 0xA0) && !(b0 == 0xED && b1 >= 0xA0)) {
					cp = (static_cast<uint32_t>(b0 & 0x0F) << 12)
						| (static_cast<uint32_t>(b1 & 0x3F) << 6)
						| static_cast<uint32_t>(b2 & 0x3F);
					len = 3;
				}
			} else if (b0 >= 0xF0 && b0 <= 0xF4 && i + 3 < n) {
				const auto b1 = static_cast<unsigned char>(utf8[i + 1]);
				const auto b2 = static_cast<unsigned char>(utf8[i + 2]);
				const auto b3 = static_cast<unsigned char>(utf8[i + 3]);
				if ((b1 & 0xC0) == 0x80 && (b2 & 0xC0) == 0x80 && (b3 & 0xC0) == 0x80
				    && !(b0 == 0xF0 && b1 < 0x90) && !(b0 == 0xF4 && b1 > 0x8F)) {
					cp = (static_cast<uint32_t>(b0 & 0x07) << 18)
						| (static_cast<uint32_t>(b1 & 0x3F) << 12)
						| (static_cast<uint32_t>(b2 & 0x3F) << 6)
						| static_cast<uint32_t>(b3 & 0x3F);
					len = 4;
				}
			}
			if (len == 0) {
				out.push_back(static_cast<char>(b0));
				++i;
				continue;
			}
			if (cp <= 0xFF) {
				out.push_back(static_cast<char>(cp));
			} else if (cp == 0x2013 || cp == 0x2014) {
				out.push_back('-');
			} else if (cp == 0x2018 || cp == 0x2019) {
				out.push_back('\'');
			} else if (cp == 0x201C || cp == 0x201D) {
				out.push_back('"');
			} else if (cp == 0x2026) {
				out.append("...");
			}
			i += len;
		}
		return out;
	}

	/** Ensure player text is valid UTF-8 before JSON serialization (transcoding ISO-8859-1 if invalid UTF-8). */
	inline std::string latin1ToUtf8(const std::string &input) {
		size_t i = 0;
		const size_t n = input.size();
		bool validUtf8 = true;
		while (i < n) {
			const auto b0 = static_cast<unsigned char>(input[i]);
			if (b0 < 0x80) {
				++i;
			} else if (b0 >= 0xC2 && b0 <= 0xDF && i + 1 < n
			           && (static_cast<unsigned char>(input[i + 1]) & 0xC0) == 0x80) {
				i += 2;
			} else if (b0 >= 0xE0 && b0 <= 0xEF && i + 2 < n
			           && (static_cast<unsigned char>(input[i + 1]) & 0xC0) == 0x80
			           && (static_cast<unsigned char>(input[i + 2]) & 0xC0) == 0x80
			           && !(b0 == 0xE0 && static_cast<unsigned char>(input[i + 1]) < 0xA0)
			           && !(b0 == 0xED && static_cast<unsigned char>(input[i + 1]) >= 0xA0)) {
				i += 3;
			} else if (b0 >= 0xF0 && b0 <= 0xF4 && i + 3 < n
			           && (static_cast<unsigned char>(input[i + 1]) & 0xC0) == 0x80
			           && (static_cast<unsigned char>(input[i + 2]) & 0xC0) == 0x80
			           && (static_cast<unsigned char>(input[i + 3]) & 0xC0) == 0x80
			           && !(b0 == 0xF0 && static_cast<unsigned char>(input[i + 1]) < 0x90)
			           && !(b0 == 0xF4 && static_cast<unsigned char>(input[i + 1]) > 0x8F)) {
				i += 4;
			} else {
				validUtf8 = false;
				break;
			}
		}
		if (validUtf8) {
			return input;
		}
		std::string out;
		out.reserve(n * 2);
		for (const char ch : input) {
			const auto b = static_cast<unsigned char>(ch);
			if (b < 0x80) {
				out.push_back(static_cast<char>(b));
			} else {
				out.push_back(static_cast<char>(0xC0 | (b >> 6)));
				out.push_back(static_cast<char>(0x80 | (b & 0x3F)));
			}
		}
		return out;
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
