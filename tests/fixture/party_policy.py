"""Synthetic eligible-catalog variety, explicitly separate from real completed hunts."""

import itertools
import json
import random
import tempfile
from collections import Counter
from pathlib import Path

from canary_brain.learning import Policy
from canary_brain.store import Store

rows = []
with tempfile.TemporaryDirectory(prefix="party-variety-") as tmp:
    for seed in range(20):
        for guid in (65001, 65003, 65004):
            policy = Policy(Store(Path(tmp) / f"{seed}-{guid}.db"), random.Random(seed))
            choices = []
            for _ in range(100):
                chosen = policy.choose(
                    guid,
                    "five-equivalent-eligible-hunts",
                    [f"hunt:{i}" for i in range(5)],
                    preferred="hunt:0",
                ).candidate_id
                choices.append(chosen)
                policy.learn(guid, "five-equivalent-eligible-hunts", chosen, 0.5)
            maximum = max(len(list(run)) for _, run in itertools.groupby(choices))
            assert len(set(choices)) >= 4 and maximum <= 3
            rows.append(
                {
                    "seed": seed,
                    "guid": guid,
                    "choices": choices,
                    "counts": dict(Counter(choices)),
                    "maximum_consecutive": maximum,
                }
            )
out = {
    "synthetic": True,
    "real_hunts_completed": 0,
    "seed_count": 20,
    "bots": 3,
    "episodes_per_seed_and_bot": 100,
    "results": rows,
}
Path("/tmp/canary-party-qa/party-variety-raw.json").write_text(
    json.dumps(out, indent=2)
)
print(
    json.dumps(
        {
            "synthetic": True,
            "selections": len(rows) * 100,
            "minimum_distinct": min(len(r["counts"]) for r in rows),
            "max_consecutive": max(r["maximum_consecutive"] for r in rows),
        }
    )
)
