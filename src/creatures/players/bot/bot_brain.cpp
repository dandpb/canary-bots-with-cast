/**
 * Canary - A free and open-source MMORPG server emulator
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 */

#include "creatures/players/bot/bot_engine_impl.hpp"
#include "creatures/players/bot/bot_potions.hpp"
#include "lua/scripts/scripts.hpp"
#if __has_include("gitmetadata.h")
#include "gitmetadata.h"
#else
#define GIT_HEAD_SHA1 "unknown"
#define GIT_IS_DIRTY 1
#endif

namespace {
	using Json = nlohmann::json;
	std::deque<double> brainTickMicroseconds;
	std::unordered_map<uint32_t, bool> brainPreviousChase;
	struct BrainCombat {
		// Retain one attacked target until the next observation so removal from
		// Game cannot turn "out of sight" into a fabricated kill.
		std::shared_ptr<Creature> target;
		uint32_t defeats = 0;
	};
	std::unordered_map<uint32_t, BrainCombat> brainCombat;
	enum SupplyPhase : uint8_t { ApproachingShop,
		                         WaitingForGreeting,
		                         VerifyingPurchase,
		                         ReturningToParty };

	std::vector<ShopBlock> brainSupplyItems(const std::shared_ptr<Player> &player, const std::shared_ptr<Npc> &npc) {
		std::vector<ShopBlock> chosen;
		bool health = false, mana = false;
		const uint32_t bit = botsupplies::vocBit(player->getVocation()->getBaseId());
		const auto &shop = npc->getShopItemVector(player->getGUID());
		for (auto def = std::rbegin(botsupplies::kPotions); def != std::rend(botsupplies::kPotions); ++def) {
			if (player->getLevel() < def->level || (def->vocMask && !(def->vocMask & bit))
			    || !((def->heals && !health) || (def->restoresMana && !mana))) {
				continue;
			}
			auto item = std::find_if(shop.begin(), shop.end(), [&](const auto &entry) { return entry.itemId == def->id && entry.itemBuyPrice > 0; });
			if (item == shop.end()) {
				continue;
			}
			chosen.push_back(*item);
			health = health || def->heals;
			mana = mana || def->restoresMana;
			if (health && mana) {
				return chosen;
			}
		}
		return {};
	}

	Json brainPartyStatus(const std::shared_ptr<Player> &player) {
		Json status = Json::array();
		auto party = player->getParty();
		if (!party) return status;
		auto add = [&](const std::shared_ptr<Player> &member) {
			if (!member || status.size() >= 20) return;
			const auto at = member->getPosition();
			status.push_back({ { "id", member->getGUID() }, { "health", std::clamp(100 * member->getHealth() / std::max(1, member->getMaxHealth()), 0, 100) },
			                   { "position", { at.x, at.y, at.z } }, { "online", !member->isRemoved() && g_game().getPlayerByID(member->getID()) == member } });
		};
		add(party->getLeader());
		for (const auto &member : party->getMembers()) add(member);
		return status;
	}

	Json brainOutcome(const std::string &world, uint32_t guid, const std::string &id, const std::string &status, const std::string &reason, Json metrics = Json::object()) {
		return { { "version", 1 }, { "type", "outcome" }, { "world", world }, { "bot_id", guid }, { "action_id", id }, { "status", status }, { "reason", reason }, { "metrics", metrics } };
	}
	void rememberOutcome(botbrain::Session &session, const std::string &id, const Json &outcome) {
		if (session.outcomes.size() >= 128) {
			Json running;
			if (auto current = session.outcomes.find(session.actionId); current != session.outcomes.end()) {
				running = current->second;
			}
			session.outcomes.clear();
			if (!running.is_null()) {
				session.outcomes[session.actionId] = std::move(running);
			}
		}
		session.outcomes[id] = outcome;
	}
} // namespace

void botbrain::retainTarget(uint32_t guid, const std::shared_ptr<Creature> &target) {
	if (auto combat = brainCombat.find(guid); combat != brainCombat.end()
	    && target && target->getMonster() && target->getHealth() > 0) {
		combat->second.target = target;
	}
}

uint32_t BotEngine::brainPotions(const std::shared_ptr<Player> &player) const {
	uint32_t total = 0;
	const auto bit = botsupplies::vocBit(player->getVocation()->getBaseId());
	for (const auto &item : player->getAllInventoryItems()) {
		for (const auto &potion : botsupplies::kPotions) {
			if (item->getID() == potion.id && player->getLevel() >= potion.level && (!potion.vocMask || (potion.vocMask & bit))) {
				total += Item::countByType(item, -1);
				break;
			}
		}
	}
	return total;
}

bool BotEngine::brainOwns(uint32_t guid) const {
	if (!brain_ || brain_->mode != "active" || botMonoMs() - brain_->heartbeat > 5000
	    || std::find(brain_->roster.begin(), brain_->roster.end(), guid) == brain_->roster.end()) {
		return false;
	}
	auto session = brain_->sessions.find(guid);
	return session != brain_->sessions.end() && (session->second.leader != 0 || brain_->autonomous == guid);
}

bool BotEngine::brainRetreat(uint32_t guid) const {
	if (!brainOwns(guid)) {
		return false;
	}
	const auto &session = brain_->sessions.at(guid);
	return !session.actionId.empty() && session.action == "retreat";
}

std::shared_ptr<Creature> BotEngine::brainTarget(BotState &bot) {
	if (!brainOwns(bot.guid)) {
		return nullptr;
	}
	const auto &session = brain_->sessions.at(bot.guid);
	if (!session.target || botMonoMs() > session.targetUntil) {
		return nullptr;
	}
	auto target = g_game().getCreatureByID(session.target);
	if (!target || !target->getMonster() || target->getHealth() <= 0 || target->getPosition().z != bot.currentPos.z
	    || Position::getDiagonalDistance(target->getPosition(), bot.currentPos) > 6) {
		return nullptr;
	}
	return target;
}

