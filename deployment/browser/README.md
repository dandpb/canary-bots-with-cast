# Browser Client Deployment (`deployment/browser`)

## Overview

This directory versions the source changes and packaging toolchain used to deploy OTClient Redemption 4.2 beside MyAAC. It includes asynchronous WebAssembly login, main-thread fetch proxying, protocol-1500 assets, required isolation headers, and a fixed WSS world adapter. It ships no client binaries, game artwork, player profiles, or credentials.

Prepare a compatible 4.2 Emscripten browser build with `otclient.js`, `.wasm`, `.data` and `.html`, its matching extracted runtime tree, a fresh `config.ini`, and verified protocol-1500 appearances/static/sprite and sound assets. Configure a fresh client `init.lua` using [the existing client instructions](../client/README.md). Keep service URLs pointed at your MyAAC site; the packager changes its `login.php` URLs to the browser endpoint. Desktop client configuration remains separate.

```sh
python3 deployment/browser/package_client.py \
  --build /artifacts/build-emscripten-web --runtime /artifacts/runtime \
  --init /configuration/init.lua --config /artifacts/config.ini \
  --assets /artifacts/assets/1500 --sounds /artifacts/assets/sounds1500 \
  --output /staging/play \
  --login-url https://game.example/play/login.php \
  --gateway-host game.example --gateway-port 8444
```

The output directory must not exist. The packager checks known loader/fetch/login signatures, rebuilds contiguous metadata offsets, includes configuration/assets, names data by SHA256, records output hashes, and publishes its staging directory atomically. Unsupported compiler output fails instead of silently producing a broken client. It was tested with the compatible 4.2 layout used by this deployment; it is not a general Emscripten patcher. Obtain and verify client/assets separately.

Install the generated directory as `play/` directly under the MyAAC web root. The adapter invokes the existing cast-aware `login.php` and rewrites only the browser response's world gateway fields. Preserve normal desktop `login.php`. Apache must allow `.htaccess` with `mod_headers`; another server must supply the same COOP/COEP/CORP headers and WASM MIME type. Use HTTPS so threads and WSS work. New profiles default to Portuguese and a compact character list; `--locale en` selects English. Existing saved preferences take precedence.

The optional systemd template runs `websockify` only on loopback, forwarding to the game's ordinary port 7172. Install `websockify` in the referenced virtualenv, adjust the user/paths, then expose it through a TLS-capable reverse proxy on the configured gateway port, including WebSocket upgrade support. Advertise that gateway to the browser adapter. The game protocol remains ordinary Tibia traffic.

```sh
python3 -m venv /opt/canary-web/venv
/opt/canary-web/venv/bin/pip install -r deployment/browser/requirements.txt
```

For reference, the earlier 4.2 browser download had SHA256 `dcf127f52843068989c2b869cccf882d6e5aa62ac24c33dbfa2e53f5beb1f8ec`; the validated assets manifest was `f9b75eff93b59a92830c67edd0e2a51b775422cb50ab57e5aa48406bf0a3c683` from `dudantas/tibia-client/15.00.249ccc` (5374 checked files, JSON CRLF checksums). Those historical hashes do not authenticate arbitrary future build artifacts.

## Interface

- `[package_client.py:main]` — CLI entry point accepting `--build`, `--runtime`, `--init`, `--config`, `--assets`, `--sounds`, `--output`, `--login-url`, `--gateway-host`, `--gateway-port` (default `8444`), and `--locale` (default `'pt'`).
- `[package_client.py:package]` — `package(build, runtime, init, config, assets, sounds, output, login_url, gateway_host, gateway_port, locale='pt')`: packages OTClient Redemption WebAssembly build and returns metadata dictionary `{'files', 'remote_package_size', 'package_uuid'}`.
- `[package_client.py:check_fresh_configuration]` — `check_fresh_configuration(init_text, config_text)`: validates `init.lua` and `config.ini` contain no saved credentials or tokens.
- `[package_client.py:login_adapter]` — `login_adapter(host, port)`: generates PHP login wrapper script rewriting `playdata.worlds` external addresses and ports to the configured WSS gateway host and port.
- `[package_client.py:digest]` — `digest(data)`: computes SHA-256 hex digest string.
- `[package_client.py:LOGIN_CALL]` / `[package_client.py:ASYNC_LOGIN]` / `[package_client.py:FETCH_SIGNATURE]` / `[package_client.py:HEADERS]` — Patch signatures and Apache `.htaccess` COOP/COEP/CORP and MIME constants.
- `[canary-websocket.service:ExecStart]` — Systemd service template running `/opt/canary-web/venv/bin/websockify 127.0.0.1:8765 127.0.0.1:7172` as user `canary`.
- `[requirements.txt:websockify]` — Python package dependency `websockify==0.13.0`.

