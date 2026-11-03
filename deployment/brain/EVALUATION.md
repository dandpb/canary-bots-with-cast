# Companion controller validation

Evaluation date: 2026-11-03. Baseline: `56fce151a10cc141d3a74800c3aec3a2dbf4e846`. Game executable/library architecture: amd64 on an ARM64 host; worker: native ARM64/Python 3.12. Main deployment modifications to startup batching and ordinary party access are preserved outside this feature worktree.

## Automated boundaries

The automated suite covers versioned contracts, a native application-time validator, private Unix datagram transport through a real worker process, leader changes, superseded messages, bounded multi-step advancement, stable retransmission identities, duplicate outcome recovery, atomic policy updates, checkpoint rollback, concurrent budget reservations, month rollover, unknown charges, provider failures/refusals/invalid choices, and function-call correlation. API collaborators are simulated explicitly; live API probes are separate.

The production model is fixed to GPT-6 Luna in both providers. No fallback model or unrestricted administrative command is implemented.

## Real provider evidence

The initial planning probes cost USD 0.0001273 and are seeded in the shared ledger. Subsequent implementation probes used that ledger, including failed requests with retained conservative reservations.

- Five Decisions calls through the new provider initially measured 310–1,387 ms on a small synthetic observation. All returned offered candidates. A subsequent probe selected the expected resupply candidate in 570 ms.
- Responses produced strict resupply proposals with both `low` and `max` reasoning. The bounded `max` case completed in approximately 3,967 ms; `low` measurements included 3,025 and 5,260 ms.
- A real correlated `function_call_output` round accurately summarized an injected insufficient-funds failure, without claiming a purchase succeeded.
- A real SDK serialization incompatibility (`async_` versus wire alias) was found and corrected by copying only the public function-call fields into continuation input. The unsuccessful request's reservation remains accounted for.

These probes are synthetic contract/latency checks. They do not establish combat-tail latency or improved live play. The one-second target deadline can expire; the native engine remains responsible for immediate combat. Retest cold/warm realistic contexts before promoting additional tactical windows.

## Learning evaluation

[evaluation-synthetic.json](evaluation-synthetic.json) contains a reproducible held-out fixture: twenty seeds, one hundred evaluation episodes per seed, five server-eligible safe hunts. Training and evaluation noise use different random streams.

| Policy | Mean synthetic progress | 95% CI across seed means |
|---|---:|---:|
| Fixed fixture rules | 0.3007 | 0.2989–0.3026 |
| Hybrid without learning | 0.4702 | 0.4652–0.4751 |
| Hybrid with learning | 0.7844 | 0.7759–0.7930 |

All seeds visited all five hunts. Survival is fixed by this safe fixture; its observed value of 1.0 and approximate zero-failure upper bound of 0.0015 do **not** measure live monster survival. This validates preference updating and variety, not usefulness or monotonically improving skill. Learned selection remains a separate promotion flag, disabled by default.

## Isolated server and release checks

Use a separate game database, game ports bound to loopback, three existing native bot characters and five normal protocol clients. Account credentials belong in a protected local file. Test setup may position fixtures administratively; model-requested actions must use ordinary gameplay adapters.

Observed before final promotion: all five protocol clients connected; three native companions joined the human-led party; shadow proposals left goals unchanged; an active hold was acknowledged once and completed after thirty seconds; a third-party message received a conversational response without acquiring objective authority. The worker heartbeat is available even when all pilots hibernate.

Final acceptance also requires normal NPC purchase and return, a coordinated authored hunt, leadership transfer/disconnection, worker loss/restart, engine replacement, and resource comparison. Record measured results here as they complete. Do not interpret synthetic replay results as those live checks.

## Human playtest rubric

Play at least three sessions with the same party and suitable equipment. Give one clear objective, one ambiguous request and one multi-step order. Repeat a hunt explicitly once, then request a different suitable hunt. Rate whether the bot understood the request, kept the party safe, reported failures honestly, chose useful alternatives and spoke without repetitive templates. Record deaths, supply costs, XP, API costs and interruptions. Promote learned selection only after live survival does not regress against the ordinary controller; otherwise roll back the policy checkpoint. More destination variety alone is insufficient evidence.
