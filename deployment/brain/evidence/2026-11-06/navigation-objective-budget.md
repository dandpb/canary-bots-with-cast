# Floor-change budget belongs to an accepted navigation objective

An autonomous bot can exhaust its five-failure floor-change allowance. Native
activity reroll normally clears that allowance, but `doActivityReroll` returns
immediately while the brain owns the bot. The accepted-intent path previously
retained the allowance from the prior objective, so a later valid objective
could inherit the refusal even though it had not made its own attempts.

Only a newly accepted `hunt`, `resupply`, `retreat` or `follow` intent now clears
that bot's consecutive floor-change failures. The existing `plannerReplan`
discards its old leg/hop/queue and requests fresh door-search data. Duplicate
action IDs return their remembered outcomes before this point; validation
failures, `continue`, target preferences and `hold` do not reset the allowance.
Ongoing execution of the same objective does not revisit the admission reset.

The reset does not clear global portal quarantine, another bot's state or the
wide-search CPU cooldown. It does not renew a timeout or grant unlimited attempts
within the same objective. The ordinary `goTo` handoff also now returns false
when `startFloorChange` refuses to start, matching the scoped planner's refusal
contract.

## Regression

```sh
python3 tools/bot_brain/test_navigation_objective.py --include /path/to/include
```

The include directory must contain `nlohmann/json.hpp` from the configured
native dependencies. On the isolated native build image it is
`/opt/installed/x64-linux/include`; `CANARY_TEST_INCLUDE` is also supported.
No dependency headers are committed by this test.

Fifteen cases compile the real protocol validator, intent-admission path,
planner reset, floor-change start, ordinary handoff and wide-search helper.
The original code failed all four newly accepted navigation actions after an
inherited five-failure allowance, and failed the refused ordinary handoff.
Four mutation controls detect a removed reset, a reset moved before duplicate
checking, an incorrectly reset `hold`, and a false-success handoff.

The regression also verifies another bot's state and the global quarantine stay
intact, and that accepting an objective does not bypass a pending failed-wide
search cooldown. It uses a controlled game boundary; it does not replace native
build or live gameplay acceptance. The previously frozen H route proof remains
at source `2986713328ab68ade2ce3927a2f0b1de564815e8`, without this follow-up.
