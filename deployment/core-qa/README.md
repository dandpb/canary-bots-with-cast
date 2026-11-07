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
python3 verify_myaac.py
python3 preflight.py --resources-only
```

Em um host sem `otbr-myaac:latest`, somente o teste específico do entrypoint
MyAAC informa `skip`; `verify_myaac.py` e o preflight completo exigem a imagem
fixada e falham se ela estiver ausente.

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
```

O preflight completo grava `runtime/evidence/preflight-receipt.json` somente
após todas as verificações passarem. O recibo contém SHA aprovado, IDs locais
observados das imagens MariaDB e MyAAC, hashes do entrypoint e do config MyAAC
gerado, hash do Compose renderizado com campos sensíveis redigidos, hash do mapa
e horário UTC. Compartilhe esse recibo sanitizado com o revisor e espere o GO
antes do primeiro `up`. O preflight não inicia serviços.

Após o GO, repita o preflight imediatamente antes de subir e execute:

```bash
cd deployment/core-qa
export SOURCE_REVISION='COLE_O_SHA_COMPLETO_APROVADO_AQUI'
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
`17172`. `verify_myaac.py` exporta a imagem somente em leitura, confere o hash
do entrypoint e executa apenas seu trecho de geração do `config.lua` com valores
fictícios. Confere `gameProtocolPort = 17172` e o SHA-256 do config gerado
`a94fa69f36a5fbe59623e7ff0d4e34191f1e41295f018c8e6a9bb06adef42f63`.
Esse recibo não executa o bootstrap do MyAAC nem inicia um container; o login
real ainda depende do smoke autorizado. Os hashes são recibos locais, não
digests de registro remoto.

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

## Etapa 2: worker fake (somente QA, nunca produção)

A etapa 1 acima (login, jogo, party e cast) mantém o brain desligado. A etapa 2
soma `compose.brain-fake.yaml`: liga a ponte só neste projeto e adiciona o
serviço `brain` com `provider: fake`, que responde por palavras-chave. Ele não
tem provider, credencial, gateway, claim, porta, variável de ambiente nem rede
(`network_mode: none`). State, ledger e replay ficam nos volumes descartáveis
`canary-core-qa_brain-ledger` e `canary-core-qa_brain-socket`. Os pilotos 65001
(explorador), 65004 e 65003 entram nos 50 bots por `BOT_POPULATION_REFERENCE_BOTS`.
O roteiro do jogador está em [ROTEIRO.md](ROTEIRO.md).

A imagem `brain` usa `pull: false` e só aceita a base `python:3.12-slim` fixada
por digest em `image-lock.json`. Se o preflight recusar a base, revise e rode
`docker pull python@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54`
e `docker tag python@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54 python:3.12-slim`.
Lacuna P3: as
dependências Python vêm do PyPI por versão fixa (`requirements.lock`), sem hashes.

```bash
cd deployment/core-qa
export SOURCE_REVISION='COLE_O_SHA_COMPLETO_APROVADO_AQUI'
QA="env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml -f compose.brain-fake.yaml --env-file .env"
# Host limpo:
python3 preflight.py --brain-fake --approved-revision "$SOURCE_REVISION"
$QA up -d --build --wait database game web brain
# Ou upgrade sobre a etapa 1 já de pé (no lugar dos dois comandos acima):
python3 preflight.py --upgrade-from-stage1 --approved-revision "$SOURCE_REVISION"
$QA up -d --build --wait game brain
# Nos dois casos, depois do up:
python3 preflight.py --record-brain-image --approved-revision "$SOURCE_REVISION"
$QA exec brain canary-brain status --state /var/lib/canary-human-qa-stage2/ledger.sqlite3
```

`--brain-fake` e `--upgrade-from-stage1` gravam o recibo da etapa 2 em
`runtime/evidence/stage2-upgrade-receipt.json`, que `--record-brain-image`
atualiza após o build. A etapa 1 mantém seu `preflight-receipt.json`.

O upgrade só aceita exatamente os objetos da etapa 1: os containers
`canary-core-qa-{database,game,web}-1`, a rede `canary-core-qa_default`, os quatro
volumes e as tags game/web, todos com os labels Compose do projeto. Ele recusa
qualquer objeto `canary-core-qa*` a mais, a menos ou com label errado, e também
recusa um container, volume ou imagem `brain` que já exista. O recibo
`runtime/evidence/stage2-upgrade-receipt.json` registra o SHA, os IDs vistos e o
`CreatedAt` de cada volume. Só o container `game` é recriado, com nova env e
montagens; `database` e `web` ficam. Para confirmar que os volumes são os mesmos,
compare o recibo com
`docker volume inspect canary-core-qa_database canary-core-qa_game-logs canary-core-qa_authored-data --format '{{.Name}} {{.CreatedAt}}'`.
`--record-brain-image` só grava o ID da imagem `brain` quando o label
`org.opencontainers.image.revision` dela, o container em execução e o recibo
batem com o HEAD aprovado.

Passa quando: `/cavebot _global brain status` (GOD) mostra `"mode":"active"`,
`"worker_alive":true` e roster `[65001,65004,65003]`; `/brain fique aqui` com
piloto na party dá `Mensagem enviada ao companheiro.` e a PM `Teste: proposta
hold; ...`; o piloto para e cerca de 30 s depois o episódio fica `completed`; o
ledger termina com `spent` 0, `reserved` 0 e nenhuma `request`.

**Kill switch.** No jogo, como GOD: `/cavebot _global brain disable` responde
`Brain disabled; native behavior retained.`, encerra as metas com
`cancelled/operator_disabled` e devolve os pilotos ao nativo até
`/cavebot _global brain reload`. Se o jogo não responder, `$QA stop brain`: sem
heartbeat por 5 s o servidor marca `worker_alive:false` e o nativo reassume;
`$QA start brain` religa.

**Rollback.** Use sempre o mesmo `$QA`, nunca `down -v`. Só os dois volumes
`brain-*` são apagados; banco, logs e cache ficam como na etapa 1.

```bash
$QA stop -t 180
mkdir -p runtime/evidence/brain
$QA cp brain:/var/lib/canary-human-qa-stage2/. runtime/evidence/brain/
$QA down
docker volume rm canary-core-qa_brain-ledger canary-core-qa_brain-socket
```
