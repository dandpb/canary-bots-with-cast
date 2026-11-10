# Fixture do B1 (companheiros) e baseline S0

Só para o B1: `CORE_QA_PROFILE=b1`, projeto `canary-qa-b1`, `compose.b1.yaml` e
`compose.b1-brain.yaml`. Nunca para a etapa 1 (`canary-core-qa`). Nunca para produção.
Aqui só há arquivos para revisar e testes offline. Nenhum SQL e nenhum Docker foram executados.

## Arquivos

| Arquivo | O que é |
|---|---|
| `b1/seed-companions.sql` | Seed dos três pilotos. Roda uma vez no banco novo do B1. |
| `b1/leader-prep.sql.template` | Preparação do líder. Parametrizada pelo nome do personagem. |
| `b1/slice.sql` | Recorte do banco. Só leitura. Método `b1-fixture-slice-v2`. |
| `b1/server.json` | Config do servidor do brain no B1. Igual à da etapa 1, com `autonomous_bot: 0`. |
| `b1/bot_market_funding.lua` | No-op revisado. Desliga o BotMarketFunding só no B1. |
| `b1/bot_market.lua` | No-op revisado. Desliga o mercado dos bots só no B1. |
| `b1_fixture.py` | Monta o initdb do B1, gera o SQL do líder e os overlays, imprime a instalação, confere o recorte. |
| `test_b1_fixture.py` | Testes offline: números contra a fonte, guarda do seed, overlays, recorte e caminho. |

## Estado declarado (v4 2.4)

Os três pilotos, no banco, antes do primeiro jogo:

| Piloto | Voc. | Nível | Exp | HP | Mana | Cap | Skills | ML | Town, posição | 266 / 268 | Moedas | Banco |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 65001 Grizzle Alyronia (guia) | knight 4 | 20 | 98800 | 365 | 95 | 770 | 50 | 4 | 8, 32369,32241,7 | 14 / 6 | 100 × 3035 | 0 |
| 65003 Sever Heartspear | paladin 3 | 20 | 98800 | 305 | 215 | 710 | 50 | 4 | 8, 32369,32241,7 | 10 / 10 | 100 × 3035 | 0 |
| 65004 Galdon Whitehoof | druid 2 | 20 | 98800 | 245 | 395 | 590 | 50 | 4 | 8, 32369,32241,7 | 6 / 14 | 100 × 3035 | 0 |

- HP e mana cheios. Skills = fist, club, sword, axe, distance, shielding e fishing.
- Orçamento comum: 10000 gp no total. São 100 platinum coins (3035), na backpack, com as poções.
- Banco (`balance`) 0. Gold 3031 e crystal 3043: zero. Poções 236/237: zero. Mortes: zero.
- O líder (preparado depois) tem o mesmo nível, exp, skills 50, ML 4, os valores da vocação
  (sorcerer e druid 245/395/590), o equipamento da vocação, town 8 e o templo.
  Backpack, conteúdo e saldo continuam dele.

### Skills 50 e magic level 4

É uma fixture simplificada de QA. Não é progressão natural. Os pilotos vinham com 100
(`database/bots/02_players.sql`). O `tests/fixture/m5_qa.py:251` já usava 50 e 4.

O motor não volta esses valores:
- O único código que põe skills e ML dos bots (tudo 100) é `BotSystem.activateBot`
  (`data/scripts/lib/bot_system.lua:2657`, `2726-2733`). Ninguém chama essa função.
- O `BotEngine::activateBot` em C++ (`bot_engine.cpp:436-611`) não toca em skills nem ML.
  Nenhum arquivo de `src/creatures/players/bot/` muda skill, ML, nível ou exp.
- Fora disso, só a troca de vocação de Dawnport (`dawnport.lua:65,83`).
- `test_skills_and_magic_level_are_not_reset_by_the_engine` fixa essa lista.

### Equipamento inicial

Comum, de começo de jogo. Nada de MPA, demon armor, DSL nem golden.

| Slot | Knight | Paladin | Druid | Sorcerer (só líder) |
|---|---|---|---|---|
| 1 cabeça | 3351 steel helmet | 3352 chain helmet | 3355 leather helmet | 3355 |
| 4 armadura | 3357 plate armor | 3359 brass armor | 3361 leather armor | 3361 |
| 5 escudo | 3409 steel shield | 3409 steel shield | 3412 wooden shield | 3412 |
| 6 arma | 3264 sword | 3277 spear | 3066 snakebite rod | 3074 wand of vortex |
| 7 pernas | 3557 plate legs | 3372 brass legs | 3362 studded legs | 3362 |
| 8 pés | 3552 leather boots | 3552 | 3552 | 3552 |
| 3 backpack | 2854 | 2854 | 2854 | (do líder) |

