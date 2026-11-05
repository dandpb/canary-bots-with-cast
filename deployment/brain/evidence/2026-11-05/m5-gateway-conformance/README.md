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

## Follow-up: cause and adapter fix (same day)

Cause, in LiteLLM 1.108.0 itself (no configuration key involved):

- The Responses bridge keeps `strict` when it turns the `function` tool into a
  Chat Completions tool
  (`litellm/responses/litellm_completion_transformation/transformation.py:2497`).
- `AnthropicConfig._map_tool_helper`
  (`litellm/llms/anthropic/chat/transformation.py:941-972`) then builds the
  Messages tool from `name`, `input_schema` and `type: "custom"` only, so
  `function.strict` is dropped. `drop_params`, `additional_drop_params` and the
  map's `supports_native_structured_output: true` do not change this.
- Same result offline with 1.100.0, 1.104.8, 1.106.7 and 1.108.0 (latest on
  PyPI on 2026-11-05); `_map_tool_helper` has no `strict` in tags v1.70 to
  v1.108.0 nor on LiteLLM `main` (`aa7917a3`, 2026-11-05).

Fix: for `provider == "anthropic"`, `GatewayProvider` now sends the choice
tool already in Messages shape (`name`, `input_schema`, `strict: true`, no
`type`). The Responses bridge passes an unknown-type tool through (`:2530`) and
`_map_tools` forwards a tool with `input_schema` as is
(`litellm/llms/anthropic/chat/transformation.py:1257`). Other providers keep
the OpenAI function tool unchanged.

Result with the fix: [haiku-native-tool-result.json](haiku-native-tool-result.json),
exit 0. Compared with the pinned run, the upstream decision request is the
same except inside the tool: `strict: true` is added and the defaults
`type: "custom"` and `description: ""` are no longer sent. The enum, forced
tool, `disable_parallel_tool_use`, `max_tokens: 256`, one upstream call per
decision, usage 15/2/17, 124 mock nanodollars and retained liability on
missing usage/HTTP 500 are unchanged (3 upstream calls in total).

This run used `litellm==1.108.0`, `openai==3.46.0` from
`gateway/requirements.lock` in a local venv (`--inside`, loopback only), not
the image digest, which was not available. `contract_qualified: true` is only
the wire gate: whether the real Haiku endpoint accepts `strict` without a
beta header, account access, prices and paid approval remain unverified.
