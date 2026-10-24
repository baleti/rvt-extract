import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from rvtx import items


class P:
    def __init__(self, by_class): self.by_class = by_class


def test_revisions_sorted():
    p = P({'ProjectRevision': [{'id': 2, 'fields': {'m_sequenceNumber': 2, 'm_numberStr': 'B', 'm_issued': 1}}, {'id': 1, 'fields': {'m_sequenceNumber': 1, 'm_numberStr': 'A'}}]})
    d, fl = items.revisions(p)
    assert [r['number'] for r in d] == ['A', 'B'] and d[1]['issued'] and not fl


def test_imports_settings():
    f = {'m_symbolInfo': {'obj': {'m_name': 'x.dwg'}}, 'm_importSettings': {'m_link': 1, 'm_viewSpecific': 0}, 'm_unitTypeId': {'m_typeId': 'mm'}, 'm_size': 5, 'm_layerCategoryIdSet': [1, 2], 'm_parentIdSet': [3]}
    d, _ = items.imports(P({'MasterImportSymbol': [{'id': 9, 'fields': f}]}))
    assert d[0] == {'id': 9, 'name': 'x.dwg', 'linked': True, 'view_specific': False, 'unit': 'mm', 'bytes': 5, 'layers': 2, 'instances': 1}


def test_schedules_columns():
    sc = {'m_pFields': [{'obj': {'m_columnHeading': 'Level', 'm_hidden': 0, 'm_columnWidth': 0.5}}], 'm_categoryId': -2000023, 'm_sortFieldArr': [1], 'm_filterArr': [], 'm_headerSet': [{'m_caption': 'H'}]}
    f = {'m_viewName': 'Doors', 'm_pSchema': {'obj': sc}}
    d, _ = items.schedules(P({'DBViewSchedule': [{'id': 1, 'fields': f}], 'DBViewLegend': [{'id': 2, 'fields': {'m_viewName': 'L'}}]}))
    s = d['schedules'][0]
    assert s['columns'][0]['heading'] == 'Level' and s['category'] == 'Doors' and s['sort_fields'] == 1 and s['headers'] == ['H'] and d['legends'][0]['name'] == 'L'
