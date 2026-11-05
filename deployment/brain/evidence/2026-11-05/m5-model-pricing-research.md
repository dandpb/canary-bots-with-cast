# M5 model and pricing research

Checked: **2026-11-05**. Scope: public primary documentation and the repository's pinned LiteLLM source; no inference calls, credentials, account entitlements, or production configuration were inspected. This is a proposal input, not model qualification or spending approval.

## Configuration and candidate status

Repository base: `a2f1e51f0a1a9566daa650c056d7a70c452c533b`. `gateway/requirements.lock` pins `litellm==1.108.0`; `gateway/compose.yaml` names `canary-litellm:1.108.0`. The checked-in `gateway/gateway.example.yaml` contains only `participant-a` mapped to `openai/gpt-6-luna`. It is an example, not evidence that an account or running proxy can serve it. No second provider is configured there.

The proposed first comparison is **native baseline + Luna + Haiku 5.5**. Gemini is an optional later amendment, not an automatic replacement if either participant fails qualification.

| Proposed alias | Native model ID | LiteLLM upstream mapping | Current status |
| --- | --- | --- | --- |
| `m5-luna` | `gpt-6-luna` | `openai/gpt-6-luna` | Existing example family; pinned source lists the model; account and live contract unverified |
| `m5-haiku` | `claude-haiku-5-5` | `anthropic/claude-haiku-5-5` | Proposed second provider; pinned source lists the model; account and live contract unverified |
| `m5-gemini` | `gemini-3.5-flash-lite` | `gemini/gemini-3.5-flash-lite` | Optional third model; pinned source lists the model; account and live contract unverified |

