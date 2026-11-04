# Optional intelligent party companions

Implements [issue #1](https://github.com/dandpb/canary-bots-with-cast/issues/1) for one to three explicitly selected native bots. The feature is disabled when `data/bot/brain.json` is absent. Other bots retain their existing engine.

The C++ engine owns gameplay and projects live observations. A native Python worker calls **GPT-6 Luna only**: Decisions selects an offered action; Responses interprets Portuguese requests and proposes objectives. Neither API receives administrative commands or database credentials. Movement, attacks, cooldowns and emergency healing remain local.

## Playing

Invite a selected companion into your normal party, using the existing `/party` interface. Speak privately to its character, speak nearby, or use `/brain <request>` (also works when typed in a party channel). Examples:

- `/brain fique aqui por um momento`
- `/brain vamos comprar poções antes da próxima hunt`
- `/brain planeje uma hunt diferente, adequada à nossa party`
- `/brain siga comigo`

The actual human party leader sets objectives. Everyone else can converse and suggest. An optional autonomous explorer accepts objectives from any real player when outside a human party; see below. Leadership transfer, logout, death, floor changes, lost candidates and expired actions are checked again by the server. Raw party-channel chat is not intercepted by the hot-loadable library; use `/brain` for that channel.

Replies describe proposals. Completion is recorded only after a matching server outcome. Long hunts use authored routes; the human leader must follow the guide. The guide waits when separated by more than six tiles. Resupply buys ordinary health/mana potions through the NPC callback, verifies increased inventory and walks back. An unavailable route, shop, funds or capacity can cause a truthful failure.

## Architecture and limits

```text
game dispatcher → bounded observation → private Unix datagram socket → ARM64 worker
game validator ← versioned intent     ← offered choice / strict function call
game outcome   → durable episode      → reward / contextual preferences
```

- Protocol version 1; one to three pilots; 32 candidates, 12 visible monsters, eight messages per bot.
- Snapshots publish at most four times per second. Publication does not imply a model call.
- At most one Decisions request per bot and one Responses request globally. Threat/action changes trigger decisions; unchanged states have a sixty-second interval. Useful ongoing objectives suppress ambient replacement.
- Local bridge reads drain at most twelve datagrams per tick, each at most 32 KiB. The server never waits for the network, SQLite or a provider.
- Tactical answers retain the original server deadline. Target preferences last at most one second. Native combat remains available when the answer arrives too late.
- A five-second worker lease releases objective ownership on failure. Invited companions finish the native rendezvous before acquiring model objective ownership. Stable action identifiers support bounded retransmission and outcome queries; they do not restart an acknowledged objective.
- Responses uses `low` effort for routine requests; explicit planning/strategy requests may use `max`, with a ten-minute per-bot cooldown, 4,096 output-token allowance and 45-second request deadline. Planning cannot occupy Decisions slots.
- Multi-step requests have at most three objective steps and stop after two failures. Each step needs a terminal server result before replanning against fresh eligible candidates. One correlated `function_call_output` reflection may follow a human-requested step.
- Learning is a contextual bandit, **not model-weight training**. Context includes level band, vocation, party size, floor and region. Counts, recency-weighted rewards, recent choices and checkpoints persist. Exploration defaults to 15%, configurable from 5% to 50%, over eligible hunts only. Three identical consecutive choices are the limit when alternatives exist. Explicit leader orders bypass exploration.
- Policy updates use only validated terminal outcomes. Target choices, idle holds, cancellations, provider outages and hibernation cannot earn hunt rewards. Factual episodes and fallible model reflections are labelled separately.
- `learning: false` records evidence without letting learned preferences change selection for ordinary companions. Keep this setting until their pilot acceptance checks pass. The explicitly configured autonomous explorer has its own always-enabled learning policy.

### Storage decision

The worker uses its **own private SQLite file**, with schema version 1, WAL and short transactions. It creates no game MySQL tables and has no game database credentials. This keeps its accounting/experiments outside Canary's KV and character persistence. Atomic episode closure and policy updates prevent duplicate learning after restart. Policy rollback/forgetting cannot remove the spending ledger or change inventory. Back up the worker state while stopped, or use SQLite's backup API; copying only a live WAL database file is insufficient.

The optional `budget_file` shares one accounting database across isolated evaluation workers and production, while their `state_file` values remain distinct. All real-model tools must use that shared ledger.

## Installation

Build the `bot_engine` target with the repository's normal CMake/vcpkg toolchain. The library architecture and dependency ABI must match the running **game binary**, even when the host is ARM64 and that binary runs under amd64 emulation. The worker runs natively on the host. This change does not alter `IBotEngine` or the shared `BotState` layout.

```sh
cmake --build build --target bot_engine
python3 -m venv /opt/canary-brain/venv
/opt/canary-brain/venv/bin/pip install -r deployment/brain/requirements.lock
/opt/canary-brain/venv/bin/pip install --no-deps ./deployment/brain
```

Use `server.example.json`, `worker.example.json` and `canary-brain.service` as templates. Replace the sample GUIDs with existing bot character GUIDs; configurations must select the same bots and mode. Install the Lua `/brain` action and the updated `bot_system.lua` reload helper with the ordinary scripts deployment. Existing inventory is retained across library replacement. Configured pilots also retain their backpacks during ordinary activation, including purchases and loot, without seeding duplicate supply bags; the rest of the population keeps its original loadout rules.

Run game and worker under the same Unix identity. A root game process can also share its socket with the owner of the private runtime directory. Create the runtime/state directories with mode `0700`, and the credential file with `0600`; use a protected file containing `OPENAI_API_KEY=...`. Configure only its path. The key is never passed to the game, clients, prompts or logs.

For Docker, bind the socket directory at the **same absolute path** inside and outside the container: Unix sender addresses include the bound path. Example:

```yaml
volumes:
  - /run/canary-brain:/run/canary-brain
  - /etc/canary-brain/server.json:/canary/data/bot/brain.json:ro
```

By default the worker has no TCP listener. The optional operator console binds
to loopback; Docker deployments may bind inside the container with a
loopback-only published port. No Internet inbound port is required. Existing
client and cast ports are independent.

## Live supervision and conversation

The WSL deployment exposes the local console at **http://127.0.0.1:8091/**.
It monitors the autonomous explorer and controls it through the existing
server-offered actions. Installing or updating the console requires replacing
only the Python worker; the game process and casts can remain connected.
After installation, advice, route exclusions, pause/resume and recovery take
effect without rebuilding or restarting either process.

- **Conversar** answers questions using recent state, confirmed outcomes and
  conversation history. It cannot change the objective.
- **Orientar e agir** can propose an eligible objective. A changed world,
  objective generation, operator intervention or unavailable candidate prevents
  an old reply from issuing an order. The timeline reports native acceptance
  and completion separately from the model's words.
- **Guardar orientação** stores labelled operator advice in the worker's
  SQLite state, includes it in future decisions/conversation/strategy, and
  allows removal. It is contextual memory, not model-weight training or a
  fabricated reward. Native terminal results remain the only policy rewards.
- **Evitar rota atual** excludes the active hunt for 30 minutes. It affects
  future selection; use **Recuperar rota** to leave the current task. Exclusions
  expire automatically and may be removed early with **Liberar**.
- **Pausar** sends a normal hold and renews it while paused. Native combat and
  emergency healing stay available. **Retomar** selects fresh eligible work.
- **Recuperar rota** cancels the blocked objective via a normal hold, waits for
  native acknowledgement and a new observation, then chooses another allowed
  hunt, resupply or retreat. The previous hunt is avoided temporarily. There
  are no teleports, Lua snippets, arbitrary coordinates or administrative
  commands in this interface.
- Automatic recovery requires five minutes without actual movement, XP or new
  defeats during a task that requires progress. It does not interrupt nearby
  combat or a character below 80% HP blindly. It waits at least ten minutes
  between recoveries and attempts at most two per hour. A missing acknowledgement
  stops recovery and leaves an explicit failure for operator review.
  A hunt that the native server fails after five minutes with no XP or defeats
  is also excluded temporarily, so the next decision does not immediately
  retry it. This is a confirmed unsuccessful hunt, not proof of a movement stall.

Controls require a live autonomous bot outside a human party, active mode and
an observation no older than three seconds. Human party authority is unchanged.
The chart shows **live Player XP**, not necessarily the latest saved database
row. Objective defeat counters reset between tasks. The existing technical
monitor and native `brain status` still expose the route/waypoint diagnostics;
the console displays only telemetry available through the worker protocol.

The optional worker configuration is `operator_port: 8091` and
`operator_host: "127.0.0.1"`. WSL uses `operator_host: "0.0.0.0"` inside the
container with Compose publishing **127.0.0.1:8091:8091**. Preserve that host-side
binding. The console checks Host, Origin and a per-process same-origin request
token, has no CORS permission, and exposes no credentials. The worker still
has no game database credentials.

Automation clients may GET `/api/state`, then POST JSON to `/api/command` with
the returned `token` in `X-Operator-Token` and the matching local `Origin`.
Commands contain `bot`, `operation`, and only the operation's inputs:
`chat` (`text`, `act`), `note` (`text`), `forget_note` (`id`), `automatic`
(`enabled`), `allow_route` (`candidate`), or `pause`, `resume`, `recover`,
`retreat`, `avoid`. This console's token is not an OpenAI credential.

This mechanism can recover objectives and change learned preferences while
running. It cannot repair a defect in the native pathfinding implementation
or edit an authored route; those still need their normal code/data workflow.

Install and start the service after editing its user and paths:

```sh
sudo install -m 0644 deployment/brain/canary-brain.service /etc/systemd/system/canary-brain.service
sudo systemctl daemon-reload
sudo systemctl enable --now canary-brain
```

Start with both modes `shadow`, inspect proposed episodes, enable one pilot, then expand to three. Changing the server configuration requires the authorized operator command `/cavebot _global brain reload`. Restart the worker after changing its configuration. Do not use the unrelated general Lua `/reload scripts` operation for library deployment.

The operator-only `brain refresh_helpers` command refreshes the hardcoded bot helper file while preserving live Lua tables, strong Player references and runtime settings. It refuses to run during a bot reload. A normal native library reload snapshots registered bots, including those between Player instances, pauses population scheduling while materializing them and restores the previous scheduler state. Explicit `reload debug off` also repairs missing canonical registrations. A reported incomplete restoration requires operator investigation.

## Accounting and operations

The application cap is at most **USD 50 per calendar month in America/Sao_Paulo**. Integer nanodollars avoid rounding drift. Every billable attempt first reserves a conservative upper bound; successful responses settle returned input/cache/output usage. Reasoning is included in Responses output usage. Unknown charges retain reservations across restarts and month boundaries. There are no automatic SDK retries or model fallbacks. Provider faults back off for up to sixty seconds.

The cap covers this integration's ledger, not other applications using the same project/key. Configure an independent project limit in OpenAI if a project-wide limit is needed. Documented standard rates are encoded in `provider.py`; recheck them before changing model/pricing. Conservative retained reservations can require operator reconciliation against provider usage.

```sh
canary-brain status --state /var/lib/canary-brain/state.sqlite3
canary-brain inspect --state /var/lib/canary-brain/state.sqlite3
canary-brain checkpoint --state /var/lib/canary-brain/state.sqlite3 --name before-promotion
canary-brain rollback --state /var/lib/canary-brain/state.sqlite3 --name before-promotion
canary-brain forget --state /var/lib/canary-brain/state.sqlite3 --kind memory --key BOT_GUID:PLAYER_GUID
```

When `budget_file` differs, run `status` against it for financial/request telemetry and against `state_file` for gameplay/learning telemetry. `record-cost` seeds historical probe expenditure, with a unique ID, month and integer `--nanousd`; it refuses duplicate reservations.

Authorized in-game operator controls:

```text
/cavebot _global brain status
/cavebot _global brain disable
/cavebot "Bot Name" brain disable
/cavebot _global brain reload
```

Disable releases owned goals and hunt reservations while retaining native gameplay. Stop the worker for an immediate API-spending stop; native ownership expires within five seconds. To roll back the library, disable first, preserve a copy of the old library, replace by an atomic file rename and use the normal bot-engine hot reload. Never overwrite the bytes of a library that is currently memory-mapped. Docker mounts of individual files retain their inode: recreate that container to pick up an atomic replacement.

## Verification

```sh
python3 -m venv .venv
.venv/bin/pip install -r deployment/brain/requirements-dev.lock
.venv/bin/pip install --no-deps -e deployment/brain
.venv/bin/mypy deployment/brain/src
.venv/bin/ruff check deployment/brain
.venv/bin/python -m pytest deployment/brain
g++ -std=c++20 -Isrc tests/unit/players/bot_brain_protocol_test.cpp -lgtest_main -lgtest -pthread -o /tmp/brain-protocol-test
/tmp/brain-protocol-test
lua tools/bot_brain/test_reload.lua
luajit tools/bot_brain/test_reload.lua
.venv/bin/python deployment/brain/tools/evaluate.py --output /tmp/brain-evaluation.json
```

`provider: "fake"` is an explicit offline fixture; it requires no key, issues no billable request and is never selected automatically. The Unix datagram integration test drives the real worker process with this fixture. Native unit tests also join the existing `canary_ut` target.

Opt-in real probes use the same monthly ledger and do not send game actions:

```sh
.venv/bin/python deployment/brain/tools/probe.py --live \
  --credential /etc/canary-brain/openai.env \
  --state /var/lib/canary-brain/budget.sqlite3 \
  --output /var/lib/canary-brain/probe.json --samples 10 --max-effort --tool-result
```

See [EVALUATION.md](EVALUATION.md) for measured evidence, limitations and the human playtest rubric.

Official references: [Decisions guide](https://developers.openai.com/api/docs/guides/decisions), [Decisions API](https://developers.openai.com/api/reference/resources/decisions/methods/create), [function calling](https://developers.openai.com/api/docs/guides/function-calling), [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna).


### Autonomous explorer

Set `autonomous_bot` in the **server** configuration to one GUID already in `bots`
(maximum three pilots total). Omit it or use `0` to retain party-only behavior.
This one bot stays awake, executes the same bounded hunt/shop adapters without a
party, and uses its persistent contextual policy even if the worker's global
`learning` gate is false. Other pilots retain that gate. This is experience-based
selection and memory, not online model-weight training.

Outside a party any real player can send `/brain <objective>` to the explorer.
Within a party the human leader controls goals; other players can converse and
suggest. Messages are bounded and rate limited. Newer authorized requests supersede
older unfinished responses. The native action catalog, level, stock, leases and
health checks constrain every proposal.

GPT-6 Luna Responses provides dialogue and a strategy hypothesis at most once per
ten minutes while idle; Decisions chooses from current safe actions. Verified
outcomes update the persistent policy; exploration and repetition penalties apply
to eligible hunts. The shared USD 50 monthly ledger covers both APIs and tests.
No available alternative means the bot may repeat the only suitable hunt; it never
unlocks an unsafe hunt just to create variety. Native healing/combat continues
without waiting for an API. Worker failure releases its goals to native AI.

The explorer leaves a native bot-only party when model ownership resumes, and
ordinary native recruitment excludes it while its model configuration is active.
Human parties retain normal invitation and leader authority. Idle explorers prefer
available work over an empty continuation; interrupted objectives can be retried
after reload without being mistaken for completed activities. When no hunt or
shop is available on the current floor, an idle explorer returns to town by the
normal planner; a healthy bot already near the temple cannot loop that return.
An ongoing return is allowed to finish without repeated automatic orders resetting
its planner. Navigation can still fail and must report that outcome. Native library
reactivation retains the engine's existing random home-city spawn behavior.

Native bots deliberately receive no experience or level progression in this
server. Hunt learning therefore also counts confirmed monster deaths: an acquired
target is retained before the first attack so one-hit kills are observable.
Solo hunts evaluate a five-minute window; party hunts use fifteen minutes.
No confirmed combat progress is a failed hunt, rather than a positive reward for
walking. Stock increases are verified before rewarding a purchase. NPC approaches
use the actual live NPC's reachable interaction range, including shop counters.

Party hunt offerings require online members with at least 60% HP, within six tiles
on the same floor. The movement guard also runs before monster chasing; it pauses
the route while healing and existing attacks continue. Humans must still play
actively, especially through stairs. This does not guarantee an AFK player's survival.
