# security

## Overview
Provides cryptographic primitives for account authentication and login packet decryption, specifically Argon2id password verification (`Argon2`) and OpenSSL BIGNUM/Montgomery-based 1024-bit RSA decryption (`RSAManager`).

## Interface
- `Argon2` (`[argon.hpp:Argon2]`): Password verifier supporting Argon2id hash comparison (`[argon.hpp:Argon2::argon]`) and dynamic cost parameter loading from `ConfigManager` (`[argon.hpp:Argon2::updateConstants]`).
- `RSAManager` & `g_RSA` (`[rsa.hpp:RSAManager]`, `[rsa.hpp:g_RSA]`): DI-backed singleton (`[rsa.cpp:RSAManager::getInstance]`) managing RSA private keys from PEM files or p/q prime strings (`[rsa.hpp:RSAManager::start]`, `[rsa.hpp:RSAManager::loadPEM]`, `[rsa.hpp:RSAManager::setKey]`) and performing in-place 128-byte RSA block decryption (`[rsa.hpp:RSAManager::decrypt]`).

## Invariants
- `Argon2::parseBitShift` requires the `M_CONST` configuration string to match `<base> << <shift>` with `0 <= shift < 32`, returning `0` on malformed or out-of-range inputs (`[argon.cpp:Argon2::parseBitShift]`).
- `RSAManager::RSAManager` requires non-null OpenSSL allocations for `n`, `d`, and `mont_ctx`, throwing `std::runtime_error` on allocation failure (`[rsa.cpp:RSAManager::RSAManager]`).
- `RSAManager::decrypt` operates on a fixed 128-byte (1024-bit) buffer in-place, zero-padding leading bytes when the decrypted `BIGNUM` is shorter than 128 bytes (`[rsa.cpp:RSAManager::decrypt]`).
- `RSAManager::loadPEM` extracts `n`, `d`, and recomputes `mont_ctx` into temporaries before committing ownership to member pointers atomically (`[rsa.cpp:RSAManager::loadPEM]`).

## Side Effects
- `Argon2::updateConstants` reads `M_CONST`, `T_CONST`, and `PARALLELISM` from `g_configManager()` (`[argon.cpp:Argon2::updateConstants]`).
- `RSAManager::loadPEM` reads private key PEM files (default `"key.pem"`) from disk via OpenSSL `BIO_new_file`, and `RSAManager::start` falls back to the standard CipSoft RSA primes if loading fails (`[rsa.cpp:RSAManager::start]`, `[rsa.cpp:RSAManager::loadPEM]`).
- `RSAManager::decrypt` mutates the caller's 128-byte `msg` buffer in-place and maintains a `thread_local` OpenSSL `BN_CTX` (`[rsa.cpp:RSAManager::decrypt]`).
- Logs warnings and errors via `g_logger()` / `Logger` on malformed hashes, invalid base64 inputs, or OpenSSL failures (`[argon.cpp:Argon2::verifyPassword]`, `[argon.cpp:Argon2::base64_decode]`, `[rsa.cpp:RSAManager::decrypt]`, `[rsa.cpp:RSAManager::loadPEM]`).

## Verification
- Run: `ctest --test-dir build --output-on-failure`
