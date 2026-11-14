import json, os, tempfile, unittest
from rvtx import cli


def _bad(c): raise ValueError(c)


class T(unittest.TestCase):
    def test_nan_inf_strict(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'm.json')
            cli.write_json(p, [{'a': float('nan'), 'b': [float('inf'), -float('inf'), 1.5], 'c': {'n': 2}}])
            v = json.loads(open(p, encoding='utf-8').read(), parse_constant=_bad)
        self.assertEqual(v, [{'a': 'NaN', 'b': ['Infinity', '-Infinity', 1.5], 'c': {'n': 2}}])
