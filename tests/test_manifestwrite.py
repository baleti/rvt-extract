import json, os, tempfile, unittest
from rvtx import cli


class ManifestWrite(unittest.TestCase):
    def test_unserialisable_keeps_old_and_no_temp(self):
        d = tempfile.mkdtemp(); p = os.path.join(d, 'm', 'manifest.json'); cli.write_json(p, {'a': 1})
        class Bad:
            def __str__(self): raise RuntimeError('boom')
        with self.assertRaises(RuntimeError): cli.write_json(p, {'a': Bad()})
        self.assertEqual(json.load(open(p)), {'a': 1}); self.assertEqual(os.listdir(os.path.dirname(p)), ['manifest.json'])

    def test_roundtrip(self):
        d = tempfile.mkdtemp(); p = os.path.join(d, 'manifest.json'); cli.write_json(p, [{'n': 'ünï'}])
        self.assertEqual(json.load(open(p)), [{'n': 'ünï'}])
