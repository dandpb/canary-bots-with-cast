# Canary com bots e cast no WSL

Implantação local em `/home/daniel/canary-bots-wsl`, criada a partir do commit
`7a61f9540` da `main`. O código executado fica no disco Linux; os ajustes locais são preservados.
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

## Worker de IA

A imagem `canary-bots-wsl-brain:local` contém a implementação desta branch.
O perfil `ai` está ativo. A credencial autorizada fica em
`runtime/secrets/openai.env` com permissão `0600`, fora do Git e do contexto de
build. O arquivo é montado apenas no worker. Não envie chaves pelo chat.

```bash
docker compose --profile ai up -d brain
docker compose --profile ai logs --tail=50 brain
```

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

Para parar sem excluir dados, execute `docker compose stop -t 180`. Os logs de build
ficam neste diretório. Não use `down -v` para uma parada normal.

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

Por padrão, os bots de população mantêm o nível original. O bot configurado
como `autonomous_bot` no brain ativo recebe XP e sobe de nível pelo mesmo fluxo
dos jogadores, incluindo os aumentos normais de atributos. O opt-in é refeito
no carregamento da configuração; nível e experiência são carregados e salvos
pelos registros normais do personagem. Desabilitar a IA revoga o opt-in sem
remover a experiência já conquistada. O Grizzle começou no nível 8 com 4.200 XP.
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
