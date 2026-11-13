import unicodedata, unittest
from rvtx.safepath import Namer

class NamerCollisions(unittest.TestCase):
    def test_distinct_outputs_for_lookalike_names(self):
        names = ['A' * 300 + 'x', 'A' * 300 + 'y', 'Fam', 'fam', 'FAM ', 'Fam.', 'Fam..', 'é', 'é']
        n = Namer()
        out = [n.take('c', x, '.rfa') for x in names]
        self.assertEqual(len({unicodedata.normalize('NFC', o).lower() for o in out}), len(out))
        self.assertTrue(all(o.endswith('.rfa') for o in out))

    def test_reserved_and_long_names_are_safe(self):
        n = Namer()
        for x in ['CON', 'nul', 'Com1', 'LPT9', 'aux.x', '\u00e9' * 200, '\u65e5\u672c\u8a9e' * 80, '..', '.', ' ']:
            o = n.take('c', x, '.rfa')
            self.assertLessEqual(len(o.encode()), 255)
            self.assertNotIn(o.split('.')[0].upper(), ('CON', 'NUL', 'COM1', 'LPT9', 'AUX', '..', ''))

if __name__ == '__main__':
    unittest.main()
