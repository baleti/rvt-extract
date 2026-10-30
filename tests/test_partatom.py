import unittest
import xml.etree.ElementTree as ET
from rvtx import smallstreams as SS


class PartAtom(unittest.TestCase):
    def test_wellformed_for_hostile_names(self):
        for n in ['M_Door & Frame', 'a<b>c', 'x"y\'z', 'ctl\x01\x1fchar', 'lone\ud800surrogate', 'ünï ✓']:
            root = ET.fromstring(SS.part_atom(n, 'Doors & <Cat>', n + '.rfa'))
            self.assertTrue(root.find('{http://www.w3.org/2005/Atom}title').text)

    def test_plain_name_unchanged(self):
        self.assertIn(b'<title>M_Door</title>', SS.part_atom('M_Door', 'Doors', 'M_Door.rfa'))
