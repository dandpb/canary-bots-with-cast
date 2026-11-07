# Lens tracing

Install the optional exporter with `pip install '.[tracing]'`. Set these variables in a private environment file loaded by the worker service:

```dotenv
CANARY_TRACE_BOTS=65045
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1:4318/v1/traces
OTEL_EXPORTER_OTLP_TRACES_HEADERS=Authorization=Bearer <dedicated Lens tracing key>
```

Create the tracing key in Lens using an administrator account. Keep the environment file outside the repository with mode `0600`. The loopback address works when Lens publishes port 4318 on the same host as the brain worker; remote agents need their own reachable address.

The worker records actual Responses and Decisions requests and replies, and native action submission and its first validated server receipt. A receipt of `accepted` or `running` confirms submission, not completion of a hunt. Tool activity shares the decision trace. Export is asynchronous with a bounded queue; collector outages do not change provider routing, action authority or the existing budget ledger. No additional inference requests are made for tracing.

This also supports `provider: "litellm"`. Gateway spans include the returned `litellm.call_id` and deployment ID so Lens can join the trace to its exported spend record. Set `CANARY_GATEWAY_WORKER_USER_ID` on the gateway to the user owning the dedicated Lens tracing key when that ownership is appropriate. The worker credential retains its model-only endpoint allowlist and cannot administer the gateway. Existing deployments without this variable keep their current identity behavior.

Lens source revision `5109b59` reports `incomplete_evidence` for Decisions spans without a provider response ID, even with a gateway call ID. Their spend records still arrive in ClickHouse and can be matched to that call ID; a blank trace cost does not mean the call was free. This does not affect worker budget settlement.

With GPT-6 Luna Decisions on LiteLLM 1.108.0, set `gateway.decisions_output_nanousd: 0` while retaining the Responses output rate in `gateway.prices.output_nanousd`. The adapter converts Decisions `input_json` parts to JSON text before reserving the request budget because this gateway version accepts text parts. Responses calls retain their independent output cap and pricing. Keep the gateway version, configuration hash and deployment mapping pinned; a changed catalog requires revalidating the worker manifest before restarting it.

Only selected bot IDs are traced. Provider credentials are never exporter inputs. Known credential fields and key patterns are removed; game context and conversations are recorded and should be treated as private data. Pending receipts expire after five minutes when another action is submitted, or end as `worker_stopped` at shutdown.

Without `CANARY_TRACE_BOTS`, tracing is disabled and the optional SDK is not imported. Remove the tracing environment file from the service and restart the worker to disable export. Retain Lens credentials and its ClickHouse volume across restarts. Never use `docker compose down -v` for recovery.

See the [Lens deployment guide](https://github.com/BerriAI/lens/blob/main/deploy/lens/README.md) and [OpenTelemetry Python exporters](https://opentelemetry.io/docs/languages/python/exporters/) for the deployment and export protocols. A standalone Lens service can be connected to LiteLLM using its native Lens adapter; keep their API contracts compatible and pin the selected artifacts.
