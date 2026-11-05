# M5 decision-deadline qualification (offline)

Real LiteLLM 1.108.0 (pinned `gateway/requirements.lock`, Python 3.12, no Docker)
in front of a local fake Responses upstream that sleeps for an injected delay.
No provider, credential, shared server or paid call was used. Base: main
`ad59204444211002eb25aff54cd0a826129f3431`.

```bash
# inside the canary-litellm:1.108.0 image (default) or any env with the lock installed
python deployment/brain/tools/deadline_smoke.py            # docker, --network none
PYTHONPATH=deployment/brain/src python deployment/brain/tools/deadline_smoke.py --inside
```

Grid: configured `decision_timeout` 1.2 s (runtime default), 2.5 s, 10 s
(Experiment default) × catalogs with server TTLs 5000 ms (hunt/resupply),
1500 ms (retreat/continue) and 1000 ms (target) × delays 0.5/1.19/1.21/1.85/3 s.
Result: [smoke-result.json](smoke-result.json), all 14 checks true.

## What the deadline really is

`GatewayProvider.decide` passes `min(decision_timeout, min(ttl_ms)/1000)`
(`src/canary_brain/gateway.py:156-160`). The value that reached `_request`:

| Configured | 5000 ms catalog | 1500 ms catalog | 1000 ms catalog |
| ---: | ---: | ---: | ---: |
| 1.2 s | 1.2 s | 1.2 s | 1.0 s |
| 2.5 s | 2.5 s | 1.5 s | 1.0 s |
| 10 s | 5.0 s | 1.5 s | 1.0 s |

With a 1.85 s upstream delay (about 2.0 s end to end; Luna's real 1,854 ms was
already end to end) only the 5000 ms catalog succeeds, and only with a configured
value above the end-to-end time. Gateway plus adapter overhead
over the injected delay was 144-198 ms, so the 1.19 s case also times out at 1.2 s.
The deadline fired 35-62 ms late on this host.

## Failure and money accounting

- 25/45 cases timed out; each raised `TimeoutError`, recorded one `failed` request
  event, counted in replay `provider_failures`, settled nothing and kept its full
  upper-bound reservation (about 0.81 mUSD versus 0.05 mUSD actual usage).
- Every late answer still completed at the upstream (a provider would bill it);
  none settled afterwards. Ledger reserved = unsettled rows = replay
  `reserved_nanousd` = 20,334,750 nanodollars; spent = 21 successes x 50,000.
- Before this branch, every deadline miss was recorded as `CancelledError`
  (the outer `asyncio.timeout` cancels the transmission first), indistinguishable
  from world-change or shutdown cancellation. Now it is `TimeoutError` with
  `deadline_ms`; an external cancellation stays `CancelledError`.

## Limits

Offline only: fixed synthetic delays, one host, warm gateway, no real provider
tail, no game. Replay latency percentiles cover finished requests only, so they
are censored at the deadline; report them together with the timeout rate.
