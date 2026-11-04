import unittest
import xml.dom.minidom as minidom
from rvtx import smallstreams as S


class PartAtomHostile(unittest.TestCase):
    def test_hostile_names_stay_wellformed_xml(self):
        for t in ['a<b>&"\'', 'tab\there', 'bell\x07x', 'nul\x00x', '\ud800lone', 'x\x1fy', '￾￿', 'x' * 5000]:
            minidom.parseString(S.part_atom(t, 'Cat<>', 'f&.rfa'))


if __name__ == '__main__':
    unittest.main()
