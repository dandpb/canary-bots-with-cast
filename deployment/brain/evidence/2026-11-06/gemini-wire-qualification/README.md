# Gemini JSON Schema preservation and SDK usage counters

Offline qualification on2026-11-06, based on main
`5e0be6ce811ff2e808ca0072cb388355313108b0`. No real provider, provider credential,
shared service, game server or monthly ledger was used.

## Reproduced problems

LiteLLM1.108.0's Gemini `_map_function` removes `additionalProperties` and
`strict` before constructing its native `parameters` object. The original
Responses-to-Gemini wire probe confirmed the strict enum function reached the
fake upstream without the additional-properties constraint.

The full application→OpenAI SDK→LiteLLM proxy→fake Gemini loop then exposed a
second problem: the pinned OpenAI SDK adds `cache_write_tokens:null` to its
`model_dump` even when the actual response omitted that optional field.
The application rejected otherwise positive usage as malformed and retained
the reservation. The real SDK MockTransport regression fails on main for the
omitted-counter case; explicit null is deliberately still rejected.

## Change

`GatewayProvider` preserves the JSON Schema via LiteLLM's supported native
`extra_body` merge after OpenAI tool mapping. Its native declaration is
`functionDeclarations[].parametersJsonSchema`, containing the unchanged enum,
required field and `additionalProperties:false`. The generic Responses tool
and forced named tool choice remain present. The OpenAI SDK requires one
outer `extra_body` wrapper so the inner provider override reaches the proxy.

`model_dump(exclude_unset=True)` now preserves absence rather than turning it
into a synthesized null. Explicit null remains in the response and the existing
usage validator retains liability. No nullable usage counter is silently
converted to zero. Positive cache writes with unknown pricing are handled by
the separate central Provider/Prices change; this patch does not introduce a
provider-specific pricing exception.

The proxy policy must admit only this exact Gemini tool override and must not
permit arbitrary provider `extra_body`. Integration with that guard is a
separate required check before a real request.

## Verification

```bash
cd deployment/brain
PYTHONPATH=src /tmp/canary-replay-venv/bin/python tools/gemini_gateway_smoke.py
PYTHONPATH=src /tmp/canary-replay-venv/bin/python -m pytest -q \
  tests/test_gateway.py tests/test_gateway_sdk_usage.py tests/test_provider.py \
  tests/test_decision_deadline.py tests/test_gateway_auth.py
```

The HTTP smoke uses the pinned image
`sha256:6b2498fa2e23faa4a23a99420fc47bc77a87f8e19e493fac80ff02e3ddb3ff48`
with `--network none`, real OpenAI SDK and LiteLLM1.108.0, and a Gemini-shaped
upstream bound only to the disposable container's loopback. It asserts:

- exactly one upstream request and a valid returned `resupply` function call;
- unchanged native JSON Schema, including the enum and additional-properties ban;
- native modeANY, allowed function `choose_action` and output bound256;
- input10/output7, including5 reasoning tokens, settled as161 fixture nanodollars;
- zero reserved balance after the valid positive usage response.

Twenty-nine directed tests passed, Ruff lint/format passed, strict mypy passed
for19 source modules, and diff check passed. Temporary containers use `--rm`.
The SDK tests use an in-process MockTransport, not a socket or provider account.

## Native semantics and remaining boundary

Google's [FunctionDeclaration reference](https://ai.google.dev/api/generate-content#FunctionDeclaration)
defines `parametersJsonSchema` as a JSON Schema alternative to `parameters`,
with an additional-properties prohibition in its example. Its
[GenerateContent function-calling guide](https://ai.google.dev/gemini-api/docs/generate-content/function-calling?authuser=0&hl=en)
describes modeANY as forcing function prediction with schema adherence.
The [official API proto](https://github.com/googleapis/googleapis/blob/master/google/ai/generativelanguage/v1beta/content.proto)
also distinguishes ANY from VALIDATED, the latter allowing natural-language output.
The newer Interactions documentation uses a different request/mode surface;
this smoke qualifies the GenerateContent translation, not Interactions.

These sources describe the supported native contract. A fake endpoint proves
preservation on the wire, not real account acceptance or perfect model behavior.
Real-provider conformance remains necessary. Local rejection of invalid model
output is not presented as proof of native enforcement. The smoke's explicit
model is `gemini-3.5-flash-lite`; it is not evidence for a silently substituted model.