Linhas em `data/items/items.xml`: 3351:9555 (armor 6), 3352:9563 (armor 2),
3355:9587 (armor 1), 3357:9603 (armor 10), 3359:9628 (armor 8), 3361:9654 (armor 4),
3557:11144 (armor 7), 3372:9782 (armor 5), 3362:9662 (armor 2), 3552:11090 (armor 1),
3264:8233 (ataque 14), 3277:8405 (ataque 25), 3066:7040 e 3074:7167 (nível 6),
3409:10217 (defesa 21), 3412:10253 (defesa 14), 2854:5931, 3035:6807.
Por que inicial: armadura até 10, escudo até 21, nenhum requisito acima do nível 6.
O peso de tudo, poções e moedas incluídas, cabe no cap (teste).

O motor recoloca esse equipamento. Por isso há o overlay de `equipment.csv`:
- `equipBot` só é chamado ao ativar o bot (`bot_engine.cpp:515`).
- Ele procura a linha `nível * 10 + vocação base` (`bot_data.cpp:1112`) e troca cada slot
  diferente (`bot_data.cpp:1133-1161`). Arma no slot 6, escudo no 5 (`bot_data.cpp:1128-1129`).
  Uma backpack existente fica.
- A tabela vem de `{BOT_AUTHORED_DIR}/equipment.csv` (`bot_data.cpp:95`, `734-770`),
  `data/bot/authored` (`bot_engine_impl.hpp:1405`), isto é `/canary/data/bot/authored`,
  o volume `authored-data` (`compose.yaml:53`). Lida quando o motor carrega os dados.
- O overlay troca só as linhas de nível 20 a 29 das vocações 1-4 por esse equipamento.
  O resto do arquivo fica igual, byte a byte. Assim um nível a mais no B1 não traz de volta
  o equipamento alto.
- **Alcance:** TODO bot do B1 de nível 20 a 29, não só os pilotos, recebe esse equipamento
  comum quando é ativado. `render-overlays` e `install-plan` dizem isso em `loadout_scope`.
- Os `player_items` do seed são a linha de nível 20 do overlay (teste).
- `equipBot` também põe o anel 3099 e a runa 3165 (`bot_data.cpp:1167-1260`). O recorte
  mostra isso no T0 como diferença relatada.

### Ouro: orçamento comum

Cada piloto tem 10000 gp no total: 100 platinum coins (3035), banco 0.
- Por que platinum: uma pilha só, valor exato, 1000 oz de peso, cabe no cap.
  O NPC cobra com `removeMoney(..., useBalance=true)` (`npc_functions.cpp:630`). Ele junta as
  moedas do inventário por valor, parte a pilha e devolve o troco (`game.cpp:2680-2760`).
  O banco só paga o que as moedas não cobrem. Com banco 0, nada sai do banco.
- Compra esperada no Xodet (266 = 50 gp, 268 = 56 gp, `xodet.lua:34-35`), até 20 de cada
  (`bot_brain.cpp:911-920`): knight 1084 gp, paladin 1060 gp, druid 1036 gp. Saem 11 platinum;
  o troco volta em gold.

Dois scripts da imagem ficam desligados só no B1:
- `bot_market_funding.lua:15-38` põe `balance = 100000000000` em todo bot da conta 65000,
  30 s depois de cada start: na memória e por SQL.
- `bot_market.lua` registra os eventos `BotMarketSeller` (30-120 s, `:169-185`),
  `BotMarketAccept` (`:455-474`), `BotMarketMonitor`, `BotMarketPurge`, `BotMarketDepth` e
  `BotMarketTrim`. O seller escolhe qualquer bot da conta 65000, pilotos incluídos, e cobra
  taxa (≥20 gp) ou reserva preço + taxa com `removeMoney`, moedas primeiro
  (`game_bot_market.cpp:147-166`). O accept paga ou cobra o bot (`game_bot_market.cpp:249`,
  `278-282`). Com o no-op, nenhum desses eventos existe no B1.

Como:
- Os dois estão na imagem (`/canary/data/scripts/globalevents`), fora do volume `authored-data`
  (`/canary/data/bot/authored`). Por isso não vão pelo overlay de authored-data.
