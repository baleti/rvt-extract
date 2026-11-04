import unittest
from rvtx import rfa as RFA


class Fake(RFA.Builder):
    def __init__(self, edges): self.edges = edges
    def nested_docs(self, k, seen=None): return [(c, 'g') for c in self.edges.get(k, [])]


class Cycle(unittest.TestCase):
    def test_mutual_nesting_terminates(self):
        self.assertEqual(Fake({1: [2], 2: [1]}).nested_depth(1), 1)

    def test_longer_cycle_and_diamond(self):
        self.assertEqual(Fake({1: [2], 2: [3], 3: [1]}).nested_depth(1), 2)
        self.assertEqual(Fake({1: [2, 3], 2: [4], 3: [4]}).nested_depth(1), 2)

    def test_plain_depths_unchanged(self):
        self.assertEqual(Fake({}).nested_depth(1), 0)
        self.assertEqual(Fake({1: [2], 2: [3]}).nested_depth(1), 2)
