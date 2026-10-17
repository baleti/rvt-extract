"""Family manifest entries from the decoded project + embedded family docs."""
import json, os, collections
from . import RESEARCH
from .core import eid

_cat = json.load(open(os.path.join(RESEARCH, 'category_names.json')))
_par = json.load(open(os.path.join(RESEARCH, 'param_names.json')))


def sgn(v):
    v = eid(v)
    if v >= (1 << 63): return v - (1 << 64)
    return v - (1 << 32) if v >= (1 << 31) and v < (1 << 32) else v


def category_name(cid):
    v = sgn(cid)
    return _cat.get(str(v), 'Unknown(%d)' % v)


def param_name(pid, caps):
    v = eid(pid)
    if v in caps: return caps[v]
    return _par.get(str(sgn(v)), 'Param(%d)' % sgn(v))


def family_entry(prj, fam_rec, doc):
    f = fam_rec['fields']
    recs = doc['records'] if doc else {}
    l2p = doc['l2p'] if doc else {}
    caps = {}                                    # family-local id and project id -> caption
    params = []
    for pid, r in recs.items():
        if r['class'] == 'ParamElemFamily':
            d = r['fields']['m_pParamDef']['obj']
            caps[pid] = caps[r['A']] = d['m_caption']
            params.append({'name': d['m_caption'], 'id': r['A'], 'project_id': pid, 'instance': bool(r['fields'].get('m_instanceParam')),
                           'unit_type': d.get('m_unitType'), 'read_only': bool(d.get('m_readOnly')), 'description': r['fields'].get('m_description', '')})
    types = []
    pt = f.get('m_pFamilyTypes')
    for t in (pt['obj']['m_pairs'] if pt and pt.get('obj') else []):
        vals = {}
        for e in t['params'].get('m_params', []):
            nm = param_name(e['m_paramId'], caps)
            if e.get('m_str'): v = e['m_str']
            elif eid(e.get('m_elemId', 0xFFFFFFFF)) not in (0xFFFFFFFF, 0xFFFFFFFFFFFFFFFF): v = {'element_id': eid(e['m_elemId'])}
            elif e.get('m_value'): v = e['m_value']
            else: v = e.get('m_int', 0)
            vals[nm] = {'value': v, 'instance': bool(e.get('m_instance'))}
        types.append({'name': t['name'], 'values': vals})
    cls = collections.Counter(r['class'] for r in recs.values())
    return {
        'family_id': fam_rec['id'], 'name': f.get('m_name'), 'category': category_name(f['m_categoryId']),
        'category_id': sgn(f['m_categoryId']), 'omniclass': f.get('m_omniClassCode') or None,
        'in_place': bool(f.get('m_inPlace')), 'shared': bool(f.get('m_bShared')), 'host_based': bool(f.get('m_bIsHostBased')),
        'work_plane_based': bool(f.get('m_isWorkPlaneBased')), 'is_2d': bool(f.get('m_is2d')), 'parametric': bool(f.get('m_isParametric')),
        'source_path': f.get('m_path') or None, 'content_doc_guid': doc and doc['guid'], 'fam_doc_guid': f['m_famDocGUID']['m_guid'],
        'embedded_doc': bool(doc), 'embedded_records': len(recs), 'embedded_classes': dict(cls),
        'types': types, 'parameters': sorted(params, key=lambda p: p['name']),
    }
