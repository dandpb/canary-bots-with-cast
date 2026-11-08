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

A imagem `game` usa o mesmo `deployment/wsl/Dockerfile` da produção, cujo
`ARG BASE_IMAGE` continua `ubuntu:24.04` por padrão. Só este QA passa
`BASE_IMAGE: ubuntu:24.04@sha256:<digest>` no `compose.yaml`, com `pull: false`.
O digest, a plataforma (`linux/amd64`) e o ID local ficam em `game_base` no
`image-lock.json`; o valor no `compose.yaml` deve ser o mesmo digest. O preflight
e o `game-rollout-gate` recusam um lock com placeholder, uma base ausente ou com
ID, plataforma ou digest diferente. Nunca deixe o build puxar a base: se faltar,
revise e carregue o digest do recibo do host antes de buildar.

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

## Sem shutdown diário no game de QA

`config.lua.dist` mantém `globalServerSaveShutdown = true`: às 06:00 o save global
desliga o servidor (no QA, saída 0 às 06:05). Só o `game` deste projeto define
`GAME_DISABLE_GLOBAL_SAVE_SHUTDOWN: "1"`; o entrypoint então acrescenta
`globalServerSaveShutdown = false` ao `config.lua`. Sem a variável, o `config.lua`
gerado é idêntico byte a byte ao de antes (produção e WSL não a definem).

O save diário continua salvando. Antes, quem salvava era o estado
`GAME_STATE_SHUTDOWN` (ou `GAME_STATE_CLOSED`). Agora `global_server_save.lua`
chama `saveServer()` (o mesmo save do autosave horário) quando nem close nem
shutdown estão ligados. Com os padrões de produção (shutdown `true`) nada muda:
`tests/lua/global_server_save_test.lua` cobre as quatro combinações. O preflight
renderiza o `config.lua` do `game` com o ambiente do Compose de QA e falha fechado
se `globalServerSaveShutdown` ou `globalServerSaveClose` não forem `false` (o valor
efetivo é a última atribuição).

**Rollout só do `game`, após revisão, nesta ordem.** A imagem atual tem o entrypoint
antigo, então é preciso rebuild do `game` e recriar só ele. `database`, `web`, rede
e volumes ficam. Não rode sem o GO do responsável:

```bash
cd deployment/core-qa
export SOURCE_REVISION='SHA_COMPLETO_REVISADO_DO_MERGE'
QA="env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env"
# 1 e 2. gate antes do build, só leitura
python3 stage1_baseline.py game-rollout-gate --approved-revision "$SOURCE_REVISION" \
  --historical-receipt /caminho/para/web-rollout-after.json
# 3. só agora: build e recriação só do game (stop -t 180 salva os personagens)
$QA build --pull=false game
$QA stop -t 180 game
$QA up -d --no-build --no-deps --wait game
# 4 e 5. recibo do game e conferência do config.lua vivo, só leitura
python3 stage1_baseline.py game-rollout --historical-receipt /caminho/para/web-rollout-after.json
```

`game-rollout-gate` não muda nada. Grava `runtime/evidence/game-rollout-gate.json`
só se:
- o SHA aprovado, `SOURCE_REVISION` e o HEAD forem iguais, com árvore limpa;
- o Compose de QA passar `assert_compose` (com o contrato do `config.lua`);
- `database` e `web` baterem com `web-rollout-after.json`;
- eles, a rede e os quatro volumes baterem com a `stage1-baseline.json` fixada
  (ID, `CreatedAt` e labels);
- o `game` ainda for o da baseline.

O `game` pode estar parado, e o recorte do banco não é comparado.

`game-rollout` recusa sem esse gate, com gate adulterado, com mais de 12 h, de outra
revisão, baseline ou recibo web, ou se o `game` não foi recriado depois do gate. Ele
grava `runtime/evidence/game-rollout-after-<UTC>.json` só se:
- `database`, `web`, rede e volumes continuarem iguais;
- o `game` tiver sido recriado a partir de `SOURCE_REVISION` (label
  `org.opencontainers.image.revision`);
- o `config.lua` vivo tiver `globalServerSaveShutdown = false`.

O recibo traz:
- o SHA de origem;
- os IDs da imagem e do container do `game`, e o `CreatedAt`;
- o SHA-256 do `config.lua` (o conteúdo, que tem a senha do banco, não sai do
  container);
- os SHA-256 do gate, de `web-rollout-after.json` e da baseline;
- um selo `content_sha256` que acusa edição.

