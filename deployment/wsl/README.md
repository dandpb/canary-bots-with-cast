# Canary com bots e cast no WSL

Para instalar do início, configurar LiteLLM com OpenAI/Gemini e preparar replay
e benchmark, use o [guia de configuração inicial](../brain/SETUP.pt-BR.md).

Implantação local em `/home/daniel/canary-bots-wsl`. O código executado fica no
disco Linux; os ajustes locais são preservados. As validações históricas abaixo
registram suas revisões; confira imagem/binário/configuração antes de atribuir
uma revisão da `main` ao runtime atual.
O projeto Compose é `canary-bots-wsl` e usa volumes próprios. O banco não publica
porta no host. Jogo e site publicam somente em `127.0.0.1`.

## Operação

No Ubuntu/WSL:

```bash
cd /home/daniel/canary-bots-wsl/deployment/wsl
docker compose up -d database game web
docker compose ps
docker compose logs --tail=100 game
python3 smoke.py
```

Site: `http://127.0.0.1:8080/`. Serviço HTTP de login:
`http://127.0.0.1:8080/login.php`. Porta do jogo: `7172`; login binário: `7171`;
status: `7173`. A conta administrativa inicial deve ser configurada com credenciais locais seguras.
O cast usa a conta `@cast`, sem senha, após os bots carregarem. O cliente não
faz parte desta implantação; use OTClient Redemption com os assets compatíveis.
O servidor compilado anuncia o protocolo 15.00; configure o cliente como `1500`.

O banco foi importado com o schema e os sete seeds de `database/bots/` na ordem
documentada, mais `runtime-schema.sql`: persistência/telemetria ausentes da
migração distribuída e campos de charms com a mesma capacidade `uint32_t` do
código nativo. A configuração local mantém os 997 bots, garantindo a inclusão dos
três pilotos de IA. A seleção estratificada de 500 excluiria o piloto 65003.
Para ajustar, altere
`BOT_PLAYERS_ONLINE` no `.env` local e recrie o serviço `game`.
Na `main`, a inicialização carrega 50 bots por lote e pausa 35 segundos entre
lotes. O Grizzle está no primeiro lote; os 997 ficam disponíveis gradualmente.

O mapa é `otservbr.otbm` da release upstream `v3.4.1`, correspondente à base de
fevereiro de 2026. SHA-256:
`a80de1dda6a9aca3956a9d5b7fb2e0caebb451570d26853fc21beb40d5f31da2`.
Ele fica em `runtime/world/` e não é versionado.

A limpeza por inatividade e a cobrança automática de aluguel ficam desativadas
neste ambiente local. Os seeds têm datas antigas; os padrões de produção
retomariam as casas e transfeririam a decoração antes da ativação dos bots.

## Identidade do build nativo

O build de release usa `Dockerfile.release`; o Dockerfile legado e o Compose
fixado de core-qa permanecem inalterados para preservar seus recibos.
O build de release exige um clone independente nativo do Linux, completo, limpo e
com commit: não use um checkout Windows com conversão CRLF, linked worktree ou
clone com `objects/info/alternates`. Execute o build nesse clone, com
`SOURCE_REVISION` igual ao HEAD e
`BUILD_GIT_DIRECTORY` apontando para seu diretório Git absoluto:

```bash
export SOURCE_REVISION="$(git rev-parse HEAD)"
export BUILD_GIT_DIRECTORY="$(git rev-parse --absolute-git-dir)"
python3 verify-build-source.py --source "$(git rev-parse --show-toplevel)" --revision "$SOURCE_REVISION"
docker compose build game
```

