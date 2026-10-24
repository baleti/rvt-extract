import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import rvtx  # noqa
from rvtx import rfa


def test_empty_z_only_in_8_byte_years_by_default(monkeypatch):
    monkeypatch.delenv('RVTX_EMPTYZ', raising=False); monkeypatch.delenv('RVTX_EMPTYZ4', raising=False)
    assert rfa.use_empty_z(8) and not rfa.use_empty_z(4)     # Fixed boundary condition family (34 VarSketch, 2022) was refused by Revit with it


def test_empty_z_opt_in_for_4_byte(monkeypatch):
    monkeypatch.setenv('RVTX_EMPTYZ4', '1')
    assert rfa.use_empty_z(4)