**6. Recaptura da baseline da etapa 1.** Depois do rollout, `check` e o upgrade
recusam (o `game` mudou de ID, imagem e `config-hash`). O caminho é recapturar:

```bash
# o script de auditoria fica FORA do checkout e roda por caminho absoluto, com o
# diretório atual em deployment/core-qa (ele importa stage1_baseline daqui)
python3 /caminho/fora/do/checkout/make_db_audit.py --auditor "<quem auditou>" \
  --explanation "<o que foi observado e o que segue desconhecido>" --out runtime/evidence/db-audit.json
python3 preflight.py --capture-stage1-baseline \
  --historical-receipt /caminho/para/web-rollout-after.json \
  --game-rollout-receipt runtime/evidence/game-rollout-after-<UTC>.json \
  --db-audit runtime/evidence/db-audit.json
```

Nunca copie o script de auditoria para dentro do checkout: um arquivo não rastreado
suja a árvore, e o preflight da etapa 2 (`assert_source`) recusa árvore suja.
`runtime/` é ignorado pelo git, então a auditoria e a candidata ficam ali. A captura
não exige `SOURCE_REVISION` nem compara o HEAD com o `game`: ela só lê o Docker e os
recibos. Uma candidata capturada num checkout vale igual em outro, desde que o pino
anterior (`BASELINE_SHA256`) e `DB_SLICE_SQL` sejam os mesmos.

A captura recusa:
- um recibo do `game` ausente, adulterado, sem a conferência do config ou que não
  descreve o `game` vivo;
- `database` ou `web` diferentes do recibo histórico;
- rede ou volume diferentes da baseline fixada.

Só o `game` ganha a proveniência `game_rollout_<UTC>`; `database` e `web` continuam
`historical`. Sem `--game-rollout-receipt`, um `game` recriado continua recusado.

O recorte do banco nunca é aceito em silêncio. Se diferir do da baseline fixada, a
captura exige `--db-audit`, um JSON com:
- `auditor`, `audited_at_utc` e `explanation`;
- `baseline_sha256`: a baseline fixada;
- `db_slice`: igual ao recorte lido agora (`counts` e
  `qa_character_projection_sha256`).

A auditoria vai para a candidata em `db_audit`. A diferença atual (10 → 11 itens)
não prova inserção. A baseline de 06/11 contou `player_items WHERE player_id = 66100`
e fez o hash do player 66100 com
`SHA2(CONCAT_WS('|', id, account_id, name, level, posx, posy, posz), 256)`. O gate
conta `player_id >= 66100` e faz o hash das linhas tabuladas abaixo. São escopos e
métodos diferentes e não comparáveis. A auditoria deve registrar isso.

Para que isso não se repita, a candidata grava `method`, a transação e `sql_sha256`
(o SHA-256 do texto exato de `DB_SLICE_SQL`). Uma baseline com outro `sql_sha256` é
recusada pelo gate. O recorte (`qa-character-projection-equivalent-v1`) é exatamente
`DB_SLICE_SQL` de `stage1_baseline.py`, rodado como
`docker exec canary-core-qa-database-1 mariadb -ucanary -N -B canary -e "<SQL>"`:

```sql
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;
SELECT 'counts', (SELECT COUNT(*) FROM accounts), (SELECT COUNT(*) FROM players),
  (SELECT COUNT(*) FROM player_items), (SELECT COUNT(*) FROM player_items WHERE player_id >= 66100);
SELECT 'player', id, account_id, name, level, vocation, experience FROM players WHERE id >= 66100 ORDER BY id;
SELECT 'item', player_id, pid, sid, itemtype, count FROM player_items WHERE player_id >= 66100 ORDER BY player_id, sid;
COMMIT;
```

As contagens são as quatro colunas da linha `counts`: `accounts`, `players`,
`player_items` e `qa_character_items`. O hash é o SHA-256 da concatenação, na ordem
de saída, de cada linha que começa com `player\t` ou `item\t`, cada uma seguida de
`\n` (UTF-8).

**7. Pino da candidata.** A candidata de 2026-11-08T00:10:45Z foi revisada e
fixada: `stage1-baseline.json` e `BASELINE_SHA256`
`47351521b9b690fce7053e1b6e6e6ea97585f30da0f1a8d4fb5ad41eeb49fb04`. Ela registra
`previous_baseline_sha256`
`272c35fbab6496376a366565ac81368e8885297c1cc9febf7ef73e7cdd554789` (a baseline de
06/11). A auditoria do banco que a acompanha está em `stage1-db-audit-20261108.json`,
byte a byte (SHA-256 em `db_audit.sha256` da baseline).

