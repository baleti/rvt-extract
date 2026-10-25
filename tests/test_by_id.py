"""regression: an incomplete placeholder record sharing an id with a real record must not hide it (family lift KeyError None when the project's KeynoteTable id was taken by a 'Hub' placeholder). Synthetic data only."""
import unittest, itertools
from rvtx import rfa as RFA

class T(unittest.TestCase):
    def test_complete_wins_in_any_order(self):
        real = {'class': 'KeynoteTable', 'complete': True}; junk = {'class': 'Hub', 'complete': False}
        for order in itertools.permutations([((6, 'KeynoteTable'), real), ((6, 'Hub'), junk), ((7, 'Level'), {'class': 'Level', 'complete': True})]):
            b = RFA.by_id(dict(order))
            self.assertEqual(b[6]['class'], 'KeynoteTable'); self.assertEqual(b[7]['class'], 'Level')
    def test_two_incomplete_keeps_one(self):
        self.assertIn(RFA.by_id({(0, 'A'): {'class': 'A', 'complete': False}, (0, 'B'): {'class': 'B', 'complete': False}})[0]['class'], ('A', 'B'))
if __name__ == '__main__': unittest.main()
