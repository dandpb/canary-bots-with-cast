# start Canary with Docker Compose

This Compose project runs a MariaDB database, the Canary game server and the
OpenTibiaBR login service. Run the following commands from the repository root
with Docker and the Compose plugin. For the local WSL deployment with MyAAC,
cast and the AI worker, see the [WSL guide](../deployment/wsl/README.md).

## Validate the Compose file

This command uses the example settings and lists the expected services
`database`, `server` and `login`.

```sh
docker compose --env-file docker/.env.dist -f docker/docker-compose.yml config --no-env-resolution --services
```

## Start the stack

Copy `docker/.env.dist` to `docker/.env` for a new deployment. Edit the
credentials and addresses before starting. Keep an existing `docker/.env`
when updating your checkout.

```sh
cp -n docker/.env.dist docker/.env
docker compose --env-file docker/.env -f docker/docker-compose.yml up -d --build
docker compose --env-file docker/.env -f docker/docker-compose.yml ps
```

The example publishes HTTP login on `8080`, game on `7172`, status on `7171`,
login gRPC on `9090` and MariaDB on `3306`. The default HTTP login URL for a
local client is `http://127.0.0.1:8080/login.php`. MariaDB stores its data in
the Compose volume `db-volume`.

Rebuild the game server after changing its source.

```sh
docker compose --env-file docker/.env -f docker/docker-compose.yml up -d --build server
```
