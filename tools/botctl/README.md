# Bot Control CLI (`tools/botctl`)

## Overview
Provides `botctl.py`, a synchronous CLI wrapper that inserts `/cavebot` commands into the live server's `bot_commands` MySQL table, polls for completion, and exits with structured status codes (`OK`, `FAULT`, `NO-RESPONSE`, `ERROR`).

## Interface
- `Channel` (`[botctl.py:Channel]`): Database channel supporting `insert`, `poll`, `drop_unprocessed`, and `bot_names` via `mysql.connector` or fallback `tools/botperf/driver.py` (`BotCommandDriver`).
- `split_target(ch, text, bot)` (`[botctl.py:split_target]`): Parses `/cavebot` prefixes, quoted bot names, unquoted longest-prefix bot names from `players WHERE account_id = 65000`, or `_global`.
- `run_one(ch, bot, command, timeout, interval)` (`[botctl.py:run_one]`): Enqueues one row, polls until `processed == 1` or `--timeout`, and classifies faults using `FAULT_RE`.
- `main()` (`[botctl.py:main]`): CLI supporting single commands and `--bench N` latency benchmarking (`p50`/`p95`/`max`).

## Invariants
- Exit codes follow the fixed contract: `0` (`OK`), `2` (`FAULT`), `3` (`NO-RESPONSE`), `4` (`ERROR`) (`[botctl.py:EXIT_OK]`).
- Timed-out commands (`NO-RESPONSE`) call `drop_unprocessed` (`DELETE FROM bot_commands WHERE id = ... AND processed = 0`) so stale commands do not execute on a later server boot (`[botctl.py:Channel.drop_unprocessed]`, `[botctl.py:run_one]`).

## Side Effects
- Reads DB credentials from `.claude/secrets.local` (or `BOTPERF_SECRETS`) and inserts/deletes rows in `bot_commands` and reads `players` in the target database (`--db` / `BOTPERF_DB`, default `canary_1525_port`) (`[botctl.py:main]`).

## Verification
- Run `python tools/botctl/botctl.py --help` to verify CLI parsing; run against a live DB/server instance to exercise end-to-end command execution.
