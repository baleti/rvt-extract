import unittest
from rvtx import rfa


class T(unittest.TestCase):
    def test_int_zero_is_not_a_reference(self):
        # 2026-10-31: a plain 0 under an ...Id key pulled the project's CategoryElem with id 0 into 2022 nested families; Revit 2024 rejected them (needs recovery)
        out = set(); rfa._eids({'m_phaseId': 0, 'm_materialId': 5, 'x': {'m_ElemIds': [0, 7]}}, out)
        self.assertEqual(out, {5, 7})


if __name__ == '__main__': unittest.main()
