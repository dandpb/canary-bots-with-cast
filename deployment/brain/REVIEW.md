# Independent reviews

Candidate reviewed: `6e9809f`, against `56fce151a10cc141d3a74800c3aec3a2dbf4e846`. Two independent read-only reviewers evaluated the documented standards and [issue #1](https://github.com/dandpb/canary-bots-with-cast/issues/1). Findings below refer to that candidate; the remediation notes describe subsequent changes.

## Standards

No unequivocal documented-standard breaches found. CONTRIBUTING requires KV persistence in the game integration; worker SQLite is separate private accounting/learning state, with no game database access or MySQL schema additions. It is not automatically a forbidden game persistence change. Tool-enforced formatting was excluded.

Three heuristic findings:

1. Possible duplicated code: hold completion existed in both `tickBrain` and `brainPartyMove`, with different comparison operators. Regroup movement was also repeated.
2. Possible primitive obsession: native action strings and numbered supply phases make transitions less explicit.
3. Possible primitive obsession: persisted Python plans use dictionaries for remaining steps, failures and phases instead of a validated plan type.

Remediation: hold completion is centralized in `tickBrain`; supply phases have names. Wire action strings and the bounded persisted plan representation remain deliberate small-module tradeoffs; limits are enforced before billable replanning. Extracting a typed plan record is a future maintainability improvement, not a release correctness exception.

Standards: zero confirmed hard breaches; three heuristic findings in the reviewed candidate.

## Spec

Six findings, with originating requirements:

1. “Disabling the feature releases ownership cleanly.” Per-bot disable removed roster membership while `brainOwns` could retain ownership through another pilot's heartbeat.
2. “Preserve attack, healing, and self-defense when holding position.” Combat chasing could run before the hold adapter and skip it entirely.
3. “Resolve the real human leader server-side.” Observations used the current party leader, while movement could retain the former leader's cached creature ID.
4. “Limit tool rounds, plan length, and replanning attempts.” Paid malformed/stale replans could leave a plan ready and trigger another request on each observation.
5. “Normalize progress and efficiency for level, role, party, and requested objective.” Reward ignored recorded yield, consumables and cohesion, using a fixed efficiency default.
6. “Track recent hunts, destinations, activities, and conversation patterns per bot.” Variety history covered hunt identifiers but lacked timed activity controls and explicit conversational variety guidance.

Remediation: ownership checks roster membership; holds clear walking and suppress chasing while keeping combat/healing; controlled movement refreshes the actual human leader; each replan consumes a durable attempt before calling the provider and cannot remain ready after failure. A regression test covers malformed paid output across eight later observations. Reward now uses per-level/party yield, supplies, elapsed time and cohesion, with survival weighted above yield. Hunt repeat penalties now include cooldowns; autonomous activity repetition has a cooldown, holds require a human request, and bounded conversation history guides varied phrasing. Explicit human orders bypass exploration/cooldowns.

No material unrequested scope was identified. Live validation and human usefulness remain separate from static correctness.

Spec: six findings in the reviewed candidate; the worst control/lifecycle defects were disabled ownership, stale leadership and unbounded paid replanning, addressed before promotion.

## Follow-up lifecycle review

The independent spec reviewer rechecked the hold fix and subsequent game-test changes. Additional findings were a resupply floor-hop surviving cancellation, and duplicate supply-bag seeding after backpack preservation. Closing a resupply goal now clears its planner and floor-change state. Retained pilot backpacks skip destructive replacement and fresh supply-bag seeding. Queued heartbeats are consumed before lease evaluation, terminal acknowledgements remain queryable after disable/unavailability, and native party rendezvous completes before model objective ownership.

The Lua reload fixture covers replacement of stale Player userdata and retention of unmatched references for orphan recovery. It failed before the reference-merge fix and passes under Lua and LuaJIT afterward. Game validation also found that authored NPC stands can lie behind counters; the companion approaches any reachable tile in the live NPC interaction range instead of requiring the inaccessible stand.

The long-game fixture exposed retained dead/offline human Player references. Canonical online-map identity checks now guard observation authority and native fallback selection. Human-follow parties with no online humans drain before proximity gating; native autonomous parties are excluded with `partyHuntId == 0`. The independent reviewer caught and verified that exclusion. Fallback leadership now transfers to the selected real online human. A final native test verified worker lease expiry/restart, leadership transfer after logout, and all three companions leaving PARTY with no owned objectives after the last human left.


## Autonomous explorer follow-up

Reviewed delta `dcebded..5bc9d4f` on independent Standards and Spec axes.

Standards: two integration findings, zero separate heuristic findings. The safety
pause returned before druid party healing, and the solo retreat scanner could
continue chasing monsters. Both were corrected: native role healing/attacks run
before movement is stopped; retreat clears pursuit and bypasses acquisition.

Spec: four findings. Besides those two, the solo scanner lacked the brain hunt's
script context and disabled explorers could remain exempt from hibernation.
The scanner now temporarily projects the selected script and restores ambient
fields; both hibernation exemption and automatic wake require current ownership
(roster membership, active mode and a fresh worker heartbeat). The reviewers
rechecked the corrections and identified the wake condition in a follow-up;
that condition was corrected before deployment.

The reload regression now covers registered bots between Player instances,
inactive bots, stale asynchronous registry rows, scheduler OFF preservation and a
transient materialization failure. The live projector was also tested with an
actual critically injured human: the old implementation offered a hunt, while
the corrected implementation withheld it and restored eligibility for a healthy,
assembled party of five humans and three bots.
