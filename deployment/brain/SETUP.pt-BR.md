# Configuração inicial: LiteLLM, replay e benchmark

Este guia descreve a configuração e as ferramentas integradas na `main`.
Integração do código não significa aceite de uma fixture ou autorização do piloto.
Use o código da revisão escolhida; uma imagem local antiga continua antiga
depois de um merge. Os comandos de servidor abaixo são para Ubuntu/WSL.

O caminho é: preparar o servidor → abrir o LiteLLM → cadastrar credenciais e
rotas → validar o replay offline → configurar o worker → qualificar a fixture →
executar uma campanha autorizada. Instalar o gateway não muda o provider de um
worker existente. Reprodução e exportação offline não fazem chamadas de IA.

## 1. Escolher a instalação e conferir os pré-requisitos

Tenha Docker Desktop com integração WSL e Compose, Git e Python 3.11 ou superior.
O jogo precisa de mapa/datapack compatíveis e imagens da arquitetura correta.
A receita web deste projeto depende da imagem local `otbr-myaac:latest`.
Mapa e assets proprietários não acompanham este guia.

Para uma instalação nova, clone em um diretório Linux ainda inexistente:

```bash
git clone https://github.com/dandpb/canary-bots-with-cast.git "$HOME/canary-bots-wsl"
cd "$HOME/canary-bots-wsl"
git rev-parse HEAD
docker compose version
docker image inspect otbr-myaac:latest --format '{{.Id}}'
```

Se já existe uma implantação, use seu diretório e preserve `.env`, `runtime/`
e volumes. A cópia operacional pode ser uma exportação sem `.git`: nesse caso,
prepare os novos fontes separadamente e faça uma implantação controlada.
Os caminhos `/home/daniel/` nas próximas etapas são os do ambiente de referência;
ajuste-os ao seu usuário e à cópia que realmente está implantada.
`git pull` não atualiza imagens, bibliotecas carregadas nem arquivos exportados.
Confira game e worker por revisão da imagem, binários e configuração efetiva;
um label histórico sozinho não atesta alterações feitas por hot reload.

Para rodadas longas, mantenha fontes exportados, inputs, saídas e temporários no
filesystem Linux do WSL, por exemplo em `/home/USUARIO/canary-m5` e `/tmp`.
Os caminhos `/mnt/c`, `/mnt/e` e equivalentes são drives Windows/DrvFS: uma
referência de cwd pode ficar presa a um mount desanexado mesmo quando o arquivo
continua acessível pelo caminho absoluto. Execute o launcher a partir de `/`,
use caminhos e `PYTHONPATH` absolutos e confira o filesystem com `findmnt -T`.
O Python no container deve ter `working_dir: /`; monte fonte e inputs somente
para leitura no mesmo caminho absoluto. Essa conferência de mounts deve ser
registrada antes do piloto, além dos hashes; o preflight não prova ext4/RO sozinho.

## 2. Preparar servidor e gateway

Na raiz da instalação nova:

```bash
python3 deployment/wsl/setup.py
python3 deployment/wsl/setup-gateway.py
cd deployment/wsl
docker compose --profile gateway config --quiet
test -s runtime/world/otservbr.otbm
sha256sum runtime/world/otservbr.otbm
```

O teste do mapa só passa depois de colocar uma cópia compatível nesse caminho.
Veja a origem/hash usados na implantação de referência no [guia WSL](../wsl/README.md).
`setup.py` prepara seeds/configurações e preserva as credenciais existentes;
os seeds de banco só são importados quando o volume MariaDB está vazio.
`setup-gateway.py` cria apenas arquivos ausentes, com permissão `0600`.

Em uma instalação nova, depois de conferir mapa e imagem web:

```bash
SOURCE_REVISION="$(git rev-parse HEAD)" docker compose build game web
docker compose up -d database game web
docker compose --profile gateway up -d --build --wait litellm
docker compose --profile gateway ps
python3 smoke.py
```

Os nomes dos serviços pertencem ao projeto `canary-bots-wsl`. O perfil `ai`
fica para a etapa do worker. Recompilar `game` em uma atualização requer
planejar a troca; preserve juntos executável e biblioteca de bots compatíveis.
O primeiro carregamento da população é gradual e pode demorar vários minutos.

