import os, unittest
from rvtx import safepath as P


class T(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(P.safe_name('a<b>:c/d'), 'a_b__c_d')
        self.assertEqual(P.safe_name('  x. '), 'x'); self.assertEqual(P.safe_name(None), 'Unnamed'); self.assertEqual(P.safe_name('...'), 'Unnamed')
        self.assertEqual(P.safe_name('café'), 'café')

    def test_reserved(self):
        for n in ('CON', 'con', 'Nul', 'COM1', 'lpt9', 'aux.txt'):
            self.assertTrue(P.safe_name(n).startswith(n[:3]) and P.safe_name(n) != n, n)
        self.assertEqual(P.safe_name('CONSOLE'), 'CONSOLE')

    def test_long(self):
        s = 'x' * 300; r = P.safe_name(s, 50)
        self.assertEqual(len(r), 50); self.assertIn('~', r)
        self.assertNotEqual(P.safe_name('x' * 300 + 'a', 50), P.safe_name('x' * 300 + 'b', 50))

    def test_namer(self):
        n = P.Namer()
        self.assertEqual(n.take('d', 'Door', '.rfa'), 'Door.rfa')
        self.assertEqual(n.take('d', 'door', '.rfa'), 'door (2).rfa')
        self.assertEqual(n.take('d', 'DOOR', '.rfa'), 'DOOR (3).rfa')
        self.assertEqual(n.take('e', 'Door', '.rfa'), 'Door.rfa')
        self.assertEqual(n.take('d', 'a/b', ''), 'a_b'); self.assertEqual(n.take('d', 'a:b', ''), 'a_b (2)')
        m = P.Namer(); self.assertEqual([m.take('d', 'x') for _ in range(3)], ['x', 'x (2)', 'x (3)'])

    def test_budget(self):
        root = '/tmp/out'; parts = ['c' * 100, 'f' * 150 + '.rfa']
        r = P.relpath_budget(root, parts, 120)
        self.assertLessEqual(len(os.path.join(root, *r)), 120); self.assertEqual(len(r), 2)
        self.assertEqual(P.relpath_budget(root, ['a', 'b.rfa'], 240), ['a', 'b.rfa'])
        with self.assertRaises(ValueError): P.relpath_budget('/' + 'r' * 200, ['a', 'b'], 100)

    def test_rfa_target(self):
        cat, stem = P.rfa_target('/tmp/out', 'C' * 120, 'F' * 120)
        self.assertLessEqual(len(os.path.join('/tmp/out', 'families', cat, stem + ' (99).rfa')), 240)
        self.assertNotEqual(stem, 'F' * 120)
        self.assertEqual(P.rfa_target('/tmp/out', 'Doors', 'A door'), ('Doors', 'A door'))
        self.assertEqual(P.rfa_target('/' + 'r' * 300, 'Doors', 'x'), ('Doors', 'x'))


if __name__ == '__main__':
    unittest.main()


class TestNamerCaseDirs(unittest.TestCase):
    def test_case_variant_directories_share_name_space(self):
        # Linux keeps "Doors" and "doors" apart, Windows merges them
        from rvtx import safepath
        n = safepath.Namer()
        a = n.take("out/Doors", "Door", ".rfa")
        b = n.take("out/doors", "Door", ".rfa")
        self.assertNotEqual(a.lower(), b.lower())


class Collisions(unittest.TestCase):
    def test_hostile_collisions_never_share_a_filename(self):
        n = P.Namer(); names = ['x.', 'x', 'X', 'CON', 'con_', 'CON.', 'café', 'café', 'a/b', 'a:b', 'F' * 300, 'F' * 299 + 'G']
        got = [n.take('d', s, '.rfa') for s in names]
        import unicodedata
        keys = [unicodedata.normalize('NFC', g).lower() for g in got]
        self.assertEqual(len(set(keys)), len(keys), got)
        for g in got: self.assertLessEqual(len(g), 130); self.assertNotIn(g.split('.')[0].upper(), ('CON', 'PRN', 'AUX', 'NUL'))
