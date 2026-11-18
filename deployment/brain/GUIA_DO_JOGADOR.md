# Guia de iniciantes dentro do Tibia

## Como seria jogar com o guia

No OTClient conectado ao Canary, o jogador digitaria `/guia Sou druida nível 8. Como me curo?` e receberia uma resposta privada, mesmo jogando sozinho. Uma resposta esperada é “Use Light Healing (`exura`) para curar a si mesmo. Ela custa 20 de mana. Coloque a magia em um atalho para consegui-la usar durante a caça.” A regra está tanto no [datapack deste servidor](../../data/scripts/spells/healing/light_healing.lua) quanto na [biblioteca oficial do Tibia](https://www.tibia.com/library/?spell=lighthealing&subtopic=spells).

Com um bot na party, o jogador poderia perguntar `/guia O Grizzle tem poções para continuar?`. O guia daria a contagem e explicaria o que ela permite concluir. Se decidisse parar, o líder usaria o comando existente `/brain fique aqui por um momento`. Essa divisão permite pedir conselhos antes de decidir o que fazer.

O Canary já registra [`/brain`](../../data/scripts/talkactions/player/brain.lua), recebe mensagens privadas para companheiros e verifica quem pode definir objetivos. O console do worker também tem o modo **Conversar**, de somente leitura. O comando solo `/guia`, a busca de referências e a consulta ao personagem humano descritos abaixo são a proposta de integração. [Conversa e supervisão existentes](README.md)

## Instruções do agente

> Você é o guia de iniciantes deste servidor de Tibia. Responda em português do Brasil. Comece pelo que o jogador pode fazer agora e explique o motivo em uma frase. Na primeira ocorrência de um termo como *hunt*, dê seu significado. Use o nome de item, magia ou NPC que o jogador verá no cliente.
>
> Para perguntas gerais, consulte uma referência e identifique a fonte. Para regras deste mundo, prefira os dados da versão implantada do Canary. Se as versões diferirem, diga qual regra vale aqui. Quando a informação faltar, diga o que conseguiu verificar. Peça apenas o detalhe que mudaria a orientação.
>
> Identifique de quem o jogador está falando. Use os dados do personagem para perguntas sobre “eu” e os dados do companheiro para perguntas sobre o bot. Diga quando a última observação for antiga. Ao retomar uma pergunta, preserve o assunto e o personagem da conversa privada.
>
> No canal de guia, ofereça conselhos. Se o jogador quiser dar uma ordem, mostre a mensagem que ele pode enviar pelo canal de comandos. Nesse canal, proponha somente uma ação oferecida pelo servidor ao jogador autorizado. Diferencie “propus”, “o servidor aceitou” e “terminou”. Para afirmar que algo aconteceu, consulte o resultado da mesma ação.

## Ferramentas propostas

Os nomes abaixo definem o contrato para integração. A identidade do jogador e o mundo vêm da sessão autenticada pelo servidor.

| Ferramenta | Entrada | O que entrega ao guia |
| --- | --- | --- |
| `consultar_tibia` | Pergunta e escopo, servidor local ou Tibia oficial | Trechos relevantes com origem e versão ou data. Pesquisa itens, magias, criaturas, NPCs e missões nos dados do servidor e no material de referência. Se não encontrar, retorna sem resultados. Para os primeiros passos, usar também o [manual da CipSoft](https://www.tibia.com/gameguides/?subtopic=manual). |
| `ler_personagem` | O próprio jogador da sessão | Nível, vocação, vida e mana atuais e máximas, posição e horário da leitura. Distingue valor absoluto de percentual. Campos indisponíveis ficam explícitos. |
| `ler_companheiro` | Companheiro identificado na party | Última observação permitida, com nome, poções, objetivo, ações disponíveis e idade da leitura. Uma party sem esse companheiro recebe “indisponível”. |
| `propor_objetivo` | Ação oferecida pelo Canary e observação correspondente | Identificador da proposta ou motivo da recusa. Disponível no fluxo de comando do bot. O worker e o servidor revalidam a autoridade, a oferta e o estado. |
| `ler_resultado` | Identificador da ação e companheiro | Situação confirmada pelo servidor e motivo, inclusive em caso de expiração ou falha. Uma ação sem resultado terminal continua pendente. |

Na integração, o handler de `/guia` deve expor apenas as três ferramentas de consulta e responder em privado. Assim, mesmo que o modelo interprete “devo parar?” como um pedido para parar, ele só consegue responder. O [protocolo existente](src/canary_brain/protocol.py) oferece observações de bots e resultados de ações. A posição e a vida de um membro da party não substituem uma leitura completa do personagem humano.

## Teste de ponta a ponta proposto

Use um mundo de QA. Prepare uma druida nível 8 com 25 de mana e um companheiro chamado Grizzle com 2 poções. Esses números são dados de teste. Registre as ferramentas chamadas e os resultados do servidor para comparar com o que aparece no chat.

| Passo | O que o jogador faz | Como verificar |
| --- | --- | --- |
| 1 | Entra sozinho e pergunta `/guia Como eu me curo?` | Resposta privada recomenda `exura`, informa o custo de 20 de mana e identifica a fonte local. O registro mostra consulta ao personagem e à magia. |
| 2 | Pergunta `/guia E quantas vezes consigo usar agora?` | Com os mesmos 25 de mana, responde “uma vez, antes de recuperar mana”. O agente mantém o assunto e lê novamente a mana. |
| 3 | Convida Grizzle para a party e pergunta `/guia O Grizzle só tem duas poções. Devo voltar?` | O guia confere a contagem e explica a recomendação. Repita com 10 poções na observação e o mesmo texto do jogador. A nova resposta deve usar 10. Nenhuma das perguntas gera uma ordem. |
| 4 | Como líder, envia `/brain fique aqui por um momento` com a ação de esperar disponível | O bot propõe esperar. Confira se a confirmação do servidor tem o mesmo identificador. Uma aceitação permite informar que o bot aceitou a ordem. |
| 5 | Como líder, pede reposição quando ela estiver disponível | O guia só comunica compra concluída após o resultado de conclusão correspondente. Se o NPC ou o dinheiro faltar, deve informar a falha relatada. |
| 6 | Transfere a liderança enquanto uma ordem da antiga líder aguarda resposta | A resposta atrasada não muda o objetivo. Ao remover o bot da party e perguntar sobre as poções dele, o guia informa que o estado está indisponível. |
| 7 | Pergunta por um NPC inventado com as fontes indisponíveis | O guia informa que não conseguiu verificar e não fornece coordenadas. A conversa continua disponível para nova pergunta. |

## Verificação offline que já pode ser repetida

No Ubuntu/WSL, a partir de `deployment/brain` e com as dependências de desenvolvimento instaladas, rode os quatro testes existentes com modelo simulado:

```bash
python3 -m pytest -q -p no:cacheprovider \
  tests/test_supervision.py::test_readonly_chat_cannot_execute_even_if_model_proposes_action \
  tests/test_supervision.py::test_chat_order_uses_fresh_offer_and_brief_hold_can_be_resumed \
  tests/test_controller.py::test_former_leader_cannot_apply_a_slow_response_after_transfer \
  tests/test_plans.py::test_plan_advances_only_after_terminal_matching_outcome
```

O resultado esperado é `4 passed`. Esses testes exercitam o console e o controlador atuais, incluindo uma troca de liderança e a confirmação da primeira etapa de um plano. O roteiro dentro do cliente depende da integração do comando `/guia`.
