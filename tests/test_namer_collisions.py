import unicodedata, unittest
from rvtx.safepath import Namer

class NamerCollisions(unittest.TestCase):
    def test_distinct_outputs_for_lookalike_names(self):
        names = ['A' * 300 + 'x', 'A' * 300 + 'y', 'Fam', 'fam', 'FAM ', 'Fam.', 'Fam..', 'é', 'é']
        n = Namer()
        out = [n.take('c', x, '.rfa') for x in names]
        self.assertEqual(len({unicodedata.normalize('NFC', o).lower() for o in out}), len(out))
        self.assertTrue(all(o.endswith('.rfa') for o in out))

if __name__ == '__main__':
    unittest.main()