O `rollback` da etapa 2 volta a imagem `game` desta baseline
(`sha256:358ee666…0181`, revisão de origem `3431b404…`, sem shutdown diário).

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
QA_UP="env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml -f compose.brain-fake.yaml -f compose.game-pin.yaml --env-file .env"
# Host limpo:
python3 preflight.py --brain-fake --approved-revision "$SOURCE_REVISION"
$QA build game web brain
$QA up -d --no-build --no-deps --pull never --wait database game web brain
# Ou upgrade sobre a etapa 1 já de pé (no lugar dos três comandos acima).
# O game NÃO é rebuildado: roda a imagem da baseline pelo ID exato.
python3 preflight.py --upgrade-from-stage1 --approved-revision "$SOURCE_REVISION"
$QA_UP build brain
$QA_UP up -d --no-build --no-deps --pull never --wait game brain
# Nos dois casos, depois do up:
python3 preflight.py --record-brain-image --approved-revision "$SOURCE_REVISION"
$QA exec brain canary-brain status --state /var/lib/canary-human-qa-stage2/ledger.sqlite3
```

Os builds não puxam base: `compose.yaml` e `compose.brain-fake.yaml` têm
`pull: false`, e o preflight recusa outra coisa. Nenhum `up` builda ou puxa imagem
(`--no-build --pull never`), e `--no-deps` impede que o Compose reconcilie
`database` ou `web`.

`--brain-fake` e `--upgrade-from-stage1` gravam o recibo da etapa 2 em
`runtime/evidence/stage2-upgrade-receipt.json`, que `--record-brain-image`
atualiza após o build. A etapa 1 mantém seu `preflight-receipt.json`.

**O upgrade recria o `game`, e isso é esperado.** `compose.brain-fake.yaml`
acrescenta ao `game` `CANARY_BRAIN_CONFIG`, `BOT_POPULATION_REFERENCE_BOTS`, o
`server.json` e o volume do socket; com outra configuração, o Compose recria o
container. O que não muda é a imagem: `compose.game-pin.yaml` fixa `game.image` no
ID exato da imagem `game` da baseline (`sha256:358ee666…0181`) com
`pull_policy: never`. Assim nem um rebuild, nem um pull, nem uma troca da tag
`canary-core-qa-game:local` entre o gate e o `up` mudam o binário. O preflight
renderiza o Compose com esse override e recusa se ele faltar ou fixar outro ID que
não o `image_id` do `game` na baseline; o gate também recusa se a tag local não
apontar para essa imagem. O `#85` (`BASE_IMAGE` fixado por digest) só vale para um
build novo do `game`; não autoriza nem dispara rebuild no upgrade.

Duas revisões ficam separadas, sem uma ser rotulada como a outra:
- a das ferramentas: `SOURCE_REVISION` = HEAD aprovado, que builda o `brain` e
  aparece em `approved_source_revision` e `brain_image.source_revision`;
- a da imagem `game`: o label `org.opencontainers.image.revision` dela
  (`3431b404…`), com proveniência `game_rollout_20261108T000636Z`. Ela vem da
  baseline e do recibo do rollout, nunca do HEAD. Nenhum gate do upgrade exige que
  as duas sejam iguais.

O recibo da etapa 2 guarda o `game` antes (`stage1_upgrade.observed`) e o pino
(`game_image_pin`). Depois do `up`, `--record-brain-image` acrescenta
`stage2_game`, com o `game` antes e depois: outro ID e `CreatedAt`, mas a mesma
imagem pelo ID e a mesma revisão de origem. Ele recusa se o `game` não foi
recriado, se foi rebuildado ou se veio da tag, e também se `database`, `web`, a
rede ou os quatro volumes diferirem da baseline.

### Handoff do build a1d9: adaptador `stage2_handoff.py`

Depois de `$QA_UP build brain`, repetir `--upgrade-from-stage1` recusa a própria
imagem do build autorizado (`assert_images(brain_allowed=False)`), e a ordem acima
não tem gate entre o build e o `up`. Para o build a1d9 já feito, os gates de a1d9
ficam como estão, estritos. O caminho é o adaptador `stage2_handoff.py`, revisado
aqui e executado como **cópia fixada pelo sha256**, fora do checkout a1d9:

- `--source-checkout`: o checkout a1d9 limpo. Só fornece as ferramentas
  (`preflight.py`, `stage1_baseline.py`, importadas sem alteração) e o gravador
  `--record-brain-image`.
