import os, tempfile, unittest
from rvtx import safepath as S


class NameBytes(unittest.TestCase):
    def test_multibyte_names_fit_a_file_system_component(self):
        d = tempfile.mkdtemp(); seen = set()
        for n in ['日' * 100, '😀' * 70, '日' * 85 + 'x', '日' * 85 + 'y', 'é' * 200, 'a' * 300]:
            s = S.safe_name(n)
            self.assertLessEqual(len((s + ' (99).rfa').encode()), 255)
            open(os.path.join(d, s + ' (99).rfa'), 'w').close()      # must not raise ENAMETOOLONG
            self.assertNotIn(s, seen); seen.add(s)                    # names differing only in the tail stay distinct

    def test_short_names_unchanged(self):
        self.assertEqual(S.safe_name('Door - Single'), 'Door - Single')
        self.assertEqual(S.safe_name('日本語'), '日本語')


def test_lone_surrogate_name_does_not_crash():
    from rvtx import safepath
    n = safepath.safe_name('Tag\ud800x')
    n.encode('utf-8')
    assert n.startswith('Tag')
