# Stage 9 · Implementation readiness

All three fresh-context reviewers completed. The plans reviewer checked the
two guide designs and three experiment pilots. The codebase reviewer checked
native qualification, persistence, replay, B1 and paid admission code. The
operating clarity reviewer checked WSL, desktop, browser and replay procedures.
They used current local source and existing test cases. Their reviews were
read-only. The orchestrator separately ran the focused tests and setup checks.

## Operating and qualification paths

| ID | Priority | What needs to change before handoff |
| --- | --- | --- |
| R1 | Blocker | Fresh WSL setup omits an input required by fixed Compose mounts. Move the site-specific Lua template bind to an override or prepare and verify it, plus every other active mount. `deployment/brain/SETUP.pt-BR.md:49`, `deployment/wsl/compose.yaml:132`, `deployment/wsl/game-entrypoint.py:53`. |
| R2 | Blocker | The setup guide's whole-stack stop conflicts with the game save and recovery order. Use the save-aware WSL runbook and include the optional Gemini Decisions profile when stopping associated services. `deployment/brain/SETUP.pt-BR.md:632`, `deployment/wsl/README.md:316`, `src/game/game.cpp:8635`. |
| R3 | Blocker | A 10-second documented smoke invokes a supervisor requiring at least 1,800 seconds, while the result gate expects the requested short window. An event-payload unit test does not exercise this integration. `tests/fixture/M5_CURRENT_QA.md:35`, `tests/fixture/m5_current_qualification.py:722`, `deployment/brain/src/canary_brain/benchmark.py:808`, `deployment/brain/src/canary_brain/benchmark_stops.py:160`, `tests/fixture/test_m5_qualification_gates.py:329`. |
| R4 | Blocker | Both M5 drivers advertise separate native and app revisions, but the worker receives the app SHA as its native pin. Preserve admission checks and pass the intended verified SHA or document the same-revision requirement. `tests/fixture/m5_current_qualification.py:343,733`, `tests/fixture/m5_current_lowstock.py:139,266`, `deployment/brain/src/canary_brain/benchmark.py:809`, `deployment/brain/src/canary_brain/runtime.py:60`. |
| R5 | Major | The replay runbook uses the old observed-start and tail-status description. Current supervision requires native admission, a matched terminal fence, and stored proof after close. The code tests cover missing admission, late fence, persisted payload and peer replacement. `deployment/brain/REPLAY.md:69,133`, `deployment/brain/src/canary_brain/supervised_native.py:237,303`, `deployment/brain/tests/test_supervised_admission.py:112,212,266,305`. |
| R6 | Blocker | The B1 SQL commands and generated ready-check command omit authentication required by the fresh database. Reuse container-side authentication used by Stage 1. `deployment/core-qa/B1_FIXTURE.md:194`, `deployment/core-qa/b1_fixture.py:758`, `deployment/core-qa/stage1_baseline.py:230`. |
| R7 | Major | The persistence witness has an opt-in adapter and controlled Lua/SQLite tests. The normal runner uses legacy save. A fresh owned run still needs the reviewed mounts, callback closure, embedded ARM64 LuaJIT proof and final evidence. The C8 description predates a later shutdown implementation. `tests/fixture/m5_qa.py:162,496`, `docs/design/fixture-persistence-witness.md:158,184,244`, `src/game/game.cpp:8625`. |
| R8 | Major | The abbreviated WSL rebuild omits the source identity that the native build requires. Link the existing clean-source recipe at the runnable command. `deployment/wsl/README.md:89,302`, `deployment/wsl/verify-build-source.py:12`. |
| R9 | Major | Changing only the route type in the recommended worker template leaves billable output, which Decisions rejects. The local configuration validator reproduced the failure. Publish a consistent route example without weakening the cap. `deployment/wsl/README.md:258`, `deployment/brain/worker-replay.example.json:18`, `deployment/brain/src/canary_brain/gateway.py:49`. |
| R10 | Major | The desktop asset and HTTP login settings need a profile and supported client. The browser adapter test uses a synthetic backend. Add a deployed browser test for headers, WASM, login and WSS. `deployment/client/README.md:11,31`, `deployment/wsl/README.md:59`, `deployment/browser/README.md:21`, `deployment/browser/test_php_adapter.py:14`. |
| R11 | Major | Visual capture variables and packaging tools exist. Base Core QA omits the capture mounts, variables and active Brain telemetry. Name the QA overlay and specify performance, liveness and evidence checks. `deployment/brain/REPLAY_VISUAL.pt-BR.md:17,47`, `deployment/core-qa/compose.yaml:33`, `deployment/core-qa/README.md:5`. |

The paid M5 wrapper implements preflight and source-bound admission before
execution. This source review did not establish a live ledger state, available
claim, provider qualification or authorization for a new campaign.

## Feature plans

| ID | Plan | Verdict and required proof |
| --- | --- | --- |
| R12 | Thais escort | Design is testable on paper. The seven floor-7 waypoints and the route lookup exist. The generic walker can queue several directions and execution can follow validation later. Choose a single movement owner and revalidate each step before execution. Define the party, reconnect, timeout and cleanup order, including pending invites and join failure. Add the fixture, stale-step and rollback tests. Verify the route on the loaded map. `design_draft.md:34,57`, `src/creatures/players/bot/bot_nav.cpp:498`, `src/creatures/creature.cpp:213`, `src/creatures/players/grouping/party.cpp:22,329`. |
| R13 | Read-only `/guia` | Proposed. Existing console tests support separation of questions and orders. They use the bot-centered transport, which lacks an authenticated solo request path. Bind requests and replies to the current character session. Specify the local lookup, freshness, action-free capability set, limits and outage behavior. Verify private delivery, membership changes, relog and rejected model actions. `deployment/brain/GUIA_DO_JOGADOR.md:21,49`, `deployment/brain/src/canary_brain/protocol.py:40,60`, `deployment/brain/tests/test_supervision.py:325`. |
| R14 | Hunt by play style | Synthetic fixtures and nearest-route control exist. A controlled pilot needs the chosen native or Brain baseline, common immutable eligible offers, seed and tie rules, a held-out set and explicit coverage and abstention scoring. `deployment/brain/EXPERIMENTOS_SYSTEM_ONE.pt-BR.md:74`, `deployment/brain/tools/jev_experiments.py:130`, `src/creatures/players/bot/bot_hunt.cpp:24`, `src/creatures/players/bot/bot_brain.cpp:378`. |
| R15 | Detective quest | Proposed. Author clue IDs and a deterministic relationship to hypotheses. Require one identified, discovered clue for advancement. Define the manual fallback and request-to-player phase binding. Test discordant answers, late replies, duplicates and undiscovered clues. `deployment/brain/EXPERIMENTOS_SYSTEM_ONE.pt-BR.md:75,78`. |
| R16 | Replay search | Replay time alignment, chapter navigation and synthetic clip curation exist. A question-search pilot needs a session manifest, common windows, action IDs, time tolerance, held-out labels and rules to distinguish missing coverage from a missing event. Any optional clip provider needs separate payload, cost and retention controls. `deployment/brain/EXPERIMENTOS_SYSTEM_ONE.pt-BR.md:76`, `deployment/brain/src/canary_brain/visual_replay.py:162`, `deployment/brain/tools/jev_experiments.py:211`. |
