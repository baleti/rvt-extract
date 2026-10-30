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


if __name__ == '__main__': unittest.main()
