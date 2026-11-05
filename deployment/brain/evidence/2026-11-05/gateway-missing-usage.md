# Missing upstream usage must retain the spending reservation

Date: 2026-11-05. Base: `a2f1e51f0a1a9566daa650c056d7a70c452c533b`.
Scope: #10 M5 financial gate; isolated clone, temporary SQLite ledger,
`canary-litellm:1.108.0`, local fake upstream, `docker run --network none`.
No provider credentials read, paid calls, production modification or deployment.

## Reproduction before the fix

The pinned LiteLLM Responses bridge maps missing usage to
`input_tokens=0, output_tokens=0, total_tokens=0`. The worker accepted those integers
and settled the request for zero, dropping the unknown liability.

From the repository root in WSL with the brain environment available:

```sh
PYTHONPATH=deployment/brain/src python deployment/brain/tools/gateway_usage_smoke.py
PYTHONPATH=deployment/brain/src python deployment/brain/tools/gateway_smoke.py --bridge-usage
cd deployment/brain
python -m pytest tests/test_gateway.py -q
```

With the original `< 0` input check, the first command reported:

```json
{"calls":1,"rejected":false,"budget":{"cap":50000000000,"spent":0,"reserved":0,"available":50000000000}}
```

It failed its assertion that unknown liability remains reserved. The actual HTTP
proxy/Responses-to-chat/fake-upstream test also failed with
`AssertionError: missing upstream usage must retain liability`. Unit regressions
for zero input with output 0 or 2 reported **2 failed, 6 passed** because no
`TypeError` was raised. The positive-usage controls passed.

## Cause and correction

Three explanations were checked: the bridge can lose missing-usage provenance;
the worker can accept synthetic zero counts; or the ledger can release a reserve
without explicit settlement. The real bridge demonstrated the first; positive
usage settled normally, and the worker explicitly called `settle(..., 0)` for the
synthetic counts. The ledger's reservation transaction was not the defective seam.

For every prompt transmitted by this worker, input is nonempty. Input usage must
therefore be a positive integer before any settlement. Reject zero just like
missing or malformed usage, preserving the pre-transmission reservation and the
existing failure/backoff/attribution path. Do not infer free billing from zeros,
retry the request, or invent token counts. Cached input still counts in total
input and does not justify a zero input total.

This is conservative: if an upstream reports zero input even for a nonempty
request, its charge remains unknown pending reconciliation. It does not claim
that arbitrary positive usage is trustworthy or that every provider's accounting
has now been qualified.

## Regression and validation

The isolated bridge/worker check after correction reported one transmission,
`rejected=true`, zero settled spend, and **649,375 nanodollars retained** after
reopening the temporary ledger. Available budget fell from 50,000,000,000 to
49,999,350,625 nanodollars. These are fake-fixture values, not actual expenditure.

The wire test additionally covers native Responses passthrough and Responses
translation to a fake chat upstream. Each mode exercises a successful known-usage
request, a missing-usage response and a 500 response. Each performs exactly three
upstream calls, settles only the known 14 fixture nanodollars, and retains unknown
liabilities. No fallback/retry occurs. The Python regressions reopen the ledger to
check that the unknown liability survives a new Store instance.

Validation completed: **142 Python tests passed in 66.40 s**; Ruff lint and format
passed for all four affected Python files; strict mypy reported no issues in 18
source files. `git diff --check` passed. The exercised pinned image ID was
`sha256:a0e9d7da7b36ff52f325f1f715123e77de91fa3b6676402c06f34f9312eccf62`.
No native build is needed for this Python-only change. M5 remains blocked pending
review/integration and the separate fixture, contract and paid-approval gates.
