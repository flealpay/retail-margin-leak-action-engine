import copy
import itertools
import unittest

from analyze import action_for_pair
from bridge import FACTORS, decompose, value


def state(units=100, share=.8, price=10, discount=1, cost=6):
    return {"units": units, "cells": {
        "a": {"share": share, "price": price, "discount": discount, "cost": cost},
        "b": {"share": 1-share, "price": 20, "discount": 2, "cost": 8},
    }}


class BridgeTests(unittest.TestCase):
    def test_volume_only(self):
        before = state()
        after = copy.deepcopy(before)
        after["units"] = 120
        result = decompose(before, after)
        self.assertAlmostEqual(result["effects"]["volume"], 88)
        self.assertTrue(all(abs(v) < 1e-8 for k, v in result["effects"].items() if k != "volume"))

    def test_cost_and_mix(self):
        before = state()
        after = state(cost=7)
        self.assertAlmostEqual(decompose(before, after)["effects"]["cost"], -80)
        mixed = state(share=.2)
        self.assertAlmostEqual(decompose(before, mixed)["effects"]["mix"], 420)

    def test_matches_all_120_orders(self):
        before, after = state(), state(units=130, share=.4, price=12, discount=2, cost=7)
        contributions = {f: 0 for f in FACTORS}
        for permutation in itertools.permutations(range(5)):
            mask = 0
            for i in permutation:
                next_mask = mask | (1 << i)
                contributions[FACTORS[i]] += (value(before, after, next_mask)-value(before, after, mask)) / 120
                mask = next_mask
        result = decompose(before, after)
        for factor in FACTORS:
            self.assertAlmostEqual(result["effects"][factor], contributions[factor])
        self.assertAlmostEqual(sum(result["effects"].values()), result["current_gp"]-result["baseline_gp"])

    def test_reverse_periods_negates_effects(self):
        before, after = state(), state(units=130, share=.4, price=12, discount=2, cost=7)
        forward, reverse = decompose(before, after), decompose(after, before)
        for factor in FACTORS:
            self.assertAlmostEqual(forward["effects"][factor], -reverse["effects"][factor])

    def test_missing_cell_rejected(self):
        before, after = state(), state()
        del after["cells"]["b"]
        with self.assertRaises(ValueError):
            decompose(before, after)


def pair(units, price, discount, cost):
    return {"units": units, "list_value": price*units, "discount_value": discount*units,
            "cogs": cost*units, "revenue": (price-discount)*units, "gp": (price-discount-cost)*units,
            "product_id": "X", "product_name": "Example", "category": "Example", "tier": "Core", "region": "North", "channel": "Online"}


class ActionTests(unittest.TestCase):
    def test_high_discount_with_profit_growth_not_automatically_modified(self):
        result = action_for_pair(pair(100, 100, 5, 40), pair(200, 100, 20, 40))
        self.assertEqual(result["action"], "PROTECT")
        self.assertEqual(result["scenario_gp_eur"], 0)

    def test_discount_and_cost_scenarios_are_fixed_volume(self):
        discount = action_for_pair(pair(100, 100, 5, 60), pair(110, 100, 20, 60))
        self.assertEqual(discount["reason"], "discount")
        self.assertAlmostEqual(discount["scenario_gp_eur"], 220)
        cost = action_for_pair(pair(100, 100, 5, 60), pair(100, 103, 5, 72))
        self.assertEqual(cost["reason"], "cost")
        self.assertAlmostEqual(cost["scenario_gp_eur"], 900)

    def test_loss_making_offer_requires_review(self):
        result = action_for_pair(pair(100, 100, 0, 60), pair(100, 100, 50, 60))
        self.assertEqual(result["action"], "STOP")
        self.assertAlmostEqual(result["scenario_gp_eur"], 1000)


if __name__ == "__main__":
    unittest.main()
