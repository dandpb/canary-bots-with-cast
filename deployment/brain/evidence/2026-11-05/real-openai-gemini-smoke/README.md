# Real OpenAI/Gemini calls through LiteLLM

Daniel explicitly authorized real calls using the credentials already registered
in LiteLLM and recording their costs. Executed on **2026-11-05, 18:44 America/Sao_Paulo**.
This is a connection/contract/accounting smoke, with synthetic input and real
provider inference. No game command was issued and it is not a scored gameplay run.

## Results

| Route | Effective model | Input tokens | Output tokens | Elapsed | Choice | Calculated USD |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| `canary-openai` | `gpt-6-luna` | 428 | 20 | 1,854 ms | `resupply` | 0.0000528 |
| `canary-gemini` | `gemini-3.5-flash-lite` | 381 | 19 | 842 ms | `resupply` | 0.0001618 |

Both HTTP responses were200, returned exactly one allowed `choose_action` call,
and matched the configured deployment identity. Cached and reasoning token
counters were zero in both responses. OpenAI also reported zero cache-write
tokens; Gemini did not report that counter. The application calculation matched
LiteLLM's `x-litellm-response-cost` header to integer nanodollars for both calls.
The total was **214,600 nanodollars = USD0.0002146**.

Costs use published Standard paid-tier text rates checked on2026-11-05:

- [OpenAI Luna](https://developers.openai.com/api/docs/models/gpt-6-luna):
  USD0.10 input / USD0.50 output per million tokens; cached input0.01,
  cache writes0.125. This prompt is below the long-context threshold.
- [Gemini 3.5 Flash-Lite](https://aistudio.google.com/docs/pricing#gemini-3.5-flash-lite):
  USD0.30 input / USD2.50 output, including thinking, per million tokens;
  cached input0.03. No explicit cache creation/storage or grounding was requested.

These are usage-based calculated costs, also reported by the gateway, rather
than a reconciled provider invoice. Gemini's actual account tier/free allowance
was not established. The report's Gemini cache-write token price is an unused
placeholder: the response did not report cache-write usage, and no explicit
cache storage was requested. Nonzero writes are not qualified by this smoke.

## Accounting and attribution

Used the existing canonical `canary-bots-wsl_brain-state` volume and
`state.sqlite3`, through the application's current Store/GatewayProvider code.
No independent USD50 ledger was created, copied or reset. Each transmission
reserved its upper bound transactionally before HTTP and settled returned usage.
Each provider had a USD0.01 run cap, one attempt, SDK retries0, router/deployment
retries0, no fallback and no response cache. Both new reservations were settled.

| Monthly canonical ledger | Before USD | After USD |
| --- | ---: | ---: |
| Cap | 50.00 | 50.00 |
| Settled spend | 0.303047700 | 0.303262300 |
| Existing unknown reservations | 0.027547250 | 0.027547250 |
| Available | 49.669405050 | 49.669190450 |

No preexisting unknown liability was released. The two application request IDs
are `8e32e915ca5e4407a3ec55ab501bd99a` and
`57f0becd17ab47a2ad3638987ca2f6ef`; corresponding gateway call IDs,
usage, prices, reservations, deployment IDs and recorder events are retained in
[report.json](report.json) and [replay-events.json](replay-events.json).
The canonical ledger also has a `provider_probe` record for each run.

The as-executed run IDs were `credential-smoke-out-openai` and
`credential-smoke-out-gemini`, under the unique audit directory
`/home/daniel/canary-maintenance/litellm-real-probe-20261105T214442Z-ce3e01`.
These IDs must not be reused. The local helper was subsequently updated to
derive future run IDs from the unique audit directory; it was not rerun against
the providers. The recorded IDs/costs were preserved without rewriting history.

## Contract and limits

The same application `GatewayProvider.decide` contract sent both providers an
identical sanitized observation/memory, differing only by the explicit model
alias. It offered `continue` and `resupply`, a strict enum function schema,
forced named tool selection, `parallel_tool_calls=false`, `store=false`, and
`max_output_tokens=256`. Named credentials `openai`/`gemini` were resolved inside
LiteLLM; provider keys were not exported to the harness. The worker credential
included pinned configuration/version/upstream-model headers.

The probe allowed30 s and used synthetic action TTLs30 s to qualify connectivity.
It did not enforce live gameplay deadlines. Luna's1,854 ms exceeds the adapter's
default1,200 ms decision budget in this single sample; production deadline
behavior remains a separate gate. Neither this sample nor Gemini's842 ms is
a p95 or evidence of comparative gameplay quality.

The adapter omitted the reasoning parameter, retaining each provider's default;
no claim of equivalent reasoning settings is made. It reported no reasoning
tokens here. No actual hunt, XP, resupply transaction or autonomy result was
measured. Full M5 fixture/horizon/stop qualification and repeated gameplay runs
remain separate from these two successful provider calls.

## Execution and verification

Application source: `908500b398fe2162536273970e47d0bee023cc47`
(dashboard changes now merged in main as `7f9e8174`). Gateway: LiteLLM1.108.0,
configuration SHA-256
`d48d546fb5789eb23d9e94efbc750aa3ea654b09d66422a2dec750126bf8b316`.
Explicit upstreams were `openai/gpt-6-luna` and
`gemini/gemini-3.5-flash-lite`, with one deployment per alias.

Local commands, with private scripts containing no embedded credentials:

```bash
python3 /mnt/e/Development/tibia/.scratch/launch_litellm_real_probe_20261105.py
python3 /mnt/e/Development/tibia/.scratch/export_real_provider_probe_20261105.py
docker ps -a --format '{{.Names}}|{{.Status}}'
```

The launcher mounted the canonical state volume, policy and internal worker
credential read-only where applicable, and used a dedicated `docker run --rm`
container on the private stack network. Game, worker, web and their database
were not restarted. No temporary probe container remained afterward.
Two earlier preparation attempts failed before any HTTP request/reservation
(configuration mount and invalid synthetic party fixture); the only upstream
attempts were the two successful calls above.

The exporter independently asserted positive usage, exactly one200 per provider,
matching deployment IDs, matching costs, no new unknown liabilities and two
completed recorder runs, each with one reserve/finish pair.
[verification.json](verification.json) records the as-executed harness and
exported artifact SHA-256 hashes. No plaintext credentials or whole ledger
database are part of the exported evidence.
