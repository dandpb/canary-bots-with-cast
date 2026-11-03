import pytest
from canary_brain.protocol import Observation, intent_for
from pydantic import ValidationError


def observation():
    return {
        "version": 1,
        "type": "observation",
        "world": "world-a",
        "sequence": 10,
        "captured_ms": 1000,
        "lease": "lease-a",
        "objective_generation": 2,
        "bot": {
            "id": 7,
            "name": "Companion",
            "level": 80,
            "vocation": 1,
            "state": "PARTY",
            "position": [100, 100, 7],
            "health": 90,
            "mana": 60,
            "potions": 3,
            "xp": 1000,
            "alive": True,
        },
        "party": {"leader_id": 9, "members": [9, 7]},
        "actions": [
            {
                "id": "continue",
                "action": "continue",
                "description": "Keep the current objective",
                "ttl_ms": 1500,
            },
            {
                "id": "resupply",
                "action": "resupply",
                "description": "Restock at a reachable shop",
                "ttl_ms": 5000,
            },
        ],
    }


def test_selected_action_keeps_server_authority_and_deadline():
    snapshot = Observation.model_validate(observation())
    intent = intent_for(snapshot, "resupply", "action-1")
    assert intent.bot_id == 7
    assert intent.world == "world-a"
    assert intent.expires_ms == 6000
    assert intent.candidate_id == "resupply"
    assert intent.objective_generation == 2


def test_model_cannot_invent_a_destination_or_action():
    snapshot = Observation.model_validate(observation())
    with pytest.raises(ValueError, match="candidate"):
        intent_for(snapshot, "teleport 500,500,7", "action-2")


def test_unrecognized_versions_and_fields_are_rejected():
    packet = observation()
    packet["version"] = 2
    with pytest.raises(ValidationError):
        Observation.model_validate(packet)
    packet["version"] = 1
    packet["admin_command"] = "reload"
    with pytest.raises(ValidationError):
        Observation.model_validate(packet)