std::string BotEngine::brainCommand(const std::string &botName, const std::string &command) {
	if (command == "refresh_helpers" && botName == "_global") {
		auto &scripts = g_scripts().getScriptInterface();
		auto *state = scripts.getLuaState();
		lua_getglobal(state, "BotSystem");
		bool reloading = false;
		if (lua_istable(state, -1)) {
			lua_getfield(state, -1, "_reloadInProgress");
			reloading = lua_toboolean(state, -1);
			lua_pop(state, 1);
		}
		lua_pop(state, 1);
		if (reloading) return "Wait for the bot reload to finish before refreshing its helper.";
		return scripts.loadFile("data/scripts/lib/bot_system.lua", "bot_system.lua") == 0
			? "Bot reload helper refreshed. No gameplay scripts or global reload settings changed."
			: "Bot reload helper could not be refreshed.";
	}
	if (command == "reload") {
		if (brain_) {
			for (const auto guid : brain_->roster) {
				if (auto bot = getBotState(guid)) {
					finishBrain(*bot, "cancelled", "controller_reloaded");
				}
			}
		}
		brain_.reset();
		brainConfigured_ = false;
		return "Brain configuration will be reloaded next tick.";
	}
	if (!brain_ || !brain_->channel) {
		return "Brain disabled; native behavior is active.";
	}
	if (command == "status") {
		auto timings = std::vector<double>(brainTickMicroseconds.begin(), brainTickMicroseconds.end());
		std::sort(timings.begin(), timings.end());
		const double p95 = timings.empty() ? 0.0 : timings[std::min(timings.size() - 1, timings.size() * 95 / 100)];
		Json sessions = Json::array();
		for (const auto &[guid, session] : brain_->sessions) {
			auto leader = g_game().getPlayerByGUID(session.leader, false);
			auto shop = session.shop ? g_game().getCreatureByID(session.shop) : nullptr;
			auto bot = getBotState(guid);
			auto player = bot ? bot->getPlayer() : nullptr;
			sessions.push_back({ { "bot", guid }, { "leader", session.leader }, { "leader_creature_id", leader ? leader->getID() : 0 },
				{ "objective", session.action }, { "running", !session.actionId.empty() }, { "script", session.script }, { "waypoint", session.waypoint },
				{ "shop", shop ? shop->getName() : "" }, { "supply_phase", session.supplyStep }, { "home", session.home },
				{ "walk_queue", player ? player->listWalkDir.size() : 0 }, { "pending_walk_pause", bot ? bot->pendingWalkPauseEventId : 0 },
				{ "floor_change", bot ? static_cast<int>(bot->fcState) : 0 } });
		}
		return Json({ { "version", 1 }, { "mode", brain_->mode }, { "world", brain_->world }, { "worker_alive", botMonoMs() - brain_->heartbeat <= 5000 }, { "roster", brain_->roster }, { "sessions", sessions }, { "bridge_tick_p95_us", p95 }, { "bridge_tick_samples", timings.size() } }).dump();
	}
	if (command == "disable") {
		for (const auto guid : brain_->roster) {
			auto bot = getBotState(guid);
			if (bot && (botName == "_global" || bot->name == botName)) {
				finishBrain(*bot, "cancelled", "operator_disabled");
			}
		}
		if (botName == "_global") {
			brain_.reset();
			return "Brain disabled; native behavior retained.";
		}
		brain_->roster.erase(std::remove_if(brain_->roster.begin(), brain_->roster.end(), [&](uint32_t guid) {
								 auto bot = getBotState(guid);
								 return bot && bot->name == botName;
							 }),
		                     brain_->roster.end());
		return "Selected companion returned to native behavior.";
	}
	if (command.rfind("chat ", 0) == 0) {
		const auto separator = command.find(' ', 5);
		if (separator == std::string::npos || command.size() - separator > 1025) {
			return "Mensagem invalida.";
		}
		try {
			const auto sender = static_cast<uint32_t>(std::stoul(command.substr(5, separator - 5)));
			auto player = g_game().getPlayerByID(sender);
			if (!player || player->isBotPlayer()) {
				return "Entre em uma party com um companheiro inteligente.";
			}
			for (const auto guid : brain_->roster) {
				auto bot = getBotState(guid);
				if (bot && bot->getPlayer() && player->getParty() && bot->getPlayer()->getParty() == player->getParty()
				    && brainMessage(guid, sender, command.substr(separator + 1))) {
					return "Mensagem enviada ao companheiro.";
				}
			}
			if (brain_->autonomous && brainMessage(brain_->autonomous, sender, command.substr(separator + 1))) {
				return "Mensagem enviada ao bot explorador.";
			}
			return "Nenhum companheiro inteligente disponivel.";
		} catch (const std::exception &) {
			return "Mensagem invalida.";
		}
	}
	return "Brain commands: status, reload, disable.";
}