## Invariants

- `[package_client.py:check_fresh_configuration]` — `config.ini` must be valid INI syntax and must not contain non-empty sensitive keys (`account`, `accountname`, `email`, `login`, `loginemail`, `password`, `passwordhash`, `token`, `authenticatortoken`, `sessionkey`, `accesstoken`, `refreshtoken`); `init.lua` must not contain assignments or `g_settings.set` calls for sensitive account/token/session fields.
- `[package_client.py:login_adapter]` — Gateway host must match `r'[A-Za-z0-9][A-Za-z0-9.-]{0,252}'` and gateway port must satisfy `1 <= port <= 65535`.
- `[package_client.py:package]` — `login_url` must use `https` scheme, have a hostname, end with `/login.php`, and contain no credentials, query, fragment, quotes, backslashes, or control characters; `locale` must match `r'[a-z]{2}'`.
- `[package_client.py:package]` — Target `output` directory must not already exist (existing deployments are never overwritten).
- `[package_client.py:package]` — Emscripten metadata `remote_package_size` in `otclient.js` must equal the byte length of `otclient.data`; `init.lua` must contain at least one `http(s)://.../login.php` URL and exactly one `g_modules.ensureModuleLoaded('modulelib')`; `modules/client_entergame/entergame.lua` must contain `LOGIN_CALL` exactly once; `otclient.js` must contain `"otclient.data"`, `var PACKAGE_UUID=metadata["package_uuid"];`, `FETCH_SIGNATURE`, and a `proxiedFunctionTable` containing `_emscripten_websocket_new`.
- `[canary-websocket.service:Service]` — Executes with `NoNewPrivileges=true`, `PrivateTmp=true`, `User=canary`, `Restart=on-failure`, `RestartSec=3`.

## Side Effects

- `[package_client.py:package]` — Reads Emscripten build artifacts (`otclient.js`, `otclient.data`, `otclient.wasm`, `otclient.html`), runtime `entergame.lua`, `init.lua`, `config.ini`, and asset/sound directories; writes packaged bundle (`otclient-<hash>.data`, `otclient.js`, `otclient.wasm`, `index.html`, `.htaccess`, `login.php`, `init.lua`, `entergame.lua`, `package-manifest.json`) to a temporary staging directory via `tempfile.mkdtemp` and atomically renames it to `output` (cleaning up staging on error).
- `[package_client.py:main]` — Writes JSON summary (`{'files', 'bytes', 'uuid'}`) to `stdout`.
- `[canary-websocket.service:ExecStart]` — Binds loopback TCP port `127.0.0.1:8765` for WebSocket traffic and forwards connections to `127.0.0.1:7172`.

## Verification

- Run: `pytest`

```sh
python3 deployment/browser/test_package_client.py
python3 deployment/browser/test_php_adapter.py --container your-php-test-container
```

Tests cover rebuilt file contents/offsets/hashes, mismatched artifacts, unsupported fetch code, unsafe inputs, saved credentials, and preservation of existing outputs. The PHP test uses a fake backend in an automatically removed temporary directory; it checks fixed WSS fields, session retention, and unchanged error responses. The deployed version of these runtime fixes was also exercised in Chromium with cast character switching, advancing game frames, and no JavaScript errors. That historical deployment evidence is separate from the portable packager's tests.
