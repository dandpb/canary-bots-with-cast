# M5 Haiku wire qualification — 2026-11-05

The pinned route is **not qualified for paid M5 execution**. This is a local
protocol test, not a model quality result or a check of account access.

## Reproduction

From the repository in WSL, with the existing Python environment and local image:

```sh
PYTHONPATH=deployment/brain/src /tmp/canary-replay-venv/bin/python \
  deployment/brain/tools/haiku_gateway_smoke.py
```

Expected exit status for this finding: **1**, with
`contract_qualified: false`. The container has `--network none`; the proxy and
fake Anthropic Messages server communicate only over container loopback. All
keys are newly generated or explicit mock values. No provider credential or
external service is accessed.

Tested image: `canary-litellm:1.108.0`, local content ID
`sha256:a0e9d7da7b36ff52f325f1f715123e77de91fa3b6676402c06f34f9312eccf62`.
Route: `anthropic/claude-haiku-5-5`. The script uses the actual
`GatewayProvider.decide` request and the repository's gateway authentication
policy. Retries, fallback, response caching and parameter dropping are disabled.

## Observed contracts

The [captured result](haiku-pinned-result.json) records:

- The upstream request reached `/v1/messages`, forced the named `choose_action`
  tool, disabled parallel tools, retained the candidate enum and enforced the
  output limit of 256 tokens.
- The native tool **did not contain `strict: true`**, despite the strict tool
  requested by the worker. JSON Schema with `additionalProperties: false`
  alone does not prove native strict tool use. Anthropic documents these as
  distinct controls in its [structured outputs documentation](https://platform.claude.com/docs/en/build-with-claude/structured-outputs),
  checked 2026-11-05.
- Positive usage conversion passed: 10 uncached input, 3 cache-read, 2
  cache-write and 2 output tokens became 15 input / 2 output / 17 total.
  Unequal **mock** rates of 7/2/11/13 nanodollars gave exactly **124
  nanodollars**; these rates are not quoted provider prices.
- Missing usage and HTTP 500 each caused one upstream call and retained
  unresolved liability after reopening the local ledger. Total upstream calls:
  three; settled spend remained 124 mock nanodollars.

The local candidate validation still applies. This finding concerns the
native strict protocol gate for this exact version/configuration; it does not
establish that every LiteLLM configuration or newer release has the same
behavior. It also provides no evidence of real account/model availability.

## Required next gate

Review a LiteLLM configuration or version change and reproduce the strict flag
on the captured native wire, retaining all accounting and single-call checks.
Do not weaken the scored contract, silently substitute another model, bypass
LiteLLM, or start paid requests to investigate this finding.
