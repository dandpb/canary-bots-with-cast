# Cast Viewer Sink

## Overview
Defines the `CastViewerSink` interface (`src/creatures/players/cast/cast_viewer_sink.hpp`), decoupling `Player` network packet fan-out from concrete `ProtocolGame` sessions so live cast streams can broadcast to multiple viewers without circular header dependencies.

## Interface
- `CastViewerSink` (`[cast_viewer_sink.hpp:CastViewerSink]`): Abstract interface implemented by `ProtocolGame` exposing viewer lifecycle and broadcast methods (`isConnectionExpired`, `getIP`, `getViewerName`, `setViewerName`, `getViewerId`, `setViewerId`, `disconnectClient`, `releaseCastSession`, `sendPacket`, `sendViewerChat`, `sendViewerChannelEvent`, `syncOpenContainers`).

## Invariants
- `CastViewerSink` is a pure abstract interface with no state; concrete implementations must safely handle viewer packet forwarding and session release when the broadcaster logs out or stops casting (`[cast_viewer_sink.hpp:CastViewerSink]`).

## Side Effects
- None directly (header-only interface; concrete implementations perform network I/O and session teardown).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