std::shared_ptr<Npc> BotEngine::brainShop(BotState &bot) {
	auto &session = brain_->sessions[bot.guid];
	if (session.shop) {
		auto creature = g_game().getCreatureByID(session.shop);
		if (creature && creature->getNpc()) {
			return creature->getNpc();
		}
	}
	if (botMonoMs() - session.lastShopScan < 30000) {
		return nullptr;
	}
	session.lastShopScan = botMonoMs();
	int32_t best = 250;
	std::shared_ptr<Npc> chosen;
	for (const auto &npc : g_game().getNpcs()) {
		if (!npc || npc->getCurrency() != ITEM_GOLD_COIN || npc->getPosition().z != bot.currentPos.z) {
			continue;
		}
		const int32_t distance = Position::getDiagonalDistance(bot.currentPos, npc->getPosition());
		if (distance >= best) {
			continue;
		}
		if (brainSupplyItems(bot.getPlayer(), npc).empty()) {
			continue;
		}
		Position stand;
		bool fallback = false;
		if (!resolveNpcApproach(bot, npc->getName(), stand, fallback)) {
			continue;
		}
		best = distance;
		chosen = npc;
	}
	if (chosen) {
		session.shop = chosen->getID();
	}
	return chosen;
}

Json BotEngine::observeBrain(BotState &bot) {
	auto player = bot.getPlayer();
	if (!player) {
		return Json();
	}
	auto &session = brain_->sessions[bot.guid];
	auto party = player->getParty();
	auto leader = party ? party->getLeader() : nullptr;
	if (leader && leader->getHealth() <= 0) {
		finishBrain(bot, "failed", "party_death");
	}
	const auto onlineHuman = [](const std::shared_ptr<Player> &member) {
		return member && !member->isBotPlayer() && member->getHealth() > 0
		    && g_game().getPlayerByID(member->getID()) == member;
	};
	if (party && brain_->autonomous == bot.guid && brainOwns(bot.guid)) {
		bool hasHuman = onlineHuman(leader);
		for (const auto &member : party->getMembers()) hasHuman = hasHuman || onlineHuman(member);
		if (!hasHuman) {
			// A fallback/native recruitment may predate the worker lease. The
			// explorer must regain solo ownership when that lease returns.
			if (bot.partyHuntId) dissolvePartyHunt(bot.partyHuntId, "brain_autonomy");
			exitPartyMode(bot);
			party = player->getParty();
			leader = party ? party->getLeader() : nullptr;
		}
	}
	// Invitations join the Canary party before the native rendezvous finishes.
	// Leave that travel/assembly in charge until the companion can execute PARTY goals.
	if (leader && (leader->isBotPlayer() || leader->isRemoved() || leader->getHealth() <= 0
	               || g_game().getPlayerByID(leader->getID()) != leader || bot.state != BotAIState::PARTY)) {
		leader = nullptr;
	}
	const bool autonomous = brain_->autonomous == bot.guid;
	const bool solo = autonomous && !party;
	const uint32_t leaderGuid = leader ? leader->getGUID() : 0;
	if (session.leader != leaderGuid) {
		finishBrain(bot, "cancelled", "authority_changed");
		session.leader = leaderGuid;
		++session.generation;
		session.offers.clear();
	}
	if (!leader && party && bot.state == BotAIState::PARTY && bot.partyHuntId == 0) {
		bool humanRemains = onlineHuman(party->getLeader());
		for (const auto &member : party->getMembers()) {
			humanRemains = humanRemains || onlineHuman(member);
		}
		if (!humanRemains) {
			// Party retains Player references after death/logout. Drain this here,
			// before the proximity gate can skip native PARTY ticks without humans.
			exitPartyMode(bot);
		}
	}
	session.lease = brain_->world + ":" + std::to_string(bot.guid) + ":" + std::to_string(session.generation);
	const auto position = player->getPosition();
	const int health = std::clamp(100 * player->getHealth() / std::max(1, player->getMaxHealth()), 0, 100);
	const int mana = std::clamp<int>(100 * player->getMana() / std::max<uint32_t>(1, player->getMaxMana()), 0, 100);
	const uint32_t potions = brainPotions(player);
	bool partyHasKnight = leader && getBaseVocation(leader->getVocationId()) == 4;
	if (party) {
		for (const auto &member : party->getMembers()) {
			partyHasKnight = partyHasKnight || getBaseVocation(member->getVocationId()) == 4;
		}
	}
	Json actions = Json::array();
	auto add = [&](const std::string &id, const std::string &action, const std::string &description, int ttl = 5000) {
		if (actions.size() >= 32) {
			return;
		}
		actions.push_back({ { "id", id }, { "action", action }, { "description", description }, { "ttl_ms", ttl } });
	};
	add("continue", "continue", "Continue the current useful objective", 1500);
	Json partyState = nullptr;
	if (leader || solo) {
		uint32_t minimumLevel = leader ? std::min(player->getLevel(), leader->getLevel()) : player->getLevel();
		uint32_t maximumLevel = leader ? std::max(player->getLevel(), leader->getLevel()) : player->getLevel();
		Json members = Json::array();
		if (leader) members.push_back(leaderGuid);
		if (leader) for (const auto &member : party->getMembers()) {
			minimumLevel = std::min(minimumLevel, member->getLevel());
			maximumLevel = std::max(maximumLevel, member->getLevel());
			if (members.size() < 20) {
				members.push_back(member->getGUID());
			}
		}
		const auto memberStatus = brainPartyStatus(player);
		if (leader) partyState = { { "leader_id", leaderGuid }, { "members", members }, { "status", memberStatus } };
		if (leader) add("follow", "follow", "Follow and support the human party leader");
		add("hold", "hold", "Hold position briefly while retaining combat and healing");
		const auto homeTown = solo ? g_game().map.towns.getTown(findNearestTown(position)) : nullptr;
		const auto homePosition = homeTown ? homeTown->getTemplePosition() : position;
		const bool awayFromHome = position.z != homePosition.z || Position::getDiagonalDistance(position, homePosition) > 3;
		if (!solo || health < 80 || awayFromHome) {
			add("retreat", "retreat", "Disengage and return to the leader or town temple for the next activity", 1500);
		}
		if (health >= 80) {
			if (potions < 40 && session.action != "resupply" && !player->isPzLocked() && brainShop(bot)) {
				add("resupply", "resupply", "Walk to the town shop to replenish supplies and return");
			}
			if (potions >= 10 && botbrain::partyReady(memberStatus, { position.x, position.y, position.z })) {
				for (const auto &script : huntScripts_) {
					if (actions.size() >= 24) {
						break;
					}
					if (!script.enabled || script.isQuest || script.scriptCategory != "hunt" || script.patrolWaypoints.empty()
					    || script.townId != bot.townId || (script.levelMin && minimumLevel < script.levelMin)
					    || (script.levelMax && maximumLevel > script.levelMax)
					    || (script.vocationMask && !(script.vocationMask & (1U << (getBaseVocation(bot.vocationId) - 1))))
					    || activeHunts_.count(script.id) || (!script.spawnGroup.empty() && activeSpawnGroups_.count(script.spawnGroup))
					    || isScriptPlayerClaimed(script.id, script.spawnGroup) || isScriptHuntRepelled(script)) {
						continue;
					}
					const auto &entry = script.travelToWaypoints.empty() ? script.patrolWaypoints.front() : script.travelToWaypoints.front();
					if (entry.pos.z != position.z || Position::getDiagonalDistance(entry.pos, position) > 200) {
						continue;
					}
					add("hunt:" + std::to_string(script.id), "hunt", "Guide a prudent party hunt: " + script.name);
				}
			}
		}
	}
	Json nearby = Json::array();
	for (const auto &entity : Spectators().find<Monster>(position, false, 7, 7, 5, 5)) {
		if (nearby.size() >= 12) {
			break;
		}
		auto monster = entity->getMonster();
		if (!monster || monster->getHealth() <= 0) {
			continue;
		}
		const auto at = monster->getPosition();
		nearby.push_back({ { "id", monster->getID() }, { "name", monster->getName() }, { "position", { at.x, at.y, at.z } } });
		if ((leader || solo) && (getBaseVocation(bot.vocationId) == 4 || !partyHasKnight) && health >= 40 && at.z == position.z && Position::getDiagonalDistance(position, at) <= 6) {
			add("target:" + std::to_string(monster->getID()), "target", "Prioritize visible monster " + monster->getName(), 1000);
		}
	}
	session.danger = std::max(session.danger, 1.0 - health / 100.0);
	Json snapshot = { { "version", 1 }, { "type", "observation" }, { "world", brain_->world }, { "sequence", ++session.sequence }, { "captured_ms", botMonoMs() }, { "lease", session.lease }, { "objective_generation", session.generation }, { "mode", brain_->mode }, { "bot", { { "id", bot.guid }, { "name", bot.name }, { "level", player->getLevel() }, { "vocation", bot.vocationId }, { "state", botStateName(bot.state) }, { "position", { position.x, position.y, position.z } }, { "health", health }, { "mana", mana }, { "potions", potions }, { "xp", player->getExperience() }, { "alive", player->getHealth() > 0 } } }, { "party", partyState }, { "autonomous", autonomous }, { "actions", actions }, { "nearby", nearby }, { "messages", session.messages } };
	snapshot["bot"]["objective"] = session.action;
	snapshot["bot"]["objective_running"] = !session.actionId.empty();
	snapshot["bot"]["objective_defeats"] = brainCombat.count(bot.guid) ? brainCombat.at(bot.guid).defeats : 0;
	return snapshot;
}

