# GPT-6 Luna through LiteLLM: validation

Validated on Ubuntu 24.04 ARM64, Python 3.12, LiteLLM 1.108.0 and Lens source `5109b59b5575a00d752a8dd3134211c573560069`.

- Full regression: `python -m pytest tests -q` — **738 passed, 8 subtests passed**, 432.73 seconds. An earlier run had a scheduler-sensitive elapsed-time assertion; its isolated rerun and this final full run passed without changing the threshold.
- Focused gateway/auth/dispatch/tracing/fault checks: **72 passed**. Ruff, strict mypy over all 21 source modules, and `pip check` passed.
- Four real calls through the restricted gateway credential passed: Decisions, Responses with low effort, Responses with maximum effort, and reflection with a tool result. All four settled in the existing shared monthly ledger, costing **USD 0.0003464** in total.
- The production worker was configured for the same three bot IDs, GPT-6 Luna and USD50/month shared ledger. State and budget file paths were preserved. The game server was not restarted.
- Tarshaw's natural Decisions call traversed the gateway and selected a target preference. Lens recorded the model input/output, the native intent, and its matching `completed / preference_applied` receipt. This confirms applying that preference, not killing the selected target.
- The actual gateway call ID matched a successful persisted spend record. The worker settlement had the same timestamp, 536 input tokens and USD 0.0000536 amount. The embedded Lens sidebar, model input/output and completed tool receipt were verified with Playwright; no page errors or externally served executable UI scripts were observed.
- Real negative checks blocked worker administration, key management, stale configuration/version, unknown model and a mismatched upstream mapping before inference.
- Game smoke checks passed: website and browser-client HTTP, cast login with 100 bots, live map positions, native TCP/status with 100 online players and Tailscale WSS upgrade/binary challenge.

Lens at this revision reports Decisions spend as `incomplete_evidence` when the response has no provider response ID. The exported gateway record and worker ledger retain the verified cost; a blank trace cost is not zero. Analysis, Signals and evals were not enabled.

Credentials, deployment-specific configuration, traces, screenshots and detailed logs remain outside Git in private deployment directories. The deployment uses the optional tracing package and a private environment file; see [LENS.md](../../LENS.md).
