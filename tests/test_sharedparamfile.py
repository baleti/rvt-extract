import unittest, uuid
from rvtx import sharedparamfile as S

G = '{AAAAAAAA-0000-4000-8000-000000000001}'
G2 = 'bbbbbbbb-0000-4000-8000-000000000002'


class T(unittest.TestCase):
    def sample(self):
        return [(2, 'Dimensions'), (1, 'Identity')], [
            dict(guid=G2, name='Width', datatype='LENGTH', group=2, description='w'),
            dict(guid=G, name='Mark', datatype='TEXT', group=1, datacategory='', visible=False, usermodifiable=False, hidewhennovalue=True)]

    def test_write_layout(self):
        t = S.write(*self.sample())
        self.assertTrue(t.startswith('# This is a Revit shared parameter file.\r\n# Do not edit manually.\r\n*META\tVERSION\tMINVERSION\r\nMETA\t2\t1\r\n*GROUP\tID\tNAME\r\n'))
        lines = t.split('\r\n')
        self.assertEqual(lines[6:8], ['GROUP\t1\tIdentity', 'GROUP\t2\tDimensions'])
        self.assertEqual(lines[9], 'PARAM\taaaaaaaa-0000-4000-8000-000000000001\tMark\tTEXT\t\t1\t0\t\t0\t1')
        self.assertEqual(lines[10], 'PARAM\tbbbbbbbb-0000-4000-8000-000000000002\tWidth\tLENGTH\t\t2\t1\tw\t1\t0')
        self.assertTrue(t.endswith('\r\n'))

    def test_roundtrip(self):
        g, p = S.parse(S.write(*self.sample()))
        self.assertEqual(g, [(1, 'Identity'), (2, 'Dimensions')])
        self.assertEqual([x['name'] for x in p], ['Mark', 'Width'])
        self.assertIs(p[0]['visible'], False); self.assertIs(p[0]['hidewhennovalue'], True); self.assertEqual(p[0]['group'], 1)
        self.assertEqual(S.write(g, p), S.write(*self.sample()))

    def test_sanitise_and_errors(self):
        t = S.write([(1, 'A\tB')], [dict(guid=G, name='x\ny', datatype='TEXT', group=1)])
        self.assertIn('GROUP\t1\tA B', t); self.assertIn('\tx y\t', t)
        with self.assertRaises(ValueError): S.write([(1, 'A')], [dict(guid=G, name='x', datatype='TEXT', group=9)])
        with self.assertRaises(ValueError): S.parse('GROUP\t1\tA\nPARAM\tnot-a-guid\tx\tTEXT\t\t1\n')
        with self.assertRaises(ValueError): S.parse('GROUP\t1\tA\nPARAM\t%s\tx\tTEXT\t\t7\n' % uuid.uuid4())

    def test_parse_tolerant(self):
        txt = '﻿# c\n*META\tVERSION\tMINVERSION\nMETA\t2\t1\n\n*GROUP\tID\tNAME\nGROUP\t5\tG\nJUNK\tx\n*PARAM\tGUID\n\nPARAM\t%s\tn\tTEXT\t\t5\n' % G2
        g, p = S.parse(txt)
        self.assertEqual(g, [(5, 'G')]); self.assertEqual(len(p), 1)
        self.assertEqual((p[0]['visible'], p[0]['usermodifiable'], p[0]['hidewhennovalue'], p[0]['description']), (True, True, False, ''))

    def test_merge(self):
        a = ([(1, 'Identity')], [dict(guid=G, name='Mark', datatype='TEXT', group=1)])
        b = ([(7, 'Identity'), (8, 'Other')], [dict(guid=G, name='Mark2', datatype='TEXT', group=7), dict(guid=G2, name='Mark', datatype='TEXT', group=7), dict(guid=str(uuid.uuid4()), name='Q', datatype='TEXT', group=8)])
        g, p = S.merge(a, b)
        self.assertEqual(len(p), 3); self.assertEqual(len({x['guid'].lower() for x in p}), 3)
        names = {x['name'] for x in p}; self.assertIn('Mark', names); self.assertNotIn('Mark2', names)
        ids = {i for i, n in g}; self.assertTrue(all(x['group'] in ids for x in p)); self.assertEqual(sum(1 for i, n in g if n == 'Identity'), 1)


if __name__ == '__main__':
    unittest.main()
