"""Project-level content extractors. Each takes a core.Project and returns (json_data, [(relative_path, bytes)])."""
import json, re, io, zipfile, struct, collections
from .core import eid
from . import manifest

_BASE = {'m_pParamValueSetDouble', 'm_pParamValueSetInt', 'm_pParamValueSetAString', 'm_pParamValueSetElementId', 'm_geomSteps', 'm_pGeomTable', 'm_constrInfo',
         'm_docAccess', 'm_assocLevelId', 'm_famId', 'm_unplacedOwnerId', 'm_ownerDBViewId', 'm_createdPhaseId', 'm_demolishedPhaseId', 'm_designOptionId',
         'm_locked', 'm_moribund', 'm_dummy', 'm_cellList'}


def ob(o):
    return o.get('obj', o) if isinstance(o, dict) else o


def sg(v):
    return manifest.sgn(v)


def _cls(prj, c):
    return sorted(prj.by_class.get(c, []), key=lambda r: r['id'])


def fill_patterns(prj):
    out = []
    for r in _cls(prj, 'FillPatternElem'):
        p = ob(r['fields'].get('m_pFillPattern')) or {}
        out.append({'id': r['id'], 'name': p.get('m_name'), 'drafting': p.get('m_fpTarget') == 0, 'orientation': p.get('m_fpOrientation'),
                    'scale': p.get('m_scale'), 'grid_lines': [ob(g) for g in p.get('m_gridsArr', [])]})
    return out, []


def line_patterns(prj):
    out = []
    for r in _cls(prj, 'LinePatternElem'):
        p = ob(r['fields'].get('m_pLinePattern')) or {}
        out.append({'id': r['id'], 'name': p.get('m_name'), 'segments': [{'type': {0: 'dash', 1: 'space', 2: 'dot'}.get(s.get('m_type'), s.get('m_type')), 'length_ft': s.get('m_data')} for s in p.get('m_segs', [])]})
    return out, []


def shared_parameters(prj):
    """manifest + a Revit shared-parameter .txt (data type is the stored unit code: Revit's spec names are not recovered, TEXT where unknown)"""
    out = []
    for r in _cls(prj, 'ParamElemExternal'):
        if _scope(r['fields'])[0]: continue                  # shared parameter element of a loaded family's own document
        d = ob(r['fields'].get('m_pParamDef')) or {}
        g = r['fields'].get('m_externalParamKey', {}).get('m_guidValue', {}).get('m_guid')
        if not g: continue
        b = bytes.fromhex(g)
        guid = '%08x-%04x-%04x-%s-%s' % (int.from_bytes(b[0:4], 'little'), int.from_bytes(b[4:6], 'little'), int.from_bytes(b[6:8], 'little'), b[8:10].hex(), b[10:16].hex())
        out.append({'id': r['id'], 'guid': guid, 'name': d.get('m_caption'), 'unit_type': d.get('m_unitType'), 'group_id': sg(d.get('m_groupElemId', 0xFFFFFFFF)),
                    'visible': bool(d.get('m_userVisible', 1)), 'description': r['fields'].get('m_description', ''), 'user_modifiable': bool(r['fields'].get('m_userModifiable', 1)),
                    'bindings': [eid(b) for b in r['fields'].get('m_bindingIds', [])]})
    lines = ['# This is a Revit shared parameter file reconstructed by rvt-extract.', '*META\tVERSION\tMINVERSION', 'META\t2\t1', '*GROUP\tID\tNAME', 'GROUP\t1\tExtracted',
             '*PARAM\tGUID\tNAME\tDATATYPE\tDATACATEGORY\tGROUP\tVISIBLE\tDESCRIPTION\tUSERMODIFIABLE\tHIDEWHENNOVALUE']
    for p in sorted(out, key=lambda p: p['name'] or ''):
        lines.append('PARAM\t%s\t%s\tTEXT\t\t1\t%d\t%s\t%d\t0' % (p['guid'], p['name'], p['visible'], p['description'].replace('\t', ' '), p['user_modifiable']))
    return out, [('shared_parameters.txt', ('\r\n'.join(lines) + '\r\n').encode('utf-16le'))]


def project_parameters(prj):
    bind = {r['id']: r for r in _cls(prj, 'ParamBinding')}
    out = []
    for r in _cls(prj, 'ParamElemProject'):
        d = ob(r['fields'].get('m_pParamDef')) or {}
        cats = []; inst = None
        for b in r['fields'].get('m_bindingIds', []):
            br = bind.get(eid(b))
            if br:
                cats.append(manifest.category_name(br['fields']['m_categoryId'])); inst = bool(br['fields'].get('m_elemOrSymbol'))
        out.append({'id': r['id'], 'name': d.get('m_caption'), 'instance': inst, 'categories': sorted(set(cats)), 'unit_type': d.get('m_unitType')})
    return out, []


def filters(prj):
    out = []
    for r in _cls(prj, 'ParameterFilterElement'):
        if _scope(r['fields'])[0]: continue
        f = r['fields']; cr = ob(f.get('m_oCategoryRule')) or {}
        out.append({'id': r['id'], 'name': f.get('m_name'), 'categories': [manifest.category_name(c) for c in cr.get('m_categories', [])], 'rules': ob(f.get('m_oRuleCombination'))})
    return out, []


