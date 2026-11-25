# security

## Overview
Provides cryptographic primitives for account authentication and login packet decryption, specifically Argon2id password verification (`Argon2`) and 1024-bit RSA decryption (`RSAManager`) backed by pluggable `RsaBackend` implementations (including mbedTLS via `rsa_backend_mbedtls.cpp`).

## Interface
- `Argon2` (`[argon.hpp:Argon2]`): Password verifier supporting Argon2id hash comparison (`[argon.hpp:Argon2::argon]`) and dynamic cost parameter loading from `ConfigManager` (`[argon.hpp:Argon2::updateConstants]`).
- `RSAManager` & `g_RSA` (`[rsa.hpp:RSAManager]`, `[rsa.hpp:g_RSA]`): DI-backed singleton (`[rsa.cpp:RSAManager::getInstance]`) delegating to `std::unique_ptr<RsaBackend> backend` to manage RSA private keys from PEM files or p/q prime strings (`[rsa.hpp:RSAManager::start]`, `[rsa.hpp:RSAManager::loadPEM]`, `[rsa.hpp:RSAManager::setKey]`) and perform in-place 128-byte RSA block decryption (`[rsa.hpp:RSAManager::decrypt]`).
- `RsaBackend` & `createMbedTlsRsaBackend` (`[rsa_backend.hpp:RsaBackend]`, `[rsa_backend.hpp:createMbedTlsRsaBackend]`, `[rsa_backend_mbedtls.cpp:createMbedTlsRsaBackend]`): Abstract RSA backend interface (`loadPEM`, `setKey`, `decrypt`) and mbedTLS implementation supporting both mbedTLS 2.x and 3.x APIs.

## Invariants
- `Argon2::parseBitShift` requires the `M_CONST` configuration string to match `<base> << <shift>` with `0 <= shift < 32`, returning `0` on malformed or out-of-range inputs (`[argon.cpp:Argon2::parseBitShift]`).
- `RSAManager::decrypt` operates on a fixed 128-byte (1024-bit) buffer in-place via the active `RsaBackend` (`[rsa.hpp:RSAManager::decrypt]`, `[rsa_backend.hpp:RsaBackend::decrypt]`).
- `RsaBackend` implementations (`createMbedTlsRsaBackend`) load PEM keys or p/q primes into local contexts before committing state on success (`[rsa_backend_mbedtls.cpp]`).

## Side Effects
- `Argon2::updateConstants` reads `M_CONST`, `T_CONST`, and `PARALLELISM` from `g_configManager()` (`[argon.cpp:Argon2::updateConstants]`).
- `RSAManager::loadPEM` reads private key PEM files (default `"key.pem"`) from disk via the active `RsaBackend`, and `RSAManager::start` falls back to standard CipSoft RSA primes if loading fails (`[rsa.cpp:RSAManager::start]`, `[rsa.cpp:RSAManager::loadPEM]`).
- `RSAManager::decrypt` mutates the caller's 128-byte `msg` buffer in-place (`[rsa.cpp:RSAManager::decrypt]`).
- Logs warnings and errors via `g_logger()` / `Logger` on malformed hashes, invalid base64 inputs, or RSA backend failures (`[argon.cpp:Argon2::verifyPassword]`, `[argon.cpp:Argon2::base64_decode]`, `[rsa.cpp:RSAManager::decrypt]`, `[rsa.cpp:RSAManager::loadPEM]`).

## Verification
- See the [C++ build and test guide](../../tests/README.md#running-tests).