- O diretório do projeto Compose é o diretório original de QA, que o manifesto do
  bundle fixa (`qa_project_directory`, com seu `.env`). Arquivo `-f`, mount ou
  diretório do projeto dentro do checkout, ou cópia fora do projeto que não esteja no
  manifesto, é recusa.
- Revisões separadas em todo recibo: ferramentas (a1d9), imagem `brain` (label
  a1d9), imagem `game` (label `3431b404…`) e a revisão do próprio adaptador. Nada é
  rerrotulado.

O manifesto fixado (`qa-stage2-bundle-manifest-a1d9.json`, sha256
`bc4fb5af6c1ff5ff76e08ac15125b463222bcbc27dc98b7b35a75f7f4f4202f0`) liga, e o
adaptador confere ao vivo contra ele:

- cada recibo por caminho absoluto e sha256 (`receipt_files`);
- a imagem `brain` por ID completo, plataforma, label de revisão e tag
  (`brain_image`), contra o manifesto **e** o `docker image inspect`;
- a config do resgate por `rescue_container_config.config_sha256`, com a mesma
  serialização de `container()`: `json.dumps({"config", "host_config"},
  sort_keys=True)` com os padrões do Python (um hash só de `Config` ou com
  separadores compactos não confere);
- o `.env` original pelo sha256 dos bytes crus (`env_file`);
- o render pelo sha256 do stdout cru de `render_argv` e pelo sanitizado.

Fases, cada uma só leitura e com um recibo JSON selado que cita o anterior (caminho
e sha256):

1. `post-build`: todos os recibos do manifesto; imagem `brain`; `.env`; nenhum
   container ou volume `brain`; tags `game`/`web` exatas; identidades, mounts e
   recorte exato; resgate e candidato parados; binds equivalentes aos caminhos do host.
2. `pre-stop`: gate vivo de novo (running/healthy e recorte exato), resgate e
   candidato, e a ausência de humanos: a última mensagem de diagnóstico de âncoras de
   `bot_hibernation.lua` mostra 0 âncoras, fresca e deste container (ver abaixo),
   personagens humanos de QA offline no SQL (corroboração, possivelmente velha), zero
   sessões TCP estabelecidas nas portas 17171/17172 em `/proc/net/tcp` e `tcp6`
   dentro do `game`) e o aviso de janela do coordenador (`--window-notice` e
   `--window-notice-sha256`), além da atestação (`--attested-by`, `--attested-at`).
   Sela `docker stop -t 180 <ID do game>`.
3. `post-stop`: só o `game` pode passar a `exited` (código 0, mesmo ID, `CreatedAt`,
   imagem e config; só o health dele, agora velho, sai da comparação). Banco e `web`
   continuam running/healthy **exatamente**; rede, volumes e o **mesmo** recorte
   exato. Deriva é HOLD: recusa, com o recibo guardado.
4. `bundle`: os 4 Compose, os 2 configs fake e o `.env` pelos hashes; o estado do
   post-stop de novo; outros games preservados e parados; zero writers e nenhum
   container novo; o render (hash privado e sanitizado); os **valores** do ambiente
   por chave (sha256 de `CHAVE=VALOR`, só hashes); os binds. Sela o argv do `up`.
5. `fallback-plan` e `fallback-verify`: o resgate do manifesto (ID, config, imagem,
   mounts, sem dono Compose) parado com código 0 e `restart=no`. Para os containers
   novos de `game`/`brain` (pelos labels), prova zero conexões no banco e sela um
   único `docker start` do resgate.
6. `rescue-verify`: depois desse start, o resgate só conta como usável com um health
   check `healthy` mais novo que o próprio start.

Fallbacks fora do Compose: `qa-game-candidate-3431b404` (`4188037d…b605`) e
`qa-old-rescue-20261107` (`64385641…d608`). Os dois estão `exited`, código 0,
`restart=no`, com um Health "unhealthy" velho. Parados, esse Health é ignorado e
vale exited + 0 + `restart=no` + ID e dono fixados. Só o resgate tem hash de config
no manifesto (`rescue_container_config`) e é conferido por ele; o candidato **não
tem** hash de config no manifesto e é ligado por ID, nome, imagem, `CreatedAt`,
mounts, `restart` e dono. Qualquer start futuro só conta depois de um health check
novo.

Ausência de humanos (substitui o contrato `--native-roster` de b4ea4441, retirado:
a fonte 3431 não tem coletor passivo de GUID → tipo com frescor;
`bot_active_players` é um espelho assíncrono sem época nem watermark). Nada novo no
servidor de QA: nenhum endpoint, reload, instrumentação ou rebuild.

