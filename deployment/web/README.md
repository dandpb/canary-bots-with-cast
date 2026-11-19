# MyAAC hosting and browser prerequisites

The Dockerfile and Apache/PHP settings reproduce the deployed PHP 8.3 image,
including MySQL, image, ZIP and internationalization extensions. Apache permits
MyAAC/browser `.htaccess` rules and recognizes HTTPS forwarded by the TLS proxy.
The prepared site and its private configuration are mounted separately; the image
contains no site credentials or player data.

Prepare MyAAC using its own installation instructions and the account database
already used by Canary. Install this directory's cast-aware `login.php`, optionally
the [world-map plugin](plugins/worldmap/README.md), and the generated
[browser package](../browser/README.md). The cache-info response also supplies the
`discord_online` numeric field expected by the deployed client.

```sh
MYAAC_ROOT=/path/to/site CANARY_NETWORK=your-canary-network \
  docker compose -f deployment/web/compose.example.yml config --quiet
MYAAC_ROOT=/path/to/site CANARY_NETWORK=your-canary-network \
  docker compose -f deployment/web/compose.example.yml up -d --build
```

Configure MyAAC's database connection in its protected site configuration. The
database service is reachable as `database` when sharing the example server
network. Set `CANARY_NETWORK` to the actual Docker network; the default matches
the ARM64 Compose example. Mount the site's intended UID/GID permissions before
starting. TLS terminates at your HTTPS proxy; HTTP binds to loopback port 8080
unless configured otherwise.

The generated browser directory supplies its own isolation/MIME headers. Its WSS
gateway remains a separate loopback bridge/TLS proxy described in the browser
README. The existing desktop login endpoint remains available.

## Overview
Provides the Apache/PHP 8.3 MyAAC container image, cast-aware `login.php` HTTP login endpoint, World Map plugin, and the local Thais Voxel Explorer frontend.

## Interface
- `[login.php:$action]` — HTTP JSON login endpoint handling `cacheinfo` (including `discord_online` and `playersonline`), `login` (including `@cast` / `@livestream` broadcaster list lookup), and rate-limited password authentication.
- `[Dockerfile:FROM]` / `[compose.example.yml:services]` — PHP 8.3 Apache container definition with MySQL, GD/image, ZIP, and intl extensions.
- Subdirectories:
  - `plugins/worldmap`: [`./plugins/worldmap/README.md`](./plugins/worldmap/README.md) — MyAAC Community World Map plugin.
  - `voxel-explorer`: [`./voxel-explorer/README.md`](./voxel-explorer/README.md) — Interactive 3D/Canvas2D Thais Voxel Explorer app.

## Invariants
- `[login.php:$blocked_seed]` unconditionally rejects login for legacy seed account `id === 1` whenever the stored password hash or submitted password matches SHA-1 fingerprint `f45ca43bc9b20edf28d705024aac6c0b2c67072f`, incrementing the per-IP rate limiter on failure.
- Site credentials and player databases are never baked into the container image; `MYAAC_ROOT` is mounted at runtime.

## Side Effects
- Queries MySQL (`accounts`, `players`, `players_online`, `cast_broadcasters`) and updates IP rate-limiter state on failed login attempts (`[login.php]`).

## Verification
- Run: `MYAAC_ROOT=/tmp/site CANARY_NETWORK=test docker compose -f deployment/web/compose.example.yml config --quiet`

