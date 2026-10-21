"""Contract tests: the committed baseline deliberately has TWO failing tests."""
import unittest

from pricing import total
from labels import slug


class PricingTests(unittest.TestCase):
    def test_quantities(self):
        self.assertEqual(total([(5, 3), (2, 0), (4, 2)]), 23)

    def test_empty(self):
        self.assertEqual(total([]), 0)

    def test_unit_quantity(self):
        self.assertEqual(total([(5, 1), (2, 1)]), 7)


class LabelTests(unittest.TestCase):
    def test_mixed_whitespace(self):
        self.assertEqual(slug("  Hello   SWARM\tLab\n "), "hello-swarm-lab")

    def test_blank(self):
        self.assertEqual(slug("  "), "")

    def test_simple(self):
        self.assertEqual(slug("Hello Lab"), "hello-lab")


if __name__ == "__main__":
    unittest.main()
