import unittest

from resources.core import Pools


def world():
    return Pools(order=("rage", "mana"))


class BasicTest(unittest.TestCase):
    def test_unknown_pool_is_zero(self):
        self.assertEqual(world().get("p1", "rage"), 0)

    def test_set_then_get(self):
        target = world()
        target.set("p1", "rage", 3, 10)
        self.assertEqual(target.get("p1", "rage"), 3)

    def test_order_is_stored(self):
        self.assertEqual(world().order, ["rage", "mana"])

    def test_refund_of_unknown_req_returns_false(self):
        self.assertFalse(world().refund("p1", "ghost"))

    def test_scanned_starts_at_zero(self):
        self.assertEqual(world().scanned_count(), 0)


class CapTest(unittest.TestCase):
    def test_set_clamps_amount_above_cap(self):
        target = world()
        target.set("p1", "rage", 10, 5)
        self.assertEqual(target.get("p1", "rage"), 5)

    def test_set_clamps_amount_below_zero(self):
        target = world()
        target.set("p1", "mana", -3, 5)
        self.assertEqual(target.get("p1", "mana"), 0)

    def test_set_reclamps_when_cap_lowered(self):
        target = world()
        target.set("p1", "rage", 4, 10)
        target.set("p1", "rage", 4, 3)
        self.assertEqual(target.get("p1", "rage"), 3)


class OrderTest(unittest.TestCase):
    def test_spend_follows_order_list(self):
        target = world()
        target.set("p1", "mana", 1, 100)
        target.set("p1", "rage", 2, 100)
        self.assertTrue(target.spend("p1", 2, "r1"))
        self.assertEqual(target.get("p1", "rage"), 0)
        self.assertEqual(target.get("p1", "mana"), 1)

    def test_unlisted_pools_come_last_sorted_by_name(self):
        target = Pools(order=("rage",))
        target.set("p1", "zeta", 5, 100)
        target.set("p1", "alpha", 5, 100)
        target.set("p1", "rage", 1, 100)
        self.assertTrue(target.spend("p1", 4, "r1"))
        self.assertEqual(target.get("p1", "rage"), 0)
        self.assertEqual(target.get("p1", "alpha"), 2)
        self.assertEqual(target.get("p1", "zeta"), 5)

    def test_spend_only_touches_owning_player(self):
        target = world()
        target.set("p1", "rage", 1, 100)
        target.set("p2", "rage", 10, 100)
        self.assertTrue(target.spend("p1", 1, "r1"))
        self.assertEqual(target.get("p1", "rage"), 0)
        self.assertEqual(target.get("p2", "rage"), 10)


class RollbackTest(unittest.TestCase):
    def test_insufficient_total_returns_false_and_changes_nothing(self):
        target = world()
        target.set("p1", "rage", 1, 100)
        target.set("p1", "mana", 2, 100)
        self.assertFalse(target.spend("p1", 5, "r1"))
        self.assertEqual(target.get("p1", "rage"), 1)
        self.assertEqual(target.get("p1", "mana"), 2)

    def test_failed_spend_does_not_partially_drain_first_pools(self):
        target = world()
        target.set("p1", "rage", 3, 100)
        target.set("p1", "mana", 0, 100)
        self.assertFalse(target.spend("p1", 4, "r1"))
        self.assertEqual(target.get("p1", "rage"), 3)

    def test_failed_spend_is_memoized(self):
        target = world()
        target.set("p1", "rage", 1, 100)
        self.assertFalse(target.spend("p1", 5, "r1"))
        target.set("p1", "rage", 100, 100)
        self.assertFalse(target.spend("p1", 5, "r1"))
        self.assertEqual(target.get("p1", "rage"), 100)


