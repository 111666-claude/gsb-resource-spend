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


class OrderTest(unittest.TestCase):
    def test_spend_follows_order(self):
        target = world()
        target.set("p1", "mana", 1, 100)
        target.set("p1", "rage", 2, 100)
        self.assertTrue(target.spend("p1", 2, "r1"))
        self.assertEqual(target.get("p1", "rage"), 0)
        self.assertEqual(target.get("p1", "mana"), 1)

    def test_unlisted_pools_come_last_by_name(self):
        target = Pools(order=("rage",))
        target.set("p1", "zeta", 5, 100)
        target.set("p1", "alpha", 5, 100)
        target.set("p1", "rage", 1, 100)
        self.assertTrue(target.spend("p1", 3, "r1"))
        self.assertEqual(target.get("p1", "rage"), 0)
        self.assertEqual(target.get("p1", "alpha"), 3)
        self.assertEqual(target.get("p1", "zeta"), 5)


class RollbackTest(unittest.TestCase):
    def test_insufficient_total_returns_false_and_changes_nothing(self):
        target = world()
        target.set("p1", "rage", 1, 100)
        target.set("p1", "mana", 2, 100)
        self.assertFalse(target.spend("p1", 5, "r1"))
        self.assertEqual(target.get("p1", "rage"), 1)
        self.assertEqual(target.get("p1", "mana"), 2)

    def test_successful_spend_conserves_total(self):
        target = world()
        target.set("p1", "rage", 3, 100)
        target.set("p1", "mana", 4, 100)
        self.assertTrue(target.spend("p1", 5, "r1"))
        total = target.get("p1", "rage") + target.get("p1", "mana")
        self.assertEqual(total, 2)


class CapTest(unittest.TestCase):
    def test_set_clamps_to_cap(self):
        target = world()
        target.set("p1", "rage", 10, 5)
        self.assertEqual(target.get("p1", "rage"), 5)

    def test_set_clamps_negative_to_zero(self):
        target = world()
        target.set("p1", "rage", -3, 5)
        self.assertEqual(target.get("p1", "rage"), 0)


class IdempotencyTest(unittest.TestCase):
    def test_duplicate_req_id_charges_once(self):
        target = world()
        target.set("p1", "rage", 10, 100)
        self.assertTrue(target.spend("p1", 3, "same"))
        self.assertTrue(target.spend("p1", 3, "same"))
        self.assertEqual(target.get("p1", "rage"), 7)

    def test_failed_spend_replays_as_failed(self):
        target = world()
        target.set("p1", "rage", 1, 100)
        self.assertFalse(target.spend("p1", 5, "r1"))
        target.set("p1", "rage", 10, 100)
        self.assertFalse(target.spend("p1", 5, "r1"))
        self.assertEqual(target.get("p1", "rage"), 10)


class RefundTest(unittest.TestCase):
    def test_refund_restores_amounts(self):
        target = world()
        target.set("p1", "rage", 10, 100)
        target.spend("p1", 3, "r1")
        self.assertTrue(target.refund("p1", "r1"))
        self.assertEqual(target.get("p1", "rage"), 10)

    def test_refund_restores_across_pools(self):
        target = world()
        target.set("p1", "rage", 2, 100)
        target.set("p1", "mana", 2, 100)
        target.spend("p1", 3, "r1")
        self.assertTrue(target.refund("p1", "r1"))
        self.assertEqual(target.get("p1", "rage"), 2)
        self.assertEqual(target.get("p1", "mana"), 2)

    def test_refund_only_once(self):
        target = world()
        target.set("p1", "rage", 10, 100)
        target.spend("p1", 3, "r1")
        self.assertTrue(target.refund("p1", "r1"))
        self.assertFalse(target.refund("p1", "r1"))
        self.assertEqual(target.get("p1", "rage"), 10)

    def test_refund_of_failed_spend_returns_false(self):
        target = world()
        target.set("p1", "rage", 1, 100)
        self.assertFalse(target.spend("p1", 5, "r1"))
        self.assertFalse(target.refund("p1", "r1"))


class ScanTest(unittest.TestCase):
    def test_scanned_does_not_grow_with_total_pools(self):
        target = Pools(order=("rage",))
        for index in range(3000):
            target.set("p-%d" % index, "rage", 100, 100)
        for index in range(3000):
            target.spend("p-2999", 1, "r-%d" % index)
        self.assertLessEqual(target.scanned_count(), 6000)


if __name__ == "__main__":
    unittest.main()
