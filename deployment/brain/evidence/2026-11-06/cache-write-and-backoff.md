# Unqualified cache-write accounting and backoff attribution

Refs #10. Scope: shared application accounting/recording guard before the M5
pilot. No runtime configuration, real ledger or provider credential was opened;
no paid request or game test was made.

## Unknown is distinct from free

`Prices.cache_write_nanousd` accepts an explicit JSON `null` for an unqualified
cache-write tariff. Numeric0 remains an explicitly free tariff, retaining
compatibility for profiles that legitimately declare free writes. Known
positive per-token tariffs retain their existing calculation.

The Gemini pilot profile must declare `null`: its explicit cache storage charge
is not a qualified per-token write tariff, and explicit cache creation/storage
is outside this campaign. If a response nevertheless reports positive
`cache_write_tokens`, Provider raises `UnpricedCacheWrite` before `Store.settle`.
The full pre-request reservation remains unknown liability after reopening
SQLite. Unknown writes are never silently multiplied by zero and released.
The ordinary no-write response with an unknown write tariff still settles
known input/output usage. Reservation calculation uses known input tariffs;
it does not claim an upper bound for an unqualified storage charge.

Regression through `GatewayProvider.decide` exercises positive write usage,
one transmission, retained liability after restart, no writes with an unknown
tariff, and explicitly free/paid write tariffs. The initial main failed to
represent either unknown-tariff case; both cases pass with the nullable profile.

## Backoff skips carry their own identity

A cooldown skip now raises `ProviderBackoff`, a RuntimeError subclass, rather
than an indistinguishable RuntimeError. Before raising, the recorder receives a
`request` event with phase `skipped`, reason `backoff`, `deadline_ms`, and zero
reservation. The existing record helper attaches request/decision/model IDs.
There is no `Store.reserve`, SQL requests row, new upstream attempt or new
financial liability for that skip. The controller naturally records the more
specific fallback reason from the exception class.

The recorder regression uses a real Recorder/ReplayReader and temporary SQLite
Store: one transmitted failure followed by one skip yields one reserved event,
one failed event, one attributed skipped event and one SQL request. Budget and
upstream call count remain unchanged by the skip. Reports must count committed
financial attempts from reserved events, and skips separately; historical generic
RuntimeError events remain ambiguous.

Validation: directed gateway/provider/cache/deadline tests and replay metric/HTTP
tests pass; Ruff lint/format and strict mypy pass. These tests do not establish
provider-native strict schema support, immutable gateway routing or admission of
the current fixture; those remain separate gates owned by the coordinator.