void BotEngine::finishBrain(BotState &bot, const std::string &status, const std::string &reason) {
	if (!brain_) {
		return;
	}
	auto &session = brain_->sessions[bot.guid];
	if (!session.actionId.empty()) {
		auto player = bot.getPlayer();
		if (auto previous = brainPreviousChase.find(bot.guid); previous != brainPreviousChase.end()) {
			if (player) {
				player->setChaseMode(previous->second);
			}
			brainPreviousChase.erase(previous);
		}
		if (player && (session.action == "hunt" || session.action == "resupply" || session.action == "hold" || session.action == "retreat" || session.action == "follow")) {
			player->listWalkDir.clear();
			player->stopEventWalk();
		}
		if (session.action == "resupply" || session.action == "retreat" || session.action == "hunt") {
			clearPlannerWalk(bot.guid);
			resetFloorChange(bot);
		}
		releaseNpcApproach(bot.guid);
		const double elapsed = std::max<int64_t>(0, botMonoMs() - session.started) / 1000.0;
		const double xp = player && player->getExperience() >= session.xp ? player->getExperience() - session.xp : 0;
		const auto potionDelta = player ? static_cast<int64_t>(brainPotions(player)) - session.potions : 0;
		auto leader = player && player->getParty() ? player->getParty()->getLeader() : nullptr;
		const double distance = player && leader ? Position::getDiagonalDistance(player->getPosition(), leader->getPosition()) : 0;
		auto outcome = brainOutcome(brain_->world, bot.guid, session.actionId, status, reason, { { "elapsed_seconds", elapsed }, { "level", player ? player->getLevel() : 1 }, { "party_size", player && player->getParty() ? player->getParty()->getMemberCount() + 1 : 1 }, { "xp_delta", xp }, { "defeats_delta", brainCombat.count(bot.guid) ? brainCombat.at(bot.guid).defeats : 0 }, { "supply_delta", potionDelta }, { "party_distance", distance }, { "progress", status == "completed" ? 1.0 : 0.0 }, { "danger", session.danger }, { "deaths", reason == "death" || reason == "party_death" ? 1.0 : 0.0 } });
		rememberOutcome(session, session.actionId, outcome);
		brain_->channel->send(outcome);
	}
	if (session.script != 0) {
		if (auto reservation = activeHunts_.find(session.script); reservation != activeHunts_.end() && reservation->second == bot.guid) {
			activeHunts_.erase(reservation);
		}
		for (const auto &script : huntScripts_) {
			if (script.id == session.script && !script.spawnGroup.empty()) {
				auto group = activeSpawnGroups_.find(script.spawnGroup);
				if (group != activeSpawnGroups_.end() && group->second == bot.guid) {
					activeSpawnGroups_.erase(group);
				}
			}
		}
	}
	brainCombat.erase(bot.guid);
	session.actionId.clear();
	session.action = "follow";
	session.script = 0;
	session.waypoint = 0;
	session.skipped = 0;
}