- Cada um é trocado por um bind só leitura no serviço `game` de `compose.b1.yaml`:
  `b1/bot_market_funding.lua` e `b1/bot_market.lua`, só comentários. O loader lê todo `.lua`
  de `data/scripts` (`scripts.cpp:76`); um arquivo sem código carrega e não registra nada.
- O preflight exige cada bind exatamente uma vez: no `game`, no alvo certo, da origem certa,
  só leitura (`reviewed_targets`, `assert_profile_binds`). Recusa: bind ausente, gravável, de
  outro arquivo, em outro serviço, repetido em outro serviço ou o arquivo em outro alvo.
  A lista de binds do up-gate também só aceita esses arquivos no `game` (`reviewed_placement`).
- A etapa 1 recusa qualquer bind desses alvos ou desses arquivos.
- `render-overlays` e `install-plan` mostram o hash de cada no-op e o do original (`binds`,
  `noop_binds`).

Busca por outros eventos de mercado: só `bot_market.lua` registra eventos `BotMarket*` (além do
funding) e só ele chama `Game.botCreateMarketOffer`/`botAcceptMarketOffer`. Em C++, só a ligação
Lua chama essas funções (`game_functions.cpp:1187,1197`). Teste fixa isso.

Outros caminhos de dinheiro (busca na fonte):
- **Ofertas vencidas.** No start, `IOMarket::checkExpiredOffers` (`canary_server.cpp:91`) devolve
  no banco o valor de ofertas de compra vencidas (`iomarket.cpp:~224`). O banco novo do B1 não tem
  ofertas dos pilotos, e o mercado dos bots não cria mais. Sem efeito.
- **Aluguel de casa.** Os pilotos têm casas (`database/bots/14_houses.sql`) com aluguel não pago.
  `Houses::payHouses` só cobra se `balance >= rent` (`house.cpp:1017`). Com banco 0, não cobra.
  Manda cartas de aviso e, depois de 7, tira a casa. O dinheiro não muda.
- Sem efeito nos pilotos: `equipBot` não cria moedas (pilotos têm backpack, então nem poções);
  `send_first_items.lua` não roda para bots (sem onLogin); `autoBank` desligado; brain só compra;
  `/addmoney` e `/attr` só GM; cancelar oferta (`game_bot_market.cpp:354`) não tem chamador.

### Outras fontes

- Exp: `Player::getExpForLevel` (`player.cpp:4299-4301`). Nível 20 = 98800.
- HP/mana/cap: nível 1 = 150/0 (`schema.sql:56-57,66-67`), cap 400
  (`player.hpp:1737`). Até o nível 8, vocação None (5/5/10, `vocations.xml:3`). Depois, a
  vocação (`player.cpp:3497-3510`; `vocations.xml:15,27,39,51`). Druid: 395 ≥ 120.
- Poções: no nível 20 só 266 e 268 (`bot_potions.hpp:19-22`; `bot_brain.cpp:32-54,96-108`).
- Town 8 = Thais (`data-otservbr-global/lib/tables/town.lua:9`).
- `pid` = slot ou `sid` do container (`iologindata_load_player.cpp:569`).

## Como é aplicado e por que não chega à etapa 1

A identidade do banco vem do portão operacional. É a primeira linha:
- perfil `CORE_QA_PROFILE=b1` e projeto `canary-qa-b1`;
- o preflight confere os binds de cada perfil (`assert_profile_binds`): só o B1 monta
  `runtime/b1/initdb` e `b1/server.json`;
- um volume novo `canary-qa-b1_database`. O MariaDB só roda o initdb num volume vazio.

A guarda do seed é a segunda linha. Antes de qualquer escrita, até da tabela de marca:
- recusa se `qa_b1_fixture` já existe (reaplicação);
- recusa conta ≥65001 ou personagem ≥66100;
- compara cada piloto com a linha inteira de `02_players.sql` (todas as 103 colunas);
- exige zero `player_items`, depot, inbox, mortes e `players_online` dos pilotos;
- exige o número de linhas de `player_storage` de `03_player_storage.sql` (299, 133, 300).
- e as linhas de `player_storage` uma a uma: cada (player_id, key, value) do arquivo 03. Com a chave
  (player_id, key) do `schema.sql`, N iguais e N no total é o mesmo conjunto. Valor trocado ou
  chave trocada com a mesma contagem são recusados.
