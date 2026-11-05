# M5 — proposta de piloto de progresso autônomo

Data: **2026-11-05**. Base de código examinada: `a2f1e51f0a1a9566daa650c056d7a70c452c533b`.
Estado: **proposta para revisão, sem autorização de gasto ou execução paga**.
Relacionadas: #10, coordenação #14. Não altera produção, modelos em uso, preços em código ou o teto mensal.

## Pergunta e recorte

Quanto progresso um controller configurado consegue obter autonomamente, com quais mortes, períodos sem assistência e custos, sob a mesma fixture inicial?

O primeiro piloto compara **baseline nativa + GPT-6 Luna + Claude Haiku 5.5**, um bot knight por run, memória congelada e seleção de objetivos via LiteLLM. Mede a stack completa com sua tradução de API e defaults documentados, não uma capacidade isolada de raciocínio. Combate, cura, movimento e validação continuam nativos. Não substitui o playtest humano da #1 nem estabelece segurança AFK.

## Perfis e disponibilidade

LiteLLM fixado em **1.108.0**, dependências de `gateway/requirements.lock`; registrar também digest da imagem construída e hash da configuração. O único alias no arquivo de exemplo atual é `participant-a -> openai/gpt-6-luna`. Nenhuma conta, credencial, configuração privada ou lista autenticada de modelos foi inspecionada. Portanto, “consta no mapa de suporte” e “disponível na conta” são estados distintos.

| Participante proposto | ID / rota LiteLLM | Admissão |
| --- | --- | --- |
| `native` | Sem inferência, shadow com keep-awake | Qualificação gratuita da fixture |
| `m5-luna` | `gpt-6-luna` / `openai/gpt-6-luna` | Suporte estático identificado; contrato, acesso e uso faturado por qualificar |
| `m5-haiku` | `claude-haiku-5-5` / `anthropic/claude-haiku-5-5` | Segundo provider proposto; contrato, acesso e uso faturado por qualificar |
| Opcional futuro | `gemini-3.5-flash-lite` / `gemini/gemini-3.5-flash-lite` | Fora do orçamento e dos nove runs propostos; exige emenda revisada |

Usar aliases e deployment IDs exclusivos, uma implantação por alias, sem balanceamento. Congelar gateway, upstream, modelo efetivo, versão de preço e hash do prompt/configuração no manifesto. Aliases mutáveis do provider não provam uma revisão imutável do modelo. Falha de um participante bloqueia sua admissão; não substituí-lo silenciosamente.

## Preços e dimensão do custo

Valores padrão síncronos em USD por milhão de tokens, consultados em **05/11/2026**, sem batch, flex, prioridade, sobretaxa regional, web search ou outras ferramentas pagas:

| Modelo / faixa de entrada | Entrada | Saída | Leitura cache | Escrita cache |
| --- | ---: | ---: | ---: | ---: |
| Luna, até 272K | 0,10 | 0,50 | 0,01 | 0,125 |
| Haiku 5.5, até 100K | 0,10 | 0,50 | 0,01 | 0,125 em 5 min; 0,20 em 1 h |
| Gemini 3.5 Flash-Lite, opcional | 0,30 | 2,50 | 0,03 | Cache explícito cobra armazenamento: 1,00/MTok-h |

