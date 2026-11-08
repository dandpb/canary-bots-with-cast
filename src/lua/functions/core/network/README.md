# Core Network Lua Functions

## Overview
Provides Lua bindings for low-level network packet construction/parsing (`NetworkMessage`) and outbound HTTP Discord webhook notifications (`Webhook`).

## Interface
- `CoreNetworkFunctions` (`[core_network_functions.hpp:CoreNetworkFunctions]`) — Aggregator `LuaScriptInterface` subclass that initializes `NetworkMessageFunctions` and `WebhookFunctions` via `CoreNetworkFunctions::init(lua_State* L)` (`[core_network_functions.hpp:CoreNetworkFunctions::init]`).
- `NetworkMessageFunctions` (`[network_message_functions.hpp:NetworkMessageFunctions]`) — Registers the `NetworkMessage` shared Lua class (`getByte`, `getU16`, `getU32`, `getU64`, `getString`, `getPosition`, `addByte`, `addU16`, `addU32`, `addU64`, `add8`, `add16`, `add32`, `add64`, `addString`, `addPosition`, `addDouble`, `addItem`, `reset`, `skipBytes`, `sendToPlayer`, `delete`) via `NetworkMessageFunctions::init(lua_State* L)` (`[network_message_functions.cpp:NetworkMessageFunctions::init]`).
- `WebhookFunctions` (`[webhook_functions.hpp:WebhookFunctions]`) — Registers the `Webhook` Lua table (`sendMessage`) via `WebhookFunctions::init(lua_State* L)` (`[webhook_functions.cpp:WebhookFunctions::init]`).

## Invariants
- `NetworkMessageFunctions::luaNetworkMessageAddItem` requires valid `Item` and `Player` userdata and a non-null `player->client` (`ProtocolGame`) to serialize the item (`[network_message_functions.cpp:NetworkMessageFunctions::luaNetworkMessageAddItem]`).
- `NetworkMessageFunctions::luaNetworkMessageSendToPlayer` requires a valid `NetworkMessage` userdata and a valid online `Player` (`[network_message_functions.cpp:NetworkMessageFunctions::luaNetworkMessageSendToPlayer]`).

## Side Effects
- Mutates internal buffer state of `NetworkMessage` instances when reading, writing, resetting, or skipping bytes (`[network_message_functions.cpp:NetworkMessageFunctions::luaNetworkMessageAddByte]`, `[network_message_functions.cpp:NetworkMessageFunctions::luaNetworkMessageReset]`).
- Transmits raw network packets to a player's client connection via `player->sendNetworkMessage(*message)` (`[network_message_functions.cpp:NetworkMessageFunctions::luaNetworkMessageSendToPlayer]`).
- Enqueues outbound webhook HTTP payloads via `g_webhook().sendMessage(...)` (`[webhook_functions.cpp:WebhookFunctions::luaWebhookSendMessage]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
