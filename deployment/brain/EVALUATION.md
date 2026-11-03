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

The three pilots retained exactly 40 potions each through library replacement, including pilots that subsequently hibernated and woke. All three also retained those 40 potions through a full isolated-server stop/start. An initial replacement during the 997-bot production run retained 996 registrations. The autonomous follow-up below fixes that limitation and verifies normal reload at 997/997. The long hunt fixture travelled the authored route and produced real wolf combat, including floor changes. Native bots deliberately receive no XP; experience animations were not evidence of actual XP gain. The fixture did **not** pass party-survival acceptance: passive headless humans failed to follow a floor transition, two died to wolves and the others were eventually idle-kicked. This is not evidence of safe AFK play or improved survival. Canonical online-map identity checks and human-follow party cleanup corrected retained dead/offline leader references. Native autonomous parties remain excluded from the general cleanup. The subsequent client fixture sends ordinary turns as well as keepalives, avoiding idle-kick confusion. Ordinary companions' learned selection stays disabled pending human playtests; the user explicitly enabled learning for the special explorer.

## Human playtest rubric

Play at least three sessions with the same party and suitable equipment. Give one clear objective, one ambiguous request and one multi-step order. Repeat a hunt explicitly once, then request a different suitable hunt. Rate whether the bot understood the request, kept the party safe, reported failures honestly, chose useful alternatives and spoke without repetitive templates. Record deaths, supply costs, XP, API costs and interruptions. Promote learned selection only after live survival does not regress against the ordinary controller; otherwise roll back the policy checkpoint. More destination variety alone is insufficient evidence.

## Initial deployment evidence

[evaluation-live.json](evaluation-live.json) records the redacted final measurements. The final worker-loss test released the goal in 4.325 seconds, restarted successfully, transferred leadership to the remaining online human and left all three companions in IDLE with no owned goals after all humans logged out. No retained human-follow party remained.

The initial production startup restored **997/997 active bots**, with 997 online flags and three controller pilots configured active with learned selection disabled. Test workers/clients and the isolated game were stopped. The original deployment's 50-bot batching and 35-second pause were restored exactly after a one-time faster restoration. The follow-up below records the subsequent explorer deployment.

A post-startup sample measured the game at 34.75% of one CPU core and 1.762 GiB RAM, the native ARM64 worker at approximately 40.7 MB, and roughly 7 GiB host memory available. The idle bridge's latest 256-sample p95 was 713.885 microseconds; these are a deployment sample, not combat-tail or full-load guarantees. The website client returned HTTP 200, and native @cast login returned a valid 255-entry protocol list.

Settled integration/probe usage totalled USD 0.041065075, with USD 0.0028885 in conservative unresolved reservations, against the shared USD 50 application cap. Human party-survival/usefulness acceptance remains open; the passive-client hunt above must not be counted as a successful survival trial.

## Autonomous explorer follow-up

The user requested one continuously learning solo explorer, accepting orders from **any real player outside a party**, and retaining human-leader authority within a party. Production now selects existing knight **Tarshaw Steelheart**, GUID 65045, level 90; the other two pilots remain 65004 and 65003. His original level, equipment and funds were retained. An operator placed him in Thais for initial setup; model actions use ordinary routes and purchases, never administrative teleports. The global learned-selection flag stays false for the other two companions; Tarshaw's persistent contextual policy is enabled independently. This updates preferences and memory, not model weights.

Automated release checks passed: **34 Python tests**, ruff, mypy across nine source files, three native protocol/policy tests, and both reload fixtures under Lua and LuaJIT. The amd64 library was cross-compiled for the actual game binary. New regressions cover the first worker lease before an intent, cancelled-goal retry, fixed-XP combat rewards, autonomous authority, safe idle choices and persistent variety. Lua regressions cover between-instance registrations, inactive rows, live strong references, scheduler OFF, bounded retry, canonical repair and helper refresh retaining runtime/configuration table identities.

Observed on the isolated real game:

- Five healthy human protocol clients and three native companions could form the eight-member party. At 20/245 HP, a human incorrectly allowed a hunt in the old projector; the corrected projector withheld it and restored eligibility after healing.
- A three-minute real-Luna party check kept all eight alive and paused guide movement when the leader fell seven tiles behind. It did not complete a hunt and does not resolve human-survival acceptance.
- A player outside the explorer's party issued a hold through Responses; the native goal was accepted within two seconds.
- A sixteen-minute solo soak had no human/cast proximity anchors. The explorer remained awake, moved along the authored route and retained full health.
- A real-Luna solo hunt completed after **300.005 seconds**, with **34 confirmed monster defeats**, no deaths, no danger, zero XP and reward **0.95** committed to the persistent policy. Additional completed windows recorded 29 defeats each. Only matching verified outcomes earned rewards.
- A separate explicitly simulated provider fixture exercised the real native combat adapter with two spawned wolves, one set to 1 HP (4%) through a temporary QA administrator. Both deaths were counted, including the one-hit kill. QA privileges and provider configuration were restored afterward. This is native accounting evidence, not a real-model reasoning test.

Observed on production:

- Tarshaw bought 38 ordinary compatible potions through the real NPC adapter, reaching **40 potions** in **28.091 seconds**. Earlier route failures remain recorded as failures.
- He selected a solo hunt through Luna and defeated monsters with no human leader. A hunt with no confirmed combat progress correctly failed; an interrupted hunt retained eight confirmed defeats without claiming completion.
- After the final library reload, a real-Luna solo hunt completed in **300.050 seconds**, with **34 confirmed defeats**, no deaths, peak measured health deficit 3% and reward **0.941** persisted. Tarshaw retained 40 potions and recovered to full health.
- Normal library reload passed at **997 active before and 997 active after**. A later targeted Lua helper refresh preserved the brain world, running hunt and 997/997 population without another library reload. Native bot-only recruitment can no longer capture the active explorer; recovery releases a stale bot-only party while preserving human parties.
- Main worker is enabled and active; isolated game, worker and clients are stopped. The web client still returns HTTP 200. Startup batching remains 50 with the original 35-second pause.

All real provider tests and production calls share the USD 50 monthly application cap. Follow-up accounting is timestamped in [evaluation-live.json](evaluation-live.json); costs continue to accrue during normal operation and unknown charges retain conservative reservations. Responses/Decisions remain fixed to GPT-6 Luna. No claim of improved human survival, safe AFK play or monotonically improving intelligence follows from these checks.

The final cycle check exposed empty continuation underground and repeated retreat orders resetting the native planner. Public regressions failed before the fixes and the full 34-test suite passed afterward. The model then walked from floor 8 to floor 7 and selected a new hunt without further operator movement. The last leg to the temple reported `return_route_unavailable`; this is **not** a successful full return. Existing native library reactivation randomizes home-city spawn positions, so restoring the original underground position was explicit operator fixture setup. Navigation failures and a catalog without suitable work remain observable limits.

A final active-bridge sample measured p95 **2.999781 ms** over the latest 256 ticks, above the initial 2 ms tuning target. Earlier busy samples reached about 6.3 ms. These are emulated-game samples, not full-load tail guarantees; performance tuning and real human usefulness remain follow-up acceptance work. The game still reported 997/997 active bots and the worker remained healthy.
