"""probe_del.py PROJECT GTROOT NAME : for each shared element of one family print project m_deletion, Revit's m_deletion and ours (remote-host)"""
import sys, os, re, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')); sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import rvtx
from rvtx import core, rfa, manifest, partition as PT, enc
import olefile, rvt2text as T
path, gtroot, nm = sys.argv[1:4]
def safe(s): return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', s or 'Unnamed').strip(' .') or 'Unnamed'
prj = core.Project(path); pd = rfa.ProjectDocs(prj); B = rfa.Builder(pd)
fr = next(r for r in prj.families() if r['fields'].get('m_name') == nm)
cat = manifest.category_name(fr['fields']['m_categoryId']); gt = os.path.join(gtroot, safe(cat), safe(nm) + '.rfa')
b = B.build(fr)
o = olefile.OleFileIO(gt); pn = [y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')][0]
rf = PT.parse_joined(T.joined(o.openstream(pn).read()), 8)[0]
H = {i: x for i, x in rf['H']}; R = {i: x for i, x, s in rf['R']}
def dec(body):
    tag = struct.unpack_from('<H', body, 0)[0]; return enc.decode_tree(pd.sch, 8, body, 2, tag, defined=(1, 2))[0]
def dl(body): return [int(x) for x in dec(body)['m_parents']['obj']['m_deletion']]
cls = lambda body: pd.sch.name(struct.unpack_from('<H', body, 0)[0])
print('fid', fr['id'])
c = collections.Counter()
for i in sorted(set(b.all_ids) & set(H)):
    if cls(R[i]) != 'GStyleElem': continue
    orig = dl(pd.doc0['H'][i]) if i in pd.doc0['H'] else None
    m = dl(b.H[i]); g = dl(H[i]); ok = m == g
    c[ok] += 1
    if c[ok] <= 6: print('OK ' if ok else 'BAD', i, 'project', orig, 'ours', m, 'revit', g)
print(c)
