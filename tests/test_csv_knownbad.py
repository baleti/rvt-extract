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

    def test_awkward_names_roundtrip(self):
        names = ['a,b', 'q"uote', 'line\nbreak', '=1+1', '\ud800lone', 'caf\u00e9']
        fams = [{'category': 'C,x', 'name': n, 'types': [], 'parameters': [], 'embedded_records': 0, 'embedded_doc': False} for n in names]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'f.csv'); cli.write_families_csv(p, fams)
            rows = list(csv.DictReader(open(p, encoding='utf-8', newline='')))
        self.assertEqual(len(rows), len(names))
        self.assertEqual([r['name'] for r in rows[:4]], names[:3] + ["'=1+1"])      # formula-like names get a leading apostrophe (Excel formula injection); the exact name stays in manifest.json
        self.assertEqual(rows[4]['name'], '?lone'); self.assertEqual(rows[5]['name'], names[5])
        self.assertEqual(rows[0]['rfa_status'], 'no-embedded-doc')


if __name__ == '__main__': unittest.main()


class KB(unittest.TestCase):
    def test_known_bad_files(self):
        f = [{'rfa': {'status': 'written', 'file': 'b.rfa', 'known_bad': 'x'}}, {'rfa': {'status': 'written', 'file': 'a.rfa'}},
             {'rfa': {'status': 'error', 'known_bad': 'x'}}, {}]
        self.assertEqual(cli.known_bad_files(f), ['b.rfa'])
