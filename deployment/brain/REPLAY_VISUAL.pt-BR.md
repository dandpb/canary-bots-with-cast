# Replay da partida e timelapse no OTClient

O replay gráfico usa os pacotes que descrevem o que o bot vê. O OTClient reconstrói o mapa e aplica os mesmos deltas de posição, criaturas, inventário e efeitos. A linha do tempo do Brain continua registrando propostas, intenções, resultados e progresso. Juntas, as duas fontes permitem ver o que apareceu no jogo e verificar quais decisões chegaram ao servidor.

## Plano de entrega

| Etapa | Entrega | Aceite |
| --- | --- | --- |
| 1 | Captura passiva, opt-in, de uma sessão de um bot | Captura ligada/desligada preserva hibernação e número de espectadores. Nenhum login ou chat no arquivo. Falha de escrita ou limite tem indicação explícita. |
| 2 | Reprodução visual 1500, com perfil próprio | O cliente renderiza movimento, troca de andar, criaturas, combate e inventário a partir de uma captura do servidor de QA. Funciona com a pilha de QA fora do ar. |
| 3 | Timelapse em MP4 e linha do tempo com decisões e resultados | Mesmo lance visível a 1× e acelerado. Logs e vídeo devem concordar sobre a ordem da decisão, intenção e resultado. Lacunas ficam marcadas. |
| 4 | Histórico visual de uma vida, com navegação por capítulos | Cada segmento começa com mapa completo. Hibernação, reinício e coleta interrompida delimitam capítulos. A linha do tempo permite saltar para episódios de caça, morte ou reposição e informa quais têm imagem. |
| 5 | Retenção e benchmark com vídeo | Medir volume por hora, p95 do tick e comportamento com captura desligada/ligada no mesmo cenário. Depois, capturar trechos equivalentes de runs isolados e manter as métricas do Brain como evidência do benchmark. |

A primeira entrega implementa uma sessão por processo, com até 30 minutos, 128 MiB de fita e fila de até 2 MiB ou 4.096 pacotes. O arquivo gráfico tem orçamento próprio. Os 5 GB configurados para a telemetria SQLite são independentes. O gravador inicia na primeira ativação natural do GUID escolhido. Se o bot hibernar ou sair, a sessão termina ali. O histórico de uma vida com múltiplos capítulos é a etapa seguinte ao aceite em QA.

## Captura no servidor de QA

Compile `canary` e `bot_engine` juntos a partir da mesma árvore. A captura altera a estrutura interna de `Player`.

Forneça as variáveis abaixo ao processo do jogo e use um diretório de teste privado e inexistente, sob um pai gravável. Use o GUID do bot que já seria ativado pela fixture. Deixe a telemetria ligada para o mesmo bot na mesma pilha.

```text
CANARY_VISUAL_REPLAY_BOT=65001
CANARY_VISUAL_REPLAY_DIR=/private/qa/visual-chapter-01
```

O servidor escreve `game.cam` e finaliza `capture.json` em segundo plano. `queue_limit` e `storage_limit` indicam um fim truncado. Recibo ausente, bootstrap incompleto e falha de escrita impedem o empacotamento. Mesmo os pacotes visuais podem incluir nomes de personagens visíveis, então mantenha o arquivo privado. Prefira uma fixture sem jogadores externos.

## Preparar, assistir e exportar

```text
canary-brain replay visual-pack --capture <pasta-da-captura> --recording <replay.sqlite3> --run <run-id> --output <pacote-novo>
canary-brain replay visual-stage --package <pacote> --runtime <OTClient-1500> --output <pasta-nova> --mode frames
```

Execute `visual-stage` no Windows com o OTClient e os recursos 1500 já instalados. Ele prepara uma cópia de execução com perfil gravável exclusivo, configurações de servidor desativadas e os módulos base. O comando devolve `launch.json` com o diretório de trabalho e a lista de argumentos. Abra o executável dessa pasta com os argumentos do recibo. O modo `watch` toca o arquivo diretamente. O modo `frames` captura a janela durante o replay. Aguarde o fim antes de exportar. A captura de tela é feita em tempo real, então mantenha a janela visível durante a gravação.

```text
canary-brain replay visual-video --package <pacote> --frames <perfil>/frames --speed 8 --fps 24 --output <partida.mp4>
```

O MP4 inclui legendas que agrupam os eventos por segundo de vídeo e capítulos para decisões, resultados e marcos observados em players que os exibem. `timeline.json` conserva os horários e IDs individuais, incluindo os eventos que ficaram fora da legenda agrupada. O arquivo `partida.mp4.json` vincula as entradas e o MP4 e registra as partes das bordas que ficaram fora da renderização. O pacote registra dados de progresso e ações observáveis. Os motivos só aparecem quando o evento os registrou.

A sincronização usa o relógio de parede do servidor e o instante em que o Brain recebeu o evento. Em QA, use a mesma máquina ou calibre `--offset-ms` com um evento visível nos dois registros. Isso fornece uma aproximação, com atraso de transporte. Um marcador compartilhado entre os dois produtores é necessário para atribuição mais precisa.

## Aceite antes de ampliar

Use uma rodada curta com movimento, combate, passagem entre andares, abertura de mochila e ressuprimento. Confirme no OTClient um exemplo visível de cada evento. Aplique o aceite de hibernação e custo de CPU, fila, fita e disco. Já é possível comparar saídas com o replay amostrado original. O MP4 não contém áudio nesta versão e registros antigos sem pacotes continuam usando a visualização original.