Fontes primárias: [OpenAI Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [Anthropic Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview), [Google pricing](https://aistudio.google.com/docs/pricing#gemini-3.5-flash-lite). IDs, limites, cache e contrato estão detalhados na [pesquisa datada](m5-model-pricing-research.md). Revalidar preços e tier antes do opt-in; esta proposta não instala os valores.

Nos perfis curtos Luna/Haiku, a representação por token é 100/10/125/500 nanodólares para entrada/cache-read/cache-write/saída. Proibir caching explícito de 1 h e recursos de cache com cobrança por tempo: o ledger atual não tem uma dimensão de armazenamento nem duas tarifas de escrita. Registrar cache nativo retornado, sem cache de respostas no gateway. Manter requests muito abaixo dos limites de faixa; recusar payload acima de 32 KiB na qualificação, em vez de truncar evidência silenciosamente. Validar o maior corpo realmente transmitido antes da admissão.

Exemplo aritmético, **não previsão medida**: 8.192 tokens de entrada sem cache + 256 de saída custam US$ 0,0009472; 360 escolhas custariam US$ 0,340992. Tokenização, frequência e contexto reais podem diferir. A reserva conservadora do worker usa bytes UTF-8 + 4.096, a maior tarifa de entrada/cache e a saída máxima, não essa estimativa média.

## Contrato comum e bloqueador contábil

Usar `/v1/responses`, uma função estrita `choose_action`, enum dos candidatos fornecidos pelo servidor, ferramenta forçada, sem chamadas paralelas e `max_output_tokens=256`. Uma única opção elegível continua sendo escolha local, explicitamente atribuída. Não usar Decisions com saída cobrada: o adapter atual não impõe seu limite de saída.

`reasoning:false` no adapter remove o campo; não desliga o default do provider. Luna documenta default medium; Haiku 5.5 pula thinking na chamada forçada, segundo sua documentação. Esses comportamentos devem constar do manifesto e da inspeção do corpo traduzido, sem declarar esforços equivalentes. Qualificar o caminho exato; se o limite de 256 impossibilitar o contrato, revisar a proposta antes de aumentar saída ou trocar o modo. Memória congelada impede overrides por aprendizado e reflexões autônomas; não enviar diálogo humano ou avaliações extras no conjunto pontuado.

**Bloqueador reproduzido antes de admissão:** o bridge Responses do LiteLLM 1.108.0 pode transformar `usage` ausente em zeros; o worker da base examinada aceita esses zeros e liquida a reserva como custo zero. A correção/regressão foi publicada no [PR #23](https://github.com/dandpb/canary-bots-with-cast/pull/23), head `6cd050566ed12ffbd0c54a361fd1b9e36b76e4ad`: 142 testes Python, Ruff, mypy e ensaios HTTP no proxy real sem rede externa passaram. [Reprodução e limites](https://github.com/dandpb/canary-bots-with-cast/blob/6cd050566ed12ffbd0c54a361fd1b9e36b76e4ad/deployment/brain/evidence/2026-11-05/gateway-missing-usage.md). Não executar o piloto enquanto o defeito não estiver revisado e integrado. Receber contadores bem formados não prova que vieram do upstream.

Qualificação gratuita obrigatória: proxy real fixado + upstreams simulados; observar o corpo HTTP traduzido, enum/strict/tool choice, limite de saída, identidade, contadores de entrada/cache/saída incluindo reasoning e apenas uma transmissão por tentativa. Injetar ausência de usage, zeros sintetizados, uso malformado, timeout, erro e troca de modelo/deployment. Desconhecido mantém reserva após reabrir o ledger. Zero retries no SDK, router, deployment e transporte; sem fallback, cache de respostas ou drop de parâmetros. Referências: [Responses LiteLLM](https://docs.litellm.ai/docs/response_api) e [reliability](https://docs.litellm.ai/docs/proxy/reliability).

## Fixture equivalente e qualificação gratuita

Executar em clone e imagem de QA isolados, no host que possa usar **o ledger mensal canônico existente**. Não criar um ledger de US$ 50 por host ou provider. Não copiar o ledger para “compartilhar” saldo e não montar SQLite entre hosts por um filesystem de rede. Se Oracle não puder usar a mesma autoridade de orçamento, executar o piloto no WSL que já a possui ou resolver a arquitetura contábil antes.

Fixture nova e sanitizada, sem dump privado de produção:

- Um knight GUID de QA, nível 20/XP 98.800, skills, HP/mana máximos normais do nível e vocation, equipamento inicial fixo, 40 poções, 10.000 gp, mesmo spawn/posição/floor. A capacidade e o equipamento precisam passar por validação nativa; registrar os IDs/atributos exatos em `fixture-manifest.json` antes de congelar. Não reutilizar os 500 HP/mana artificiais do ensaio de party.
- Mapa compatível com a imagem e com a montagem esperada pelo runner, hash SHA-256, datapack/CSV/Lua/rotas/rates e revisão do binário+SO iguais. Não renomear mapa Canary para fingir que é otservbr: se outro mapa exigir alteração de mount, fazê-la e testá-la em entrega separada.
- Uma população registrada de um bot, sem party/humanos/cast viewers. Mesma política keep-awake em todos os participantes; shadow na baseline, active nos modelos.
- Pelo menos duas caças elegíveis apropriadas ao knight, acesso normal a um NPC de poções e rotas de ida/retorno. Sem comandos humanos durante o relógio pontuado, teleporte de operador ou resgate manual.
- `database.sql` completo sanitizado, `character.json` com os seis campos exigidos pelo runner e manifesto adicional de skills/inventário/banco/condições. Mesmo seed de memória vazio/congelado, estado e pendências independentes por run. Hash de fixture + mapa conferido antes de cada restauração; query inicial completa e snapshot final persistido.
- Cada tentativa em projeto `canary-bench-*`, banco/runtime/rede próprios, sem portas de jogo/DB publicadas, sem volumes de produção. Apenas o gateway privado tem saída para providers. SQL e comandos administrativos de setup pertencem ao harness, nunca ao modelo.

**Gate anterior a qualquer probe pago:** executar gratuitamente baseline e fake por 30 min cada na fixture candidata. Exigir crescimento de XP real confirmado no banco, pelo menos um ciclo de caça completado e múltiplas alternativas elegíveis registradas; demonstrar separadamente compra normal e retorno na mesma topologia. Conferir observações/lifecycle e contabilidade de mortes, gaps, resets e intervenções. Caso a fixture não produza progresso, corrigir/congelar novamente e repetir a qualificação; não pagar para descobrir esse problema. Os ensaios prévios da #10 com XP zero não passam esse gate, e a caça guiada curta da #22 não o substitui.

Não prometer determinismo do mundo: RNG, scheduling e encontros após divergência podem variar. O seed da política é `42 + repetição`, compartilhado no bloco, sem controlar todo o servidor.

## Duração, repetições e ordem

Após revisão, correção contábil integrada, qualificação gratuita e opt-in pago:

1. **Conformidade paga limitada:** no máximo seis tentativas predeclaradas por modelo sobre observações gravadas equivalentes (duas escolhas de caça, suprimentos, baixo HP, viagem e vencimento), sem executar ações no jogo. US$ 0,50 por modelo; sem retry automático. Confirmar conta, contrato, identidade e uso faturado. As duas escolhas devem vir dos mesmos inputs/memória, respeitando TTL. Probes são parte do custo M5, mas não contam como runs de jogo.
2. **Piloto pontuado:** 30 min por tentativa, três repetições por participante, nove tentativas/4,5 h de jogo no total; seis tentativas com modelo, 3 h com modelo. Rodar sequencialmente, sem competição de CPU/DB entre tentativas.
3. Bloco 0: native → luna → haiku. Bloco 1: luna → haiku → native. Bloco 2: haiku → native → luna. Restaurar do zero a mesma fixture a cada tentativa. Nova identidade para a campanha e diretório novo/vazio, nunca reciclar raws. Configuração alterada cria nova campanha, não sobrescreve a anterior.

Horizon = 1.800 s observados desde a primeira observação válida; registrar timestamps do início de provisionamento e primeiro/último snapshot. O worker tem esse relógio; o orquestrador também mantém um deadline após startup e pode encerrá-lo antes. Qualificar os relógios e exigir intervalo observado entre 1.795 e 1.805 s nos runs completos. Se não for cumprido, corrigir o runner em PR separado ou classificar a tentativa incompleta; não afirmar 30 min apenas porque `seconds=1800` consta no JSON. Provisionamento e shutdown não entram como progresso pontuado.

## Métricas e interpretação

| Dimensão | Medida e fonte |
| --- | --- |
| Progresso | XP líquido inicial/final confirmado em DB e gravação, XP/h de parede e ativo, nível, tempo até +1 nível com censura quando não atingido |
| Sobrevivência | Mortes de lifecycle, tempo até primeira morte, recuperação/respawn; não inferir mortes só de HP amostrado |
| Autonomia | Duração sem intervenção humana, causas de parada, episódios completados/falhos, tempo em fallback nativo e tempo estagnado apenas quando observável |
| Custo | US$ liquidado, reserva desconhecida, tokens entrada/cache/saída, requests falhos/tardios/descartados, preço versionado; probes separados e custo total M5 reconciliado |
| Participação do modelo | Candidatos, propostas válidas, aceitação, escolha local única, overrides, resultados confirmados e cobertura efetiva do modelo |
| Latência e overhead | Requests p50/p95/deadline miss, bridge e tick separados, CPU/RSS, filas/gaps/storage. Não confundir latência do provider com tempo de jogo nativo |

Usar versão 2 das métricas e o mesmo analisador para todos. Publicar valores por tentativa, mediana/faixa, denominadores, duração e resultados incompletos; três runs por stack são piloto de viabilidade, não prova de superioridade. Não contar ticks/frames como amostras independentes. Comparação em blocos só como descritiva, já que os encontros não são idênticos. XP/US$ é indisponível com reserva pendente; custo zero da baseline não vira eficiência infinita. Sobrevivência e assistência são apresentadas antes de rendimento; não esconder mortes numa pontuação única.

## Paradas e falhas

- Parada normal no horizonte. Parada financeira antes da próxima transmissão se reserva exceder o teto da run ou o saldo mensal, incluindo passivos desconhecidos. `budget_stop` é resultado retido, nunca descartado.
- Abort de infraestrutura em fixture/hash/modelo/deployment/configuração divergente, erro do ledger, capability ausente, observação stale ou recorder com perda de evidência crítica. Preservar gravação parcial, diagnóstico, custos e o estado salvo possível.
- Critérios propostos de supervisão: três mortes do bot, dez minutos contínuos de estagnação comprovada, ou mais de 30 s sem proposta válida quando existem múltiplos candidatos em oportunidades observadas. Encerrar a tentativa com causa; não resgatar personagem. Continuação nativa ou candidato único não contam como falha de provider.
- Qualquer solicitação de parada do operador encerra o worker; nenhuma nova chamada. Request transmitido/cancelado não é presumido gratuito. Não aumentar teto nem reiniciar uma tentativa sob a mesma identidade.
- Limites observacionais/death/stall além dos gates internos existentes precisam de supervisor validado antes do opt-in. Não estão implementados só por estarem escritos aqui. Validar a saída graciosa e a limpeza de todos os recursos, inclusive sob kill, na QA gratuita.
- Falha de conformidade bloqueia o participante e o início do conjunto pontuado; cinco respostas bem formadas não compensam uma cobrança desconhecida liberada indevidamente. Uma tentativa interrompida permanece registrada; reposição requer decisão explícita e orçamento próprio, mantendo ambos os resultados.

## Teto financeiro e autoridade

**Proposta de autorização máxima: US$ 7,00 para M5**, sem novo teto mensal:

| Etapa | Limite individual | Quantidade | Pior caso |
| --- | ---: | ---: | ---: |
| Probes Luna/Haiku | US$ 0,50 por modelo | 2 | US$ 1,00 |
| Runs pontuados com modelo | US$ 1,00 por run | 6 | US$ 6,00 |
| Baseline/fake/offline | Sem inferência | — | US$ 0 de API |
| **Total** | | | **US$ 7,00** |

Não inclui compra de acesso/créditos nem custo de infraestrutura. Não há contingência automática. O limite global continua **US$ 50 por mês civil America/Sao_Paulo**, incluindo produção, probes antigos, novas chamadas e reservas desconhecidas de meses anteriores. O saldo atual é **não consultado/não conhecido** nesta proposta.

Antes de iniciar, obter snapshot do ledger canônico: `spent`, `reserved`, `available`, mês e data; exigir `available >= US$ 12` (US$ 7 M5 + margem operacional proposta de US$ 5). Se não houver saldo, reduzir escopo em proposta revisada ou aguardar; não abrir outro ledger nem elevar o teto. Essa margem é critério de admissão, não reserva atômica garantida: consumo concorrente de produção pode reduzi-la.

O runner verifica os seis tetos de US$ 1 contra `campaign_cap_nanousd=6000000000`; cada request faz reserva transacional contra run e mensal. Probes têm run IDs e tetos de 500000000 cada no **mesmo** ledger. Orquestrador M5 único, provas/probes sequenciais, sem outras campanhas pagas simultâneas. Probes continuam no total de US$ 7 mesmo se falharem. Não inserir uma reserva contábil extra de US$ 7 que duplicaria o consumo individual; usar o envelope predeclarado e conferir saldo/total entre etapas. Reserva sem usage confiável não é liberada automaticamente e pode exigir conciliação humana com a fatura.

## Evidência e passagem para execução

Entregar manifesto sanitizado, hashes e versões; qualificação gratuita; resultados dos probes; todos os nove IDs e causas de falha; raws/eventos, ledger redigido por tentativa, estado final; resumo JSON, relatório offline comparável e timelapse derivado da gravação. O replay e o vídeo não fazem novas chamadas. A chave real e os prompts com dados privados não entram nos exports.

Sequência proposta: corrigir/revisar bloqueador usage → qualificar fixture + contratos com fake → congelar modelos/configuração e mostrar saldo → revisar esta proposta com Socrates → obter opt-in explícito de Daniel para perfis e US$ 7 → probes limitados → conferir contratos/saldo → nove runs → relatório com incerteza. Aprovar um documento ou integrar PR de correção não autoriza inferência paga.

Esta entrega é planejamento e pesquisa; nenhuma qualificação nova de jogo, consulta de credenciais, chamada paga ou alteração de produção é alegada.
