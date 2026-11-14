import unittest
from unittest import mock
from rvtx import items


class NoParentCategory(unittest.TestCase):
    def test_category_without_parent_does_not_drop_the_section(self):
        top = {'id': 4, 'fields': {'m_pCategory': {'m_name': 'Lines'}, 'm_gstyleIds': []}}
        thin = {'id': 5, 'fields': {'m_pCategory': {'m_name': 'Thin', 'm_parentCategoryId': -2002000}, 'm_gstyleIds': []}}
        rows = {'LinePatternElem': [], 'GStyleElem': [], 'CategoryElem': [top, thin]}
        with mock.patch.object(items, '_cls', side_effect=lambda prj, n: rows[n]), \
             mock.patch.object(items, 'sg', side_effect=lambda x: int(x)):
            out, _ = items.line_styles(object())
        self.assertEqual([e['name'] for e in out], ['Thin'])


if __name__ == '__main__':
    unittest.main()
