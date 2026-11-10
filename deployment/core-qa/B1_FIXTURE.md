# Fixture do B1 (companheiros) e baseline S0

Só para o B1: `CORE_QA_PROFILE=b1`, projeto `canary-qa-b1`, `compose.b1.yaml` e
`compose.b1-brain.yaml`. Nunca para a etapa 1 (`canary-core-qa`). Nunca para produção.
Aqui só há arquivos para revisar e testes offline. Nenhum SQL foi executado.

## Arquivos

| Arquivo | O que é |
|---|---|
| `b1/seed-companions.sql` | Seed dos três pilotos. Roda uma vez no banco novo do B1. |
| `b1/leader-prep.sql.template` | Preparação do líder. Parametrizada pelo nome do personagem. |
| `b1/slice.sql` | Recorte do banco. Só leitura. |
| `b1/server.json` | Config do servidor do brain no B1. Igual à da etapa 1, com `autonomous_bot: 0`. |
| `b1_fixture.py` | Monta `runtime/b1/initdb`, gera o SQL do líder e o overlay, confere o recorte. |
| `test_b1_fixture.py` | Testes offline: números contra a fonte, escopo do SQL, recorte e caminho. |

## Estado declarado (v4 2.4)

Os três pilotos, no banco, antes do primeiro jogo:

| Pilot | Voc. | Nível | Exp | HP | Mana | Cap | Town | Posição | 266 / 268 | Ouro |
|---|---|---|---|---|---|---|---|---|---|---|
| 65001 Grizzle Alyronia (guia) | knight 4 | 20 | 98800 | 365/365 | 95/95 | 770 | 8 | 32369,32241,7 | 14 / 6 | banco 10000 |
| 65003 Sever Heartspear | paladin 3 | 20 | 98800 | 305/305 | 215/215 | 710 | 8 | 32369,32241,7 | 10 / 10 | banco 10000 |
| 65004 Galdon Whitehoof | druid 2 | 20 | 98800 | 245/245 | 395/395 | 590 | 8 | 32369,32241,7 | 6 / 14 | banco 10000 |

- Poções 236/237 e moedas 3031/3035/3043: zero para os três. Mortes: zero.
- Equipamento (slot: item): 1 golden helmet 3365, 3 backpack 2854, 4 armadura, 5 blessed
  shield 3423, 6 arma, 7 dragon scale legs 3363, 8 golden boots 3555.
  Knight: magic plate armor 3366 e ice rapier 3284. Paladin: 3366 e hunting spear 3347.
  Druid: demon armor 3388 e necrotic rod 3069. As poções ficam dentro da backpack.
- O líder (preparado depois) tem nível 20, 98800 de exp, os valores da vocação
  (sorcerer e druid 245/395/590, paladin 305/215/710, knight 365/95/770), o mesmo
  equipamento da vocação, town 8 e o templo. Backpack, conteúdo e saldo continuam dele.

### Fontes

- Exp: `Player::getExpForLevel` (`src/creatures/players/player.cpp:4299-4301`). Nível 20 = 98800.
- HP/mana/cap: nível 1 = 150 HP e 0 de mana (`schema.sql:56-57,66-67`) e 400 de cap
  (`capacity = 40000`, `src/creatures/players/player.hpp:1737`). Até o nível 8 o ganho é o da
  vocação None (5/5/10, `data/XML/vocations.xml:3`); depois, o da vocação
  (`player.cpp:3497-3510`; knight 15/5/25, paladin 10/15/20, druid e sorcerer 5/30/10,
  `vocations.xml:15,27,39,51`). Confere com o knight 365/95 de `tests/fixture/m5_qa.py:353-355`
  e o cap 770 de `m5_qa.py:251`. Druid: 395 ≥ 120 (`bot_party.cpp:1553-1554`).
- Equipamento: linha de nível 20 de `data/bot/authored/equipment.csv` (a mesma de
  `m5_qa.py:252-268`). `equipBot` põe a arma (`slot_right`) no slot 6 e o escudo no 5
  (`src/creatures/players/bot/bot_data.cpp:751-752,1122-1129`). O seed usa a mesma posição.
- Poções: no nível 20 só 266 e 268 contam e são compradas (`bot_potions.hpp:19-22`;
  `brainPotions`, `bot_brain.cpp:96-108`; `brainSupplyItems`, `bot_brain.cpp:32-54`).
  Total 20 e cada tipo abaixo de 20, então o resupply compra os dois (`bot_brain.cpp:911-920`).
  A divisão segue a vocação: knight mais vida, druid mais mana, paladin meio a meio.
  Compra esperada no NPC (Xodet, 266 = 50 gp, 268 = 56 gp, `xodet.lua:34-35`):
  knight 6+14 = 1084 gp, paladin 10+10 = 1060 gp, druid 14+6 = 1036 gp. Depois, 20/20.