Qualquer diferença: `SIGNAL`, o init para e nada é escrito. Um banco jogado é recusado.
Depois vêm as escritas numa transação e uma checagem final antes do `COMMIT`.

Passos:
1. `prepare.py` gera `runtime/initdb` como sempre.
2. `CORE_QA_PROFILE=b1 python3 b1_fixture.py prepare-initdb` copia esses arquivos para
   `runtime/b1/initdb` e soma `900_b1_seed_companions.sql`.
3. `CORE_QA_PROFILE=b1 python3 b1_fixture.py render-overlays` grava
   `runtime/b1/authored/equipment.csv` e `hunt_scripts.csv` (só a hunt 399) e
   `runtime/b1/evidence/overlay-manifest.json` com os hashes.
4. Só `compose.b1.yaml` monta o initdb do B1. Só `compose.b1-brain.yaml` monta `b1/server.json`.

## Instalação dos overlays (NÃO executada)

Antes do primeiro start do `game`. `CORE_QA_PROFILE=b1 python3 b1_fixture.py install-plan`
imprime os comandos. Ele recusa outro projeto e qualquer nome da etapa 1 (teste).
Em `deployment/core-qa`:

```
env -u MARIADB_PASSWORD -u MARIADB_ROOT_PASSWORD -u BOT_PLAYERS_ONLINE docker compose -p canary-qa-b1 -f compose.yaml -f compose.brain-fake.yaml -f compose.b1.yaml -f compose.b1-brain.yaml --env-file .env create --no-build --pull never game
docker run --rm --pull never --network none -v canary-qa-b1_authored-data:/canary/data/bot/authored -v <repo>/deployment/core-qa/runtime/b1/authored:/b1-overlay:ro --entrypoint sh canary-qa-b1-game:local -c 'cp /b1-overlay/equipment.csv /b1-overlay/hunt_scripts.csv /canary/data/bot/authored/ && sha256sum /canary/data/bot/authored/equipment.csv /canary/data/bot/authored/hunt_scripts.csv'
```

O `sha256sum` tem de dar os hashes de `overlay-manifest.json`.
Os dois no-ops não precisam de cópia: os binds de `compose.b1.yaml` já os põem no lugar.

## Líder (depois que Daniel cria o personagem)

1. Suba só `database` e `web`. Daniel cria conta e personagem no MyAAC do B1, em privado.
2. `CORE_QA_PROFILE=b1 python3 b1_fixture.py render-leader "<nome>"` grava
   `runtime/b1/leader-prep.sql` e mostra os hashes.
3. Com o personagem offline e o `game` parado:
   `docker exec -i canary-qa-b1-database-1 mariadb -ucanary canary < runtime/b1/leader-prep.sql`.
4. O SQL recusa: sem a marca `b1-companions-v3`; nome ausente ou repetido; id < 66100;
   conta < 65001; ids 6, 65001, 65003, 65004; vocação fora de 1-4; online; outro líder;
   slot com container cheio. Nunca lê conta nem senha.
5. O SQL não dá banco, poções nem moedas ao líder. Só troca os seis slots de equipamento.
   O estado dele (banco, backpack, poções) fica como ele criou (teste).

## Recorte antes/depois

`b1/slice.sql` roda numa transação `REPEATABLE READ`, `READ ONLY`. Cobre os pilotos e todo
personagem ≥66100:

```
docker exec -i canary-qa-b1-database-1 mariadb -ucanary -N -B canary < b1/slice.sql > <ponto>.tsv
python3 b1_fixture.py check s0|leader|ready <ponto>.tsv
```

- Linhas: `fixture`, `humans`, `player` (com skills e ML), `slot` (pid 1-11), `stock`
  (236, 237, 266, 268, 3031, 3035, 3043), `deaths`, `death`.
- Hash: SHA-256 das linhas, na ordem, cada uma com `\n`.
- Toda linha tem a forma da sua marca (número de colunas, números onde há números) e aparece
  uma vez por chave. Linha fora da forma é `malformed`, em todo `check`.
- `check s0`: igual a `python3 b1_fixture.py expected`. Hash S0 esperado:
  `170a78f86420ab6abefaf0d837284a932f2c5867580ee3c466e5f506f90b8b05`.
  É do B1. Não é o `BASELINE_SHA256` da etapa 1.
