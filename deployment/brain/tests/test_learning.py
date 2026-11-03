import random

from canary_brain.learning import Policy
from canary_brain.learning import episode_reward
from canary_brain.store import Store


def test_experience_changes_preferences_and_survives_restart(tmp_path):
    store = Store(tmp_path / "brain.db")
    policy = Policy(store, random.Random(42), epsilon=0)
    for _ in range(8):
        policy.learn(7, "knight-party", "hunt:a", 0.9)
        policy.learn(7, "knight-party", "hunt:b", 0.1)
    restored = Policy(Store(tmp_path / "brain.db"), random.Random(42), epsilon=0)
    assert restored.choose(7, "knight-party", ["hunt:a", "hunt:b"]).candidate_id == "hunt:a"
    assert restored.statistics(7, "knight-party")["hunt:a"]["count"] == 8


def test_equivalent_hunts_remain_varied_instead_of_repeating_forever(tmp_path):
    policy = Policy(Store(tmp_path / "brain.db"), random.Random(3))
    choices = [f"hunt:{index}" for index in range(5)]
    selected = [policy.choose(7, "party", choices, preferred="hunt:0").candidate_id for _ in range(100)]
    assert len(set(selected)) >= 4
    assert all(len(set(selected[index:index + 4])) > 1 for index in range(97))


def test_learning_does_not_change_another_context_and_idle_does_not_farm_rewards(tmp_path):
    policy = Policy(Store(tmp_path / "brain.db"))
    policy.learn(7, "party", "hunt:a", 1)
    assert policy.statistics(8, "party") == {}
    assert policy.statistics(7, "solo") == {}
    assert episode_reward("completed", {"progress": 0, "elapsed_seconds": 1000}) is None
    assert episode_reward("cancelled", {"progress": 1, "elapsed_seconds": 1000}) is None
    assert episode_reward("completed", {"progress": 1, "elapsed_seconds": 1000, "deaths": 1}) == 0
