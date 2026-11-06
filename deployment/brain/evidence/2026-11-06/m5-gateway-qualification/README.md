# Recibo público da qualificação do gateway

Observação de **06/11/2026, 12:40:38 UTC**, com a fonte `f4bfbdc90eeee966fcc911ce82cd8e1c56b2115f`.

O gateway LiteLLM 1.108.0 foi qualificado no projeto `canary-bots-wsl`, serviço
`benchmark-gateway`, alias interno `gateway`, sem portas publicadas no host.
Readiness retornou 200; o endpoint administrativo retornou 401 para anônimo e
master e 403 para worker.

O ensaio preservou os nove serviços persistentes e os logs do gateway anterior.
A primeira sessão encerrou por SIGTERM com saída 130, journal `cleaned`, container
removido e alias liberado. Uma segunda sessão distinta ficou pronta.
**A qualificação enviou zero inferências; o M5 pago registrava zero requests.**

`gateway-qualification.public.json` contém somente campos permitidos e hashes das
provas operacionais privadas. `checksums.json` verifica os dois arquivos públicos.
O pacote descreve provisionamento e ciclo de vida; gameplay e comparação de modelos
mantêm seus gates próprios. A disponibilidade corresponde ao horário registrado.

O pacote foi gerado exclusivamente a partir de arquivos existentes, sem consultar
Docker, bancos ou APIs. As provas privadas completas permanecem fora deste recibo.