def phases(prj):
    out = {'phases': [r['fields'].get('m_name') for r in _cls(prj, 'ProjectPhase')],
           'phase_filters': [r['fields'].get('m_name') for r in _cls(prj, 'PhaseFilterElem')],
           'design_options': [{'id': r['id'], 'name': r['fields'].get('m_strName'), 'set_id': eid(r['fields'].get('m_DesignOptionSetId', 0))} for r in _cls(prj, 'DesignOption')]}
    return out, []


def _S(o, *path):
    for k in path:
        o = ob(o)
        if not isinstance(o, dict) or k not in o: return None
        o = o[k]
    return ob(o)


def _scope(f):
    """(family_internal, design_option) of an element: m_famId set = lives in a loaded family's document; m_designOptionId other than -1 = inside a design option (Revit's default collectors skip those)"""
    def v(k):
        x = f.get(k); x = getattr(x, 'v', x)
        return None if x is None else (x - (1 << 64) if x >= (1 << 63) else x - (1 << 32) if x >= (1 << 31) and x < (1 << 32) else x)
    return v('m_famId') not in (None, -1), v('m_designOptionId') not in (None, -1)


def levels_grids(prj):
    lv = []; gr = []
    for r in _cls(prj, 'Level'):
        fam, dopt = _scope(r['fields'])
        if fam: continue                     # family-internal level, not a project level
        lv.append({'id': r['id'], 'name': r['fields'].get('m_text', ''), 'elevation_ft': (_S(r['fields'], 'm_pSurface', 'm_origin') or [None] * 3)[2], 'design_option': dopt})
    lv.sort(key=lambda l: (l['elevation_ft'] is None, l['elevation_ft']))
    for r in _cls(prj, 'Grid'):
        fam, dopt = _scope(r['fields'])
        if not fam: gr.append({'id': r['id'], 'name': r['fields'].get('m_text', ''), 'design_option': dopt})
    rp = [{'id': r['id'], 'name': r['fields'].get('m_text', '')} for r in _cls(prj, 'RefPlane') if r['fields'].get('m_text') and not _scope(r['fields'])[0]]
    return {'levels': lv, 'grids': gr, 'named_reference_planes': rp}, []


def views(prj):
    """all views incl. view templates (m_isTemplate) and sheets with their placed views"""
    names = {r['id']: (r['fields'].get('m_text') or r['fields'].get('m_viewName') or r['fields'].get('m_name') or '') for rs in prj.by_class.values() for r in rs}
    vs = []; sheets = []
    for c, lst in prj.by_class.items():
        if not c.startswith('DBView'): continue
        for r in lst:
            f = r['fields']; n = f.get('m_viewName')
            if n is None: continue
            if c == 'DBViewDrafting' and f.get('m_sheetNumber'):
                sheets.append({'id': r['id'], 'number': f.get('m_sheetNumber'), 'name': n, 'issue_date': f.get('m_issueDate'), 'drawn_by': f.get('m_drawnBy'),
                               'checked_by': f.get('m_checkedBy'), 'designed_by': f.get('m_designedBy'), 'approved_by': f.get('m_approvedBy'),
                               'viewport_ids': [eid(v) for v in (f.get('m_sheetViewportElemIds') or [])]})
            else: vs.append({'id': r['id'], 'name': n, 'class': c, 'is_template': bool(f.get('m_isTemplate')), 'scale': f.get('m_scale')})
    vp = {r['id']: eid(r['fields'].get('m_dbViewId', -1)) for r in prj.by_class.get('Viewport', [])}
    for sh in sheets: sh['views'] = [names.get(vp[v], '') for v in sh.pop('viewport_ids') if v in vp]
    return {'views': sorted(vs, key=lambda v: (v['class'], v['name'])), 'sheets': sorted(sheets, key=lambda x: str(x['number']))}, []


def images(prj):
    out = []; files = []
    for r in _cls(prj, 'ImageHolder'):
        f = r['fields']; blob = ob(f.get('m_pRasterImage') or {}).get('m_compressedImage')
        nm = ob(f.get('m_symbolInfo') or {}).get('m_name') or 'image_%d' % r['id']
        if isinstance(blob, (bytes, bytearray)) and blob[:4] == b'\x89PNG' or isinstance(blob, (bytes, bytearray)) and blob[:2] == b'\xff\xd8':
            fn = 'images/%d_%s' % (r['id'], re.sub(r'[^\w.\- ]', '_', nm)); files.append((fn, bytes(blob))); out.append({'id': r['id'], 'name': nm, 'file': fn, 'bytes': len(blob)})
    return out, files


KINDS = {'fill_patterns': fill_patterns, 'line_patterns': line_patterns, 'shared_parameters': shared_parameters, 'project_parameters': project_parameters,
         'filters': filters, 'phases': phases, 'levels_grids': levels_grids, 'views': views, 'images': images}
