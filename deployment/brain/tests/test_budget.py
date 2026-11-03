from concurrent.futures import ThreadPoolExecutor

import pytest

from canary_brain.store import BudgetExceeded, Store


def test_concurrent_requests_cannot_spend_the_same_remaining_budget(tmp_path):
    store = Store(tmp_path / "brain.db", cap=1000)

    def reserve(index):
        try:
            store.reserve(str(index), 600, "2026-11")
            return True
        except BudgetExceeded:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(reserve, [1, 2])) == [False, True]
    reopened = Store(tmp_path / "brain.db", cap=1000)
    assert reopened.budget("2026-11")["reserved"] == 600
    with pytest.raises(BudgetExceeded):
        reopened.reserve("retry", 500, "2026-11")