- `check leader` exige exatamente:
  - as linhas dos pilotos como no S0;
  - exatamente duas linhas de marca, `fixture` e `leader`, e o líder é o nome da marca;
  - `humans 1 1` e um só personagem ≥66100, de conta ≥65001;
  - a linha do líder como declarada, os seis slots do equipamento como linhas inteiras
    (item e quantidade 1), as sete linhas de stock, `deaths 0` e nenhuma linha `death`.
  Linha repetida, a mais ou faltando é problema. Saldo, stock e outros slots do líder só são
  observados: vão em `observed` e no hash.
- `check ready` (prontidão, antes do T0): veja abaixo.
- T0 e T1 (com o `game` ligado): hash e diferenças relatadas.

## Prontidão (depois do start, antes do T0)

`install-plan` imprime os comandos em `readiness` (NÃO executados). Com o `game` saudável há
pelo menos 60 s (o funding esperaria 30 s) e antes do `brain`:
1. `exec -T game sha256sum` dos dois alvos dá o hash de cada no-op.
2. O log do `game` vai para `runtime/b1/evidence/ready/game.log`. `check-log` recusa qualquer
   linha `[BotMarket...]` (funding incluído) ou `[MARKET_...]`.
3. Recorte em `runtime/b1/evidence/ready/db-slice.tsv` e `check ready`.

`check ready` olha o elenco: os 3 pilotos e o líder. Recusa:
- linha de qualquer outro personagem, em qualquer marca (`player`, `slot`, `stock`, `deaths`, `death`);
- personagem do elenco sem exatamente uma linha `player`, as sete linhas de stock e uma `deaths`;
- piloto com banco 100000000000 (o funding rodou de novo) ou qualquer banco diferente de 0;
- piloto com moedas diferentes da fixture (3031 = 0, 3035 = 100, 3043 = 0);
- marca que não seja a do B1 com um líder, linhas fora da forma ou repetidas.
Os valores do resto (HP, anel do `equipBot`, posição) só são observados. Não exige o S0 inteiro.
Marca, `humans` e a escolha do líder são o mesmo código do `check leader` (`identify`).
Do líder, grava banco e stock REAIS como observados, com `recorded_sha256`. Nada é esperado.

Limite: o recorte lê o banco. Um valor só na memória aparece depois que o servidor salva.

## Baseline S0

Quem: o operador. Quando: depois do init do banco e antes do MyAAC, do `game` e de qualquer
login. Tudo vai para `runtime/b1/evidence/s0/`.

| Arquivo | Conteúdo |
|---|---|
| `source.txt` | `git rev-parse HEAD`, `HEAD^{tree}`, `git status --porcelain` vazio |
| `preflight-receipt.json` | Recibo do preflight do B1: render e IDs das imagens |
| `fixture.sha256` | `sha256sum` de `b1/*`, `brain/worker.json`, `compose.b1*.yaml`, `b1_fixture.py` |
| `initdb-manifest.json` | Saída de `prepare-initdb` |
| `overlay-manifest.json` | Saída de `render-overlays` e o `sha256sum` da instalação |
| `elf.sha256` | `canary` e `libbot_engine.so` da imagem do game do B1 |
| `db-slice.tsv`, `db-check.json` | Recorte e `check s0` (o hash acima, sem problemas) |
| `S0.SHA256SUMS` | `sha256sum` de todos acima. Seu hash é o id da baseline S0 |

Ordem:
1. `prepare.py`, `prepare-initdb`, `render-overlays`, preflight do B1, build.
2. `up -d --no-build --pull never --wait database`. Recorte S0 e `check s0`.
3. Instalação dos overlays (acima). Grave os arquivos e o `S0.SHA256SUMS`.
4. Só então: `web`, conta do líder, `leader-prep`, `check leader`, `game`, prontidão
   (`check ready`), `brain`, T0.

## Em aberto

- **Mercado desligado para todos os bots do B1.** O no-op tira o mercado de todos, não só dos
  pilotos (decisão do revisor).
- **Outros bots.** O overlay vale para todo bot do B1 de nível 20 a 29 que for ativado.
- **Docker e MariaDB não executados.** Ordem do initdb, `DELIMITER`, `SIGNAL`, parada no
  primeiro erro, troca do bind pelo alvo e cópia da imagem para o volume vazio. Nos testes,
  a guarda, as escritas, as checagens e o recorte rodam em SQLite; o resto é só texto.
- **Poções e ouro do líder.** O v4 não pede. O SQL do líder não mexe neles.
- **Três pilotos no mesmo tile.** No login o servidor põe cada um num tile livre perto.
