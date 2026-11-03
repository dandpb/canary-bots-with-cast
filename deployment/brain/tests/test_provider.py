from types import SimpleNamespace

import pytest

from canary_brain.provider import Provider
from canary_brain.protocol import Observation
from canary_brain.store import Store
from test_protocol import observation


class APIResult:
    def model_dump(self, **kwargs):
        return {"model": "gpt-6-luna", "answers": [{"type": "choice", "name": "action", "choice": "resupply"}],
                "usage": {"input_tokens": 100, "output_tokens": 0}}


async def test_decision_uses_only_supplied_choices_and_accounts_for_real_usage(tmp_path):
    requests = []

    async def create(**kwargs):
        requests.append(kwargs)
        return APIResult()

    store = Store(tmp_path / "brain.db")
    provider = Provider(store, SimpleNamespace(decisions=SimpleNamespace(create=create)))
    assert await provider.decide(Observation.model_validate(observation())) == "resupply"
    assert requests[0]["model"] == "gpt-6-luna"
    choices = requests[0]["questions"][0]["choices"]
    assert {choice["value"] for choice in choices} == {"continue", "resupply"}
    assert store.budget()["spent"] == 10000
    assert store.budget()["reserved"] == 0
