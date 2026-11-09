# Canary Brain Operator & Replay Dashboard (`dashboard`)

## Overview

Browser-side static frontend assets (`app.js`, `index.html`, `replay.js`, `replay.html`, `style.css`, `replay.css`) served by `canary_brain.operator_http` and `canary_brain.replay_cli` for live autonomous bot supervision, operator conversation/advice, route avoidance, and multi-run replay comparison.

## Interface

- `[app.js:refresh]` — Polls `GET /api/state` and invokes `render()` to synchronize live supervision UI state.
- `[app.js:render]` / `[app.js:renderChat]` / `[app.js:renderNotes]` / `[app.js:renderEvents]` / `[app.js:renderChart]` — Updates live supervision DOM elements (`#conversation`, `#notes`, `#routes`, `#events`, `#xp-line`) from `state.bots[0]` and `state.token`.
- `[app.js:command]` / `[app.js:action]` — Sends `POST /api/command` with `X-Operator-Token` header and operation payload (`pause`, `resume`, `recover`, `retreat`, `avoid`, `note`, `forget_note`, `allow_route`, `automatic`, `chat`).
- `[app.js:objectives]` / `[app.js:phases]` / `[app.js:number]` / `[app.js:notice]` / `[app.js:element]` / `[app.js:$]` — UI formatting and DOM helpers.
- `[index.html:#chat-form]` / `[index.html:#note-form]` / `[index.html:[data-command]]` / `[index.html:#automatic]` — Operator controls for chat/orders, guidance notes, route avoidance, pause/resume/recover/retreat, and automatic stall recovery.
- `[replay.js:api]` — Queries `window.REPLAY_ARCHIVE` (offline static bundle) or fetches `GET /api/<path>` (`replays`, `replay`, `replay/summary`, `replay/track`, `replay/timeline`, `replay/seek`).
- `[replay.js:refresh]` / `[replay.js:select]` / `[replay.js:renderChoices]` / `[replay.js:layout]` — Loads available replay runs, manages run selection, and populates `#arena` comparison cards from `[replay.html:#card]`.
- `[replay.js:draw]` / `[replay.js:drawMap]` / `[replay.js:drawChart]` / `[replay.js:inspect]` / `[replay.js:jump]` / `[replay.js:frame]` — Synchronizes time scrubber, draws 2D floor trajectory and XP curves on `<canvas>`, fetches seek/timeline events, and advances `requestAnimationFrame` playback.
- `[replay.js:state]` / `[replay.js:labels]` / `[replay.js:fmt]` / `[replay.js:clock]` / `[replay.js:offset]` / `[replay.js:timeFor]` / `[replay.js:nearest]` — Replay state, time-alignment math, and binary search helpers.

## Invariants

- `[app.js:command]` — Requires both `bot` and `token` to be present before issuing `POST /api/command`.
- `[app.js:render]` — Considers bot connected only when `bot.observation_age <= 3` seconds; disables `#automatic`, `#send`, and all `[data-command]` buttons when disconnected.
- `[app.js:render]` — Disables `[data-command=avoid]` when `!bot.candidate`, `[data-command=retreat]` when `'retreat'` is not in `bot.actions`, `[data-command=resume]` when `!bot.control.paused && bot.control.phase === 'idle' && bot.objective !== 'hold'`, and `[data-command=pause]` when `bot.control.paused`.
- `[app.js:renderChat]` — Deduplicates DOM updates by comparing `JSON.stringify(bot.chat)` against `lastChat` (and `lastNotes` in `[app.js:renderNotes]`, `lastEvents` in `[app.js:renderEvents]`).
- `[index.html:#message]` — Enforces `maxlength=1024` and `required` on chat message input; `[index.html:#note]` enforces `maxlength=1000` and `required` on guidance notes.
- `[replay.js:select]` — Enforces a maximum of 4 concurrently selected runs (`state.chosen.size >= 4`).
- `[replay.js:timeFor]` — Clamps run-relative playback time to `[0, run.meta.duration_ms]`.
- `[replay.js:drawMap]` / `[replay.js:drawChart]` — Breaks trajectory and XP curve polyline segments across recorded observation gaps (`r.summary.metrics.gap_times`) and filters map points to the current floor (`b.position[2]`).
- `[replay.js:inspect]` — Uses a monotonic request counter (`generation !== state.request`) to discard stale asynchronous seek/timeline responses and renders at most 40 timeline events.

## Side Effects

- `[app.js:refresh]` — Performs initial `fetch('/api/state', {cache: 'no-store'})` on load and schedules recurring polling every `2000` ms via `setInterval`.
- `[app.js:command]` — Sends HTTP `POST` requests to `/api/command` with `X-Operator-Token` and mutates server-side bot control, chat, notes, and route exclusions.
- `[app.js:render]` — Mutates DOM elements in `index.html` and registers event listeners on `[data-command]`, `#automatic`, `#chat-mode`, `#chat-form`, and `#note-form`.
- `[replay.js:api]` / `[replay.js:frame]` / `[replay.js:refresh]` — Issues HTTP `GET` requests to `/api/replay*` endpoints when `window.REPLAY_ARCHIVE` is unset, runs a `requestAnimationFrame` loop polling `inspect()` at most every `700` ms while playing, and populates `#runs` and `#arena`.

## Verification

- Run: `pytest`
