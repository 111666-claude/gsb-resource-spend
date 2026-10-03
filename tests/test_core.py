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

    def test_refund_of_unknown_req_returns_true(self):
        self.assertTrue(world().refund("p1", "ghost"))

    def test_scanned_starts_at_zero(self):
        self.assertEqual(world().scanned_count(), 0)


if __name__ == "__main__":
    unittest.main()
