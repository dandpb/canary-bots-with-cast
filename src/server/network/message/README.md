# Message

## Overview
Provides binary packet serialization, deserialization, header framing, and pooled outgoing message buffering for the network layer. `NetworkMessage` implements fixed-buffer read/write primitives (primitives, strings, positions, variable-length item counts), while `OutputMessage` and `OutputMessagePool` manage outgoing packet headers, XTEA padding, lock-free pooled allocation, and periodic auto-sending on the dispatcher thread.

## Interface
- `NetworkMessage` (`[networkmessage.hpp:NetworkMessage]`): Base packet buffer class providing read primitives (`decodeHeader()`, `getByte()`, `getPreviousByte()`, `get<T>()`, `getString()`, `getPosition()`, `getDouble()`, `skipBytes()`) and write primitives (`addByte()`, `add<T>()`, `addBytes()`, `addPaddingBytes()`, `addString()`, `addDouble()`, `addPosition()`, `writeCount()`, `append()`).
- `OutputMessage` (`[outputmessage.hpp:OutputMessage]`): Non-copyable subclass of `NetworkMessage` for outgoing packets, exposing `getOutputBuffer()`, `writePaddingAmount()`, `writeMessageLength()`, `addCryptoHeader()`, and `append()`.
- `OutputMessagePool` (`[outputmessage.hpp:OutputMessagePool]`): Singleton pool and auto-send scheduler (`getInstance()`, `getOutputMessage()`, `sendAll()`, `scheduleSendAll()`, `addProtocolToAutosend()`, `removeProtocolFromAutosend()`).

## Invariants
- `NetworkMessage::INITIAL_BUFFER_POSITION` is `7` (`[networkmessage.hpp:NetworkMessage::INITIAL_BUFFER_POSITION]`), reserving 7 leading bytes in the `NETWORKMESSAGE_MAXSIZE` buffer for unencrypted size (2 bytes), checksum (4 bytes), and padding size (1 byte).
- `NetworkMessage::get<T>()` and `NetworkMessage::add<T>()` enforce at compile time that `T` is trivially copyable and not `double` (`[networkmessage.hpp:NetworkMessage::get]`, `[networkmessage.hpp:NetworkMessage::add]`).
- Buffer reads verify `canRead(size)` (`size <= (info.length - (info.position - INITIAL_BUFFER_POSITION))`) (`[networkmessage.cpp:NetworkMessage::canRead]`), and writes verify `canAdd(size)` (`(size + info.position) < MAX_BODY_LENGTH`) (`[networkmessage.cpp:NetworkMessage::canAdd]`).
- `OutputMessage::add_header<T>()` asserts and requires `outputBufferStart >= sizeof(T)` before decrementing `outputBufferStart` to prepend header bytes (`[outputmessage.hpp:OutputMessage::add_header]`).
- `NetworkMessage::writeCount(uint32_t)` only encodes values `< 0x40000000` (30-bit maximum) into 1, 2, or 4 bytes, returning `false` on larger counts or insufficient buffer capacity (`[networkmessage.cpp:NetworkMessage::writeCount]`).

## Side Effects
- `OutputMessagePool::getOutputMessage()` allocates `OutputMessage` instances using `LockfreePoolingAllocator<OutputMessage, OUTPUTMESSAGE_FREE_LIST_CAPACITY>` (`[outputmessage.cpp:OutputMessagePool::getOutputMessage]`).
- `OutputMessagePool::scheduleSendAll()` and `OutputMessagePool::sendAll()` schedule recurring 10ms (`OUTPUTMESSAGE_AUTOSEND_DELAY`) events on `g_dispatcher()` and flush buffered messages across registered `bufferedProtocols` (`[outputmessage.cpp:OutputMessagePool::scheduleSendAll]`, `[outputmessage.cpp:OutputMessagePool::sendAll]`).
- Mutates internal buffer state (`buffer`, `info.position`, `info.length`, `outputBufferStart`) and logs buffer overflows or out-of-bounds reads via `g_logger()` (`[networkmessage.cpp:NetworkMessage::getByte]`, `[networkmessage.cpp:NetworkMessage::addString]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
