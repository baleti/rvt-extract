"""lift_cmp.py PROJECT GTROOT NAME[,NAME] : build families and compare items with Revit's own rfa (remote-host)"""
import sys, os, re, collections, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import rvtx
from rvtx import core, rfa, manifest, partition as PT, enc
import rvt_decode as D, fmt_parser as fp
from rvtfmt import inflate_stream
import olefile, rvt_scan as S
path, gtroot = sys.argv[1], sys.argv[2]; names = [x for a in sys.argv[3:] for x in a.split(',') if x]
def safe(s): return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', s or 'Unnamed').strip(' .') or 'Unnamed'
prj = core.Project(path); pd = rfa.ProjectDocs(prj); B = rfa.Builder(pd); NEG = (1 << 64) - 1
import rvt_scan, rvt2text as T
for nm in names:
    fr = next(r for r in prj.families() if r['fields'].get('m_name') == nm)
    cat = manifest.category_name(fr['fields']['m_categoryId']); gt = os.path.join(gtroot, safe(cat), safe(nm) + '.rfa')
    b = B.build(fr)
    o = olefile.OleFileIO(gt); pn = [y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')][0]
    j = T.joined(o.openstream(pn).read()); rf = PT.parse_joined(j, 8)[0]
    H = {i: x for i, x in rf['H']}; R = {i: x for i, x, s in rf['R']}; Z = {i: x for i, x, s in rf['Z']}
    mine_ids = set(b.all_ids); gt_ids = {i for i in H if i != NEG}
    cls = lambda body: pd.sch.name(struct.unpack_from('<H', body, 0)[0])
    print('==', nm, cat, 'ids mine', len(mine_ids), 'gt', len(gt_ids), 'only mine', len(mine_ids - gt_ids), 'only gt', len(gt_ids - mine_ids))
    om = sorted(mine_ids - gt_ids)[:10]; og = sorted(gt_ids - mine_ids)[:10]
    print('  only mine', [(i, cls(b.R[i][0])) for i in om]); print('  only gt', [(i, cls(R[i])) for i in og])
    st = collections.Counter(); bad = collections.defaultdict(list)
    for i in mine_ids & gt_ids:
        for k, a, c in (('H', b.H[i], H[i]), ('R', b.R[i][0], R[i]), ('Z', (b.Z.get(i) or (None,))[0], Z.get(i))):
            if a != c: st[k] += 1; bad[k].append(i)
    print('  diffs', dict(st))
    for k, v in bad.items(): print('   ', k, [(i, cls(R[i])) for i in v[:8]])
    from tdiff import walk_diff
    def dec(body):
        tag = struct.unpack_from('<H', body, 0)[0]; return enc.decode_tree(pd.sch, 8, body, 2, tag, defined=(1, 2))[0]
    for i in bad.get('R', [])[:3]:
        out = []; walk_diff(dec(b.R[i][0]), dec(R[i]), '', out); print('   R', i, cls(R[i]), [str(o)[:200] for o in out[:6]])
    for i in bad.get('H', [])[:3]:
        out = []; walk_diff(dec(b.H[i]), dec(H[i]), '', out); print('   H', i, cls(R[i]), [str(o)[:200] for o in out[:4]])