- `bot_hibernation.lua` em 3431b404 (`data/scripts/globalevents/`), linhas 84-89:
  âncoras são os jogadores não-bot **e** os bots assistidos por cast. Linhas 133-141:
  a cada 60 ticks de 300 ms (18 s nominais) ele registra
  `[BotHibernation] %d bots: hibernated=%d awake=%d, %d real players`; o último `%d`
  é o número de âncoras. Com o padrão spdlog de 3431
  (`[%Y-%d-%m %H:%M:%S.%e] [%^%l%$] %v `) e `docker logs --timestamps`, a linha é
  `<RFC3339Nano>Z [AAAA-DD-MM hh:mm:ss.mmm] [info] [BotHibernation] N bots:
  hibernated=H awake=A, K real players `.
- O adaptador liga o sha256 dos bytes do script lidos de dentro do `game` pelo ID
  completo (`docker exec <id> cat`) aos bytes de 3431 (`b2496d78…bf01`), a imagem
  `358ee666…` com revisão 3431, o ID completo e um `StartedAt` inalterado (antes e
  depois da coleta, e desde o pre-stop).
- Coleta `docker logs --timestamps --since 120s <id>` com timeout. O recibo guarda a
  captura crua, o sha256 e os limites de relógio de parede e monotônico.
- Toda linha com `[BotHibernation]` é candidata, com qualquer sufixo. Só é pulada a
  linha benigna da lista fechada, `bot_hibernation.lua:66-67`
  (`[BotHibernation] tick #N firing`, com o prefixo exato do Docker e do spdlog). A
  **última** candidata é interpretada de forma estrita: tem de ser a mensagem de
  âncoras completa, de qualquer valor (não a última zerada). Recusa se ela estiver
  ausente, truncada, no singular, desconhecida (inclusive
  `getBotHibernationStates returned nil`, linha 128), diferente de zero, no futuro,
  com mais de 30 s ou anterior ao `StartedAt`.
- Privacidade: a captura crua fica guardada para auditoria (não é trocada pelas linhas
  extraídas), em `game-log-*.raw.log`. Uma cópia sanitizada para compartilhar,
  `game-log-*.sanitized.json`, guarda só as linhas de `bot_hibernation.lua` que
  passaram na interpretação estrita e o `raw_sha256` do arquivo cru. Recibos e logs
  são gravados 0600 num diretório de evidência 0700. Um diretório ou arquivo
  existente acessível ao grupo ou ao mundo, um componente ou alvo que seja symlink, ou
  um diretório de outro usuário são recusados e nunca consertados; nenhuma evidência
  existente é reescrita.
- Recibo: `native_roster_unavailable=true`, `native_anchors=0` e o SQL como
  corroboração possivelmente velha. Não há `bot_only` nem roster completo; a conta
  65000 não prova tipo, e a contagem de bots da linha vem de um cache, nunca é um
  total nativo.
- Limitação temporal: o timestamp do Docker é o frescor da emissão do log (logger
  assíncrono do spdlog, flush a cada 3 s no máximo), não um relógio independente do
  callback. Entre o último diagnóstico e o stop, um login só é pego pelo TCP.
- No `exec-step` do stop, tudo é refeito (logs, SQL, `tcp`/`tcp6`, aviso de janela) e
  o stop tem de rodar até **5 s monotônicos** depois da checagem final de sessão, com
  os outros limites de frescor ainda válidos. Expirou antes do claim: recusa sem
  mutação e sem claim (o mesmo recibo pode ser tentado de novo, com tudo refeito).
  Expirou depois do claim: recusa sem mutação, mas o claim fica consumido, com um
  resultado `executed: false`; é preciso um novo pre-stop.

Binds no Docker Desktop (WSL): o inspect mostra a origem traduzida. O adaptador
aceita, para o caminho do host `H`, só `H`, `/run/desktop/mnt/host/wsl/Ubuntu` + `H`
ou `/run/desktop/mnt/host/wsl/docker-desktop-bind-mounts/Ubuntu/<sha256(H)>`. A forma
com hash é a que o manifesto real mostra para o mapa e o `initdb`, e os testes
conferem essa equivalência nos dados reais.

