"""The separate supply goal cannot pass from phase names or purchase alone."""

import unittest

from m5_current_lowstock import goal_checks


class LowStockGoalTests(unittest.TestCase):
    def checks(self, purchase=True, returned=True):
        return goal_checks(
            {"bank": 10000, "potions": 2},
            {"bank": 7986, "potions": 40},
            {"posx": 32371, "posy": 32238, "posz": 7},
            {"posx": 32369, "posy": 32241, "posz": 7},
            {"status": "completed", "metrics": {"supply_delta": 38}}
            if purchase
            else {},
            {"status": "completed", "reason": "party_rejoined"} if returned else {},
            {"gaps": 0, "deaths": 0},
            0,
        )

    def test_authoritative_purchase_return_and_saved_state_pass(self):
        self.assertTrue(all(self.checks().values()))

    def test_purchase_alone_is_not_completed_return(self):
        self.assertFalse(all(self.checks(returned=False).values()))

    def test_return_without_observed_purchase_is_not_accepted(self):
        self.assertFalse(all(self.checks(purchase=False).values()))


if __name__ == "__main__":
    unittest.main()
