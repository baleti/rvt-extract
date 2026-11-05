"""A family that references project-level electrical elements (load classification, demand factor, their parameters) must carry them: Revit 2024 rejects the Snowdon Electrical 'Lobby Chandelier' without them (ModificationForbiddenException on open; fixed record set == Revit's own EditFamily+SaveAs: 6 x ParamElemElectricalLoadClassification, 1 ElectricalLoadClassification, 1 ElectricalDemandFactorDefinition)."""
import unittest
from rvtx import rfa

class T(unittest.TestCase):
    def test_electrical_classes_are_copied_dependencies(self):
        for c in ('ElectricalLoadClassification', 'ElectricalDemandFactorDefinition', 'ParamElemElectricalLoadClassification'):
            self.assertIn(c, rfa.EXTRA)

if __name__ == '__main__': unittest.main()
