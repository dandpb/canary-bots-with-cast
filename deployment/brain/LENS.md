# Lens tracing

Install the optional exporter with `pip install '.[tracing]'`. Set these variables in a private environment file loaded by the worker service:

```dotenv
CANARY_TRACE_BOTS=65045
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1:4318/v1/traces
OTEL_EXPORTER_OTLP_TRACES_HEADERS=Authorization=Bearer <dedicated Lens tracing key>
```

Create the tracing key in Lens using an administrator account. Keep the environment file outside the repository with mode `0600`. The loopback address works when Lens publishes port 4318 on the same host as the brain worker; remote agents need their own reachable address.

The worker records actual Responses and Decisions requests and replies, and native action submission and its first validated server receipt. A receipt of `accepted` or `running` confirms submission, not completion of a hunt. Tool activity shares the decision trace. Export is asynchronous with a bounded queue; collector outages do not change provider routing, action authority or the existing budget ledger. No additional inference requests are made for tracing.

Only selected bot IDs are traced. Provider credentials are never exporter inputs. Known credential fields and key patterns are removed; game context and conversations are recorded and should be treated as private data. Pending receipts expire after five minutes when another action is submitted, or end as `worker_stopped` at shutdown.

Without `CANARY_TRACE_BOTS`, tracing is disabled and the optional SDK is not imported. Remove the tracing environment file from the service and restart the worker to disable export. Retain Lens credentials and its ClickHouse volume across restarts. Never use `docker compose down -v` for recovery.

See the [Lens deployment guide](https://github.com/BerriAI/lens/blob/main/deploy/lens/README.md) and [OpenTelemetry Python exporters](https://opentelemetry.io/docs/languages/python/exporters/) for the deployment and export protocols. A standalone Lens service can be connected to LiteLLM using its native Lens adapter; keep their API contracts compatible and pin the selected artifacts.