bool BotEngine::brainMessage(uint32_t guid, uint32_t sender, const std::string &text) {
	if (!brain_ || !brain_->channel || std::find(brain_->roster.begin(), brain_->roster.end(), guid) == brain_->roster.end()) {
		return false;
	}
	auto bot = getBotState(guid);
	auto player = g_game().getPlayerByID(sender);
	if (!bot || !player || player->isBotPlayer() || text.empty() || text.size() > 1024) {
		return false;
	}
	if (brain_->mode == "active" && botMonoMs() - brain_->heartbeat > 5000) {
		return false;
	}
	if (bot->hibernated && !wakeBot(guid)) {
		return false;
	}
	auto &session = brain_->sessions[guid];
	auto party = player->getParty();
	const bool leaderOrder = party && party->getLeader() == player && bot->getPlayer() && bot->getPlayer()->getParty() == party;
	if (!leaderOrder && botMonoMs() - session.lastMessage < 2000) {
		return brain_->mode == "active";
	}
	session.lastMessage = botMonoMs();
	if (session.messages.size() >= 8) {
		session.messages.erase(session.messages.begin());
	}
	session.messages.push_back({ { "id", brain_->world + ":" + std::to_string(++brain_->messageSequence) },
	                             { "player_id", player->getGUID() },
	                             { "text", text },
	                             { "channel", "pm" } });
	return brain_->mode == "active";
}

