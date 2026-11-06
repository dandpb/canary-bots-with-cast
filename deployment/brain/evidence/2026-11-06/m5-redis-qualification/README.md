# Recibo público: Redis de coordenação do LiteLLM

Correção integrada pelo [PR #50](https://github.com/dandpb/canary-bots-with-cast/pull/50),
fonte `b33e1602fa03120e5c9e37e6e2b19679f2d7ed12`.

Redis 7.4.12 foi implantado permanentemente no projeto `canary-bots-wsl`, privado,
com autenticação, AOF e imagem fixada por digest. UI e gateway privado usam
coordenação compartilhada e um worker configurado cada. O cache de respostas
continua desligado; modelos, retries e fallbacks foram preservados.

O teste antes/depois removeu `no_redis` da API usada pela UI, sem suprimir o aviso.
No Chrome já autenticado, após reload, Deployment health mostrou **No active warnings**.
PING autenticado, conexões próprias dos dois proxies e um contador atômico entre
processos confirmaram transporte e estado compartilhado. A entrada administrativa
estava realmente presente no Redis, com TTL positivo, antes de o privado manter
as recusas 401/403. SIGTERM encerrou a sessão privada com saída 130 e journal
`cleaned`; Redis foi mantido e uma nova sessão ficou pronta.

Oito serviços originais fora do alvo permaneceram intactos; a recriação da UI foi
autorizada. A política original e os quatro arquivos de credenciais existentes
foram preservados. No recorte pelo snapshot original de 12:40:38 UTC, os agregados
de 86 pendências anteriores continuam presentes; há três pendências posteriores
classificadas como produção, sem atribuição causal. O JSON distingue o horário
financeiro do horário da observação operacional. O export original não guardava
um baseline de IDs individuais. Nenhuma reserva foi liberada por esta operação.

**Zero inferências e zero escritas no ledger canônico nesta qualificação.**
O piloto M5 permanece separado e precisa atualizar/revalidar seus pins após a
mudança de política. Este recibo descreve o horário registrado, não disponibilidade
contínua. Ele não inclui credenciais, headers, ledger bruto ou caminhos privados.

`redis-qualification.public.json` contém a projeção permitida; `checksums.json`
verifica os dois arquivos públicos. As provas completas permanecem privadas.