class ConservationTest(unittest.TestCase):
    def test_successful_spend_reduces_total_by_exact_cost(self):
        target = world()
        target.set("p1", "rage", 4, 100)
        target.set("p1", "mana", 6, 100)
        before = target.get("p1", "rage") + target.get("p1", "mana")
        self.assertTrue(target.spend("p1", 5, "r1"))
        after = target.get("p1", "rage") + target.get("p1", "mana")
        self.assertEqual(before - after, 5)

    def test_amounts_never_go_negative(self):
        target = world()
        target.set("p1", "rage", 4, 100)
        target.set("p1", "mana", 6, 100)
        self.assertTrue(target.spend("p1", 5, "r1"))
        self.assertGreaterEqual(target.get("p1", "rage"), 0)
        self.assertGreaterEqual(target.get("p1", "mana"), 0)


class IdempotencyTest(unittest.TestCase):
    def test_duplicate_req_id_does_not_double_charge(self):
        target = world()
        target.set("p1", "rage", 10, 100)
        self.assertTrue(target.spend("p1", 3, "same"))
        self.assertTrue(target.spend("p1", 3, "same"))
        self.assertEqual(target.get("p1", "rage"), 7)

    def test_duplicate_req_id_returns_same_result(self):
        target = world()
        target.set("p1", "rage", 1, 100)
        self.assertFalse(target.spend("p1", 3, "same"))
        target.set("p1", "rage", 10, 100)
        self.assertFalse(target.spend("p1", 3, "same"))
        self.assertEqual(target.get("p1", "rage"), 10)

    def test_different_req_ids_settle_independently(self):
        target = world()
        target.set("p1", "rage", 10, 100)
        self.assertTrue(target.spend("p1", 3, "a"))
        self.assertTrue(target.spend("p1", 3, "b"))
        self.assertEqual(target.get("p1", "rage"), 4)


class RefundTest(unittest.TestCase):
    def test_refund_restores_exact_amounts(self):
        target = world()
        target.set("p1", "rage", 4, 100)
        target.set("p1", "mana", 6, 100)
        self.assertTrue(target.spend("p1", 5, "r1"))
        self.assertTrue(target.refund("p1", "r1"))
        self.assertEqual(target.get("p1", "rage"), 4)
        self.assertEqual(target.get("p1", "mana"), 6)

    def test_refund_only_once(self):
        target = world()
        target.set("p1", "rage", 10, 100)
        self.assertTrue(target.spend("p1", 3, "r1"))
        self.assertTrue(target.refund("p1", "r1"))
        self.assertFalse(target.refund("p1", "r1"))
        self.assertEqual(target.get("p1", "rage"), 10)

    def test_refund_of_unknown_req_returns_false(self):
        target = world()
        target.set("p1", "rage", 10, 100)
        self.assertFalse(target.refund("p1", "ghost"))

    def test_refund_other_player_req_returns_false(self):
        target = world()
        target.set("p1", "rage", 10, 100)
        target.set("p2", "rage", 10, 100)
        self.assertTrue(target.spend("p1", 3, "r1"))
        self.assertFalse(target.refund("p2", "r1"))
        self.assertEqual(target.get("p1", "rage"), 7)
        self.assertEqual(target.get("p2", "rage"), 10)

    def test_refund_does_not_replay_spend(self):
        target = world()
        target.set("p1", "rage", 10, 100)
        self.assertTrue(target.spend("p1", 3, "r1"))
        self.assertTrue(target.refund("p1", "r1"))
        self.assertTrue(target.spend("p1", 3, "r1"))
        self.assertEqual(target.get("p1", "rage"), 10)


class ScanCostTest(unittest.TestCase):
    def test_scanned_does_not_grow_with_unrelated_pools(self):
        target = Pools(order=("rage",))
        for index in range(10000):
            target.set("p-%d" % index, "rage", 100, 100)
        self.assertTrue(target.spend("p-9999", 1, "r1"))
        self.assertLessEqual(target.scanned_count(), 2)

    def test_scanned_is_proportional_to_used_pools(self):
        target = Pools(order=("rage",))
        for index in range(5000):
            target.set("other-%d" % index, "rage", 10000, 10000)
        for index in range(3000):
            self.assertTrue(target.spend("other-4999", 1, "r-%d" % index))
        self.assertLessEqual(target.scanned_count(), 6000)


if __name__ == "__main__":
    unittest.main()