Quem executa: Pitagoras, no WSL, roda as fases e cada mutação só como
`stage2_handoff.py exec-step --receipt <recibo> --receipt-sha256 <sha>`. Logo antes
da mutação, ele refaz todos os gates do passo (antes do stop: gate vivo, resgate,
candidato e exclusão humana; antes do `up`: o estado exato do post-stop, o recorte, o
render, o ambiente, outros games, writers). Depois grava um claim durável e atômico
(`O_CREAT|O_EXCL`, fsync do arquivo e do diretório) em
`<projeto>/runtime/evidence/stage2-handoff-claims/`, pela chave sha256 do recibo +
passo, independente de `--evidence`. Só então roda o argv selado, uma vez. Um claim
sem resultado (queda, falha ao gravar o recibo) continua consumido: HOLD, nunca se
repete. Recibo com data no futuro ou com mais de 15 min é recusado. Ninguém redigita
comando, e nada roda `up` sozinho. Depois do `up`, vale o `--record-brain-image` de
a1d9, a partir do checkout. O `stage1_baseline.py rollback` de a1d9 renderiza o
Compose relativo ao próprio checkout, então não é rodado do checkout isolado. O
retorno deste handoff é o fallback.

### Gate de upgrade: comparação exata com a baseline revisada

`stage1-baseline.json` é a baseline da etapa 1 recapturada só em leitura no stage 1
real por Pitagoras em 2026-11-08T00:10:45Z, depois do rollout só do `game`. Ela
está versionada aqui, sanitizada, e fixada pelo SHA-256
`47351521b9b690fce7053e1b6e6e6ea97585f30da0f1a8d4fb5ad41eeb49fb04` em
`stage1_baseline.py`. Se o arquivo mudar um byte, o gate recusa. Uma baseline nova
exige um commit revisado que troque o arquivo e o pino. A anterior, de
2026-11-06T22:20:30Z, fica registrada como `previous_baseline_sha256`
(`272c35fbab6496376a366565ac81368e8885297c1cc9febf7ef73e7cdd554789`).

`--upgrade-from-stage1` (ou `python3 stage1_baseline.py check`, só leitura) recusa
com a lista de diferenças quando qualquer item diverge:

- containers `database`, `game` e `web`: ID, ID e ref da imagem, label
  `org.opencontainers.image.revision`, `CreatedAt`, estado, health e labels
  Compose (`project`, `service`, `config-hash`);
- rede `canary-core-qa_default`: ID, `CreatedAt` e labels;
- os quatro volumes: nome, `CreatedAt` e labels. Um volume recriado com o mesmo
  nome e label tem outro `CreatedAt` e é recusado;
- recorte do banco: as quatro contagens (`accounts`, `players`, `player_items`,
  itens dos personagens de QA) e o SHA-256 da projeção dos personagens de QA;
- nada de `brain` ainda: nem container, nem `brain-ledger`/`brain-socket`, nem a
  imagem `canary-core-qa-brain:local`; e nenhum objeto `canary-core-qa*` estranho
  ou faltando.

Proveniência, separada no código, nos recibos e aqui:

- `historical`: ID, ID da imagem e `CreatedAt` de `database` e `web`. Foram
  cruzados com o recibo histórico `web-rollout-after.json` (SHA-256 na baseline).
- `game_rollout_20261108T000636Z`: ID, ID da imagem, `CreatedAt` e revisão de origem
  do `game`, conferidos com o recibo selado `game-rollout-after-20261108T000636Z.json`
  (SHA-256 na baseline).
- `captured_now`: rede, volumes, labels, estado e o recorte do banco. Foram lidos
  pela primeira vez na captura. São comparados exatamente, mas não são história
  da primeira subida; o recibo histórico não tinha esses campos.

O recorte do banco roda numa transação `REPEATABLE READ`, `READ ONLY`, `WITH
CONSISTENT SNAPSHOT`. A baseline não registra a query da projeção, então
`stage1_baseline.py` usa um equivalente documentado
(`qa-character-projection-equivalent-v1`): personagens de QA são os players com
`id >= 66100` (o `AUTO_INCREMENT` de `prepare.py`; todo player semeado tem id
menor), e o hash cobre as linhas `id, account_id, name, level, vocation,
experience` e `player_id, pid, sid, itemtype, count` dos itens, na saída exata de
`mariadb -N -B`. Se não for o método da captura, o gate recusa (falha fechado)
até alinhar o método ou recapturar a baseline.

**Se a etapa 1 mudou antes do upgrade** (por exemplo, o personagem de QA jogou
e o recorte do banco diverge), o gate recusa e não há como aceitar a diferença em
silêncio. A igualdade exata do recorte é a política decidida e não é afrouxada.

O recorte se move com o jogo de pé. Ele conta todos os `player_items`, e os 50 bots e
o save diário os regravam: o total foi 2597 → 2603 → 2613 entre capturas. A
candidata fixada é só o retrato observado às 00:10:45Z e não promete estabilidade
futura. Se houver deriva, o gate continua recusando. O caminho concreto só é
decidido depois de uma revisão.

