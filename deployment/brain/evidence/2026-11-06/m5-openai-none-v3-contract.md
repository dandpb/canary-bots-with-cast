# One explicit-none controller profile inside the complete USD7 envelope

This contract implements preparation for `openai_none_performance_v3`, requiring
admission `controller_profile:"openai_none_gemini_default_v1"`. It does not
authorize inference or resume/replace either closed default-profile attempt.
A separately reviewed packet and new root GO are required for one invocation.

The immutable functional reference is tracked at
`deployment/brain/tools/m5_openai_none_reference.v2.json`, SHA256
`ee78816aa2d48d965806b8202ee12370d1d8d6c042d264d342daa2a30ebc97f3`.
It projects the six actually captured R2 inputs and is mandatory in the frozen
source manifest. The wrapper validates its bytes against that constant, not
only a newly supplied hash. Execute the tool and its asset from the same frozen
export; all modules remain subject to the existing source/import checks.

## Exactly one functional change

OpenAI must have `reasoning:false` and literal
`decision_reasoning_effort:"none"` in both probe and scored gateway configs.
Gemini keeps `reasoning:false` and absent/null effort, preserving omission.
The default OpenAI profile is not silently changed or retrospectively accepted.
JSON types, keys and list order are compared before Pydantic can supply defaults
or coerce values. Duplicate keys, extra controls, merely matching two modified
configs and a different profile are rejected.

Everything else matches the reference: models/deployments, gateway policy and
route projection, four pinned images, dependency versions, prices, decision
fixtures, fixture/world hashes, output cap256, effective deadlines, seed42,
frozen memory, 1800-second horizons, three repetitions and ABC/BCA/CAB order.
The cap256 remains the decision SDK contract; it is not an output-text allowance
in addition to reasoning. Admission binds `gateway_image`,
`gateway_route_projection_sha256`, `common_worker_image` and dependency versions.

Only the enumerated identity relocations are allowed: fresh name/output/source,
fixture/world paths with unchanged content, restricted credential host mount
with the same internal credential path, and probe socket/state/recording paths
inside the new output. Both old namespaces are denied case-insensitively.
No closed p6/f6/p7/f7 packet or earlier authorization is edited or reused.

## Every prior liability remains inside USD7

The 18:21:10.457077 UTC public Finance receipt, SHA256
`8750cf48751b7958a68078e6cd3179cc097d3115e2ed74b68c75bd7b58a08be8`,
observed ten requests: two historical smokes, five reserved application attempts
in the first invocation and three in R2. Confirmed spend was 863500 nanoUSD,
unknown reserved 4299300 and complete liability 5162800. These are bounded
historical observations, not credit or a substitute for a fresh canonical read.

The reference fixes every prior request-to-run association. All ten must exist;
the historical two retain their exact settled values. Unexpected extra rows in
the three closed probe runs block admission. Money types are checked before
SQLite sums. Known `spent=0` stays distinct from `spent IS NULL`; unknowns use
their full current reservation. The three runs are:

- `decisions:e9b235a5fcd24566b020fc332cd44e0d:65001`
- `decisions:3f5394354a1a43ef8072c99256c4cbb3:65001`
- `decisions:bdf836b5a98e4247a47cce1352fae837:65001`

One read transaction establishes prior presence, current money, monthly balance
and claim state. Two new conformance blocks are capped at 490000000 each; six
paid game runs at 1000000000 each. Require current `L + 6980000000 <= 7000000000`,
the existing USD50 monthly authority and at least USD12 available. The observed
complete worst case was 6985162800 nanoUSD, with 14837200 margin. The three native
runs emit no paid requests. No reservation is released, settled to zero or
copied into another authority by this contract.

## Global single use before inference

Preserve the consumed `records(m5_recovery_v2,single_use)` grant. Its presence
still closes legacy/V1/V2; the new profile cannot fall back to those policies.
V3 requires that row to exist and its new global
`records(m5_openai_none_v3,single_use)` row to be absent. Any existing new row,
including malformed data, blocks every policy regardless of namespace/source.

Preflight reads only. Execution holds the canonical kernel lease and uses
`BEGIN IMMEDIATE`/FULL synchronization to revalidate the full current envelope,
claims, approved input hashes and frozen functional reference, then commits the
new row before the first SDK boundary. It binds policy/profile, namespace,
source/input hashes, reference hash, prior runs and current L. Error or process
death after commit retains the row; there is no automatic reset or retry.

Each new provider receives at most one complete qualification block. Both must
pass the declared long-response route/usage/action contract before games. Only
reconciled short-deadline/causal-backoff negatives may proceed under the admitted
performance policy, within all caps. Preserve failure outcomes, unknown charges
and `financial_final:false`; no game result or winner follows from a probe.

## Offline validation scope

Tests use temporary SQLite ledgers, controlled filesystem/image boundaries and
fake SDK responses. They exercise all ten missing/wrong associations, extra
closed-run rows, money types and the exact USD7/+1 boundary; functional drift,
duplicate JSON, reference-manifest tampering, profile omission and path escape;
WAL snapshot coherence, concurrent claims, preflight races, failure and real
process exit after commit. The fake SDK records explicit OpenAI none, Gemini
omission, cap256 and the scored profile passed to the campaign boundary.
These checks do not qualify a live account, gateway or paid campaign.
