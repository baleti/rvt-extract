import json, os, subprocess, sys, tempfile, unittest
from rvtx import mdiff as M

def fam(name, cat='Doors', types=('A',), params=(), rec=10):
    return dict(name=name, category=cat, types=list(types), parameters=[dict(p) for p in params], embedded_records=rec, rfa=dict(status='written'))

P1 = dict(name='Width', datatype='LENGTH', shared=False, formula=None)


class T(unittest.TestCase):
    def test_same_ignores_rfa(self):
        a = [fam('D1', params=[P1])]; b = [fam('D1', params=[P1])]; b[0]['rfa'] = dict(status='error')
        d = M.diff(a, b)
        self.assertEqual((d['only_a'], d['only_b'], d['changed'], d['same']), ([], [], [], 1))

    def test_only_and_changed(self):
        a = [fam('D1', params=[P1]), fam('D2'), fam('W1', cat='Windows')]
        b = [fam('D1', types=('A', 'B'), params=[dict(P1, formula='x*2'), dict(name='Hgt', datatype='LENGTH')], rec=12), fam('W1', cat='Windows'), fam('D3')]
        d = M.diff(a, b)
        self.assertEqual(d['only_a'], [['Doors', 'D2']]); self.assertEqual(d['only_b'], [['Doors', 'D3']]); self.assertEqual(d['same'], 1)
        c = d['changed'][0]
        self.assertEqual((c['category'], c['name'], c['types_added'], c['types_removed'], c['records']), ('Doors', 'D1', ['B'], [], [10, 12]))
        self.assertEqual(c['params_added'], ['Hgt']); self.assertEqual(c['params_removed'], [])
        self.assertEqual(c['params_changed'], [dict(name='Width', field='formula', a=None, b='x*2')])

    def test_duplicates_and_render(self):
        a = [fam('D1', rec=1), fam('D1', rec=2)]; b = [fam('D1', rec=2)]
        self.assertEqual(M.diff(a, b)['same'], 1)
        d = M.diff([fam('D2')], [fam('D3')])
        for r in (M.render_text(d), M.render_md(d)):
            self.assertIn('D2', r); self.assertIn('D3', r); self.assertTrue(r.rstrip().endswith('0 same, 0 changed, 1 only in A, 1 only in B'))

    def test_cli(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(M.__file__)))
        with tempfile.TemporaryDirectory() as t:
            pa, pb = os.path.join(t, 'a.json'), os.path.join(t, 'b.json')
            json.dump([fam('D1')], open(pa, 'w')); json.dump([fam('D1')], open(pb, 'w'))
            run = lambda *x: subprocess.run([sys.executable, os.path.join(root, 'tools', 'manifest_diff.py'), *x], capture_output=True, text=True)
            self.assertEqual(run(pa, pb).returncode, 0)
            json.dump([fam('D2')], open(pb, 'w'))
            r = run(pa, pb, '--format', 'json'); self.assertEqual(r.returncode, 1); self.assertEqual(json.loads(r.stdout)['only_b'], [['Doors', 'D2']])
            self.assertEqual(run(pa, os.path.join(t, 'missing.json')).returncode, 2)


if __name__ == '__main__':
    unittest.main()
