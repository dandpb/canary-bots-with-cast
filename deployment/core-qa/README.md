# Core jogável em QA isolada

Esta branch parte da `main` em `a1caa920e506bacdeff7243f6e0c83fad96e1729`
e usa o projeto `canary-core-qa`. Ela contém somente MariaDB, Canary e MyAAC.
Não inicia brain, LiteLLM nem qualquer inferência. O jogo não recebe socket,
configuração ou ledger do ambiente operacional; sem arquivo de configuração do
brain, seu modo é `disabled`. Banco, cache, logs, dados autorais e mapa ficam
sob este projeto. As imagens usam tags próprias e os serviços não reiniciam
automaticamente.

O MyAAC deste stack gera seu `config.lua` a partir de `CANARY_GAME_PORT` e
`login.php` anuncia `gameProtocolPort` desse arquivo. Para que o cliente chegue
ao jogo de QA, o entrypoint do Canary escuta nas mesmas portas. O HTTP de login
é `http://127.0.0.1:18080/login.php`; jogo `17172`, login binário `17171` e
status `17173`, todos publicados apenas em loopback. O cliente deve usar
protocolo `1500`. Nenhuma dessas portas aponta ao stack `canary-bots-wsl`.

## Preparação e verificações offline

Use um checkout isolado desta branch, sem alterações de código posteriores ao
commit revisado para o smoke. Estes comandos não iniciam containers:

```bash
cd deployment/core-qa
python3 prepare.py --skip-map
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env config -q
python3 -m unittest -v test_offline.py
```

`prepare.py` cria senhas de banco exclusivas deste QA em `.env` e copia schema
e seeds para `runtime/initdb`. Preserva a `.env` se já existir. O mapa não é
versionado: antes de iniciar serviços, rode `python3 prepare.py --download-map`
para obter a release upstream `v3.4.1` com SHA-256 fixado, ou use
`python3 prepare.py --map /caminho/para/otservbr.otbm` para copiar uma cópia
já baixada. Um hash diferente impede a preparação. `--skip-map` serve apenas
para validar a configuração offline. A configuração do jogo desativa download
automático do mapa.

## Smoke humano após autorização

Ainda não execute estes comandos sem a aprovação do responsável pelo smoke:

```bash
cd deployment/core-qa
python3 prepare.py --download-map
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env config -q
SOURCE_REVISION="$(git rev-parse HEAD)" env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env up -d --build --wait database game web
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env ps
```

Abra o site em `http://127.0.0.1:18080/` e use o endpoint HTTP de login no
OTClient Redemption. Confira no retorno de login que `externalport` é `17172`
e que o personagem entra no jogo de QA. O cast `@cast` fica disponível quando
os bots selecionados terminarem de carregar. O padrão é 50 bots; ajuste
`BOT_PLAYERS_ONLINE` apenas na `.env` deste QA se o teste pedir outro número.
O banco de QA nasce vazio e recebe os seeds próprios na primeira subida; contas
criadas nele não são copiadas do ambiente operacional.

## Coleta e rollback

Execute no diretório deste QA. `stop -t 180` permite salvar personagens antes
de interromper o jogo. Colete o estado e os logs antes de remover os
containers; `down` preserva todos os volumes para análise ou nova subida.

```bash
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env stop -t 180
mkdir -p runtime/evidence
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env ps -a > runtime/evidence/containers.txt
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env logs --no-color --timestamps database game web > runtime/evidence/services.log 2>&1
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env down
```

Não use `down -v`: isso apagaria o banco e os dados do teste. Os comandos acima
atuam apenas no projeto `canary-core-qa`, sem parar ou recriar serviços do
projeto operacional.
