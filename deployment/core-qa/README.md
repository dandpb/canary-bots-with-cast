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
export SOURCE_REVISION="$(git rev-parse HEAD)" # conferência preliminar, não é aprovação para subir
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env config -q
python3 -m unittest -v test_offline.py
python3 preflight.py --resources-only
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
export SOURCE_REVISION='COLE_O_SHA_COMPLETO_APROVADO_AQUI'
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env config -q
python3 preflight.py --approved-revision "$SOURCE_REVISION"
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env up -d --build --wait database game web
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env ps
```

Abra o site em `http://127.0.0.1:18080/` e use o endpoint HTTP de login no
OTClient Redemption. Confira no retorno de login que `externalport` é `17172`
e que o personagem entra no jogo de QA. O cast `@cast` fica disponível quando
os bots selecionados terminarem de carregar. O padrão é 50 bots; ajuste
`BOT_PLAYERS_ONLINE` apenas na `.env` deste QA se o teste pedir outro número.
O banco de QA nasce vazio e recebe os seeds próprios na primeira subida; contas
criadas nele não são copiadas do ambiente operacional.
O preflight completo exige o mapa validado e recusa containers, volumes, redes
ou tags de imagem `canary-core-qa` já existentes, inclusive após um rollback.
Também exige que o SHA aprovado, `SOURCE_REVISION` e HEAD sejam idênticos, com
árvore Git limpa; nunca aceita a revisão `unknown`. Obtenha o SHA aprovado do
responsável pela revisão após o merge. Não o substitua pelo HEAD atual sem
conferir a aprovação.
Nesse caso, inspecione os recursos antes de qualquer nova subida; não os remova
automaticamente. Ele consulta o Docker somente em leitura e não acessa o
ledger ou o provider. Repita-o imediatamente antes do primeiro `up`.

`image-lock.json` registra os IDs locais da imagem base web
`otbr-myaac:latest` e do MariaDB `11.4`. O preflight confere ambos com
`docker image inspect`; o Compose não faz pull desses artefatos. Se qualquer
ID mudar ou faltar, interrompa o smoke e revise a origem antes de atualizar o
lock. O tag final web `canary-core-qa-web:local` é exclusivo do QA. No ID web
registrado, o script `myaac-entrypoint` tem SHA-256
`a007f92ec02398d05205c447c9645ab1add7cfb74603d3284e9f03eaf38c43e9`
e escreve `gameProtocolPort` a partir de `CANARY_GAME_PORT`; este QA fornece
`17172`. É um recibo de conteúdo local, não um digest de registro remoto.

## Coleta e rollback

Execute no diretório deste QA. `stop -t 180` permite salvar personagens antes
de interromper o jogo. Colete o estado e os logs antes de remover os
containers; `down` preserva todos os volumes para análise ou nova subida.

```bash
export SOURCE_REVISION="$(git rev-parse HEAD)" # somente para renderizar o Compose no rollback
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env stop -t 180
mkdir -p runtime/evidence
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env ps -a > runtime/evidence/containers.txt
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env logs --no-color --timestamps database game web > runtime/evidence/services.log 2>&1
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env down
```

Não use `down -v`: isso apagaria o banco e os dados do teste. Os comandos acima
atuam apenas no projeto `canary-core-qa`, sem parar ou recriar serviços do
projeto operacional.
