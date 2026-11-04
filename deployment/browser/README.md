# Browser client deployment

This directory versions the source changes used to deploy OTClient Redemption
4.2 beside MyAAC. It includes asynchronous WebAssembly login, main-thread fetch
proxying, protocol-1500 assets, required isolation headers and a fixed WSS world
adapter. It ships no client binaries, game artwork, player profiles or credentials.

Prepare a compatible 4.2 Emscripten browser build with `otclient.js`, `.wasm`,
`.data` and `.html`, its matching extracted runtime tree, a fresh `config.ini`,
and verified protocol-1500 appearances/static/sprite and sound assets. Configure a
fresh client `init.lua` using [the existing client instructions](../client/README.md).
Keep service URLs pointed at your MyAAC site; the packager changes its login.php
URLs to the browser endpoint. Desktop client configuration remains separate.

```sh
python3 deployment/browser/package_client.py \
  --build /artifacts/build-emscripten-web --runtime /artifacts/runtime \
  --init /configuration/init.lua --config /artifacts/config.ini \
  --assets /artifacts/assets/1500 --sounds /artifacts/assets/sounds1500 \
  --output /staging/play \
  --login-url https://game.example/play/login.php \
  --gateway-host game.example --gateway-port 8444
```

The output directory must not exist. The packager checks known loader/fetch/login
signatures, rebuilds contiguous metadata offsets, includes configuration/assets,
names data by SHA256, records output hashes and publishes its staging directory
atomically. Unsupported compiler output fails instead of silently producing a
broken client. It was tested with the compatible 4.2 layout used by this deployment;
it is not a general Emscripten patcher. Obtain and verify client/assets separately.

Install the generated directory as `play/` directly under the MyAAC web root.
The adapter invokes the existing cast-aware `login.php` and rewrites only the
browser response's world gateway fields. Preserve normal desktop login.php.
Apache must allow `.htaccess` with `mod_headers`; another server must supply the
same COOP/COEP/CORP headers and WASM MIME type. Use HTTPS so threads and WSS work.
New profiles default to Portuguese and a compact character list; `--locale en`
selects English. Existing saved preferences take precedence.

The optional systemd template runs `websockify` only on loopback, forwarding to
the game's ordinary port 7172. Install websockify in the referenced virtualenv,
adjust the user/paths, then expose it through a TLS-capable reverse proxy on the
configured gateway port, including WebSocket upgrade support. Advertise that
gateway to the browser adapter. The game protocol remains ordinary Tibia traffic.

```sh
python3 -m venv /opt/canary-web/venv
/opt/canary-web/venv/bin/pip install -r deployment/browser/requirements.txt
```

For reference, the earlier 4.2 browser download had SHA256
`dcf127f52843068989c2b869cccf882d6e5aa62ac24c33dbfa2e53f5beb1f8ec`;
the validated assets manifest was
`f9b75eff93b59a92830c67edd0e2a51b775422cb50ab57e5aa48406bf0a3c683`
from `dudantas/tibia-client/15.00.249ccc` (5374 checked files, JSON CRLF checksums).
Those historical hashes do not authenticate arbitrary future build artifacts.

## Verification

```sh
python3 deployment/browser/test_package_client.py
python3 deployment/browser/test_php_adapter.py --container your-php-test-container
```

Tests cover rebuilt file contents/offsets/hashes, mismatched artifacts, unsupported
fetch code, unsafe inputs, saved credentials and preservation of existing outputs.
The PHP test uses a fake backend in an automatically removed temporary directory;
it checks fixed WSS fields, session retention and unchanged error responses.
The deployed version of these runtime fixes was also exercised in Chromium with
cast character switching, advancing game frames and no JavaScript errors. That
historical deployment evidence is separate from the portable packager's tests.