| Acesso local | Endereço | Finalidade |
| --- | --- | --- |
| Site/login | `http://127.0.0.1:8080/` e `/login.php` | Entrar no jogo |
| LiteLLM UI | `http://127.0.0.1:4000/ui` | Administrar credenciais/modelos |
| LiteLLM API no host | `http://127.0.0.1:4000/v1` | Clientes no WSL/host |
| LiteLLM API no Compose | `http://litellm:4000/v1` | Worker na mesma rede privada |
| Supervisão do worker | `http://127.0.0.1:8091/` | Disponível ao iniciar o worker |
| Replay independente | `http://127.0.0.1:8092/replay` | Disponível ao executar `replay serve` |

MariaDB do jogo, PostgreSQL do LiteLLM e Redis de coordenação são serviços
separados, sem portas publicadas no host. Dentro de um container, `127.0.0.1`
aponta para esse container.

## 3. Entender o login e as chaves

Na preparação padrão, o painel usa usuário `admin`. A senha é `UI_PASSWORD`,
se configurada em `runtime/secrets/litellm-ui.env`; caso contrário, usa
`LITELLM_MASTER_KEY` de `runtime/secrets/litellm-worker.env`.
Consulte o arquivo em um editor local ou seu cofre; não envie o conteúdo ao chat,
ao Git ou a relatórios. [Contrato de login do LiteLLM](https://docs.litellm.ai/docs/proxy/ui).

| Arquivo local em `deployment/wsl/` | Conteúdo/uso |
| --- | --- |
| `runtime/secrets/litellm-worker.env` | Master key e chave restrita do worker; montado apenas no gateway |
| `runtime/secrets/litellm-ui.env` | Conexão PostgreSQL, usuário UI e salt persistente |
| `runtime/secrets/litellm-db.env` | Usuário/senha do PostgreSQL exclusivo |
| `runtime/secrets/litellm-redis.env` | Endpoint interno e senha do Redis de coordenação/autenticação |
| `runtime/secrets/litellm-provider.env` | Alternativa para credenciais por variáveis de ambiente |
| `runtime/secrets/litellm-client.env` | Arquivo a criar para o worker: apenas `LITELLM_API_KEY` |
| `runtime/secrets/litellm-admin.env` | Opcional, criado pelo operador: `LITELLM_ADMIN_KEY` para ferramentas administrativas |

Uma virtual key administrativa de API não substitui automaticamente a senha
do formulário nem a master key. As chaves dos providers ficam no gateway.
Conserve banco, master key e `LITELLM_SALT_KEY` em backups protegidos: mudar a
salt pode tornar credenciais antigas indecifráveis.

O painel precisa de PostgreSQL e Prisma. Para conferir sem inferência:

```bash
docker compose --profile gateway ps litellm litellm-db
curl --fail --silent --show-error http://127.0.0.1:4000/health/readiness
```

Health confirma disponibilidade; confira também login e listagem de modelos.
Ao consultar logs de inicialização, mantenha-os privados e remova segredos
antes de compartilhar.

### Redis de coordenação e número de workers

A preparação nova também cria `litellm-redis.env`, privado (`0600`), com
`REDIS_HOST=litellm-redis`, `REDIS_PORT=6379` e senha interna aleatória. O serviço
`litellm-redis` pertence a `canary-bots-wsl`, usa imagem fixada por digest e não
publica porta. Ele recebe apenas seu próprio env file; as chaves de providers,
o banco do jogo e a conexão PostgreSQL não são passados a ele.

Redis usa AOF em volume próprio, `appendfsync everysec`, limite de 128 MB e
`noeviction`, para não descartar contadores ao atingir o limite. A configuração
com senha é criada somente em tmpfs privado dentro do container, com `0600`;
a senha não aparece no argv. O healthcheck autenticado usa `REDISCLI_AUTH`.
O processo roda como `redis`, com filesystem-base somente leitura, sem
capabilities e com `no-new-privileges`. Preserve esse volume em paradas normais.

O perfil configura `general_settings.coordination_redis` explicitamente, com
referências a `REDIS_*`, banco 0 e namespace `canary-bots-wsl:litellm`.
`litellm_settings.enable_redis_auth_cache: true` compartilha o cache de autenticação.
Isso é diferente de cache de respostas: mantenha `litellm_settings.cache: false`
e `router_settings.cache_responses: false` no M5. O ledger mensal canônico continua
sendo SQLite; Redis não abre outro saldo nem substitui reservas financeiras.
A UI recebe `NUM_WORKERS=1`; confirme também o número efetivo de processos ao
qualificar a implantação. A existência de Redis, sozinha, não prova multiworker.
O bloco de coordenação e a condição do aviso estão na implementação fixada do
[LiteLLM 1.108.0](https://github.com/BerriAI/litellm/blob/v1.108.0/litellm/proxy/proxy_server.py#L5974)
e no [endpoint de warnings](https://github.com/BerriAI/litellm/blob/v1.108.0/litellm/proxy/health_endpoints/_health_endpoints.py#L1745).

Em uma atualização, execute primeiro a preparação sem a flag de coordenação:
ela cria arquivos ausentes, incluindo `litellm-redis.env`, e preserva exatamente
os env files e a política originais:

```bash
cd /home/daniel/canary-bots-wsl/deployment/wsl
python3 setup-gateway.py \
  --directory /home/daniel/canary-bots-wsl/deployment/wsl
```

O helper de coordenação aceita uma política **JSON**, mesmo com extensão `.yaml`,
como a produzida pela preparação padrão. Se a original está nesse formato,
gere a política derivada sem editar a original:

```bash
python3 setup-gateway.py \
  --directory /home/daniel/canary-bots-wsl/deployment/wsl --coordination
```

O novo arquivo é `runtime/config/litellm-coordination.yaml`. Uma segunda execução
igual o preserva; se ele já existir com conteúdo diferente, o helper recusa
sobrescrevê-lo. Se a política existente usa sintaxe YAML em vez de JSON, não use
`--coordination`: crie uma cópia privada nova com o nome acima e mescle os campos
abaixo nas seções correspondentes, preservando os demais campos e sem duplicar
chaves de seção. Revise o diff contra a original antes de montar a cópia:

```yaml
general_settings:
  coordination_redis:
    host: os.environ/REDIS_HOST
    port: os.environ/REDIS_PORT
    password: os.environ/REDIS_PASSWORD
    db: 0
    namespace: canary-bots-wsl:litellm
litellm_settings:
  enable_redis_auth_cache: true
  cache: false
router_settings:
  cache_responses: false
```

Para montar a cópia na UI, crie um override local privado, por exemplo
`runtime/config/compose.coordination.yaml`, com o conteúdo abaixo; não substitua
um override existente. Ele altera somente a origem do mount em `/app/gateway.yaml`:

```yaml
services:
  litellm:
    volumes:
      - type: bind
        source: /home/daniel/canary-bots-wsl/deployment/wsl/runtime/config/litellm-coordination.yaml
        target: /app/gateway.yaml
        read_only: true
        bind:
          create_host_path: false
```

Conserve o Compose e a política operacionais anteriores. Em instalações novas,
a política padrão já inclui a coordenação e esse override é desnecessário.

Registre o caminho **efetivamente montado** em `/app/gateway.yaml` como
`ACTIVE_POLICY`: na instalação nova é `runtime/config/litellm.yaml`; na migração
acima é `runtime/config/litellm-coordination.yaml`. Use o mesmo arquivo para
editar rotas, revisar conteúdo e calcular o hash. Antes de um ensaio, congele
uma cópia em outro caminho e monte essa cópia. Se precisar alterar uma política
já congelada, crie outra revisão e atualize o mount/manifesto; não edite a cópia
em uso nem espere que `--coordination` substitua um alvo divergente.

Guarde também o comando Compose completo em `GATEWAY_COMPOSE`, incluindo a base
e **todos os overrides ativos**. Exemplo para selecionar os arquivos da implantação:

```bash
GATEWAY_COMPOSE=(env COMPOSE_REMOVE_ORPHANS=0 COMPOSE_IGNORE_ORPHANS=1 \
  docker compose -p canary-bots-wsl \
  -f /home/daniel/canary-bots-wsl/deployment/wsl/compose.yaml)
ACTIVE_POLICY=/home/daniel/canary-bots-wsl/deployment/wsl/runtime/config/litellm.yaml
# Se migrado, use a política derivada e acrescente o override revisado que a monta:
# ACTIVE_POLICY=/home/daniel/canary-bots-wsl/deployment/wsl/runtime/config/litellm-coordination.yaml
# GATEWAY_COMPOSE+=(-f /home/daniel/canary-bots-wsl/deployment/wsl/runtime/config/compose.coordination.yaml)
```

Inclua também outros overrides existentes nesse array. Reiniciar somente com a
base descartaria a seleção da política derivada e outras opções operacionais.

Inicie primeiro somente `litellm-redis` e confira seu healthcheck; depois recrie
apenas a UI e o gateway privado que precisem da nova conexão/configuração. A UI
do Compose rastreado já depende da saúde de PostgreSQL e Redis. Não reinicie jogo,
MariaDB ou brain para essa alteração. Preserve logs e ateste os CIDs esperados
antes/depois. Redis inacessível, cliente ainda em memória e quantidade de workers
desconhecida são estados diferentes: verifique conexão/cliente efetivos além da
ausência de warnings, sem desativar limites para esconder o aviso.

Uma política derivada tem outro hash: fixe seus bytes e atualize os manifestos
antes de uma nova campanha. Acrescentar Redis/env/Compose não muda os bytes da
imagem `32b563…` qualificada anteriormente, mas exige revalidar readiness, auth,
conexão Redis, ausência de cache de respostas e limpeza da sessão. A validade
temporal de um recibo anterior não cobre a configuração nova.

## 4. Cadastrar credenciais e associar modelos

No painel, abra a área de credenciais de LLM e cadastre:

- Nome `openai`, provider OpenAI, campo `api_key` com sua chave OpenAI.
- Nome `gemini`, provider Gemini, campo `api_key` com sua chave Gemini.

Reutilize entradas já cadastradas. Cada credencial ainda precisa de uma rota
com modelo explícito: o gateway não escolhe um modelo padrão automaticamente.
O [exemplo com credenciais nomeadas](gateway/gateway.named-credentials.example.json)
contém duas rotas, sem chaves:

| Alias chamado pelo worker | Modelo upstream | Credencial | Deployment ID do exemplo |
| --- | --- | --- | --- |
| `canary-openai` | `openai/gpt-6-luna` | `openai` | `canary-openai-luna-v1` |
| `canary-gemini` | `gemini/gemini-3.5-flash-lite` | `gemini` | `canary-gemini-flash-lite-v1` |

Edite o arquivo ativo definido em `ACTIVE_POLICY` na etapa 3 para adicionar
essas entradas em `model_list`. JSON também é YAML válido. Preserve os demais
settings: retries zero no router e LiteLLM, sem fallbacks/cache, `drop_params:false`,
`custom_auth`, `custom_auth_settings:{mode:auto}` e o bloco de coordenação Redis.
No WSL, copie do exemplo apenas `model_list`: o exemplo genérico não configura
Redis nem seus env files. Se importar uma política inteira sem coordenação,
siga o fluxo de migração da etapa 3 e atualize `ACTIVE_POLICY` e o override antes
de reiniciar. Preserve IDs e configurações de uma instalação existente.
Use uma definição por alias: não duplique a mesma rota no arquivo e no banco UI.
Rotas do arquivo aparecem no painel como configurações gerenciadas pelo arquivo.

```bash
"${GATEWAY_COMPOSE[@]}" --profile gateway up -d --no-deps --force-recreate --wait litellm
sha256sum "$ACTIVE_POLICY"
```

Guarde esse hash no manifesto/configuração do participante. Alterar alias,
modelo, deployment ou arquivo exige revalidar a identidade e iniciar outra
campanha. As chaves `openai`/`gemini` continuam resolvidas dentro do LiteLLM.

Para uma campanha pontuada, prepare um **processo privado de inferência** a partir
de [Dockerfile.benchmark](gateway/Dockerfile.benchmark), separado do painel.
Ele usa `CANARY_BENCHMARK_GATEWAY_ONLY=1`, mantém `STORE_MODEL_IN_DB=True` desde
o startup e rejeita credenciais administrativas. O painel continua disponível
para administrar as credenciais existentes; apenas o gateway as acessa.
O worker recebe somente sua chave restrita, nunca chaves OpenAI/Gemini nem a
conexão PostgreSQL. Fixe imagem, arquivo de política, aliases, deployment IDs e
preços antes da revisão. Não edite rotas pelo painel durante a medição.

Mantenha esse serviço temporário sob o projeto `canary-bots-wsl`, na rede privada.
No perfil M5, o alias de rede é `gateway` e os participantes usam
`http://gateway:4000/v1`; `litellm` continua sendo o serviço do painel na tabela
anterior. Não publique uma nova porta para o gateway privado.

O [Compose privado rastreado](gateway/compose.benchmark.yaml) e o launcher abaixo
provisionam somente esse serviço, sem iniciar worker ou enviar inferência.
Antes, conclua a etapa 2: a rede `canary-bots-wsl_default` e o PostgreSQL do
LiteLLM devem existir, com o schema já preparado pelo serviço UI. Reutilize os
quatro env files `litellm-{provider,worker,ui,redis}.env`, privados (`0600`), no runtime;
o launcher só confere seus caminhos/permissões, sem ler ou exibir seus valores.
Fixe a política revisada em um arquivo novo e não a altere durante o ensaio.

Na raiz dos fontes escolhidos, em Linux/WSL:

```bash
REVISION="$(git rev-parse HEAD)"
docker build -f deployment/brain/gateway/Dockerfile.benchmark \
  --label "org.opencontainers.image.revision=$REVISION" \
  -t canary-litellm-benchmark:reviewed .
GATEWAY_IMAGE="$(docker image inspect canary-litellm-benchmark:reviewed --format '{{.Id}}')"
GATEWAY_LAUNCHER="$(pwd -P)/deployment/brain/tools/benchmark_gateway.py"
GATEWAY_RUNTIME=/home/daniel/canary-bots-wsl/deployment/wsl/runtime
GATEWAY_POLICY=/caminho/absoluto/politica-congelada.yaml
cd /
python3 "$GATEWAY_LAUNCHER" \
  --runtime "$GATEWAY_RUNTIME" --policy "$GATEWAY_POLICY" \
  --image "$GATEWAY_IMAGE" --revision "$REVISION" --check
```

O Dockerfile fixa a imagem base por digest; o launcher exige o content ID local
resultante, sem pull por tag. `--check` executa somente `compose config --quiet`,
sem imprimir configuração/env nem acessar providers. Depois, no mesmo terminal dedicado:

```bash
python3 "$GATEWAY_LAUNCHER" \
  --runtime "$GATEWAY_RUNTIME" --policy "$GATEWAY_POLICY" \
  --image "$GATEWAY_IMAGE" --revision "$REVISION" --serve
```

Ele aguarda readiness e mantém o processo até Ctrl+C/SIGTERM. Recusa serviço ou
alias `gateway` já ocupado, inclusive por outro projeto, sem adotar a instância.
Durante uma mutação Docker, adia o cancelamento até a CLI terminar, em sessão
separada. O journal privado `benchmark-gateway-<sessão>.json` registra o resultado.
Somente após preservar e sincronizar os logs privados e confirmar a remoção dos
CIDs próprios por UUID, labels e imagem, ele registra `cleaned`. UI, banco e
outros serviços permanecem fora da limpeza. Se os logs não puderem ser salvos,
tenta parar o próprio CID e o conserva para recuperar a evidência, sem removê-lo.
Timeout/erro da CLI é resultado incerto: conserva o journal e exige recuperação
manual, mesmo se o CID ainda não aparecer. Journals não resolvidos bloqueiam
uma nova execução; não os apague para forçar outra tentativa. O lockfile também
é mantido para evitar corridas. SIGKILL/queda do host exige conferir os órfãos por
identidade antes de tentar novamente. Esse launcher não substitui o admission do M5 e não
deve substituir um gateway já ativo durante uma campanha.

## 5. Validar o replay offline primeiro

Esta etapa funciona sem servidor, credenciais ou gateway. Na raiz dos fontes:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r deployment/brain/requirements.lock
.venv/bin/python -m pip install --no-deps ./deployment/brain
REPLAY_QA="$(mktemp -d /tmp/canary-replay.XXXXXX)"
.venv/bin/canary-brain replay demo --recording "$REPLAY_QA/recording.sqlite3"
.venv/bin/canary-brain replay list --recording "$REPLAY_QA/recording.sqlite3"
.venv/bin/canary-brain replay serve --recording "$REPLAY_QA/recording.sqlite3" --port 8092
```

Abra `http://127.0.0.1:8092/replay`. Compare as duas runs sintéticas, navegue
pela timeline, mude velocidade/andar e inspecione decisões. Encerre com Ctrl+C.
Guarde o caminho retornado por `REPLAY_QA` para os comandos de exportação.
Essa demonstração valida a ferramenta; não mede inteligência ou XP real.

## 6. Configurar o worker com uma rota LiteLLM

Use [worker-replay.example.json](worker-replay.example.json) como esquema,
preservando os valores locais de socket, GUIDs e servidor. O mesmo worker usa
uma rota por configuração; os participantes de uma campanha têm suas próprias
configurações. Antes de iniciar um worker real, confira:

| Campo do worker | Valor a conferir |
| --- | --- |
| `provider` | `litellm` |
| `gateway.base_url` | `http://litellm:4000/v1` no Compose, ou loopback no host |
| `gateway.alias` | Alias exato, como `canary-openai` |
| `gateway.effective_model` | ID sem prefixo, como `gpt-6-luna` |
| `gateway.upstream_model` | ID completo, como `openai/gpt-6-luna` |
| `gateway.deployment_id` | ID efetivo da rota; não inventar outro no worker |
| `gateway.configuration_sha256` | Hash calculado após a configuração final |
| `gateway.version` | Versão implantada; implementação qualificada: `1.108.0` |
| `gateway.prices` | Tarifas revisadas e datadas; não copiar uma tarifa OpenAI para Gemini |
| `credential_file` | Caminho interno para arquivo com `LITELLM_API_KEY` |
| `budget_file` | Ledger mensal canônico já existente |
| `recording.path` | Outro SQLite, separado de estado e orçamento |

O exemplo de preços é OpenAI e exige revisão antes de uso pago. O valor de
`reasoning:false` só omite o parâmetro; não desliga o default do provider.
No M5, substitua a URL pelo gateway privado descrito acima. Se a tarifa de escrita
em cache não estiver definida, use `cache_write_nanousd:null`, não zero;
uso positivo sem esse preço impede liquidação.
O prazo efetivo é `min(decision_timeout, menor TTL oferecido pelo servidor)`.
Configurar 10 s não permite usar respostas depois de um TTL de 1 ou 1,5 s.
Timeouts mantêm a reserva desconhecida e deixam o motor nativo continuar.

Para gerar o arquivo do cliente sem mostrar/copiar chaves de provider,
execute em `deployment/wsl`:

```bash
python3 - <<'PY'
import os
from pathlib import Path
os.umask(0o077)
private = Path('runtime/secrets')
source = dict(line.split('=', 1) for line in (private / 'litellm-worker.env').read_text().splitlines() if '=' in line)
target = private / 'litellm-client.env'
content = 'LITELLM_API_KEY=' + source['LITELLM_WORKER_KEY'] + '\n'
if target.exists():
    assert not target.is_symlink() and target.read_text() == content, 'Revise o arquivo de cliente existente'
else:
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(content)
target.chmod(0o600)
print('Credencial restrita do cliente preparada; valor não exibido.')
PY
```

No serviço `brain` do Compose, substitua a montagem antiga de
`openai.env:/etc/canary-brain/openai.env:ro` por
`./runtime/secrets/litellm-client.env:/etc/canary-brain/gateway.env:ro`.
Ajuste `credential_file` para `/etc/canary-brain/gateway.env`.
Preserve as montagens de configuração, socket e `brain-state`.

Na implantação WSL de referência, o ledger existente é
`/var/lib/canary-brain/state.sqlite3`, no volume `canary-bots-wsl_brain-state`.
Se `budget_file` não existia na configuração, esse próprio `state_file` era
a autoridade financeira. Aponte o novo campo para ele: um novo
`budget.sqlite3` criaria outro saldo de USD50. Não copie o SQLite para
"compartilhar" orçamento. Workers isolados precisam acessar a mesma autoridade,
mantendo seus estados de aprendizado e replays separados.

Para gravar a vida, acrescente `recording` ao worker, com caminho próprio,
namespace estável e amostragem, por exemplo1000 ms. Use o mesmo namespace ao
reiniciar a mesma vida; um reset deliberado do personagem cria outra linhagem.
A gravação começa no primeiro dado observado, sem reconstruir passado ausente.

Depois da revisão de configuração e autorização do uso real:

```bash
cd /home/daniel/canary-bots-wsl/deployment/wsl
SOURCE_REVISION="$(git rev-parse HEAD)" docker compose --profile ai build brain
docker compose --profile ai up -d --no-deps brain
docker compose --profile ai ps brain
```

Em uma cópia sem `.git`, forneça a revisão atestada dos fontes usados no build.
Iniciar o worker com provider real pode fazer chamadas pagas. `shadow` impede
aplicar escolhas ao jogo, mas não é garantia de ausência de inferência.

## 7. Preparar o benchmark e autorizar a execução paga

Comece com [experiment.example.json](experiment.example.json) e a
[referência do runner](REPLAY.md#prepare-an-isolated-experiment).
Preencha caminhos absolutos, imagem do jogo e MariaDB por digest, revisão,
fixture/hash, ledger compartilhado, participantes, prazo, repetições e tetos.
O template não vem com uma fixture completa pronta para jogo.

Volte à raiz dos fontes, onde a `.venv` foi instalada na etapa5:

```bash
cd /home/daniel/canary-bots-wsl
```

Uma fixture precisa de `database.sql` sanitizado e `character.json` com
`id`, `level`, `experience`, `posx`, `posy`, `posz`, mais mapa compatível.
Congele inventário, skills, fundos, rotas, configuração, população e memória.
Calcule o hash com:

```bash
.venv/bin/canary-brain benchmark hash --fixture /caminho/fixture --world-map /caminho/otservbr.otbm
```

Qualifique primeiro baseline/fake gratuitamente: mesmo estado inicial, duração
observada completa, XP confirmado no banco, caça/ressuprimento/retorno e paradas
testadas. O runner canônico aceita `native`, `fake` e `litellm`; `fake` usa uma
política local explícita, sem inferência de provider. `--live` ainda é necessário
para iniciar o jogo real. Registre a política/harness e sua revisão; progresso
do jogo real com decisões fake não é desempenho de um modelo. A [evidência #25](https://github.com/dandpb/canary-bots-with-cast/pull/25)
é uma qualificação histórica, não uma fixture aceita por padrão.

Para o M5, use o [wrapper de admissão](tools/M5_PILOT.md), que chama o mesmo
runner canônico após os probes de conformidade. Prepare em diretório novo:

- A campanha com `native`, `openai` e `gemini`, três repetições de 1.800 s e
  memória congelada; fixe imagens, fixture, modelos, preços e prazos.
- Duas configurações de probes, as observações com origem declarada e o envelope
  financeiro, incluindo custos anteriores e reservas desconhecidas.
- Uma exportação dos fontes da revisão escolhida contendo `deployment/brain/src`
  e `deployment/brain/tools`; registre revisão, caminho absoluto e SHA-256 dos
  módulos Python e do próprio wrapper em `source_manifest`.
- O `pilot.plan.json` e o admission revisado. `approved_inputs_sha256` vincula os
  bytes de campanha, envelope, manifesto, observações e ambos os workers.
  Mantenha a candidatura não aprovada até a revisão das evidências.

O contrato completo dos campos e gates está em [M5_PILOT.md](tools/M5_PILOT.md).
O perfil limita probes a USD0,49 por modelo e seis runs pagas a USD1 cada;
o total, com histórico, deve caber em USD7 dentro do ledger mensal de USD50.
O wrapper exige ainda pelo menos USD12 disponíveis na autoridade canônica.
Esses limites são verificações do plano, não uma autorização de gasto.

Execute dentro do harness com a imagem comum fixada, Docker acessível e a
exportação montada somente para leitura no **mesmo caminho absoluto**. Monte
diretamente `canary-bots-wsl_brain-state` em `/var/lib/canary-brain`: a autoridade
é exatamente `state.sqlite3`, não um backup ou outro arquivo nesse volume.
Os estados e replays das runs continuam separados do orçamento.

```bash
SOURCE=/home/USUARIO/canary-m5/fontes-congelados
PILOT_PLAN=/home/USUARIO/canary-m5/pilot.plan.json
cd /
PYTHONPATH="$SOURCE/deployment/brain/src" python "$SOURCE/deployment/brain/tools/m5_pilot.py" --plan "$PILOT_PLAN" --preflight
```

Esse preflight lê arquivos, ledger e metadados do próprio container, sem criar
Store, reservar saldo, iniciar jogo ou fazer inferência. Uma candidatura ainda
não aprovada é recusada; o comando não aprova gates automaticamente. O comando
genérico `canary-brain benchmark preflight` tem outro contrato e pode inicializar
Store: não o use para descobrir ou criar o ledger do M5.

Somente depois dos gates e da autorização explícita do plano pago, no mesmo
harness e com os mesmos arquivos aprovados:

```bash
PYTHONPATH="$SOURCE/deployment/brain/src" python "$SOURCE/deployment/brain/tools/m5_pilot.py" --plan "$PILOT_PLAN" --execute
```

`--execute` pode cobrar inferência já nos probes. Credenciais cadastradas ou
um smoke anterior não autorizam a campanha. O wrapper captura os bytes antes
de validar e executa esses mesmos bytes; mudança de fonte/configuração requer
novo freeze e revisão. Use saída nova: ele não substitui nem repete uma tentativa.
Falha de contrato, timeout ou custo desconhecido no probe interrompe antes do
jogo, retém a evidência e exige revisão; não aumente TTL nem repita em silêncio.
Registre custos, reservas, falhas, timeout por classe de TTL, decisões puladas
por backoff, XP, mortes, intervenções e duração realmente observada. O p95
somente das respostas concluídas não descreve os requests que estouraram prazo.

## 8. Exportar, recuperar e encerrar

Para o M5, preserve `execution-result.json`, `ledger.json`, `inputs/` e os
artefatos de cada trial. O [relatório M5](tools/M5_PILOT.md#review-the-pilot-offline)
cruza replay, parada do supervisor, personagem salvo, imagens/limpeza e saldo
canônico; ele é separado do HTML visual do replay. Seu resultado descreve o
piloto e inconsistências, sem declarar vencedor ou fechar a issue automaticamente.

Na raiz dos fontes, liste o replay e copie um ID real da saída para `RUN_ID`.
Se abriu outro terminal, defina `REPLAY_QA` com o diretório criado na etapa5:

```bash
.venv/bin/canary-brain replay list --recording "$REPLAY_QA/recording.sqlite3"
RUN_ID='ID_COPIADO_DA_LISTAGEM'
.venv/bin/canary-brain replay summary --recording "$REPLAY_QA/recording.sqlite3" --run "$RUN_ID"
.venv/bin/canary-brain replay export --recording "$REPLAY_QA/recording.sqlite3" --run "$RUN_ID" --output "$REPLAY_QA/bot.replay.zip"
.venv/bin/canary-brain replay report --recording "$REPLAY_QA/recording.sqlite3" --run "$RUN_ID" --output "$REPLAY_QA/report.html"
.venv/bin/canary-brain replay video --recording "$REPLAY_QA/recording.sqlite3" --run "$RUN_ID" --output "$REPLAY_QA/timelapse.mp4" --speed 60 --fps 24
```

Vídeo exige FFmpeg com librsvg/libx264 e ffprobe. É um mapa amostrado; não é
captura do cliente. Mantenha o MP4 junto do JSON sidecar e use destinos novos.
Uma exportação posterior recupera transações próprias interrompidas sem
sobrescrever um par completo. Para backup de SQLite ativo, use a API de backup
ou pare o produtor; copiar só o `.sqlite3` ignora o WAL.

QA temporária deve preservar logs/evidências antes de remover seus containers.
Use `--rm` ou a limpeza em `finally` do runner e confirme com `docker ps -a`.
Confira também a remoção do gateway privado e do harness após a revisão;
remova somente os containers temporários identificados, preservando serviços
ativos, imagens, volumes e a autoridade financeira. `resources_cleaned` deve
refletir a conferência real, não uma suposição do relatório.
Para parar a implantação mantendo dados, use todos os arquivos ativos do array
da etapa 3 e inclua os perfis opcionais:

```bash
"${GATEWAY_COMPOSE[@]}" --profile ai --profile gateway stop -t 180
```

Sem ativar os perfis, `stop` não seleciona os serviços opcionais de IA/gateway
([perfis do Compose](https://docs.docker.com/compose/how-tos/profiles/)).
Não use `down -v` como limpeza normal.

## Diagnóstico rápido

| Sintoma | Conferência |
| --- | --- |
| `Not connected to DB!` no login | Saúde de `litellm-db`, `DATABASE_URL` e imagem UI com Prisma/migrações |
| Painel abre, lista de modelos vazia | Credencial foi salva, mas `model_list`/rota ainda não foi configurado |
| `401` | Chave e finalidade corretas; o worker usa `LITELLM_API_KEY`, não master/admin |
| `403` com chave do worker | Administração pelo worker é bloqueada; confira a rota chamada |
| `409` na inferência | Hash, versão e upstream do manifesto; recrie o gateway após editar o arquivo |
| `TimeoutError` e reserva aberta | Chamada ultrapassou o prazo efetivo; manter passivo e investigar/conciliar |
| Conexão recusada dentro do worker | Verificar DNS/rede `litellm`, evitando loopback do próprio container |
| Build/merge recente, comportamento antigo | Conferir imagens, revisão e binários efetivamente implantados |

Os exemplos e [as duas chamadas reais documentadas](evidence/2026-11-05/real-openai-gemini-smoke/README.md)
validam contratos específicos. O estado de aceite do piloto e seus limites
estão na [#10](https://github.com/dandpb/canary-bots-with-cast/issues/10).
