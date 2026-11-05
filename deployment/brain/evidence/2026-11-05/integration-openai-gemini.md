# LiteLLM integration checkpoint — 2026-11-05

Daniel selected **OpenAI + Gemini through standard LiteLLM provider routes** for
the initial pilot. No actual model IDs were selected in that instruction and no
keys were read or real inference calls made. Anthropic is no longer a gate for
the first pilot; its already-merged compatibility support remains optional.

The intended path is game → worker → private LiteLLM gateway → explicit provider
model. The gateway keeps upstream credentials; the worker has only its internal
gateway credential. A friendly alias such as `openai-default` or `gemini-default`
must map to a specific model ID before a scored run. It is not a universal default
chosen automatically by LiteLLM. See the official
[model management](https://docs.litellm.ai/docs/proxy/model_management),
[OpenAI](https://docs.litellm.ai/docs/providers/openai) and
[Gemini](https://docs.litellm.ai/docs/providers/gemini) documentation.

## Current implementation and limits

- The private gateway, shared worker adapter, explicit identity checks, bounded
  tool choices and usage/financial liability handling are implemented and have
  offline tests. The pinned project image remains LiteLLM1.108.0; this checkpoint
  does not upgrade it based on newer online documentation.
- The existing gateway example configures only OpenAI. Gemini needs its explicit
  mapping and route-specific tool/usage/cost qualification. Neither provider has
  been qualified against Daniel's real account in this work.
- Retry, fallback and response-cache changes remain forbidden in scored runs.
  The existing monthly ledger is the budget authority; mock ledgers do not create
  a new spending allowance. Prices and limits must be reviewed for the selected
  model IDs before an authorized account smoke.
- Old controlled native/fake windows and the separate actual purchase/return
  evidence remain frozen in PR25. They do not establish real model quality or
  account access. The historical native database attestation remains absent.

## Standards

Independent read-only review of integration915d0616 against mainf7e435af found
**zero documented-standard violations**. The worker uses its private SQLite
storage carveout and introduces no game MySQL schema or heavy Lua logic.

One nonblocking judgment call remains: the historical QA stop-policy copy has
diverged from the canonical supervised policy. The old fixture uses wall elapsed
completion; the canonical policy requires actual observation coverage and filters
old sequences. The historical distinction is documented rather than overwritten.
Future qualification should use the canonical policy or an explicitly versioned
historical fixture. This is a duplication smell, not evidence that a paid gate
passed or that the old exact-horizon contract was exercised.

## Spec

Independent review found and reproduced two additional correctness defects in
the pre-correction combination:

1. SIGINT during character restoration could create a worker; during socket/game
   startup it could leave the worker running until the blocking operation ended.
2. A financial stop could overwrite a critical stale/world/startup cause, allowing
   the campaign to treat an infrastructure failure as ordinary budget exhaustion.

Patch12c5c6db (PR26 head9e3bac42) checks after character restoration and during
readiness, concurrently relays interruption to the worker, and preserves critical
causes ahead of budget classification. Nine new cases failed before correction;
26 directed startup/abort/horizon cases passed afterward, including SIGINT and
SIGTERM. Independent Git-extracted repros confirm zero workers started after an
interruption in character restoration, zero fake work after startup interruption,
and durable `observation_stale` when a budget marker also exists. No provider was
used by those tests.

The review also found that the ordinary runner could not express a database pin.
Patch253858f4 (PR29 head45c08a83, stacked on PR26) adds `database_image`, propagates
it into Compose and the configuration fingerprint, and rejects mutable game/DB
references for LiteLLM campaigns before credential reads. Native-only defaults
remain available. Three new tests failed before the correction. Four pin tests
passed independently against source extracted from Git; no blocking finding
remained in this separate diff. This does not retrospectively attest old images
or verify real model availability.

## Integrated validation

The checkout combines mainf7e435af (including the merged gateway compatibility
fix), PR25 head6f7a96fb, PR26 with the startup/priority fixes, and PR29's pin gate.
Runtime/source checkpoint: `253858f476dc8f8193ad72e38cef44b05bd7a742`.

```sh
cd deployment/brain
PYTHONPATH=src python -m pytest -q --basetemp=/tmp/m5-int-final-f
# 202 passed in164.99s
ruff check src/canary_brain/benchmark.py src/canary_brain/runtime.py \
  tests/test_benchmark.py tests/test_benchmark_startup_interrupt.py \
  tests/test_benchmark_image_pins.py
ruff format --check src/canary_brain/benchmark.py src/canary_brain/runtime.py \
  tests/test_benchmark.py tests/test_benchmark_startup_interrupt.py \
  tests/test_benchmark_image_pins.py
mypy src
# lint/format passed; strict typing passed in19 source modules
```

This is an integration validation branch, not evidence that all these changes
have merged to main or been deployed. Socrates coordinates reviewed merges.
There were no paid calls, real key reads, production changes or modifications to
frozen recordings. Remaining work is explicit OpenAI/Gemini model selection and
configuration, Gemini route qualification, bounded authorized real-account smoke,
then independent scored runs. Human party acceptance remains a separate issue.
