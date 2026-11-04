import os, tempfile, unittest
from rvtx import knownbad


class T(unittest.TestCase):
    def test_registry(self):
        with tempfile.NamedTemporaryFile('w', suffix='.tsv', delete=False) as f:
            f.write('# c\n2020\tRebar\t^Shape 9$\tOpenfail in Revit 2024\n*\t.\tzzz\tany year\n')
        try:
            self.assertEqual(knownbad.reason(2020, 'Rebar Shape', 'Shape 9', f.name), 'Openfail in Revit 2024')
            self.assertIsNone(knownbad.reason(2021, 'Rebar Shape', 'Shape 9', f.name))
            self.assertEqual(knownbad.reason(2024, 'x', 'azzzb', f.name), 'any year')
        finally: os.unlink(f.name)

    def test_mark(self):
        self.assertIn('known_bad', knownbad.mark({}, 2016, 'c', 'n', experimental=True))
        self.assertNotIn('known_bad', knownbad.mark({}, 2024, 'c', 'n'))

    def test_shipped_registry_2020_pile_caps(self):
        for n in ('Pile Cap - 2 Pile', 'Pile Cap - 4 Pile'):
            self.assertTrue(knownbad.reason(2020, 'Structural Foundations', n), n)
            self.assertTrue(knownbad.reason('2020', 'Structural Foundations', n), n)
        for n in ('Pile Cap - 3 Pile', 'Pile Cap - 4 Pile 2'):
            self.assertIsNone(knownbad.reason(2020, 'Structural Foundations', n), n)
        self.assertIsNone(knownbad.reason(2021, 'Structural Foundations', 'Pile Cap - 4 Pile'))


if __name__ == '__main__': unittest.main()