void BotEngine::tickBrain() {
	if (!brainConfigured_) {
		brainConfigured_ = true;
		try {
			brain_ = std::make_unique<botbrain::Runtime>();
		} catch (const std::exception &) {
			g_logger().error("[Brain] Invalid configuration or unavailable private socket; native AI retained");
		}
	}
	if (!brain_ || !brain_->channel) {
		return;
	}
	const auto processingStarted = std::chrono::steady_clock::now();
	const auto now = botMonoMs();
	const auto packets = brain_->channel->receive();
	brain_->beginTelemetryTick();
	// Consume queued heartbeats before evaluating leases. A busy dispatcher may
	// resume after five seconds even though the independent worker stayed alive.
	for (const auto &packet : packets) {
		if (packet.is_object() && packet.value("version", Json()) == 1
		    && packet.value("world", Json()) == brain_->world && packet.value("type", Json()) == "heartbeat") {
			brain_->heartbeat = now;
		}
	}
	if (now - brain_->lastHello >= 1000) {
		brain_->lastHello = now;
		brain_->channel->send({ { "version", 1 }, { "type", "hello" }, { "world", brain_->world }, { "capabilities", { { "lifecycle_telemetry", 1 }, { "telemetry_delivery", 1 }, { "telemetry_admission", 1 }, { "keep_awake", brain_->keepAwake } } } });
	}
	for (const auto guid : brain_->roster) {
		auto bot = getBotState(guid);
		if (!bot) {
			continue;
		}
		auto &session = brain_->sessions[guid];
		auto player = bot->getPlayer();
		if (guid == brain_->autonomous && (brainOwns(guid) || (brain_->keepAwake && now - brain_->heartbeat <= 5000)) && bot->active && bot->hibernated && now - session.lastPublish >= 5000) {
			session.lastPublish = now;
			wakeBot(guid);
			player = bot->getPlayer();
		}
		if (now - session.lastTelemetry >= 1000) {
			session.lastTelemetry = now;
			const std::string phase = bot->hibernated ? "hibernated" : !player || !bot->active ? "unavailable" : player->getHealth() <= 0 ? "dead" : "alive";
			session.delivery.publish(*brain_->channel, botbrain::telemetry(brain_->world, guid, ++session.telemetrySequence, now, session.deaths, phase, brainOwns(guid)));
		}
		if (!player || !bot->active || bot->hibernated || player->getHealth() <= 0) {
			finishBrain(*bot, player && player->getHealth() <= 0 ? "failed" : "cancelled", player && player->getHealth() <= 0 ? "death" : "unavailable");
			continue;
		}
		bot->cachedLevel = player->getLevel();
		if (!session.actionId.empty() && session.action == "hunt") {
			auto &combat = brainCombat[guid];
			if (combat.target && combat.target->getHealth() <= 0) {
				++combat.defeats;
				combat.target.reset();
			}
			auto target = player->getAttackedCreature();
			if (target && target->getMonster() && target->getHealth() > 0) combat.target = target;
			const auto duration = guid == brain_->autonomous && !player->getParty() ? 300000 : 900000;
			if (now - session.started >= duration) {
				finishBrain(*bot, combat.defeats > 0 ? "completed" : "failed", combat.defeats > 0 ? "hunt_progress" : "no_confirmed_combat_progress");
			}
		}
		if (now - brain_->heartbeat > 5000 && !session.actionId.empty()) {
			finishBrain(*bot, "cancelled", "worker_unavailable");
		}
		if (!session.actionId.empty() && session.action == "hold" && now - session.started >= 30000) {
			finishBrain(*bot, "completed", "hold_finished");
		}
		if (now - session.lastPublish < 250) {
			continue;
		}
		session.lastPublish = now;
		auto snapshot = observeBrain(*bot);
		if (session.offers.size() >= 12) {
			session.offers.pop_front();
		}
		session.offers.push_back(snapshot);
		brain_->channel->send(snapshot);
		if (!session.actionId.empty() && now - session.started > (session.action == "hunt" ? 1800000 : 300000)) {
			finishBrain(*bot, "failed", "objective_timeout");
		}
	}
	for (const auto &packet : packets) {
		try {
			if (packet.value("version", 0) != 1 || packet.value("world", "") != brain_->world) {
				continue;
			}
			const auto type = packet.value("type", "");
			if (type == "heartbeat") {
				brain_->heartbeat = now;
				continue;
			}
			const auto guid = packet.at("bot_id").get<uint32_t>();
			// A terminal acknowledgement remains queryable after a pilot becomes
			// unavailable or is disabled; queries never apply gameplay actions.
			if (type == "query") {
				const auto id = packet.at("action_id").get<std::string>();
				if (auto existing = brain_->sessions.find(guid); existing != brain_->sessions.end()) {
					if (auto outcome = existing->second.outcomes.find(id); outcome != existing->second.outcomes.end()) {
						brain_->channel->send(outcome->second);
						continue;
					}
				}
				brain_->channel->send(brainOutcome(brain_->world, guid, id, "rejected", "unknown_action"));
				continue;
			}
			if (std::find(brain_->roster.begin(), brain_->roster.end(), guid) == brain_->roster.end()) {
				continue;
			}
			if (type == "telemetry_admit") {
				auto &session = brain_->sessions[guid];
				// Dispatcher-serialized snapshot + counter + FIFO cut. Retry does not
				// inspect current life state, recapture O0 or allocate a second B.
				const auto reply = session.admit(packet, brain_->world, guid, GIT_HEAD_SHA1, GIT_IS_DIRTY != 0, [&]() {
					auto pilot = getBotState(guid);
					if (!pilot || !pilot->active || pilot->hibernated || !pilot->getPlayer() || pilot->getPlayer()->getHealth() <= 0) {
						throw std::runtime_error("admission unavailable");
					}
					return observeBrain(*pilot);
				});
				brain_->channel->send(reply);
				continue;
			}
			auto bot = getBotState(guid);
			if (!bot || !bot->active || !bot->getPlayer()) {
				continue;
			}
			auto &session = brain_->sessions[guid];
			if (type == "reply") {
				const auto id = packet.at("message_id").get<std::string>();
				const auto text = packet.at("text").get<std::string>();
				for (auto message = session.messages.begin(); message != session.messages.end(); ++message) {
					if (message->at("id") != id) {
						continue;
					}
					auto target = g_game().getPlayerByGUID(message->at("player_id").get<uint32_t>(), false);
					if (brain_->mode == "active" && target && !text.empty() && text.size() <= 1200) {
						target->sendPrivateMessage(bot->getPlayer(), TALKTYPE_PRIVATE_FROM, text);
					}
					session.messages.erase(message);
					break;
				}
				continue;
			}
			if (type != "intent") {
				continue;
			}
			const auto id = packet.at("action_id").get<std::string>();
			if (auto old = session.outcomes.find(id); old != session.outcomes.end()) {
				brain_->channel->send(old->second);
				continue;
			}
			Json current = observeBrain(*bot);
			auto offer = std::find_if(session.offers.begin(), session.offers.end(), [&](const Json &item) {
				return item.at("sequence") == packet.at("observation_sequence");
			});
			std::string error = "invalid_observation";
			if (offer != session.offers.end()) {
				error = botbrain::validate(packet, *offer, current, now);
			}
			if (error.empty() && !brainOwns(guid)) {
				error = "controller_unavailable";
			}
			if (!error.empty()) {
				brain_->channel->send(brainOutcome(brain_->world, guid, id, "rejected", error));
				continue;
			}
			const auto candidate = packet.at("candidate_id").get<std::string>();
			const auto &actions = current.at("actions");
			auto selected = std::find_if(actions.begin(), actions.end(), [&](const Json &item) { return item.at("id") == candidate; });
			const auto action = selected->at("action").get<std::string>();
			if (action == "continue") {
				auto outcome = brainOutcome(brain_->world, guid, id, "completed", "continuing");
				rememberOutcome(session, id, outcome);
				brain_->channel->send(outcome);
				continue;
			}
			if (action == "target") {
				session.target = static_cast<uint32_t>(std::stoul(candidate.substr(7)));
				session.targetUntil = packet.at("expires_ms").get<int64_t>();
				auto target = g_game().getCreatureByID(static_cast<uint32_t>(std::stoul(candidate.substr(7))));
				if (target && target->getMonster() && target->getHealth() > 0) {
					botbrain::retainTarget(guid, target);
					bot->getPlayer()->setAttackedCreature(target);
					bot->huntTargetId = target->getID();
				}
				auto outcome = brainOutcome(brain_->world, guid, id, "completed", "preference_applied");
				rememberOutcome(session, id, outcome);
				brain_->channel->send(outcome);
				continue;
			}
			finishBrain(*bot, "cancelled", "new_objective");
			session.actionId = id;
			session.action = action;
			session.started = now;
			session.xp = bot->getPlayer()->getExperience();
			session.potions = brainPotions(bot->getPlayer());
			const auto town = g_game().map.towns.getTown(findNearestTown(bot->getPlayer()->getPosition()));
			const auto home = town ? town->getTemplePosition() : bot->getPlayer()->getPosition();
			session.home = { home.x, home.y, home.z };
			session.danger = 0;
			if (action == "hold" || action == "retreat") {
				brainPreviousChase[guid] = bot->getPlayer()->chaseMode;
				bot->getPlayer()->setChaseMode(false);
				bot->getPlayer()->setFollowCreature(nullptr);
				bot->getPlayer()->stopWalk();
			}
			++session.generation;
			if (!bot->getPlayer()->getParty() && brain_->autonomous == guid) {
				bot->getPlayer()->stopWalk();
				bot->getPlayer()->listWalkDir.clear();
				bot->getPlayer()->stopEventWalk();
				bot->hasWalkTarget = false;
				if (action == "hunt") bot->huntIgnoredMonsters.clear();
			}
			if (action == "hunt") {
				brainCombat[guid] = {};
				session.script = static_cast<uint32_t>(std::stoul(candidate.substr(5)));
				activeHunts_[session.script] = guid;
				for (const auto &script : huntScripts_) {
					if (script.id == session.script && !script.spawnGroup.empty()) {
						activeSpawnGroups_[script.spawnGroup] = guid;
					}
				}
			}
			if (action == "resupply") {
				session.potions = brainPotions(bot->getPlayer());
				session.supplyStep = ApproachingShop;
				session.lastMove = 0;
			}
			if (action == "hunt" || action == "resupply" || action == "retreat" || action == "follow") {
				// Only a newly accepted navigation intent gets a fresh per-bot attempt.
				// Global portal quarantine and the wide-search CPU cooldown remain intact.
				plannerReplan(*bot, bot->getPlayer());
				s_fcConsecutiveFailures.erase(guid);
			}
			auto outcome = brainOutcome(brain_->world, guid, id, "accepted", "objective_started");
			rememberOutcome(session, id, outcome);
			brain_->channel->send(outcome);
		} catch (const std::exception &) {
			// Malformed local messages never escape into the dispatcher.
		}
	}
	brain_->flushTelemetry();
	brain_->sendDeliveryStatus();
	if (brainTickMicroseconds.size() >= 256) {
		brainTickMicroseconds.pop_front();
	}
	brainTickMicroseconds.push_back(std::chrono::duration<double, std::micro>(std::chrono::steady_clock::now() - processingStarted).count());
}

