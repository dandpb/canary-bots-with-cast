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
proxy. A second laboratory also exercised real administrative APIs with a
disposable PostgreSQL/schema, sharing only a networkless namespace:

```sh
python3 deployment/brain/tools/run_gateway_admin_routing_smoke.py
```

It paused worker requests after authentication, then issued `POST /model/new`,
`PATCH /model/{id}/update` and `POST /model/delete`, verifying `/model/info`
after each operation. With the duplicate DB alias present,48 selection cases
observed29 denials in the first run (21 expected fake calls,294 fixture
nanodollars). Repeating on the pinned official image observed26 denials
(24 expected calls,336 fixture nanodollars). Every provider HTTP call was
`model-a`; no rogue model or destination was sent. All denied attempts retained
their application reservations. The extra baseline/post-delete requests explain
why expected calls plus denials sum to50 rather than48. Router selection is
random across the duplicate alias; the exact denial count is not a performance
metric. All temporary PG/proxy containers were removed.

The pinned recheck image was
`ghcr.io/berriai/litellm:v1.108.0@sha256:b59b9fd52a67891be4e8dae09ddd4e6c9265e9a8cb3f25f8dd73fbabe7659965`.
The first lab used the retained local UI image
`sha256:5bc955dd82b996db85f971a701907f3b6e60ec86de5d6814267e3744399952cf`.
These are isolated tests; no production tag was relabeled.

The Gemini smoke now asserts that its auth policy is loaded from this source
tree rather than the old policy embedded in an image. The real Responses →
completion → Gemini HTTP path preserves the native closed schema. Model, ID
and API-base mutations after auth are denied before the fake Gemini endpoint;
the sole successful call settles161 fixture nanodollars while three rejected
attempts retain liability. The common smoke also imports the source-qualified
policy. Tests do not rely on an accidentally stale image copy.

## Optional private inference-only image

`gateway/Dockerfile.benchmark` starts from that official digest, overlays only
the policy, skips the UI migration entrypoint, and sets
`CANARY_BENCHMARK_GATEWAY_ONLY=1`. In that mode master/admin credentials do not
fall through to native administrative auth; only the restricted worker key is
accepted. Normal UI deployments omit the flag and keep their existing auth.
The guard is installed by successful worker authentication, so a second
`litellm_settings.callbacks` declaration is not required.

Build from the reviewed source, then record the resulting image ID:

```sh
docker build -f deployment/brain/gateway/Dockerfile.benchmark -t canary-benchmark-gateway:reviewed .
docker image inspect canary-benchmark-gateway:reviewed --format '{{.Id}}'
```

The operator must provision the existing credential DB connection/salt and
internal-key env files privately, mount a campaign-specific static policy
read-only, compute its exact SHA-256, and expose no host port. The canonical
worker/panel are separate processes; this image does not migrate their schema.
Changing policy/image requires a new qualified campaign identity. This PR does
not deploy that instance or grant permission for a new paid call.

Host, source, installed callbacks and SDK process remain trusted. This is not
a guarantee against arbitrary code/memory modification in that process. Normal
model administration and DB synchronization are covered by the tests; changes
to trusted process code/global callback implementations are outside that claim.
The persistent UI/worker were not changed by this work.
