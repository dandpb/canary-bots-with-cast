// Test-only Lua module for the labelled disposable lifecycle server. Not linked
// into the product or copied into normal runtime images.
#include "pch.hpp"
#include "creatures/players/bot/bot_engine_loader.hpp"
#include "creatures/players/player.hpp"
#include "game/game.hpp"
#include "io/iologindata.hpp"
#include "server/network/protocol/protocolgame.hpp"
#include "server/network/protocol/protocollogin.hpp"
#include "server/network/connection/connection.hpp"
#include "game/scheduling/save_manager.hpp"
#include "game/scheduling/dispatcher.hpp"
extern "C" {
#include <lua.h>
#include <lauxlib.h>
}

namespace {
// Test-only member access: invoke the real private release path without exposing
// control hooks in the product or constructing a fake implementation of it.
template<class Tag, typename Tag::Type Member> struct Access {
	friend typename Tag::Type member(Tag) { return Member; }
};
struct Release { using Type = void (Protocol::*)(); friend Type member(Release); };
struct Client { using Type = std::shared_ptr<ProtocolGame> Player::*; friend Type member(Client); };
struct Character { using Type = std::shared_ptr<Player> ProtocolGame::*; friend Type member(Character); };
struct ViewerCount { using Type = uint32_t (Player::*)() const; friend Type member(ViewerCount); };
struct Socket { using Type = asio::ip::tcp::socket Connection::*; friend Type member(Socket); };
struct CharacterList { using Type = void (ProtocolLogin::*)(const std::string&, const std::string&) const; friend Type member(CharacterList); };
template struct Access<Release, &Protocol::release>;
template struct Access<Client, &Player::client>;
template struct Access<Character, &ProtocolGame::player>;
template struct Access<ViewerCount, &Player::getRealCastViewerCount>;
template struct Access<Socket, &Connection::socket>;
template struct Access<CharacterList, &ProtocolLogin::getCharacterList>;
std::shared_ptr<ProtocolGame> caster, oldCaster, viewer;
std::shared_ptr<Player> human;
asio::io_context testIo;
std::vector<Connection_ptr> transports;
std::vector<std::shared_ptr<asio::ip::tcp::socket>> peers;
std::shared_ptr<ProtocolGame> protocol() {
	// Connected loopback sockets keep the real connection-loss guard meaningful.
	// The private test I/O context is not pumped: packet contents are tested by
	// the external login/status probes, this bridge tests lifecycle transitions.
	auto connection = std::make_shared<Connection>(testIo, nullptr);
	asio::ip::tcp::acceptor acceptor(testIo, {asio::ip::tcp::v4(), 0});
	auto peer = std::make_shared<asio::ip::tcp::socket>(testIo);
	peer->connect({asio::ip::make_address("127.0.0.1"), acceptor.local_endpoint().port()});
	acceptor.accept(connection.get()->*member(Socket{}));
	transports.push_back(connection);
	peers.push_back(peer);
	auto result = std::make_shared<ProtocolGame>(connection);
	connection->accept(result);
	return result;
}
std::atomic<int> fired {0};
std::atomic<int> destroyed {0};
struct Marker { ~Marker() { ++destroyed; } };

IBotEngine* engine(lua_State* state) {
	auto* result = BotEngineLoader::getInstance().tryGetEngine();
	if (!result) luaL_error(state, "engine unavailable");
	return result;
}

int setVirtual(lua_State* state) {
	auto* bot = engine(state)->getBotState(luaL_checkinteger(state, 1));
	if (!bot || !bot->hibernated) return luaL_error(state, "hibernated fixture required");
	bot->currentPos = Position(luaL_checkinteger(state, 2), luaL_checkinteger(state, 3), luaL_checkinteger(state, 4));
	lua_pushboolean(state, true);
	return 1;
}

int unregister(lua_State* state) {
	engine(state)->unregisterBot(luaL_checkinteger(state, 1));
	lua_pushboolean(state, true);
	return 1;
}

int pending(lua_State* state) {
	lua_pushboolean(state, bool(g_saveManager().getPendingBotPlayer(luaL_checkinteger(state, 1))));
	return 1;
}

int armPause(lua_State* state) {
	auto* bot = engine(state)->getBotState(luaL_checkinteger(state, 1));
	if (!bot) return luaL_error(state, "registered fixture required");
	if (bot->pendingWalkPauseEventId) g_dispatcher().stopEvent(bot->pendingWalkPauseEventId);
	auto marker = std::make_shared<Marker>();
	bot->pendingWalkPauseEventId = g_dispatcher().scheduleEvent(luaL_checkinteger(state, 2),
		[marker] { ++fired; }, "qa_pending_walk");
	lua_pushboolean(state, true);
	return 1;
}

int counts(lua_State* state) {
	lua_pushinteger(state, fired.load());
	lua_pushinteger(state, destroyed.load());
	return 2;
}

int roster(lua_State* state) {
	const auto snapshot = engine(state)->captureReloadState();
	lua_newtable(state);
	int index = 0;
	for (const auto& entry : snapshot.entries) {
		lua_newtable(state);
		lua_pushinteger(state, entry.guid); lua_setfield(state, -2, "guid");
		lua_pushboolean(state, entry.active); lua_setfield(state, -2, "active");
		lua_pushboolean(state, entry.hibernated); lua_setfield(state, -2, "hibernated");
		lua_pushboolean(state, entry.aiPaused); lua_setfield(state, -2, "paused");
		lua_pushinteger(state, entry.player ? entry.player->getID() : 0); lua_setfield(state, -2, "runtimeId");
		lua_pushinteger(state, entry.position.x); lua_setfield(state, -2, "x");
		lua_pushinteger(state, entry.position.y); lua_setfield(state, -2, "y");
		lua_pushinteger(state, entry.player ? (entry.player.get()->*member(ViewerCount{}))() : 0); lua_setfield(state, -2, "viewers");
		lua_rawseti(state, -2, ++index);
	}
	return 1;
}

int cast(lua_State* state) {
	const std::string action = luaL_checkstring(state, 1);
	if (action == "botState") {
		if (!BotEngineLoader::getInstance().isLoaded()) return luaL_error(state, "engine unavailable");
		auto& engine = BotEngineLoader::getInstance().getEngine();
		auto* bot = engine.getBotState(65001);
		const auto player = bot ? (bot->hibernated ? engine.getHibernatedBotPlayer(65001) : bot->playerRef.lock()) : nullptr;
		if (!player) return luaL_error(state, "loaded bot fixture required");
		lua_newtable(state);
		lua_pushinteger(state, player->getID()); lua_setfield(state, -2, "runtimeId");
		lua_pushboolean(state, bot->hibernated); lua_setfield(state, -2, "hibernated");
		lua_pushinteger(state, (player.get()->*member(ViewerCount{}))()); lua_setfield(state, -2, "viewers");
		return 1;
	}
	if (action == "watchBot") {
		viewer = protocol();
		viewer->castViewerLogin("Grizzle Alyronia");
		lua_pushboolean(state, true);
		return 1;
	}
	if (action == "list") {
		auto connection = std::make_shared<Connection>(testIo, nullptr);
		asio::ip::tcp::acceptor acceptor(testIo, {asio::ip::tcp::v4(), 0});
		asio::ip::tcp::socket peer(testIo);
		peer.connect({asio::ip::make_address("127.0.0.1"), acceptor.local_endpoint().port()});
		acceptor.accept(connection.get()->*member(Socket{}));
		auto login = std::make_shared<ProtocolLogin>(connection);
		connection->accept(login);
		(login.get()->*member(CharacterList{}))("@cast", "");
		testIo.restart(); testIo.poll();
		std::string bytes(peer.available(), '\0');
		if (!bytes.empty()) peer.read_some(asio::buffer(bytes));
		std::string hex;
		constexpr auto digits = "0123456789abcdef";
		for (const unsigned char byte : bytes) { hex += digits[byte >> 4]; hex += digits[byte & 15]; }
		lua_pushlstring(state, hex.data(), hex.size());
		connection->close(true);
		return 1;
	}
	if (action == "human") {
		caster = protocol();
		caster->login("Lifecycle Human", 64999, CLIENTOS_LINUX);
		human = g_game().getPlayerByName("Lifecycle Human");
		if (!human || human->isBotPlayer()) return luaL_error(state, "human login failed");
	} else if (!human) return luaL_error(state, "human fixture required");
	else if (action == "on") human->setCastBroadcasting(true);
	else if (action == "off") human->setCastBroadcasting(false);
	else if (action == "view") {
		viewer = protocol();
		viewer->castViewerLogin(human->getName());
	} else if (action == "release") (caster.get()->*member(Release{}))();
	else if (action == "drop") caster->getConnection()->close(true);
	else if (action == "logout") caster->logout(false, true);
	else if (action == "order") g_game().playerSay(human->getID(), 0, TALKTYPE_PRIVATE_TO,
		"Grizzle Alyronia", luaL_checkstring(state, 2));
	else if (action == "invite") {
		for (const auto& name : {"Grizzle Alyronia", "Sever Heartspear", "Galdon Whitehoof"}) {
			const auto player = g_game().getPlayerByName(name);
			if (!player) return luaL_error(state, "awake companion required");
			g_game().playerInviteToParty(human->getID(), player->getID());
		}
	}
	else if (action == "replace") {
		oldCaster = caster;
		caster = protocol();
		caster.get()->*member(Character{}) = human;
		human.get()->*member(Client{}) = caster;
	} else if (action == "lateRelease") (oldCaster.get()->*member(Release{}))();
	else if (action == "teleport") {
		const auto position = human->getPosition();
		bool moved = false;
		for (int x = -1; x <= 1 && !moved; ++x) for (int y = -1; y <= 1 && !moved; ++y) {
			if (x == 0 && y == 0) continue;
			moved = g_game().internalTeleport(human, Position(position.x + x, position.y + y, position.z), false) == RETURNVALUE_NOERROR;
		}
		if (!moved) return luaL_error(state, "fixture needs an adjacent teleport tile");
		g_game().playerSay(human->getID(), 0, TALKTYPE_SAY, "", "isolated optional engine check");
		g_game().playerSay(human->getID(), 0, TALKTYPE_PRIVATE_TO, "No Such Offline Fixture", "isolated PM check");
	}
	lua_newtable(state);
	lua_pushboolean(state, human->isCastBroadcasting()); lua_setfield(state, -2, "broadcasting");
	lua_pushinteger(state, (human.get()->*member(ViewerCount{}))()); lua_setfield(state, -2, "viewers");
	lua_pushboolean(state, bool(human.get()->*member(Client{}))); lua_setfield(state, -2, "connected");
	return 1;
}
}

extern "C" int luaopen_lifecycle_bridge(lua_State* state) {
	lua_newtable(state);
	for (const auto& [name, function] : std::initializer_list<std::pair<const char*, lua_CFunction>> {
		{"setVirtual", setVirtual}, {"unregister", unregister}, {"pending", pending},
		{"armPause", armPause}, {"counts", counts}, {"roster", roster}, {"cast", cast}}) {
		lua_pushcfunction(state, function);
		lua_setfield(state, -2, name);
	}
	return 1;
}