The exact entries were inspected in the [LiteLLM v1.108.0 model map](https://github.com/BerriAI/litellm/blob/v1.108.0/model_prices_and_context_window.json). It identifies the three providers and marks function calling and response-schema capabilities for these IDs. The Haiku entry additionally advertises forced tool use, native structured output, and `thinking_always_on: false`. Those metadata flags are static support evidence, not a successful wire test or a provider entitlement.

## Standard text prices

USD per **1,000,000 tokens**, checked on the date above; standard synchronous service, no regional premium, no batch/flex/priority discount, no external paid tools. Models tokenize the same text differently; equal bytes do not imply equal billed tokens.

| Model | Uncached input | Output | Cache read | Cache write | Price source |
| --- | ---: | ---: | ---: | ---: | --- |
| GPT-6 Luna, input <=272K | $0.10 | $0.50 | $0.01 | $0.125 | [Official OpenAI model page](https://developers.openai.com/api/docs/models/gpt-6-luna) |
| Claude Haiku 5.5, input <=100K | $0.10 | $0.50 | $0.01 | $0.125 for 5m; $0.20 for 1h | [Official Haiku 5.5 overview](https://platform.claude.com/docs/en/models/haiku-5-5/overview) |
| Gemini 3.5 Flash-Lite | $0.30 | $2.50, including thinking | $0.03 | Explicit cache storage: $1/MTok-hour; not a single token-write price | [Official Google pricing](https://aistudio.google.com/docs/pricing#gemini-3.5-flash-lite) |

OpenAI documents Luna's cache write price explicitly; it is not inferred from a different model. Above 272K input tokens, Luna input/cache rates double and output increases 1.5x. Regional processing adds 10%. The model supports Responses, function calls and reasoning; reasoning effort defaults to medium if not otherwise specified. The M5 profile must pin the actual setting rather than treating omission as disabled. [Official OpenAI documentation](https://developers.openai.com/api/docs/models/gpt-6-luna).

Haiku 5.5 has higher rates above 100K input tokens ($0.50 input/$2.50 output). Its 5m write, 1h write and cache read rates above that boundary are $0.625/$1/$0.05. It defaults to adaptive thinking and supports a 128K output limit; short bounded tool choices should not be confused with that maximum. [Official model overview](https://platform.claude.com/docs/en/models/haiku-5-5/overview).

Google labels `gemini-3.5-flash-lite` stable and lists function calling, structured output and thinking. These capabilities do not prove identical semantics under the Responses translation. [Official model page](https://aistudio.google.com/docs/models/gemini-3.5-flash-lite).

## Contract and accounting gates

Local `src/canary_brain/gateway.py` currently sends one strict `choose_action` function, an enum of offered candidate IDs, a forced named tool choice, `parallel_tool_calls=false`, and `max_output_tokens=256` for objective selection. Its `reasoning=false` removes the request field; it does **not** promise that a provider's default reasoning is disabled. Invalid or unexpected model/deployment identities are rejected after usage settlement. A single offered candidate is selected locally without inference. Responses should be the common M5 endpoint; charged Decisions output cannot presently be bounded and is rejected by configuration.

LiteLLM documents `/responses` support since v1.63.8 and translation across OpenAI, Anthropic and Gemini, but current docs alone do not qualify the pinned build. [LiteLLM Responses documentation](https://docs.litellm.ai/docs/response_api).

The [v1.108.0 Responses-to-completion transformation](https://github.com/BerriAI/litellm/blob/v1.108.0/litellm/responses/litellm_completion_transformation/transformation.py) maps `max_output_tokens` to `max_tokens` and carries strict tool schemas into the chat representation. Its usage conversion carries cache-write and reasoning details, but maps a missing usage object to zero-valued usage. Therefore, qualification must specifically establish that absent upstream usage cannot silently settle a charged attempt as free. Merely receiving syntactically valid `input_tokens=0` is insufficient.

The [pinned Anthropic transformation](https://github.com/BerriAI/litellm/blob/v1.108.0/litellm/llms/anthropic/chat/transformation.py) maps output bounds and named tool choice, and aggregates cache read/write tokens into the prompt total. Official Claude documentation states that Haiku 5.5 accepts forced tools and skips thinking for such forced calls. Do not switch to manual extended thinking: forced `any`/`tool` choices are incompatible with that setting. [Official forced-tool behavior](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools#forcing-tool-use).

Before a participant is admitted, a mock-upstream test against the exact gateway image must inspect the translated body and normalized response: candidate enum and strict schema, one forced tool, no parameter dropping, 256-token output bound, intended reasoning semantics, billed output including reasoning, total input inclusive of cache reads/writes, model/deployment identity, and exactly one transmission on failure. Inject missing usage, malformed usage, late results and model mismatch. Retain unknown charge reservations; no automatic retry or alternate deployment. Explicit 1h Anthropic caching and explicit Gemini cache resources are excluded: the current `Prices` shape has one cache-write rate and no cache-storage liability dimension. If these modes are needed later, qualify and extend accounting first.

After explicit paid approval, a capped conformance probe must also confirm account access and the live provider contract, with every attempt in the shared monthly ledger. Unsupported behavior blocks that participant; it must not silently substitute a model or change the common task. No such probe was performed for this research.

## Rate representation and illustrative envelope

For standard short-context Luna and Haiku 5m-cache profiles, the application's per-token nanodollar fields are `input_nanousd=100`, `cached_nanousd=10`, `cache_write_nanousd=125`, `output_nanousd=500`. These are conversions of the table above, not new provider prices. Set a dated price version and preserve the source URLs in the campaign manifest.

Illustrative token bill per choice: 8,192 uncached input tokens + 256 output tokens at these rates = **$0.0009472**. At 360 choices/run it would be **$0.340992**, excluding any other requests or pricing modes. This is arithmetic, not observed token usage, request frequency, or a guarantee that 360 choices suffice for 30 minutes. The actual pre-transmission reservation is more conservative: serialized UTF-8 request bytes plus 4,096, multiplied by the maximum configured input/cache rate, plus bounded output. Run, campaign and monthly liability checks must govern admission, including retained unknown reservations.

No price change is applied by this document. Recheck exact IDs, rates, processing tier, regional uplifts and gateway mappings immediately before the approved pilot; account availability and remaining November ledger capacity are unknown here.