**Janela de quietude: não utilizável até existir um desenho revisado.** O #87
registrou esta sequência: parar o `game` com save (`stop -t 180`); auditoria e
captura com o banco estável; revisão e pino; upgrade. Ela não fecha com o que o
código confere. Não execute essa sequência. Não recapture várias vezes até o gate
passar. Os conflitos:

1. **A captura precisa do `game` de pé.** Na baseline atual, o `game` tem
   proveniência `game_rollout_<UTC>`. Ele só entra numa candidata com
   `--game-rollout-receipt`, e então `game_rollout()` lê o `config.lua` vivo
   (`stage1_baseline.py:635`) com `docker exec` no `game`
   (`stage1_baseline.py:506`). Com o `game` parado, o exec falha e a captura
   recusa. Sem o recibo, o `game` recriado não está em `web-rollout-after.json`, e
   a captura recusa do mesmo jeito (`stage1_baseline.py:676-679`).
2. **O gate compara estado e health exatos.** `observe()` grava `status` e
   `health` de cada container (`stage1_baseline.py:110`, `stage1_baseline.py:270`).
   `assert_stage1_upgrade` compara os dois com a baseline
   (`stage1_baseline.py:337-340`), e o preflight do upgrade o chama
   (`preflight.py:342`). A baseline fixada tem os três containers
   `running`/`healthy`. Com o `game` parado, o gate vê `exited` e recusa. Com o
   `game` religado, os bots voltam a gravar e o recorte se move de novo.
3. **Uma baseline capturada com o `game` parado quebraria o rollback.**
   `verify-restored` exige no `game` restaurado o estado e o health da baseline
   (`stage1_baseline.py:401-411`). Ele também exige as portas 17171–17173
   escutando (`stage1_baseline.py:418`). O `game` não pode estar parado e
   escutando ao mesmo tempo.
4. **Sob o pino atual, nenhuma candidata nova passa, nem com o jogo de pé.** O
   único recibo do `game` (`game-rollout-after-20261108T000636Z.json`) foi gravado
   antes da baseline de 00:10:45Z. Ele não pode citar o SHA-256 dela, porque a
   baseline contém o SHA-256 dele. `game_rollout()` exige que o recibo cite o pino
   atual (`stage1_baseline.py:630-632`). Só um rollout novo do `game` (gate, build,
   recriação e recibo) daria um recibo aceito.

Desenhos candidatos, só para revisão (nenhum foi implementado):

- **A. Etapa 1 parada do começo ao fim.** A captura obtém o hash do `config.lua`
  sem `exec`: por `docker cp` do container parado, ou pelo hash do recibo selado
  quando ID e `CreatedAt` batem. A baseline registra o `game` `exited` como estado
  esperado, e o gate roda com o `game` parado. `verify-restored` passa a exigir
  `running`/`healthy` em vez do estado da baseline. Muda captura, gate e rollback.
- **B. Duas fases na captura e no gate.** Fase 1, com o `game` de pé e saudável:
  identidades, health e `config.lua` vivo, num recibo selado. Fase 2, depois de
  `stop -t 180` no mesmo container (mesmo ID e `CreatedAt`): só o recorte do
  banco. A baseline guarda o `running`/`healthy` da fase 1, então o rollback não
  muda. O `up` do upgrade religa o `game`.

Os dois mantêm a igualdade exata do recorte. Os dois também precisam resolver o
conflito 4: aceitar o recibo encadeado pela baseline fixada, ou exigir um rollout
novo. Até um desses desenhos ser revisado, deriva continua sendo recusa.

A captura de uma baseline nova:

```bash
python3 preflight.py --capture-stage1-baseline --historical-receipt /caminho/para/web-rollout-after.json
```

Com a baseline atual, a captura também precisa de `--game-rollout-receipt` e, se
o recorte diferir do pino, de `--db-audit`. Hoje ela recusa pelo conflito 4 acima.

Só leitura no Docker, ele recusa objeto `brain` ou estranho e grava
`runtime/evidence/stage1-baseline-candidate-<UTC>.json` sem sobrescrever nada. A
candidata traz `captured_at_utc`, `provenance` (`historical` e `captured_now`) e o
SHA-256 do recibo histórico. A captura também recusa quando o ID, o ID da imagem
ou o `CreatedAt` de um container não estão, juntos, numa mesma entrada de
`web-rollout-after.json`. A candidata não vale sozinha: depois da revisão, um
commit copia o arquivo para `stage1-baseline.json` e troca `BASELINE_SHA256` em
`stage1_baseline.py`.

