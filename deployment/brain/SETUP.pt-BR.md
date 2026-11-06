# Configuração inicial: LiteLLM, replay e benchmark

Este guia parte da implementação integrada até o PR #33, em 06/11/2026.
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

MariaDB do jogo e PostgreSQL do LiteLLM são bancos separados, sem portas
publicadas no host. Dentro de um container, `127.0.0.1` aponta para esse container.

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

Edite `runtime/config/litellm.yaml`, inicialmente JSON válido, para adicionar
essas entradas em `model_list`. JSON também é YAML válido. Preserve os demais
settings: retries zero no router e LiteLLM, sem fallbacks/cache, `drop_params:false`,
`custom_auth` e `custom_auth_settings:{mode:auto}`. O exemplo completo serve para
uma instalação nova; preserve IDs e configurações de uma instalação existente.
Use uma definição por alias: não duplique a mesma rota no arquivo e no banco UI.
Rotas do arquivo aparecem no painel como configurações gerenciadas pelo arquivo.

```bash
docker compose --profile gateway up -d --no-deps --force-recreate --wait litellm
sha256sum runtime/config/litellm.yaml
```

Guarde esse hash no manifesto/configuração do participante. Alterar alias,
modelo, deployment ou arquivo exige revalidar a identidade e iniciar outra
campanha. As chaves `openai`/`gemini` continuam resolvidas dentro do LiteLLM.

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
O prazo efetivo é `min(decision_timeout, menor TTL oferecido pelo servidor)`.
Configurar10 s não permite usar respostas depois de um TTL de1 ou1,5 s.
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

Antes de `benchmark preflight`, confira que `budget_file` é o ledger existente
e está acessível no mesmo host/mount do executor. O preflight usa Store e pode
criar um SQLite inexistente; não o use para descobrir o caminho do orçamento.
Docker Desktop não transforma automaticamente o Mountpoint de um volume
retornado por `docker volume inspect` em caminho acessível pelo Python do WSL.

```bash
.venv/bin/canary-brain benchmark preflight --config /caminho/campanha.json
```

Qualifique primeiro baseline/fake gratuitamente: mesmo estado inicial, duração
observada completa, XP confirmado no banco, caça/ressuprimento/retorno e paradas
testadas. O runner canônico não aceita `fake` como participante de campanha;
use o harness de QA apropriado e registre sua revisão. A [evidência #25](https://github.com/dandpb/canary-bots-with-cast/pull/25)
é uma qualificação histórica ainda em revisão, não uma fixture aceita por padrão.

Para OpenAI/Gemini, declare aliases/IDs/configurações e preços revisados,
mesmo estado inicial e memória, três repetições se esse for o plano aprovado,
tempo pontuado, teto por run/campanha e saldo mensal. Credenciais e autorização
para duas chamadas de smoke não autorizam automaticamente uma campanha longa.
Depois dos gates e da autorização correspondente, o comando de execução é:

```bash
.venv/bin/canary-brain benchmark run --config /caminho/campanha.json --live
```

`--live` pode iniciar servidor/banco isolados e inferência cobrada, inclusive
em avaliações de decisões gravadas. Use identidade nova para outra campanha;
retomar uma campanha mantém tentativas falhas e interrompidas no resultado.
Registre custos, reservas, falhas, timeout por classe de TTL, decisões puladas
por backoff, XP, mortes, intervenções e duração realmente observada. O p95
somente das respostas concluídas não descreve os requests que estouraram prazo.

## 8. Exportar, recuperar e encerrar

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
Use `--rm` ou a limpeza do runner e confirme com `docker ps -a`.
Para parar a implantação mantendo dados, use `docker compose stop -t 180`;
não use `down -v` como limpeza normal.

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
