import csv, os, tempfile, unittest
from rvtx import cli


class T(unittest.TestCase):
    def test_known_bad_column(self):
        fams = [{'category': 'C', 'name': 'ok', 'types': [], 'parameters': [], 'embedded_records': 1, 'embedded_doc': True,
                 'rfa': {'status': 'written', 'file': 'a.rfa'}},
                {'category': 'C', 'name': 'bad', 'types': [], 'parameters': [], 'embedded_records': 1, 'embedded_doc': True,
                 'rfa': {'status': 'written', 'file': 'b.rfa', 'known_bad': 'Revit rejects'}}]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'f.csv'); cli.write_families_csv(p, fams)
            rows = list(csv.DictReader(open(p, encoding='utf-8')))
        self.assertEqual([r['known_bad'] for r in rows], ['', 'Revit rejects'])
        self.assertEqual(rows[0]['rfa_file'], 'a.rfa')


if __name__ == '__main__': unittest.main()
