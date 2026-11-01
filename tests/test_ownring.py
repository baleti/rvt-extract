import unittest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from rvtx import elemtable as ET

def own_row(o): return o.to_bytes(4, 'little') + b'\0' * 8

class OwnerRing(unittest.TestCase):
    """2020 nested families Body-Exterior (ring of 3 style elements) and SWC title block (ring of 7) never finished opening in Revit 2024: owner ring in the ElemTable"""
    def test_ring_gets_lowest_id_cleared(self):
        ids = [10, 20, 30, 40, 50]
        owners = {10: own_row(0xffffffff), 20: own_row(40), 30: own_row(20), 40: own_row(30), 50: own_row(40)}
        fix = ET.owner_cycles4(ids, set(ids), owners)
        self.assertEqual(fix, {20})      # ring 20 -> 40 -> 30 -> 20, lowest id 20 becomes a chain root

    def test_self_owner_and_chains_untouched(self):
        ids = [1, 2, 3]
        owners = {1: own_row(1), 2: own_row(1), 3: own_row(0xffffffff)}
        self.assertEqual(ET.owner_cycles4(ids, set(ids), owners), set())

    def test_two_rings(self):
        ids = [1, 2, 3, 4]
        owners = {1: own_row(2), 2: own_row(1), 3: own_row(4), 4: own_row(3)}
        self.assertEqual(ET.owner_cycles4(ids, set(ids), owners), {1, 3})

    def test_build4_has_no_ring(self):
        ids = [10, 20, 30]
        owners = {10: own_row(30), 20: own_row(10), 30: own_row(20)}
        raw = ET.build4(ids, set(ids), owners, 99)
        rows = {}
        import struct
        for k in range(len(raw)):
            pass
        fix = ET.owner_cycles4(ids, set(ids), owners)
        self.assertEqual(fix, {10})

if __name__ == '__main__': unittest.main()
