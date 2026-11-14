"""Project-level content extractors. Each takes a core.Project and returns (json_data, [(relative_path, bytes)])."""
import json, re, io, zipfile, struct, collections, sys
from .core import eid
from . import manifest

_BASE = {'m_pParamValueSetDouble', 'm_pParamValueSetInt', 'm_pParamValueSetAString', 'm_pParamValueSetElementId', 'm_geomSteps', 'm_pGeomTable', 'm_constrInfo',
         'm_docAccess', 'm_assocLevelId', 'm_famId', 'm_unplacedOwnerId', 'm_ownerDBViewId', 'm_createdPhaseId', 'm_demolishedPhaseId', 'm_designOptionId',
         'm_locked', 'm_moribund', 'm_dummy', 'm_cellList'}


def ob(o):
    return o.get('obj', o) if isinstance(o, dict) else o


def sg(v):
    return None if v is None else manifest.sgn(v)   # absent id field (seen in real projects: schedule without category, category without parent) is None, not a crash that drops the section


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


def _sp_clean(v):
    """shared-parameter file is tab separated, one record per line: a tab or line break inside a name/description corrupts the record"""
    return re.sub(r'[\t\r\n\u2028\u2029\x0b\x0c\x85]+', ' ', str(v if v is not None else ''))


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
        lines.append('PARAM\t%s\t%s\tTEXT\t\t1\t%d\t%s\t%d\t0' % (p['guid'], _sp_clean(p['name']), p['visible'], _sp_clean(p['description']), p['user_modifiable']))
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
            fam, dopt = _scope(f)
            if fam: continue                                 # view of a loaded family's own document
            if c == 'DBViewDrafting' and f.get('m_sheetNumber'):
                sheets.append({'id': r['id'], 'number': f.get('m_sheetNumber'), 'name': n, 'issue_date': f.get('m_issueDate'), 'drawn_by': f.get('m_drawnBy'),
                               'checked_by': f.get('m_checkedBy'), 'designed_by': f.get('m_designedBy'), 'approved_by': f.get('m_approvedBy'),
                               'viewport_ids': [eid(v) for v in (f.get('m_sheetViewportElemIds') or [])]})
            else: vs.append({'id': r['id'], 'name': n, 'class': c, 'is_template': bool(f.get('m_isTemplate')), 'scale': f.get('m_scale'), 'design_option': dopt})
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


def schedules(prj):
    """schedule views: name, category, columns (heading, hidden, width) and sort field count; legends are listed by name"""
    out = []
    for r in _cls(prj, 'DBViewSchedule'):
        f = r['fields']; sc = ob(f.get('m_pSchema') or {}) or {}
        cols = [{'heading': ob(x).get('m_columnHeading'), 'hidden': bool(ob(x).get('m_hidden')), 'width_ft': ob(x).get('m_columnWidth')} for x in (sc.get('m_pFields') or [])]
        out.append({'id': r['id'], 'name': f.get('m_viewName'), 'is_template': bool(f.get('m_isTemplate')), 'category_id': sg(sc.get('m_categoryId')), 'category': manifest.category_name(sc.get('m_categoryId')) if sc.get('m_categoryId') is not None else '',
                    'columns': cols, 'sort_fields': len(sc.get('m_sortFieldArr') or []), 'filters': len(sc.get('m_filterArr') or []),
                    'headers': [h.get('m_caption') for h in (sc.get('m_headerSet') or []) if isinstance(h, dict)]})
    return {'schedules': out, 'legends': [{'id': r['id'], 'name': r['fields'].get('m_viewName'), 'components': None} for r in _cls(prj, 'DBViewLegend')]}, []


def revisions(prj):
    return [{'id': r['id'], 'sequence': r['fields'].get('m_sequenceNumber'), 'number': r['fields'].get('m_numberStr'), 'description': r['fields'].get('m_description'),
             'date': r['fields'].get('m_date'), 'issued_by': r['fields'].get('m_issuedBy'), 'issued_to': r['fields'].get('m_issuedTo'), 'issued': bool(r['fields'].get('m_issued'))}
            for r in sorted(_cls(prj, 'ProjectRevision'), key=lambda r: r['fields'].get('m_sequenceNumber') or 0)], []


