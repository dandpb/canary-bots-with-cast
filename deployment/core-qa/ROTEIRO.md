# Roteiro manual do QA (`canary-core-qa`)

Somente no QA isolado, nunca na produção. Nenhuma etapa usa modelo real, credencial
ou ledger real. Anote em cada passo: passou, falhou ou não exercitado, com hora e texto
recebido. Não cure, não teleporte nem reinicie nada para "fazer passar".

## Etapa 1: jogo nativo (stack base, brain desligado)

| # | Ação | Esperado |
|---|---|---|
| 1 | Login em `http://127.0.0.1:18080/login.php` no OTClient (protocolo 1500). | O personagem entra no jogo de QA. |
| 2 | `/party ek,ed,ms`, ande 10 a 20 passos. | `Party formed...`; os bots chegam e seguem. |
| 3 | `/brain oi`. | `Brain disabled; native behavior is active.` (esperado nesta etapa). |
| 4 | Conta `@cast`: assista à partida. | O cast mostra o jogo. |
| 5 | `/party leave`. | `Dismissed N party bot(s).` |

## Etapa 2: worker fake (README, seção Etapa 2)

`/party` escolhe bots nativos quaisquer e **não** traz os pilotos. Para ter um piloto na
party: o GOD vai até você (`/goto <seu nome>`) e traz o piloto com `/c Galdon Whitehoof`
(65004) ou `/c Sever Heartspear` (65003). Você clica com o botão direito no piloto e usa
"Invite to Party"; ele aceita em 1,5 a 4,5 s. Se `/c` não o encontrar, ele está hibernando:
tente o outro. Grizzle Alyronia (65001) é o explorador e fica fora da party.

| # | Ação | Esperado |
|---|---|---|
| 6 | GOD: `/cavebot _global brain status`. | `"mode":"active"`, `"worker_alive":true`, roster `[65001,65004,65003]`. Se vier `Brain disabled`, pare. |
| 7 | Convide um piloto como acima. | Ele entra na party. |
| 8 | `/brain fique aqui`. | `Mensagem enviada ao companheiro.` e PM `Teste: proposta hold; ...`; ele para por cerca de 30 s. |
| 9 | `/brain siga comigo` e ande. | PM `proposta follow`; ele segue. |
| 10 | `/brain oi`. | PM `proposta continue`: o fake não entende texto livre. |
| 11 | Kill switch: GOD `/cavebot _global brain disable`. | `Brain disabled; native behavior retained.`; o piloto volta ao nativo. |
| 12 | GOD `/cavebot _global brain reload`; operador `$QA stop brain`, espera 10 s, `$QA start brain`. | Parado: `worker_alive:false` em até 5 s e bot nativo. Depois: `worker_alive:true`, sem meta antiga. |
| 13 | `/party leave` e saia. | Os bots saem. Diga se ajudou, atrapalhou ou confundiu. |

Diagnóstico: `Mensagem enviada ao bot explorador.` significa que não há piloto na sua
party; `Nenhum companheiro inteligente disponivel.` que os pilotos estão offline ou você
não é o líder. Para abortar: kill switch, depois `$QA stop brain`, depois o rollback do README.