No comando Docker direto, use `-f deployment/wsl/Dockerfile.release` e
`--build-context gitmeta="$BUILD_GIT_DIRECTORY"`. O contexto normal continua
excluindo `.git`; o contexto nomeado fornece os metadados somente durante o
`RUN` de compilação, em montagem somente leitura. Nenhum `.git` é copiado para
as imagens. O CMake identifica o mesmo commit e estado limpo para executável e
biblioteca. Os bytes de cada arquivo são conferidos contra os objetos do commit,
mesmo quando flags do índice escondem uma alteração. Revisão divergente, árvore alterada ou metadados ausentes interrompem
o build em vez de gerar um binário com identidade `unknown`.

Uma cópia de implantação sem `.git` não é fonte de build: construa as imagens
num checkout limpo separado e atualize o runtime existente com as imagens
verificadas, preservando seus arquivos privados e volumes. A label OCI continua
sendo metadado da imagem e não substitui a identidade nativa verificada.

### Perfil ARM64 (aarch64)

`Dockerfile.release.arm64`: base `ubuntu:24.04` fixada pelo digest do manifesto
`linux/arm64`, triplets vcpkg target/host `arm64-linux` e
`CANARY_TARGET_ARCH=armv8-a` no lugar de `-march=native`, para que binário e
`libbot_engine.so` usem a mesma linha de base ARMv8-A portável em vez da
microarquitetura do host de build. Verificador de fonte, `SOURCE_REVISION`,
targets e estágio de runtime são idênticos ao `Dockerfile.release`, que
continua sendo o perfil padrão para WSL/x86-64. Há dois modos de execução:

**Modo 1 — host AArch64 nativo.** Sem emulação; os triplets são coerentes
por construção. Build direto no clone limpo, como no perfil x86-64:

```bash
docker build -f deployment/wsl/Dockerfile.release.arm64 \
  --build-context gitmeta="$BUILD_GIT_DIRECTORY" \
  --build-arg SOURCE_REVISION="$SOURCE_REVISION" .
```

**Modo 2 — executor isolado amd64 (WSL) por cross-build.** O executor
designado (Pitagoras) roda WSL amd64: o build é feito por emulação (ou nó
ARM externo) com `--platform linux/arm64`. Sob emulação, todas as etapas —
apt, bootstrap e ferramentas de host do vcpkg, compilador — executam como
arm64, mantendo `--host-triplet=arm64-linux` coerente.

*Inventário do builder (readonly, autorizado no estágio atual; este*
*repositório não instala binfmt nem provisiona builder):* o build é
vinculado a um builder **nomeado** — escolha um, registre a identidade e
use o mesmo nome no comando de build:

```bash
docker buildx ls                          # lista builders; 'platforms' = capacidade ANUNCIADA, não prova
docker buildx inspect <BUILDER> --bootstrap=false
# registre no handoff: driver, nó(s) e endpoint(s) deste builder
```

*Aviso de identidade da sonda:* `docker run` executa pelo daemon Docker
corrente, que pode ser **diferente** do builder selecionado pelo
`buildx build` — sucesso local (QEMU) não atesta builder remoto, e um nó
ARM externo pode executar etapas ARM mesmo com o daemon local incapaz.
Uma sonda de execução só vale se rodar **pelo mesmo builder nomeado**
(por exemplo, um build mínimo `docker buildx build --builder <BUILDER>
--platform linux/arm64`); como execução de container é ação distinta do
inventário readonly autorizado, a capacidade de execução do builder fica
**explicitamente não comprovada** até o build autorizado estabelecê-la.

*Build (somente quando autorizado), com builder nomeado, plataforma*
*explícita, recursos limitados e saída identificada:*

```bash
docker buildx build --builder <BUILDER> \
  -f deployment/wsl/Dockerfile.release.arm64 \
  --platform linux/arm64 \
  --build-context gitmeta="$BUILD_GIT_DIRECTORY" \
  --build-arg SOURCE_REVISION="$SOURCE_REVISION" \
  --build-arg BUILD_JOBS=2 \
  -t canary-game:arm64-"$SOURCE_REVISION" \
  --output type=docker .
docker image inspect canary-game:arm64-"$SOURCE_REVISION" \
  --format '{{.Architecture}} {{index .Config.Labels "org.opencontainers.image.revision"}}'
# esperado: arm64 <SOURCE_REVISION>
```

