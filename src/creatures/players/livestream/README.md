# Player Livestream Subsystem (`src/creatures/players/livestream`)

## Overview
Implements upstream Canary's built-in player livestreaming subsystem (`LivestreamManager`), managing broadcaster sessions, password protection, viewer chat/moderation (mute/ban/kick/rename), and live packet forwarding to spectator connections.

## Interface
- `LivestreamViewerInfo`, `LivestreamState` (`[livestream.hpp:LivestreamViewerInfo]`, `[livestream.hpp:LivestreamState]`): Viewer identity (`name`, `id`, `ip`) and serializable session state (`description`, `broadcast`, `password`, `names`, `mutes`, `bans`, `kick`).
- `LivestreamManager`, `g_livestream()` (`[livestream.hpp:LivestreamManager]`, `[livestream.hpp:g_livestream]`, `[livestream.cpp:LivestreamManager::getInstance]`): Singleton manager providing session inspection (`isBroadcasting`, `isViewer`, `getCasterForViewer`, `getState`, `getViewerCount`, `getPassword`, `getDescription`, `getBroadcastTimeString`, `getBroadcastingCasters`), lifecycle control (`setInitialState`, `applyState`, `stopBroadcast`), viewer admission and moderation (`canWatch`, `addViewer`, `removeViewer`, `handleChat`), packet mirroring (`broadcastPacket`), and storage synchronization (`updateViewerStorage`).

## Invariants
- Viewer sessions are keyed by caster player GUID (`sessions`) with a reverse index from viewer `ProtocolGame*` (`viewerToCaster`); `getCasterForViewer` resolves the broadcaster through `std::weak_ptr<Player>` (`[livestream.hpp:LivestreamManager::sessions]`, `[livestream.cpp:LivestreamManager::getCasterForViewer]`).
- Viewer names are bounded between `MIN_VIEWER_NAME_LENGTH` (3) and `MAX_VIEWER_NAME_LENGTH` (`NETWORKMESSAGE_PLAYERNAME_MAXLENGTH`), and viewer chat is rate-limited (`MESSAGE_LIMIT = 3` per `MESSAGE_COOLDOWN_MS = 5000` ms) (`[livestream.cpp:MESSAGE_COOLDOWN_MS]`).
- `getBroadcastingCasters` returns only non-removed, actively broadcasting casters sorted descending by viewer count (`[livestream.cpp:LivestreamManager::getBroadcastingCasters]`).

## Side Effects
- Forwards filtered game packets (`broadcastPacket`) and channel events/messages to connected viewer `ProtocolGame` clients (`[livestream.cpp:LivestreamManager::broadcastPacket]`).
- Updates viewer count storage/persistence and broadcaster icons/state via `DatabaseTasks` / `KV` (`[livestream.cpp:LivestreamManager::updateViewerStorage]`).

## Verification
- See the [C++ build and test guide](../../../../tests/README.md#running-tests).
