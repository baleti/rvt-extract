"""Global/Latest (ADocument) of a family document from the project's Latest + the family's content-document blob + the final element set.
Verified against Revit-saved .rfa files (tools/lat_check.py)."""
import struct, copy
import rvtx  # noqa
from . import enc


def _int(x):
    return int(getattr(x, 'v', x))


def shift_handles(v):
    """blob handle numbering has the document at 2 (embedded), a root Latest has it at 1"""
    if isinstance(v, dict):
        if 'ref' in v and v['ref'] >= 2: v['ref'] -= 1
        if 'handle' in v and v['handle'] != 0xFFFFFFFF and v['handle'] >= 2: v['handle'] -= 1
        for x in v.values(): shift_handles(x)
    elif isinstance(v, list):
        for x in v: shift_handles(x)


def _entries(tree, sch):
    out = {}
    for s in tree['m_pAppInfoManager']['obj']['m_appInfoArr']:
        if 'ptr' in s: out.setdefault(sch.name(s['ptr']), s['obj'])
    return out


def build_tree(sch, proj, blob, ids, remap=None):
    """proj, blob: decoded ADocument trees; ids: set of ints = element ids of the final family document. returns the rfa Latest tree"""
    remap = remap or {}                       # project element id -> id in the family document (KeynoteTable, AssemblyCodeTable are re-created with new ids)
    rm = lambda x: remap.get(_int(x), _int(x))
    t = copy.deepcopy(blob); shift_handles(t)
    t['m_elemTable'] = {'null': 0}; t['m_pHistory'] = {'null': 0}
    P = _entries(proj, sch); notes = []
    for s in t['m_pAppInfoManager']['obj']['m_appInfoArr']:
        if 'ptr' not in s: continue
        name = sch.name(s['ptr']); E = s['obj']; Pe = P.get(name)
        if Pe is None or E is None: continue
        if name == 'DBDrawingInfo':
            E['m_horzRes'] = 800; E['m_vertRes'] = 600       # Revit writes these defaults into a saved family
        for k, v in list(E.items()):
            pv = Pe.get(k)
            if k == 'm_pADoc' or pv is None: continue
            if k == 'm_elemIdSet' and isinstance(v, list):
                own = {_int(x) for x in v}; add = {rm(x) for x in pv if rm(x) in ids}
                cls = type(pv[0]) if pv else (type(v[0]) if v else int)
                E[k] = [(cls(x) if cls is not int else x) for x in sorted(own | add)] if (own | add) else []
            elif k == 'm_gstyleData':
                have = {_int(x['m_gstyleId']) for x in v}
                E[k] = [x for x in pv if _int(x['m_gstyleId']) in ids and _int(x['m_gstyleId']) not in have] + list(v)
            elif name == 'ESSchemaStorage' and k in ('m_storedForgeSchemas', 'm_storedParameterSchemas'):
                E[k] = copy.deepcopy(pv)
            elif name == 'PropagationFilterData' and k == 'm_data':
                E[k] = copy.deepcopy(pv)
            elif name == 'ElemsSetWithCellsTracking' and k == 'm_elemIdSetMap':
                for ps in pv:
                    if not any(_int(x['first']) == _int(ps['first']) for x in v):
                        keep = [i for i in ps['second']['m_idSet'] if rm(i) in ids]
                        if keep: v.append(copy.deepcopy(ps))
                for x in v:
                    ps = next((y for y in pv if _int(y['first']) == _int(x['first'])), None)
                    if ps is not None:
                        cls = type(ps['second']['m_idSet'][0]) if ps['second']['m_idSet'] else int
                        x['second']['m_idSet'] = [cls(i) if cls is not int else i for i in sorted({rm(i) for i in ps['second']['m_idSet'] if rm(i) in ids})]
            elif name == 'UniqueElementsTracking' and k == 'm_elemIds':
                for i, (a, b) in enumerate(zip(v, pv)):
                    if rm(b) in ids and rm(b) != _int(b) and _int(a) == 0xFFFFFFFFFFFFFFFF: v[i] = type(a)(rm(b))
    return t, notes


def encode(sch, W, tag, tree):
    return struct.pack('<H', tag) + enc.Enc(sch, W).body(tag, tree) + b'\0\0\0\0'
