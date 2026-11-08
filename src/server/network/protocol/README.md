# Protocol

## Overview
Implements the wire protocols for client-server communication, cryptographic framing (RSA, XTEA, Adler32/sequence checksums, zlib deflate compression), login authentication, server status queries, and in-game world synchronization. Includes support for live cast viewing (`@cast` / `@livestream`), hibernated bot auto-wake on cast connect, and authenticated cast operator `/cavebot` command execution.

## Interface
- `Protocol` (`[protocol.hpp:Protocol]`): Base protocol class managing `Connection` attachment, packet framing (`onSendMessage()`, `onRecvMessage()`, `sendRecvMessageCallback()`, `onRecvFirstMessage()`, `parsePacket()`), XTEA encryption (`enableXTEAEncryption()`, `setXTEAKey()`, `XTEA_encrypt()`, `XTEA_decrypt()`), RSA decryption (`RSA_decrypt()`), and zlib payload compression (`compression()`).
- `ProtocolGame` (`[protocolgame.hpp:ProtocolGame]`): Gameworld protocol handler (`PROTOCOL_IDENTIFIER = 0`, `SERVER_SENDS_FIRST = true`) managing player login/logout (`login()`, `logout()`), cast viewer sessions (`castViewerLogin()`, `sendCastViewerInit()`, `executeCastOperatorCommand()`), client packet parsing (`parsePacket()`, `parsePacketFromDispatcher()`), and world state serialization (`AddItem()`, `sendMapDescription()`, `sendStats()`, `sendSkills()`).
- `ProtocolLogin` (`[protocollogin.hpp:ProtocolLogin]`): Login server protocol (`PROTOCOL_IDENTIFIER = 0x01`, `SERVER_SENDS_FIRST = false`) handling account authentication and character list retrieval (`onRecvFirstMessage()`, `getCharacterList()`), including the `@cast` / `@livestream` broadcast list.
- `ProtocolStatus` (`[protocolstatus.hpp:ProtocolStatus]`): Status query protocol (`PROTOCOL_IDENTIFIER = 0xFF`, `SERVER_SENDS_FIRST = false`) serving XML and binary server/player status responses (`onRecvFirstMessage()`, `sendStatusString()`, `sendInfo()`).
- `TextMessage` (`[protocolgame.hpp:TextMessage]`): Value struct representing formatted text/channel messages sent to the client.

## Invariants
- `Protocol::XTEA_decrypt` requires the encrypted payload length (after subtracting header/checksum bytes) to be a multiple of 8 bytes and `innerLength + paddingSize <= msgLength` (`[protocol.cpp:Protocol::XTEA_decrypt]`).
- `Protocol::RSA_decrypt` requires at least 128 remaining bytes in the `NetworkMessage` buffer and verifies the leading decrypted byte is `0` (`[protocol.cpp:Protocol::RSA_decrypt]`).
- `Protocol::compression` only compresses outgoing messages when `checksumMethod == CHECKSUM_METHOD_SEQUENCE`, `outputMessage.getLength() >= 128`, and size does not exceed `NETWORKMESSAGE_MAXSIZE` (`[protocol.cpp:Protocol::onSendMessage]`, `[protocol.cpp:Protocol::compression]`).
- `ProtocolStatus::onRecvFirstMessage` enforces per-IP rate limiting via `ProtocolStatus::ipConnectMap` and `STATUSQUERY_TIMEOUT` for non-local IPs (`[protocolstatus.cpp:ProtocolStatus::onRecvFirstMessage]`).
- Cast operator command execution (`ProtocolGame::executeCastOperatorCommand`) is strictly gated on `m_castOperator == true`, a valid non-removed bot player (`player->isBotPlayer()`), and only dispatches `/cavebot` (`CAST_OPERATOR_TALKACTION`) while RAII-guarding temporary group elevation via `CastOperatorElevation` (`[protocolgame.cpp:ProtocolGame::executeCastOperatorCommand]`, `[protocolgame.cpp:CastOperatorElevation]`).
- `checkCastOperatorPassword` uses constant-time comparison (`constantTimeEquals`) and locks out an IP for 15 minutes (`CAST_OP_LOCKOUT_MS`) after 5 failed attempts (`CAST_OP_MAX_FAILURES`) within 5 minutes (`[protocolgame.cpp:checkCastOperatorPassword]`).

## Side Effects
- Enqueues packet parsing, login, character list queries, and status responses onto `g_dispatcher()` (`[protocol.cpp:Protocol::sendRecvMessageCallback]`, `[protocollogin.cpp:ProtocolLogin::onRecvFirstMessage]`, `[protocolstatus.cpp:ProtocolStatus::onRecvFirstMessage]`, `[protocolgame.cpp:ProtocolGame::onRecvFirstMessage]`).
- `ProtocolGame::login`, `ProtocolGame::logout`, and `ProtocolGame::parsePacketFromDispatcher` mutate global `Game` state (`g_game()`), player state, database records via `IOLoginData`/`IOBan`, chat channels (`g_chat()`), and `OutputMessagePool` auto-send registration (`[protocolgame.cpp:ProtocolGame::login]`, `[protocolgame.cpp:ProtocolGame::logout]`, `[protocolgame.cpp:ProtocolGame::release]`).
- `ProtocolGame::castViewerLogin` can synchronously wake hibernated bots via `BotEngine::wakeBot`, attaches viewers to the watched `Player`, and broadcasts viewer join/leave messages on `CHANNEL_CAST` (`[protocolgame.cpp:ProtocolGame::castViewerLogin]`, `[protocolgame.cpp:ProtocolGame::release]`).
- Maintains thread-local zlib `z_stream` state (`Protocol::ZStream`) for packet deflation (`[protocol.cpp:Protocol::compression]`) and static IP tracking maps (`ProtocolStatus::ipConnectMap`, `g_castOperatorFailures`) (`[protocolstatus.cpp:ProtocolStatus::onRecvFirstMessage]`, `[protocolgame.cpp:checkCastOperatorPassword]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