def imports(prj):
    """imported / linked CAD files (MasterImportSymbol): name, link flag, unit, byte size, layer count"""
    out = []
    for r in _cls(prj, 'MasterImportSymbol'):
        f = r['fields']; st = f.get('m_importSettings') or {}
        out.append({'id': r['id'], 'name': ob(f.get('m_symbolInfo') or {}).get('m_name'), 'linked': bool(st.get('m_link')) if isinstance(st, dict) else None, 'view_specific': bool(st.get('m_viewSpecific')) if isinstance(st, dict) else None,
                    'unit': (f.get('m_unitTypeId') or {}).get('m_typeId') if isinstance(f.get('m_unitTypeId'), dict) else None, 'bytes': f.get('m_size'), 'layers': len(f.get('m_layerCategoryIdSet') or []),
                    'instances': len(f.get('m_parentIdSet') or [])})
    return out, []


def worksets(prj):
    """worksets of a workshared file (PartitionTable entries): id, name, kind (0 user workset, others standard/family/view), default visibility in new views"""
    sys.path.insert(0, manifest.RESEARCH)
    import rvt_worksets
    inv = set()
    for r in _cls(prj, 'WorksetVisibilitySettingsElem'):
        for g in r['fields'].get('m_invisibleWorksets') or []:
            v = (g.get('m_guid') or {}).get('m_guid') if isinstance(g, dict) else None
            if isinstance(v, (bytes, bytearray)): v = v.hex()
            if v: inv.add(str(v).lower())
    ws = rvt_worksets.worksets(prj.path, invisible=inv)
    allw = sorted(({'id': v['id'], 'guid': g, 'name': v['name'], 'kind': v['kind'], 'default_visible': v['default_visible']} for g, v in ws.items()), key=lambda w: w['id'])
    return {'user_worksets': [w for w in allw if w['kind'] == 0], 'other_entries': len(allw) - sum(1 for w in allw if w['kind'] == 0), 'note': 'kind 0 = user workset (verified against Revit WORKSET rows); other kinds are standard, family and view worksets, not listed'}, []


def line_styles(prj):
    """line styles = subcategories of the Lines category (parent -2002000): name, line pattern (name when defined in the file, else id), pen number (weight index), colour"""
    pats = {r['id']: r['fields'].get('m_text') or r['fields'].get('m_name') for r in _cls(prj, 'LinePatternElem')}
    gst = {r['id']: r for r in _cls(prj, 'GStyleElem')}; out = []
    for r in _cls(prj, 'CategoryElem'):
        c = ob(r['fields'].get('m_pCategory') or {}) or {}
        par = c.get('m_parentCategoryId')
        if par is None or sg(par) != -2002000: continue   # top-level categories have no parent id (a real 2020 project made sg(None) raise and dropped the whole section)
        e = {'id': r['id'], 'name': c.get('m_name'), 'pattern': None, 'pen_number': None, 'color_rgb': None}
        for gid in r['fields'].get('m_gstyleIds') or []:
            g = gst.get(int(gid))
            if g is None or g['fields'].get('m_gstyleType') != 1: continue
            o = ob(g['fields'].get('m_pGStyle') or {}) or {}; pid = sg(o.get('m_linePatternId'))
            e['pattern'] = pats.get(pid) or ('Solid' if pid == -3000010 else None) or ('builtin %d' % pid if pid is not None else None); e['pen_number'] = o.get('m_penNumber')
            col = o.get('m_color')
            if isinstance(col, int): e['color_rgb'] = [col & 255, (col >> 8) & 255, (col >> 16) & 255]
        out.append(e)
    return out, []


KINDS = {'fill_patterns': fill_patterns, 'line_patterns': line_patterns, 'shared_parameters': shared_parameters, 'project_parameters': project_parameters,
         'filters': filters, 'phases': phases, 'levels_grids': levels_grids, 'views': views, 'images': images, 'schedules': schedules, 'revisions': revisions, 'cad_imports': imports, 'worksets': worksets, 'line_styles': line_styles}