Antes do upgrade e antes de qualquer mutação no rollback, o gate também exige
que a tag `canary-core-qa-web:local` ainda aponte ao ID da imagem web na baseline;
se faltar ou tiver sido substituída, recusa. Antes do upgrade, exige o mesmo da tag
`canary-core-qa-game:local` com o ID da imagem `game` da baseline.

O recibo `runtime/evidence/stage2-upgrade-receipt.json` guarda o SHA da baseline,
as classes de proveniência e o que foi observado. No upgrade só o `game` é
recriado, pela configuração do overlay e com a mesma imagem da baseline (pelo ID);
`database` e `web` ficam. Não rode `docker image prune` antes de decidir o
rollback: ele precisa da imagem `game` da baseline.
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

**Rollback para a etapa 1 jogável.** Nunca `down -v`. Com o mesmo
`SOURCE_REVISION` exportado (o Compose exige para renderizar; nada é buildado):

```bash
python3 stage1_baseline.py rollback
```

O script recusa antes de mudar qualquer coisa se a baseline não bater com o pino,
se houver objeto `canary-core-qa*` estranho ou se a imagem `game` da etapa 1
(ID da baseline) não existir mais. Ainda antes do primeiro `stop`, compara com a
baseline as identidades e labels dos containers `database` e `web`, da rede e dos
quatro volumes persistentes (incluindo IDs de containers/imagens/rede e
`CreatedAt`; volumes têm nome e `CreatedAt`). Qualquer diferença recusa o rollback
sem mutações. O `game` da etapa 2 pode ter outro ID, imagem e configuração; estado
e health são verificados depois da restauração, e o recorte do banco pode mudar
com o jogo. Depois executa, nesta ordem, e para no primeiro erro:

1. `$QA stop -t 180 brain game` (salva os personagens);
2. `$QA cp brain:/var/lib/canary-human-qa-stage2/. runtime/evidence/brain/`;
3. `$QA rm -f brain`, só o container do brain;
4. `docker volume rm canary-core-qa_brain-ledger`;
5. `docker tag <ID da imagem game da baseline> canary-core-qa-game:local`;
6. `env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-core-qa -f compose.yaml --env-file .env up -d --no-build --no-deps --wait game`,
   só o Compose da etapa 1, que recria o `game` sem o override e sem recriar
   `database` ou `web`;
7. `docker volume rm canary-core-qa_brain-socket`, livre só agora.

Banco, logs, dados autorais e cache não são tocados. Em seguida, e também sozinho
com `python3 stage1_baseline.py verify-restored`, ele confere e falha fechado:

- nenhum container ou volume `brain` restante;
- `database`, `web`, rede e volumes iguais à baseline; o `game` com novo ID, mas
  com o ID da imagem, o label de revisão, o `config-hash` e o health da baseline.
  Quando o `game` da baseline rodava a imagem pelo ID exato (proveniência
  `game_rollout_<UTC>`), o rollback o recria pela tag local com o Compose da etapa 1.
  Então só a ref (`canary-core-qa-game:local`) e o `config-hash` mudam; o hash
  esperado é o que `config --hash game` do Compose da etapa 1 renderiza. O ID da
  imagem e a revisão continuam exatamente os da baseline: tag apontando para outra
  imagem, ou outra revisão, é recusa;
- `game` com `CANARY_BRAIN_CONFIG` desligado, `GAME_*_PORT` 17171–17173,
  portas publicadas só em `127.0.0.1` e sem o volume do socket;
- `config.lua` do `web` com `gameProtocolPort = 17172`, e `verify_myaac`;
- 17171, 17172 e 17173 escutando em loopback e `login.php` em
  `http://127.0.0.1:18080` respondendo `playersonline`;
- banco íntegro agora: alcançável com o usuário de QA, tabelas `accounts`,
  `players`, `player_items` e `player_storage` presentes e com `CHECK TABLE` OK,
  e ao menos uma conta (`id >= 65001`) e um personagem (`id >= 66100`) de QA.

O recorte do banco não é comparado com a baseline no rollback: jogar nas etapas 1
e 2 muda posição, XP e itens. A continuidade vem da identidade do volume do banco,
que precisa ter o mesmo nome e `CreatedAt` da baseline (volumes Docker não têm
outro ID). O recibo guarda o recorte atual só como informação. Container, rede ou
volume com ID ou `CreatedAt` diferente continua recusado, no upgrade e no rollback.

Só com tudo certo grava `runtime/evidence/stage1-restored-receipt.json`.
