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
| Hybrid without learning | 0.4702 | 0.4652–0.4752 |
| Hybrid with learning | 0.7691 | 0.7610–0.7773 |

All seeds visited all five hunts. Survival is fixed by this safe fixture; its observed value of 1.0 and approximate zero-failure upper bound of 0.0015 do **not** measure live monster survival. This validates preference updating and variety, not usefulness or monotonically improving skill. Learned selection remains a separate promotion flag, disabled by default.

## Isolated server and release checks

Use a separate game database, game ports bound to loopback, three existing native bot characters and five normal protocol clients. Account credentials belong in a protected local file. Test setup may position fixtures administratively; model-requested actions must use ordinary gameplay adapters.

Observed on the isolated server:

- Five normal protocol clients connected; all five humans and three native companions shared one party (eight members). The low-level pilots used copied levels 8/13/11 and ordinary equipment; funds and initial positions were test fixtures only.
- Shadow proposals left goals unchanged. An active hold was acknowledged once and completed after thirty seconds. A third-party message received a conversational response without acquiring objective authority.
- Actual human leadership transfer invalidated old authority. A leader disconnect, worker restart and native library replacement were exercised. The worker heartbeat remains available when pilots hibernate.
- Normal NPC purchases and return completed for all three low-level pilots: knight 66.570 s, druid 66.181 s, paladin 85.758 s (final approach/return adapters), each gaining 38 compatible potions. Additional attempts failed on navigation or interruption; these failures are retained and are not counted as successes.
- Luna handled live private messages and supplied strict proposals through Responses. Live Decisions samples included 239, 486 and 573 ms. Real API costs share the production ledger.
- Reload exposed an inherited backpack reset and stale Lua player references. Library replacement now retains existing inventory, and a Lua/LuaJIT regression fixture verifies cache replacement for subsequent hibernation. Native rendezvous retains control until a newly invited companion reaches PARTY state. Approach walks target the live NPC interaction range, and return walks use the native NPC planner, including doors. Both report route failures. Retained pilot backpacks also skip fresh bag seeding on native activation.

The three pilots retained exactly 40 potions each through the final library replacement, including pilots that subsequently hibernated and woke. All three also retained those 40 potions through a full isolated-server stop/start. The Lua fixture also preserves unmatched references needed for orphan recovery. A replacement during the 997-bot production run retained 996 registrations; an inactive bot outside the live/pool enumeration remains a legacy reload limitation. A normal startup restores the full configured population. Prefer a normal restart when exact full-population restoration is required. The long hunt fixture travelled the authored route and produced real wolf combat/XP, including floor changes. It did **not** pass party-survival acceptance: passive headless humans failed to follow a floor transition, two died to wolves and the others were eventually idle-kicked. This is not evidence of safe AFK play or improved survival. The test also exposed retained dead/offline leader references; the controller now verifies identity in the actual online player map and drains human-follow parties without living online humans before proximity gating. Autonomous native bot-led hunts are excluded from this cleanup. The subsequent client fixture sends ordinary turns as well as keepalives, avoiding idle-kick confusion. Learned selection stays disabled pending real human playtests. Do not interpret synthetic replay results as those live checks.

## Human playtest rubric

Play at least three sessions with the same party and suitable equipment. Give one clear objective, one ambiguous request and one multi-step order. Repeat a hunt explicitly once, then request a different suitable hunt. Rate whether the bot understood the request, kept the party safe, reported failures honestly, chose useful alternatives and spoke without repetitive templates. Record deaths, supply costs, XP, API costs and interruptions. Promote learned selection only after live survival does not regress against the ordinary controller; otherwise roll back the policy checkpoint. More destination variety alone is insufficient evidence.

## Final deployment evidence

[evaluation-live.json](evaluation-live.json) records the redacted final measurements. The final worker-loss test released the goal in 4.325 seconds, restarted successfully, transferred leadership to the remaining online human and left all three companions in IDLE with no owned goals after all humans logged out. No retained human-follow party remained.

The final production startup restored **997/997 active bots**, with 997 online flags and all three approved controller pilots configured active. Their learned-selection flag remains false. Test workers/clients and the isolated game were stopped. The original deployment's 50-bot batching and 35-second pause were restored exactly after a one-time faster restoration.

A post-startup sample measured the game at 34.75% of one CPU core and 1.762 GiB RAM, the native ARM64 worker at approximately 40.7 MB, and roughly 7 GiB host memory available. The idle bridge's latest 256-sample p95 was 713.885 microseconds; these are a deployment sample, not combat-tail or full-load guarantees. The website client returned HTTP 200, and native @cast login returned a valid 255-entry protocol list.

Settled integration/probe usage totalled USD 0.041065075, with USD 0.0028885 in conservative unresolved reservations, against the shared USD 50 application cap. Human party-survival/usefulness acceptance remains open; the passive-client hunt above must not be counted as a successful survival trial.
