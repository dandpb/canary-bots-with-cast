# Gateway post-selection boundary (offline)

Base: main `5e0be6ce811ff2e808ca0072cb388355313108b0`; LiteLLM1.108.0.
No provider credentials, live gateway/database or paid request was used.

## Reproduction

The existing authentication validated only the static policy file. In a real
Router from the pinned image, adding a second deployment for the same alias
selected the unvalidated deployment39/100 times in this reproduction. A
pre-selection check has a race with normal deployment refreshes and cannot
establish which deployment will actually be sent upstream. Worker response
validation happens after a potentially billable request.

## Guard

Authentication freezes the declared model, deployment ID, API base, routing
controls and credential snapshot into request-local context. Named credentials
are restricted to `api_key`; routing fields in credential records are refused.
Worker requests use a field allowlist, rejecting credential/provider/deployment/
metadata/client overrides rather than enumerating a few known bypass fields.

The pinned vendor's public `async_pre_call_deployment_hook` runs after Router
selection and before the SDK transport. The guard checks its actual request
copy, including deployment ID, model, alias, API base, credential reference,
retry/fallback counts, caching, custom provider and client/header overrides.
It binds the frozen key and removes the named reference before LiteLLM's later
`load_credentials_from_list` step. No provider key is written to a file.
Non-worker requests have no pin and retain native administrative authentication.

Gemini's native body exception is limited to the exact projection of the same
closed `choose_action` enum schema and forced function. Routing fields or
arbitrary `toolConfig` overrides cannot use this exception.

## Checks

47 directed auth/dispatch/gateway tests passed; Ruff and strict mypy for the
changed policy passed. The existing real proxy smoke passed with three
predeclared fake calls,14 fixture nanodollars settled and missing-usage liability
retained. `gateway_routing_smoke.py` exercised the real application adapter →
HTTP proxy → Router → SDK → local fake upstream, with a deterministic mutation
after authentication and before selection:

- changing model, ID, API base, credential reference or retry count was denied
  before upstream (five attempts, five retained reservations);
- two allowed requests made exactly two fake upstream calls and settled28
  fixture nanodollars;
- changing a named credential after authentication did not change the key sent;
  the authenticated snapshot was used;
- no retry, fallback, wrong-destination call or temporary container remained.

```sh
docker run --rm --network none \
  -v /mnt/e/Development/tibia/.scratch/gateway-qualification-20261106:/source:ro \
  -e PYTHONPATH=/source/deployment/brain/src --entrypoint python \
  canary-litellm:1.108.0 /source/deployment/brain/tools/gateway_routing_smoke.py
```

The mutation seam calls actual Router add/delete operations inside the isolated
proxy; this first smoke does not claim an actual PostgreSQL/UI synchronization
race. Host, source, installed callbacks and SDK process remain trusted. This is
not a guarantee against arbitrary code/memory modification in that process.
The separate benchmark deployment and its credential access require their own
admission; the persistent UI/worker were not changed by this work.
