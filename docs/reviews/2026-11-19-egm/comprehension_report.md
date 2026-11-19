# Stage 6 · Comprehension test

English rendering of the completed reviewer result.

## What this proposes

The inventory brings together server documentation, deployment instructions,
design proposals and dated evidence. The Thais draft proposes a dedicated bot
that guides one player from the temple to the depot with `/party guia`, waits
when separated and resumes after reconnection. The `/guia` proposal describes
private, read-only advice available even when playing alone. The System One
experiments propose comparisons for hunt selection, clues and replay search.
The #72 documents describe supervised QA and a separate way to verify saved XP
and level.

## How the existing system works, per this document

Canary keeps the world, accounts, characters, combat, items, groups, market and
houses in the C++ server, with extra rules and content in Lua datapacks. Native
bots use Player characters for hunting, navigation, combat, trading,
hibernation and parties. Cast streams current sessions to viewers. Brain is an
optional Python worker for selected native bots, including a solo explorer.
The worker interprets requests and picks offered choices while the server owns
eligibility, movement, combat, completion and XP. Deployment covers Linux, WSL
with MyAAC, desktop and browser clients, isolated QA, structured replay and
visual replay.

## Findings

The reviewer could reconstruct the system and the proposals from the sampled
documents. No comprehension blocker was reported.

| Severity | Gap | Evidence |
| --- | --- | --- |
| Major | A new reader needs a map from feature to owning subsystem and an explanation of how shared Lua and the selected datapack fit together. | `README.md:490`, `src/README.md:3`, `data/README.md:3`, `data-canary/README.md:3`, `data-otservbr-global/README.md:3`, `src/creatures/players/README.md:3`, `src/game/README.md:3` |
| Major | Brain's player path says to recruit a selected pilot via the existing party interface. The QA guide states vocation-based `/party` will select other bots and directs players to find and invite the named pilot in the client. Identify how discovery and recruitment work in each profile. | `deployment/brain/README.md:13`, `README.md:310`, `deployment/core-qa/ROTEIRO.md:17` |
| Major | The reader sees protocol 13+, 1500, 15.x, 15.11 assets and 1100 layout across entry pages. Specify a compatible client build, protocol and assets for each path. | `README.md:188,252`, `deployment/client/README.md:11,47`, `deployment/browser/README.md:3,19`, `deployment/wsl/README.md:59` |
| Major | The early guide brief describes a dedicated dispatcher. The draft and engine README describe the serial game dispatcher. This affects the reader's mental model of who can access player state. Mark the earlier text as superseded and link the draft. | `concepts_brief.md:26`, `design_draft.md:28`, `src/creatures/players/bot/README.md:17` |
| Major | The Thais walk assumes a dedicated active bot near the temple. The chat guide assumes a level-8 druid with fixed mana and a known companion stock count. Each should name a QA profile and link its fixture, or say fixture preparation is pending. | `design_draft.md:36,57`, `deployment/brain/GUIA_DO_JOGADOR.md:35`, `deployment/core-qa/README.md:5,28`, `deployment/core-qa/ROTEIRO.md:7` |
| Major | Four experiment result links point outside the repository into a local scratch tree. A checkout reader gets the methodology and misses the run and revision behind the numbers. | `deployment/brain/EXPERIMENTOS_SYSTEM_ONE.pt-BR.md:7,16,80`, `deployment/brain/tools/README.md:43` |
| Nit | The admission page uses B, t0, D0 and O0 before linking to their definitions. The persistence witness assumes the reader knows a03 and C8. Link the schema and the historical identities at first use. | `docs/design/native-admission-stage.md:1,89`, `docs/design/native-supervised-harness-interface.md:76`, `docs/design/fixture-persistence-witness.md:1,47`, `docs/README.md:3` |
| Nit | The initial product brief has no forward links to the two proposals it led to. The walk draft already links the brief and the chat proposal. | `concepts_brief.md:12,54`, `design_draft.md:7`, `deployment/brain/GUIA_DO_JOGADOR.md:3` |

## Coverage

The reviewer read the 12 assigned entry documents, then the related game,
creature, player, account, item, map, Lua, bot engine, cast and datapack guides.
They checked the WSL, browser, desktop, Core QA, seed, Brain setup, replay,
native admission, supervised M5 and tools pages to see whether the texts
answered a new reader's questions. This stage used documentation only.
