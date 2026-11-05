// QA-only native adapter. Never linked into Canary or normal runtime images.
#include "pch.hpp"
#include "creatures/players/bot/bot_engine_loader.hpp"
#include "creatures/players/player.hpp"
#include "creatures/players/grouping/party.hpp"
#include "game/game.hpp"
#include "server/network/protocol/protocolgame.hpp"
#include "server/network/connection/connection.hpp"
#include "utils/tools.hpp"
#include <dlfcn.h>
#include <filesystem>
#include <nlohmann/json.hpp>
extern "C" {
#include <lua.h>
#include <lauxlib.h>
}
namespace {
	template <class Tag, typename Tag::Type Member>
	struct Access {
		friend typename Tag::Type member(Tag) {
			return Member;
		}
	};
	struct Socket {
		using Type = asio::ip::tcp::socket Connection::*;
		friend Type member(Socket);
	};
	struct WalkQueue {
		using Type = std::vector<Direction> Creature::*;
		friend Type member(WalkQueue);
	};
	struct ReadTimer {
		using Type = asio::high_resolution_timer Connection::*;
		friend Type member(ReadTimer);
	};
	template struct Access<Socket, &Connection::socket>;
	template struct Access<WalkQueue, &Creature::listWalkDir>;
	template struct Access<ReadTimer, &Connection::readTimer>;
	asio::io_context io;
	std::vector<std::shared_ptr<ProtocolGame>> clients;
	std::vector<Connection_ptr> connections;
	std::vector<std::shared_ptr<asio::ip::tcp::socket>> peers;
	std::vector<std::shared_ptr<Player>> humans;
	std::shared_ptr<ProtocolGame> client() {
		auto connection = std::make_shared<Connection>(io, nullptr);
		asio::ip::tcp::acceptor acceptor(io, { asio::ip::tcp::v4(), 0 });
		auto peer = std::make_shared<asio::ip::tcp::socket>(io);
		peer->connect({ asio::ip::make_address("127.0.0.1"), acceptor.local_endpoint().port() });
		acceptor.accept(connection.get()->*member(Socket {}));
		connections.push_back(connection);
		peers.push_back(peer);
		auto result = std::make_shared<ProtocolGame>(connection);
		connection->accept(result);
		// Direct native login bypasses the wire handshake. Disable only its unread
		// header timer; explicit Connection::close still exercises real disconnect.
		(connection.get()->*member(ReadTimer {})).cancel();
		clients.push_back(result);
		return result;
	}
	int run(lua_State* L) {
		const std::string op = luaL_checkstring(L, 1);
		auto &engine = BotEngineLoader::getInstance().getEngine();
		if (op == "login") {
			for (const auto &name : { "Party Leader A", "Party Leader B" }) {
				auto protocol = client();
				protocol->login(name, std::string(name).ends_with("A") ? 64999 : 64998, CLIENTOS_LINUX);
				auto player = g_game().getPlayerByName(name);
				if (!player || player->isBotPlayer()) {
					return luaL_error(L, "normal login fixture failed");
				}
				humans.push_back(player);
			}
		} else if (op == "keepalive") {
			// Deliberately call the same pong and idle-reset handlers as a live client.
			// This is session scaffolding, not protocol/authentication acceptance.
			for (const auto &p : humans) {
				if (!p->isRemoved()) {
					p->receivePing();
					p->resetIdleTime();
				}
			}
			io.restart();
			io.poll();
			for (const auto &peer : peers) {
				asio::error_code ec;
				const auto available = peer->available(ec);
				if (!ec && available) {
					std::string data(available, '\0');
					peer->read_some(asio::buffer(data), ec);
				}
			}
		} else if (op == "invite") {
			if (humans.size() != 2) {
				return luaL_error(L, "login first");
			}
			g_game().playerInviteToParty(humans[0]->getID(), humans[1]->getID());
			g_game().playerJoinParty(humans[1]->getID(), humans[0]->getID());
			for (auto guid : { 65001U, 65003U, 65004U }) {
				auto* bot = engine.getBotState(guid);
				if (!bot || !bot->getPlayer()) {
					return luaL_error(L, "awake bots required");
				}
				g_game().playerInviteToParty(humans[0]->getID(), bot->getPlayer()->getID());
			}
		} else if (op == "transfer") {
			g_game().playerPassPartyLeadership(humans[0]->getID(), humans[1]->getID());
		} else if (op == "dropB") {
			clients[1]->getConnection()->close(true);
		} else if (op == "dropA") {
			clients[0]->getConnection()->close(true);
		} else if (op == "order") {
			const auto who = luaL_checkinteger(L, 2);
			const std::string target = luaL_checkstring(L, 3), text = luaL_checkstring(L, 4);
			g_game().playerSay(humans.at(who)->getID(), 0, TALKTYPE_PRIVATE_TO, target, text);
		} else if (op == "town") {
			for (auto guid : { 65001U, 65003U, 65004U }) {
				auto* bot = engine.getBotState(guid);
				bot->townId = 8;
				bot->townName = "Thais";
			}
		} else if (op == "timings") {
			// The QA builder adds this export to its private library copy only.
			for (const auto &p : std::filesystem::directory_iterator("/canary")) {
				if (p.path().filename().string().starts_with("libbot_engine.so.reload-")) {
					auto handle = dlopen((p.path() / "engine.so").c_str(), RTLD_NOW | RTLD_NOLOAD);
					if (!handle) {
						continue;
					}
					auto function = reinterpret_cast<const char* (*)()>(dlsym(handle, "canaryPartyQaTimings"));
					if (function) {
						std::string result = function();
						dlclose(handle);
						lua_pushlstring(L, result.data(), result.size());
						return 1;
					}
					dlclose(handle);
				}
			}
			return luaL_error(L, "QA timing export missing");
		} else if (op == "inspect") {
			nlohmann::json rows = nlohmann::json::array();
			for (auto guid : { 65001U, 65003U, 65004U }) {
				auto* bot = engine.getBotState(guid);
				auto p = bot ? bot->getPlayer() : nullptr;
				if (!p) {
					rows.push_back({ { "guid", guid }, { "unavailable", true } });
					continue;
				}
				const auto pos = p->getPosition();
				auto party = p->getParty();
				rows.push_back({ { "guid", guid }, { "state", static_cast<int>(bot->state) }, { "paused", bot->aiPaused }, { "hp", p->getHealth() }, { "mana", p->getMana() }, { "xp", p->getExperience() }, { "position", { pos.x, pos.y, pos.z } }, { "walk_queue", (p.get()->*member(WalkQueue {})).size() }, { "leader", party ? party->getLeader()->getGUID() : 0 }, { "members", party ? party->getMemberCount() + 1 : 0 }, { "target", p->getAttackedCreature() ? p->getAttackedCreature()->getID() : 0 } });
			}
			std::string value = rows.dump();
			lua_pushlstring(L, value.data(), value.size());
			return 1;
		} else {
			return luaL_error(L, "unknown party fixture operation");
		}
		lua_pushboolean(L, true);
		return 1;
	}
}
extern "C" int luaopen_party_acceptance(lua_State* L) {
	lua_pushcfunction(L, run);
	return 1;
}
