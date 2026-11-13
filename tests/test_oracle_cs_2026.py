"""Revit 2026 removed ElementId.IntegerValue; the oracle checker must stay compilable for 2024..2026."""
import pathlib
def test_no_integervalue_in_oracle():
    for p in pathlib.Path(__file__).parent.parent.glob('oracle/*.cs'):
        assert 'IntegerValue' not in p.read_text(encoding='utf-8'), p.name