- Ouro no banco (`players.balance`, `schema.sql:95`). O orçamento da compra é
  `getMoney() + getBankBalance()` (`bot_brain.cpp:911`). O NPC paga com
  `removeMoney(..., useBalance=true)` (`npc_functions.cpp:630`; `game.cpp:2680-2740`): primeiro o
  inventário, depois o banco. Banco não pesa e é o que `m5_qa.py:251,357` usou.
- Town 8 = Thais (`data-otservbr-global/lib/tables/town.lua:9`). Templo (32369,32241,7)
  (`m5_qa.py:281-283`).
- Itens: `data/items/items.xml` (266:427, 268:434, 236:401, 237:406, 3031:6790,
  3035:6807, 3043:6839, 2854:5931, 3365:9687, 3366:9704, 3388:9957, 3363:9670,
  3555:11122, 3423:10409, 3284:8516, 3347:9498, 3069:7080, 3072:7133).
- Colunas: `players` (`schema.sql:49-98`), `player_items` (`schema.sql:645-659`;
  `pid` = slot ou `sid` do container, `iologindata_load_player.cpp:569`),
  `player_deaths` (`schema.sql:578`), `players_online` (`schema.sql:552`).

## Como é aplicado e por que não chega à etapa 1

1. `prepare.py` gera `runtime/initdb` como sempre. Nada muda nele.
2. `CORE_QA_PROFILE=b1 python3 b1_fixture.py prepare-initdb` copia esses arquivos, byte a
   byte, para `runtime/b1/initdb` e soma `900_b1_seed_companions.sql`. Grava
   `runtime/b1/evidence/initdb-manifest.json`. Sem `CORE_QA_PROFILE=b1`, recusa.
3. Só `compose.b1.yaml` monta `runtime/b1/initdb` em `/docker-entrypoint-initdb.d`. Mesmo
   alvo do `compose.yaml`: o Compose troca o bind pelo alvo. O MariaDB roda o initdb só num
   volume vazio (`canary-qa-b1_database`), em ordem de nome, depois do `099_ids.sql`.
4. Só `compose.b1-brain.yaml` monta `b1/server.json` no lugar de `brain/server.json`.
   O socket segue `/var/lib/canary-human-qa-stage2/socket`, igual ao `worker.json`, mas no
   volume `canary-qa-b1_brain-socket` do projeto B1.

Proteções:
- `compose.yaml`, `compose.brain-fake.yaml` e `brain/server.json` não mudaram
  (`test_b1_profile.py` fixa os bytes).
- O preflight confere o bind de cada perfil (`PROFILES[...]["binds"]`,
  `assert_profile_binds`). O render do B1 com `runtime/initdb` ou `brain/server.json` é
  recusado. O da etapa 1 com os do B1 também.
- O seed recusa (SIGNAL) um banco com conta ≥65001 ou personagem ≥66100. Um banco jogado,
  como o da etapa 1, nunca é alterado.
- O SQL do líder exige a marca `qa_b1_fixture` (criada só pelo seed). Sem ela, recusa.
- Toda escrita usa ids explícitos e termina com uma checagem. Diferença = SIGNAL, sem COMMIT.

## Líder (depois que Daniel cria o personagem)

1. Suba só `database` e `web`. Daniel cria conta e personagem no MyAAC do B1, em privado.
2. `CORE_QA_PROFILE=b1 python3 b1_fixture.py render-leader "<nome>"` grava
   `runtime/b1/leader-prep.sql` e mostra os hashes.
3. Com o personagem offline e o `game` parado:
   `docker exec -i canary-qa-b1-database-1 mariadb -ucanary canary < runtime/b1/leader-prep.sql`
   (mesma forma do `README.md:279`).
4. O SQL recusa: banco sem a marca do B1; nome ausente ou repetido; id < 66100; conta
   < 65001; ids 6, 65001, 65003, 65004; vocação fora de 1-4; personagem online; outro
   líder já preparado; slot com container cheio. Nunca lê conta nem senha.

## Recorte antes/depois

`b1/slice.sql` roda numa transação `REPEATABLE READ`, `READ ONLY`, como o `DB_SLICE_SQL`
da etapa 1 (`README.md:280-288`). Cobre os pilotos e todo personagem ≥66100:

```
docker exec -i canary-qa-b1-database-1 mariadb -ucanary -N -B canary < b1/slice.sql > <ponto>.tsv
python3 b1_fixture.py check s0|leader <ponto>.tsv
```

- Linhas: `fixture`, `humans`, `player`, `slot` (pid 1-11), `stock` (236, 237, 266, 268,
  3031, 3035, 3043), `deaths`, `death`.
- Hash (`b1-fixture-slice-v1`): SHA-256 das linhas marcadas, na ordem, cada uma com `\n`.
- `check s0`: igual a `python3 b1_fixture.py expected`. Hash S0 esperado:
  `b90457a629fa43b3a25e6afd8d7deac0d1356b70fd68c183871fb8011a6b9084`.
  É do B1. Não é o `BASELINE_SHA256` da etapa 1.
- `check leader`: pilotos como no S0 e o líder como declarado.
- T0 e T1 (com o `game` ligado): só hash e diferenças relatadas. Ao ativar, o motor põe
  HP/mana no máximo, ajusta a town pela posição e completa itens (anel 3099, runa 3165)
  (`bot_engine.cpp:503-515`; `bot_data.cpp:1104-1260`).

## Baseline S0

Quem: o operador. Quando: depois do init do banco e antes do MyAAC, do `game` e de qualquer
login. Tudo vai para `runtime/b1/evidence/s0/`.

| Arquivo | Conteúdo |
|---|---|
| `source.txt` | `git rev-parse HEAD`, `git rev-parse HEAD^{tree}`, `git status --porcelain` vazio |
| `preflight-receipt.json` | Recibo do `preflight.py --brain-fake` do B1: render (`compose_redacted_sha256`) e IDs das imagens |
| `fixture.sha256` | `sha256sum` de `b1/seed-companions.sql`, `b1/leader-prep.sql.template`, `b1/slice.sql`, `b1/server.json`, `brain/worker.json`, `compose.b1.yaml`, `compose.b1-brain.yaml`, `b1_fixture.py` |
| `initdb-manifest.json` | Saída de `prepare-initdb` (hash de cada arquivo do initdb do B1) |
| `overlay.json` | Saída de `render-overlay`: `hunt_scripts.csv` só com a hunt 399 ligada |
| `elf.sha256`, `elf.file.txt` | `canary` e `libbot_engine.so` da imagem do game do B1, hash e `file` (x86-64) |
| `socket.txt` | `docker volume inspect canary-qa-b1_brain-socket` e o caminho do socket |
| `db-slice.tsv`, `db-check.json` | Recorte e `check s0` (tem de dar o hash acima, sem problemas) |
| `S0.SHA256SUMS` | `sha256sum` de todos os arquivos acima. Seu hash é o id da baseline S0 |

Ordem:
1. `prepare.py`, `prepare-initdb`, `render-overlay`, preflight do B1, build.
2. `$B1 up -d --no-build --pull never --wait database`. Recorte S0 e `check s0`.
3. Grave os arquivos e o `S0.SHA256SUMS`.
4. Só então: `web`, conta do líder, `leader-prep`, `check leader`, overlay, `game`, `brain`.

## Em aberto (não decidido pela fonte)

- **Equipamento "comum".** A linha de nível 20 do `equipment.csv` é de alto nível (golden
  helmet, MPA/demon armor, DSL, golden boots, blessed shield). O motor recoloca essa linha
  ao ativar o bot (`bot_engine.cpp:515`; `bot_data.cpp:1104-1160`). O SQL não consegue deixar
  os pilotos com itens comuns. Isso exige um overlay de `equipment.csv`. O líder usa a
  mesma linha, por paridade. Decisão de Socrates.
- **Skills e magic level.** O seed não muda skills (100) nem magic level (100) de
  `02_players.sql`. O `m5_qa.py:251` usou skills 50 e ML 4 no knight. Decisão pendente.
- **Overlay da hunt 399 no volume `authored-data`.** `render-overlay` gera o arquivo e o
  hash. Como colocá-lo no volume antes do primeiro start do `game` (por exemplo
  `docker compose cp` num container criado e parado) não está implementado nem testado.
- **Poções e ouro do líder.** O v4 não pede. O SQL do líder não mexe neles.
- **Comportamento do MariaDB e do Compose.** Não executado aqui: ordem do initdb, banco
  padrão `canary`, `DELIMITER` no cliente, parada no primeiro erro e troca do bind pelo
  alvo. O S0 confirma no log do init (`900_b1_seed_companions.sql`) e no recorte.
- **Três pilotos no mesmo tile do templo.** No login o servidor põe cada um num tile livre
  perto. O S0 mostra a posição do banco, não a do jogo.