*Limites do modo emulado:* dependências do vcpkg dominam o tempo e podem
levar horas; mantenha `BUILD_JOBS` contido (o padrão do perfil é 3; 2 é um
ponto de partida seguro sob QEMU), execute apenas o build — nenhum serviço,
restart ou uso da máquina de produção nesta etapa — e exporte a imagem com
tag, label e identidade do builder (driver/nó/endpoint) registradas no
handoff antes de qualquer uso.

## Gateway LiteLLM no mesmo projeto

Os serviços opcionais `litellm`, `litellm-db` e `litellm-redis` pertencem ao projeto
`canary-bots-wsl`, junto de database/game/brain/web. O PostgreSQL exclusivo
persiste usuários, sessões e configurações do painel. O Redis permanente tem
volume próprio para coordenação/autenticação; ambos ficam sem portas no host.
Redis não substitui o ledger SQLite nem habilita cache de respostas: preserve
`litellm_settings.cache: false` e `router_settings.cache_responses: false`.
Na instalação nova, prepare os arquivos e inicie o gateway como abaixo.
Em uma atualização, os arquivos existentes são preservados: siga primeiro a
[migração de coordenação Redis](../brain/SETUP.pt-BR.md#redis-de-coordenação-e-número-de-workers)
para derivar a política e incluir o override ativo antes de recriar `litellm`.
O helper `--coordination` aceita JSON; o guia também cobre políticas YAML.

```bash
cd /home/daniel/canary-bots-wsl/deployment/wsl
python3 setup-gateway.py
docker compose --profile gateway up -d --build --wait litellm
docker compose --profile gateway ps litellm litellm-db litellm-redis
```

O endpoint local é `http://127.0.0.1:4000/v1`; outros serviços deste Compose podem
usar `http://litellm:4000/v1`. A preparação inicial deixa a lista de modelos vazia:
o container pode ficar saudável, mas as chamadas de inferência permanecem
bloqueadas até configurar modelos e credenciais autorizados. Isso não muda o
provider do worker existente nem inicia testes pagos.

O painel fica em `http://127.0.0.1:4000/ui`: usuário padrão `admin`; a senha é
`UI_PASSWORD` se definida em `runtime/secrets/litellm-ui.env`, senão
`LITELLM_MASTER_KEY` do arquivo protegido `runtime/secrets/litellm-worker.env`.
Não compartilhe essa chave. A imagem oficial inclui Prisma e executa as
migrações na inicialização. O erro `Not connected to DB!` indica ausência
da conexão PostgreSQL, mesmo quando as credenciais de login estão corretas.

Os arquivos locais são `runtime/config/litellm.yaml` e os arquivos protegidos
`runtime/secrets/litellm-{provider,worker,db,ui,redis}.env`. A preparação preserva
senhas e `LITELLM_SALT_KEY` existentes; mantenha essa salt junto do backup do
banco para conservar o acesso aos dados criptografados.
Para uma configuração preexistente, acrescente explicitamente
`general_settings.custom_auth_settings: {mode: auto}` e recrie o gateway:
isso permite que sessões administrativas sejam validadas pelo LiteLLM.
A credencial do worker continua restrita às rotas e à identidade do benchmark;
suas falhas de política nunca passam para a autenticação administrativa.
Reutilize as credenciais nomeadas `openai` e `gemini` cadastradas na UI e configure
os aliases `canary-openai`/`canary-gemini` pelo
[exemplo com credenciais nomeadas](../brain/gateway/gateway.named-credentials.example.json),
seguindo a [etapa de associação de modelos](../brain/SETUP.pt-BR.md#4-cadastrar-credenciais-e-associar-modelos).
Copie somente `model_list`, mantendo a política do gateway e a coordenação Redis.
Após alterar a configuração, recrie somente `litellm` e revalide sua identidade.
Use o serviço deste Compose para a implantação WSL; o Compose independente em
`deployment/brain/gateway/` fica disponível para outros ambientes isolados.

## Worker de IA

O perfil `ai` usa a imagem `canary-bots-wsl-brain:local`; um merge não recompila
essa imagem. Para a configuração inicial, siga a
[etapa do worker LiteLLM](../brain/SETUP.pt-BR.md#6-configurar-o-worker-com-uma-rota-litellm),
que inclui os comandos de build e inicialização: configure `provider: litellm`,
prepare `runtime/secrets/litellm-client.env` com permissão `0600` e apenas
`LITELLM_API_KEY`, e preserve o ledger canônico existente em `brain-state`.
As credenciais OpenAI/Gemini permanecem no gateway.

O template de `setup.py` e a montagem `openai.env` do Compose base pertencem ao
acesso direto OpenAI legado; `setup.py` não cria esse arquivo. No fluxo LiteLLM,
substitua essa montagem pela de `litellm-client.env` e ajuste `credential_file`
conforme o guia antes de iniciar `brain`. Preserve as configurações locais
existentes. Iniciar o provider real pode gerar consumo. Não envie chaves pelo chat.

As configurações em `runtime/config/` selecionam os bots 65001, 65004 e 65003,
modo ativo, com o bot 65001 como explorador autônomo. O worker mantém o limite
de USD 50/mês da implementação. O aprendizado dos demais pilotos permanece
desativado; o explorador segue a política específica documentada em
`deployment/brain/README.md`. Sem heartbeat do worker, o motor nativo continua
responsável pelos bots.

## Build e dados

O Dockerfile compila `canary` e `bot_engine` juntos, com o baseline vcpkg fixado,
sem exigir credenciais de cache. O site deriva da imagem local já existente
`otbr-myaac:latest`, com o login cast e o plugin worldmap deste repositório.
O artwork opcional da visão geral do worldmap não é distribuído.

`patch-myaac-status.php` aceita a porta numérica retornada pelo MyAAC; o código
original testava índices de string e recaía em 7171, exibindo offline mesmo com
7173 configurada. O World Map usa URLs relativas à origem para funcionar tanto
em `127.0.0.1` quanto em `localhost`. O smoke test verifica o banner online e a
origem do endpoint de posições nas duas formas de acesso.

```bash
cd /home/daniel/canary-bots-wsl
python3 deployment/wsl/setup.py
cd deployment/wsl
docker compose build game web
docker compose --profile ai build brain
```

`setup.py` preserva o `.env` e as configurações existentes. Os seeds são aplicados
pelo MariaDB apenas quando seu volume está vazio. Os volumes antigos `otbr_*`
não são utilizados. O volume `canary-bots-wsl_database` da primeira tentativa
incompleta foi preservado; o banco operacional usa
`canary-bots-wsl_database-seeded`.

Para parar sem excluir dados, use os mesmos arquivos Compose/overrides ativos
e `docker compose --profile ai --profile gateway stop -t 180`; os perfis incluem
os serviços opcionais. Encerre antes os harnesses/gateways temporários por seus
launchers, preservando logs e verificando a remoção dos CIDs próprios. Os logs
de build ficam neste diretório. Não use `down -v` para uma parada normal.

As edições de rotas feitas dentro do jogo são preservadas no volume
`authored-data`. Uma atualização dos CSVs da imagem não substitui automaticamente
esse volume: compare e sincronize as alterações antes de atualizar seus dados.

## Monitorar o explorador

O painel de supervisão está em **http://127.0.0.1:8091/**. Ele permite conversar
com Grizzle, guardar orientações para as próximas decisões, evitar rotas por
30 minutos, pausar, retomar e recuperar uma tarefa sem reiniciar o jogo.
No modo **Conversar**, a mensagem não altera o objetivo. **Orientar e agir**
permite ações atualmente oferecidas pelo servidor. O histórico distingue um
pedido de uma ação aceita ou concluída. A proteção automática espera cinco
minutos sem progresso e respeita combate, HP e limites de repetição.
Orientações e restrições persistem no volume `brain-state`; não são treinamento
dos pesos do modelo. Veja os limites e a interface em `deployment/brain/README.md`.

Com o Docker disponível no Windows ou WSL, execute:

```bash
python deployment/wsl/monitor-bot.py --seconds 300 --interval 30
```

O monitor registra posição, andar, objetivo, script e waypoint da IA, abates,
vida, suprimentos e XP real em `deployment/wsl/runtime/monitor-grizzle.jsonl`.
Uma execução sem `--seconds` coleta uma amostra e compara com o histórico.
`--require-floor 8` termina com falha se nenhuma amostra alcançar esse andar.
`--require-xp-increase` exige aumento real de XP durante a janela, e
`--require-level-increase` exige uma subida de nível; use uma janela que inclua
combate para essas verificações.
Suspeita de travamento exige cinco minutos sem movimento, avanço ou novos
abates durante uma tarefa que deveria progredir. Combate parado e espera
precisam ser avaliados junto com o objetivo.

Todos os bots nativos recebem XP real e sobem de nível pelo mesmo fluxo dos
jogadores, incluindo os aumentos normais de atributos, mesmo sem o brain ativo.
Nível e experiência são carregados e salvos pelos registros normais do personagem.
Os checkpoints preservam o progresso durante hibernação e reconexão; gravações
pendentes ou com falha retêm o Player para reutilização e nova tentativa de save.
A simulação de hibernação não fabrica XP. O Grizzle começou no nível 8 com 4.200 XP.
O cast e o monitor mostram o objetivo e waypoint da IA para evitar confusão com
o estado ambiente anterior `City Walk`.

## Validação desta implantação

Os três serviços `database`, `game` e `web` ficaram saudáveis. Após uma parada
normal (código 0), os 997 estados foram salvos e restaurados; as 794 casas dos
bots foram mantidas. O teste HTTP de cast retornou 997 personagens e o protocolo
nativo de status anunciou 15.0 com 997 jogadores. O novo boot não apresentou
erros de SQL nem tabelas ausentes. Há mensagens herdadas de callbacks de NPC
quando um bot fica indisponível; esse teste não é uma validação completa de
gameplay pelo cliente.

A imagem do worker passou em 34 testes Python e na checagem de tipos. O lint
encontrou 10 problemas de ordenação de imports nos testes/ferramentas já existentes.
Após autorização, a credencial foi instalada no arquivo protegido do WSL e o
perfil `ai` foi iniciado. O servidor confirmou `mode=active` e
`worker_alive=true` para os pilotos 65001, 65004 e 65003. O explorador 65001
publicou observações recentes; chamadas reais de Responses e Decisions foram
concluídas sem erros e contabilizadas no ledger persistente, mantendo o teto
de USD 50/mês. Os outros dois pilotos recebem objetivos de IA quando integram
uma party humana.

Na atualização para a `main` `7a61f9540`, o explorador deixou de aceitar uma
continuação vazia como trabalho quando há ações úteis disponíveis. O caso real
ficava em `TRAVEL_TO`, waypoint 102, sem movimento ou objetivo de IA. Após a
atualização, o servidor aceitou `resupply` e o Grizzle avançou de
`(32937,32096,6)` para `(32962,32076,6)` na janela de 25 segundos. Os testes de
Lua/LuaJIT, a publicação do mapa e o login cast também passaram. As imagens de
jogo e worker carregam o label OCI com a revisão completa implantada.

Na correção local seguinte, a IA passou a usar o planejador de portais quando
o próximo waypoint está em outro andar. Portais de caminhada são reconhecidos
pelo seguidor antes desse desvio, para que uma descida bem-sucedida não provoque
uma tentativa de voltar ao andar anterior. A progressão foi liberada para o
explorador autônomo pelo fluxo normal de XP e avanço de atributos do Player.
O cast também mostra o objetivo e waypoint do brain, nível e XP reais.

A validação usou o mapa e combate reais: XP de 4.200 para 4.581, entrada no andar
8 a partir do 7 e avanço de waypoints. O XP de 4.341 foi mantido durante a
recarga da biblioteca. Essa recarga reposicionou o personagem em Carlin; a
posição anterior em Venore foi restaurada antes da validação de caminhada,
sem colocar o personagem no destino subterrâneo. A imagem de jogo recebeu a
mesma biblioteca recarregada, preservando a correção no próximo reinício. Os
34 testes do worker, a checagem de tipos e o smoke de web/mapa/cast passaram.
O monitor do servidor verifica a navegação nativa; os testes Python do worker
não substituem essa validação com o mapa carregado.

Na correção seguinte, objetivos do brain passaram a usar o detector nativo de
caminhada bloqueada antes de esperar pela fila de passos. Uma fila parada agora
provoca recálculo do caminho; a chegada encerra a retirada sem iniciar outra
caminhada. Os campos `walk_queue`, `pending_walk_pause`, `floor_change` e `home`
do comando `brain status` permitem distinguir fila bloqueada de pausa normal.

O salvamento também passou a ignorar intervalos de login ausentes ou futuros.
Bots sem login convencional tinham `lastLoginSaved=0`, somando segundos desde
1970 ao contador de tempo online; o estouro do `INT` impedia salvar o restante
do personagem, incluindo XP e nível. A migração 63 amplia `players.onlinetime`
para `BIGINT UNSIGNED`, preservando os valores existentes. O schema inicial e
o complemento WSL usam o mesmo tipo. A imagem foi recompilada com a correção.
Uma parada normal e o novo boot preservaram o Grizzle no nível 9 com 8.825 XP;
uma gravação posterior salvou 8.944 XP sem alterar o contador legado de tempo.

As regressões de caminhada e duração de login podem ser executadas com:

```bash
python3 tools/bot_brain/test_movement.py
g++ -std=c++20 -Isrc tools/bot_brain/test_online_time.cpp -o /tmp/test_online_time
/tmp/test_online_time
```

### Checkpoints concorrentes e deadlocks

Uma disputa entre os intervalos de chaves de `player_items` pode fazer o
InnoDB reverter uma transação inteira com erro 1213. O checkpoint repete a
transação desde o início, usando o mesmo snapshot imutável, em até cinco
tentativas com espera curta no worker SQL. A transação não é reiniciada em
erros de conexão, SQL inválido ou COMMIT sem confirmação; o tratamento de
reconexão da camada `Database` mantém sua política existente. Se o limite for
atingido, o save continua pendente; isso não garante durabilidade em uma
parada com banco indisponível.

O contexto inclui a identidade da conexão e um contador de recuperações da
thread. Se houver falha de transporte ou troca de conexão durante a tentativa,
um 1213 posterior não autoriza reiniciar o snapshot. As regressões usam o
classificador real de erros e cobrem falha mista na mesma instrução, em uma
instrução anterior e reconexão transparente.

O CTest `checkpoint_deadlock_retry` cobre rollback parcial, limite de tentativas
e retenção da pendência. O ensaio com quatro conexões reais exige Docker e uma
imagem local com compilador e dependências de build:

```bash
BOT_TEST_BUILD_IMAGE=<imagem-local-de-build> \
  python3 tools/bot_brain/test_checkpoint_deadlock_db.py
```

Esse ensaio usa o MariaDB 11.4 já presente localmente, fixado pelo ID, com rede
interna e banco em tmpfs próprios. Verifica vinte checkpoints e deadlocks
provocados, incluindo XP e inventário; remove seus containers e rede no fim.
`BOT_TEST_EVIDENCE=<diretorio>` preserva os logs do banco descartável.