bool BotEngine::brainSafetyPause(BotState &bot) {
	if (!brainOwns(bot.guid)) return false;
	auto &session = brain_->sessions[bot.guid];
	auto player = bot.getPlayer();
	if (!player || session.actionId.empty() || session.action != "hunt") return false;
	const auto at = player->getPosition();
	const bool ready = botbrain::partyReady(brainPartyStatus(player), { at.x, at.y, at.z });
	if (!ready) {
		if (!brainPreviousChase.count(bot.guid)) brainPreviousChase[bot.guid] = player->chaseMode;
		player->setChaseMode(false);
		player->setFollowCreature(nullptr);
		player->listWalkDir.clear();
		player->stopEventWalk();
		return true;
	}
	if (auto previous = brainPreviousChase.find(bot.guid); previous != brainPreviousChase.end()) {
		player->setChaseMode(previous->second);
		brainPreviousChase.erase(previous);
	}
	return false;
}

bool BotEngine::brainPartyMove(BotState &bot, const Position &leaderPosition) {
	if (!brainOwns(bot.guid)) {
		return false;
	}
	if (brainSafetyPause(bot)) return true;
	auto &session = brain_->sessions[bot.guid];
	if (session.actionId.empty()) {
		return false;
	}
	auto player = bot.getPlayer();
	const auto now = botMonoMs();
	if (session.action == "hold") {
		player->setChaseMode(false);
		player->setFollowCreature(nullptr);
		player->listWalkDir.clear();
		player->stopEventWalk();
		return true;
	}
	// Autonomous goals bypass doIdle, including its walk-stall watchdog. Observe
	// the queue before the wait gates below so a blocked step can be replanned.
	if (!player->listWalkDir.empty() && plannerWalkBlocked(bot, player)) {
		castLog(bot, "BRAIN: blocked walk; replanning route");
		plannerReplan(bot, player);
	}
	if (session.action == "follow" || session.action == "retreat") {
		if (bot.currentPos.z == leaderPosition.z && Position::getDiagonalDistance(bot.currentPos, leaderPosition) <= 3
		    && now - session.started >= 5000) {
			finishBrain(bot, "completed", "party_rejoined");
			return true;
		}
		if (!player->listWalkDir.empty() || bot.pendingWalkPauseEventId != 0) {
			return true;
		}
		if (!player->getParty() && bot.guid == brain_->autonomous) {
			if (now - session.lastMove >= 500) {
				session.lastMove = now;
				if (!planScopedWalk(bot, leaderPosition, 2)) finishBrain(bot, "failed", "return_route_unavailable");
			}
		} else if (bot.currentPos.z != leaderPosition.z) {
			auto leader = player->getParty() ? player->getParty()->getLeader() : nullptr;
			if (!leader || !tryFollowLeaderTrail(bot, leader)) {
				finishBrain(bot, "failed", "return_route_unavailable");
			}
		} else if (now - session.lastMove >= 500) {
			session.lastMove = now;
			goToWithDoors(bot, leaderPosition, 2);
		}
		return true;
	}
	if (session.action == "resupply") {
		if (session.supplyStep == ReturningToParty) {
			if (bot.currentPos.z == leaderPosition.z && Position::getDiagonalDistance(bot.currentPos, leaderPosition) <= 3) {
				finishBrain(bot, "completed", "supplies_bought_and_party_rejoined");
				return false;
			}
			if (!player->listWalkDir.empty() || bot.pendingWalkPauseEventId != 0) {
				return true;
			}
			if (bot.currentPos.z != leaderPosition.z) {
				finishBrain(bot, "failed", "return_route_unavailable");
			} else if (now - session.lastMove >= 500) {
				session.lastMove = now;
				if (!planScopedWalk(bot, leaderPosition, 2)) {
					finishBrain(bot, "failed", "return_route_unavailable");
				}
			}
			return true;
		}
		auto npc = brainShop(bot);
		if (!npc) {
			finishBrain(bot, "failed", "potion_shop_unavailable");
			return false;
		}
		if (!npc->canInteract(bot.currentPos, 3)) {
			// Normal walks may deliberately pause before their first step. Replacing
			// the queued walk every publication interval can postpone it forever.
			if (!player->listWalkDir.empty() || bot.pendingWalkPauseEventId != 0) {
				return true;
			}
			if (now - session.lastMove >= 500) {
				session.lastMove = now;
				// A walkable authored stand may be behind the shop counter. Search
				// for any reachable tile in the NPC's actual interaction range instead.
				const auto shopPosition = npc->getPosition();
				bool routed = goToWithDoors(bot, shopPosition, 3);
				if (!routed) {
					// The wide planner needs a walkable endpoint; the NPC's own
					// tile (or an authored stand behind its counter) may be blocked.
					// Try a bounded ring inside the actual interaction range.
					const std::array<std::pair<int, int>, 8> offsets {{ { 0, -3 }, { 3, 0 }, { 0, 3 }, { -3, 0 }, { 3, -3 }, { 3, 3 }, { -3, 3 }, { -3, -3 } }};
					for (const auto &[dx, dy] : offsets) {
						const Position stand(shopPosition.x + dx, shopPosition.y + dy, shopPosition.z);
						if (g_game().map.canWalkTo(player, stand) && planScopedWalk(bot, stand, 0)) {
							routed = true;
							break;
						}
					}
				}
				if (routed) session.skipped = 0;
				else if (++session.skipped >= 12) finishBrain(bot, "failed", "shop_route_unavailable");
			}
			return true;
		}
		if (session.supplyStep == ApproachingShop) {
			g_game().internalCreatureSay(player, TALKTYPE_SAY, "hi", false);
			session.supplyStep = WaitingForGreeting;
			session.lastMove = now;
			return true;
		}
		if (now - session.lastMove < 1500) {
			return true;
		}
		if (session.supplyStep == WaitingForGreeting) {
			uint64_t remaining = std::min<uint64_t>(30000, player->getMoney() + player->getBankBalance());
			for (const auto &item : brainSupplyItems(player, npc)) {
				const uint32_t current = player->getItemTypeCount(item.itemId);
				const uint32_t desired = current < 20 ? 20 - current : 0;
				const uint16_t amount = static_cast<uint16_t>(std::min<uint64_t>(desired, remaining / item.itemBuyPrice));
				if (amount) {
					npc->onPlayerBuyItem(player, item.itemId, 1, amount, false, false);
					remaining -= amount * item.itemBuyPrice;
				}
			}
			session.supplyStep = VerifyingPurchase;
			session.lastMove = now;
			return true;
		}
		const auto purchased = brainSupplyItems(player, npc);
		const bool stocked = !purchased.empty() && std::all_of(purchased.begin(), purchased.end(), [&](const auto &item) { return player->getItemTypeCount(item.itemId) >= 20; });
		if (stocked && brainPotions(player) > session.potions) {
			if (!player->getParty() && bot.guid == brain_->autonomous) {
				finishBrain(bot, "completed", "supplies_bought");
				return true;
			}
			session.supplyStep = ReturningToParty;
		} else {
			finishBrain(bot, "failed", "purchase_incomplete_or_insufficient_funds");
		}
		return true;
	}
	if (session.action != "hunt") {
		return false;
	}
	// Keep the guide inside the human's viewport so ordinary client following
	// does not lose its target before the cohesion guard pauses the route.
	if (player->getParty() && (Position::getDiagonalDistance(bot.currentPos, leaderPosition) > 6 || bot.currentPos.z != leaderPosition.z)) {
		player->listWalkDir.clear();
		player->stopEventWalk();
		return true;
	}
	if (!player->listWalkDir.empty() || bot.pendingWalkPauseEventId != 0) {
		return true;
	}
	if (now - session.lastMove < 500) {
		return true;
	}
	session.lastMove = now;
	for (const auto &script : huntScripts_) {
		if (script.id != session.script) {
			continue;
		}
		const bool outbound = session.waypoint < script.travelToWaypoints.size();
		const auto &waypoints = outbound ? script.travelToWaypoints : script.patrolWaypoints;
		size_t index = outbound ? session.waypoint : session.waypoint - script.travelToWaypoints.size();
		if (index >= waypoints.size()) {
			index = 0;
		}
		// Authored travel can end on a closed shovel hole. Reaching that tile
		// does not mean the transition happened: the patrol may still be below us.
		// The generic follower skips mismatched floors, so let the portal planner
		// execute the tool/stair transition without consuming this waypoint.
		// Walk-on portals must reach the follower first: a different z can be
		// the successful arrival it is waiting to acknowledge, not a detour.
		if (bot.currentPos.z != waypoints[index].pos.z && !waypoints[index].isWalkOnFc) {
			if (!planScopedWalk(bot, waypoints[index].pos, 1)) {
				finishBrain(bot, "failed", "floor_route_unavailable");
			}
			return true;
		}
		clearPlannerWalk(bot.guid);
		WaypointFollowConfig config;
		config.logPrefix = "BRAIN";
		auto result = followWaypoints(bot, waypoints, index, session.skipped, config);
		session.waypoint = outbound ? index : script.travelToWaypoints.size() + index;
		if (result.aborted) {
			finishBrain(bot, "failed", "route_unavailable");

		}
		return true;
	}
	finishBrain(bot, "failed", "hunt_removed");
	return false;
}
