# Network

## Overview
Intermediate architectural boundary grouping all network transport, packet buffer serialization, client-server wire protocols, and outbound HTTP webhook subsystems for the Canary server.

## Subdirectories & Boundaries
- [connection](./connection/README.md): Asynchronous ASIO TCP socket management, connection lifecycle, rate limiting, and timeout handling.
- [message](./message/README.md): Binary network packet buffers (`NetworkMessage`, `OutputMessage`) and lock-free pooled auto-send scheduling (`OutputMessagePool`).
- [protocol](./protocol/README.md): Cryptographic framing (RSA, XTEA, checksums, zlib compression) and protocol handlers (`Protocol`, `ProtocolGame`, `ProtocolLogin`, `ProtocolStatus`), including cast viewer and cast operator support.
- [webhook](./webhook/README.md): Asynchronous libcurl-based HTTP POST webhook dispatcher (`Webhook`, `WebhookTask`).

## Interface
- Connection management: `ConnectionManager` (`[connection/connection.hpp:ConnectionManager]`) and `Connection` (`[connection/connection.hpp:Connection]`).
- Message serialization and pooling: `NetworkMessage` (`[message/networkmessage.hpp:NetworkMessage]`), `OutputMessage` (`[message/outputmessage.hpp:OutputMessage]`), and `OutputMessagePool` (`[message/outputmessage.hpp:OutputMessagePool]`).
- Wire protocols: `Protocol` (`[protocol/protocol.hpp:Protocol]`), `ProtocolGame` (`[protocol/protocolgame.hpp:ProtocolGame]`), `ProtocolLogin` (`[protocol/protocollogin.hpp:ProtocolLogin]`), and `ProtocolStatus` (`[protocol/protocolstatus.hpp:ProtocolStatus]`).
- Outbound webhooks: `Webhook` (`[webhook/webhook.hpp:Webhook]`), `WebhookTask` (`[webhook/webhook.hpp:WebhookTask]`), and `g_webhook` (`[webhook/webhook.hpp:g_webhook]`).

## Invariants
- All active client TCP connections are owned and tracked via `ConnectionManager` and synchronized per-connection with `Connection::connectionLock` (`[connection/connection.hpp:Connection::connectionLock]`).
- `NetworkMessage` reserves `INITIAL_BUFFER_POSITION` (7 bytes) for headers and enforces buffer bounds (`MAX_BODY_LENGTH`, `INPUTMESSAGE_MAXSIZE`) across read/write operations (`[message/networkmessage.hpp:NetworkMessage::INITIAL_BUFFER_POSITION]`, `[connection/connection.cpp:Connection::parseHeader]`).
- Encrypted protocol streams require 8-byte aligned XTEA blocks, valid Adler32 or sequence checksums, and dispatch game logic onto `g_dispatcher()` (`[protocol/protocol.cpp:Protocol::XTEA_decrypt]`, `[protocol/protocol.cpp:Protocol::onRecvMessage]`).
- Webhook queue mutations are serialized by `Webhook::taskLock` (`[webhook/webhook.hpp:Webhook::taskLock]`).

## Side Effects
- Performs asynchronous TCP socket I/O and timer scheduling via ASIO (`[connection/connection.cpp:Connection::acceptInternal]`, `[connection/connection.cpp:Connection::internalSend]`) and outbound HTTPS POST calls via `libcurl` (`[webhook/webhook.cpp:Webhook::sendRequest]`).
- Allocates pooled `OutputMessage` buffers (`[message/outputmessage.cpp:OutputMessagePool::getOutputMessage]`) and schedules packet processing, login/logout, and auto-send tasks onto `g_dispatcher()` and `ThreadPool` (`[protocol/protocol.cpp:Protocol::sendRecvMessageCallback]`, `[message/outputmessage.cpp:OutputMessagePool::scheduleSendAll]`, `[webhook/webhook.cpp:Webhook::run]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
