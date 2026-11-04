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
