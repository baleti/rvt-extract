import csv, stat, struct, argparse, gc, json, os, re, sys, time
from . import core, manifest, items, files, safepath, knownbad

KINDS = ['families'] + list(items.KINDS) + list(files.KINDS)
HELP = {'families': 'every family: manifest entry (category, types, parameters, embedded-record census); .rfa when validation passes',
        'fill_patterns': 'fill patterns (drafting/model, grid lines)', 'line_patterns': 'line patterns (dash/space/dot segments)',
        'shared_parameters': 'shared parameters as manifest + shared_parameters.txt', 'project_parameters': 'project parameters with category bindings',
        'filters': 'view filters (categories, rules)', 'phases': 'phases, phase filters, design options', 'levels_grids': 'levels with elevations, grids, named reference planes',
        'views': 'views, view templates, sheets with placed views', 'images': 'embedded raster images (PNG/JPEG blobs)', 'project_info': 'file/build info, project information, preview.png',
        'links': 'external file references (links, keynote tables) from TransmissionData', 'schedules': 'schedule views (columns, headers, category) and legend names', 'revisions': 'project revisions', 'line_styles': 'line styles (pattern, pen number, colour)', 'worksets': 'worksets (id, name, kind, default visibility)', 'cad_imports': 'imported/linked CAD files (name, units, size, layers)', 'materials': 'materials with appearance assets and textures (paths)'}


VALIDATION = {'2024': 'validated: opens in Revit 2024, facts equal to EditFamily+SaveAs (Snowdon 177/177, office project 100/100)',
              '2025': 'validated: opens in Revit 2026 (upgrade open): 57 of 57 sampled office-project families incl. nested, and 232 of 232 Snowdon Structural 2025 families; counts equal to Revit 2026 EditFamily+SaveAs on 138 of 138 compared',
              'old': 'Revit 2017-2023 files (4-byte element ids): flat and nested families open in Revit 2024 after its upgrade (Autodesk sample projects 2017, 2018, 2019, 2020, 2021, 2022, 2023: 52 of 52 each, see README)',
              'older': 'Revit 2016 files: partition layout verified against a real 2016 family but no project to test with; not validated',
              '2026': 'streams byte-identical to Revit 2026 output for tested families; Snowdon 2026 sample opens in Revit 2026 (177 of 177)'}


def catalog_cell(v):
    """type catalog .txt has no quoting: a comma or line break inside a name or value would add columns or rows"""
    return re.sub(r'[,\r\n\u2028\u2029\x0b\x0c\x85]', ' ', str(v))


def csv_cell(v):
    """spreadsheet formula injection: a family name such as =HYPERLINK(...) or @SUM(...) would run when families.csv is opened in Excel; neutralise with a leading apostrophe (text cells only)"""
    return "'" + v if isinstance(v, str) and v[:1] in ('=', '+', '-', '@', '\t', '\r') else v


def write_families_csv(path, families):
    """one row per family for auditing / standards checks; known_bad is the last column"""
    with open(path, 'w', newline='', encoding='utf-8', errors='replace') as fh:
        w = csv.writer(fh); w.writerow(['category', 'name', 'types', 'parameters', 'shared', 'in_place', 'embedded_records', 'nested', 'nested_families', 'rfa_status', 'rfa_file', 'validation', 'known_bad'])
        for e in families:
            r = e.get('rfa') or {}
            w.writerow([csv_cell(c) for c in [e['category'], e['name'], len(e['types']), len(e['parameters']), e.get('shared'), e.get('in_place'), e['embedded_records'], r.get('nested', ''), '; '.join(r.get('nested_families') or []), r.get('status', 'no-embedded-doc' if not e['embedded_doc'] else ''), r.get('file', ''), r.get('validation', ''), r.get('known_bad', '')]])


def family_source_warning(path, nfam):
    """a .rfa/.rft fed in as the source holds no family table: 0 families is expected there, say so instead of a silent empty result"""
    if nfam == 0 and os.path.splitext(path)[1].lower() in ('.rfa', '.rft'):
        return 'WARNING: %s looks like a family document, not a project; it contains no embedded families, so 0 were extracted (rvt-extract reads .rvt/.rte projects)' % os.path.basename(path)


def pre2017_refused(fmt, experimental):
    """2016 (and older) projects: .rfa only with --experimental; an unknown format is never treated as old"""
    return str(fmt).isdigit() and int(fmt) < 2017 and not experimental


def known_bad_files(families):
    """relative paths of written .rfa whose manifest entry carries known_bad"""
    return sorted((e['rfa'].get('file') or '') for e in families if (e.get('rfa') or {}).get('known_bad') and e['rfa'].get('status') == 'written')


def safe(s):
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', s or 'Unnamed').strip(' .') or 'Unnamed'


def source_damage(path, x=None):
    """{stream: damaged gzip members} for the project's Partitions/* and Global/* streams. Uses x['damaged'] when the reader provided it, else checks the file itself (the reader's cache/lowmem paths do not always report it)."""
    d = dict((x or {}).get('damaged') or {})
    if d: return d
    try:
        import olefile
        from . import core
        o = olefile.OleFileIO(path)
        for st in o.listdir():
            n = '/'.join(st)
            if n.startswith(('Partitions/', 'Global/')):
                k = core.T.damaged_members(o.openstream(st).read())
                if k: d[n] = k
    except Exception as e:
        d['(damage check failed)'] = '%s: %s' % (type(e).__name__, e)
    return d


def _fingerprint(path, limit=4 << 30):
    """sha1 of the whole source (None when unreadable or above limit): size+mtime can be restored by an in-place edit, content cannot"""
    try:
        import hashlib
        if os.path.getsize(path) > limit: return None
        h = hashlib.sha1()
        with open(path, 'rb') as f:
            for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
        return h.hexdigest()
    except OSError: return None


def exit_status(changed, src_damaged, families):
    """(code, [stderr lines]); 0 ok, 3 damaged source (family list may be incomplete), 4 source changed while read, 5 an rfa could not be written; when several apply the code is 4, then 5, then 3 and every message is still printed"""
    msgs = []; code = 0
    bad = [e for e in families if (e.get('rfa') or {}).get('status') == 'error']
    io_bad = [e for e in families if str((e.get('rfa') or {}).get('error', '')).startswith(('OSError', 'FileNotFoundError', 'PermissionError', 'IsADirectoryError'))]
    emb = [e for e in families if e.get('embedded_doc')]
    emb_bad = [e for e in emb if (e.get('rfa') or {}).get('status') == 'error']
    if emb and len(emb_bad) * 10 > len(emb):      # exit code stays 0 (per-family errors are manifest rows) but a mass failure must not pass quietly
        msgs.append('WARNING: %d of %d families with an embedded document could not be written (rfa.status error); this looks like a failed run (memory cap? damaged source?), do not trust the output' % (len(emb_bad), len(emb)))
    if src_damaged and set(src_damaged) == {'(damage check failed)'}:
        msgs.append('ERROR: the damage check could not run, so the source is unverified (not known to be damaged); output not trusted, exit code 3 (use a matching RVT_RESEARCH)'); code = 3
    elif src_damaged:
        msgs.append('ERROR: source has damaged gzip members: %d family(ies) failed, the family list itself may be incomplete; exit code 3' % len(bad)); code = 3
    if io_bad:
        msgs.append('ERROR: %d rfa could not be written (I/O error, e.g. disk full); exit code 5' % len(io_bad)); code = 5
    if changed:
        msgs.append('ERROR: the source file changed while it was being read (size, mtime or content differ); outputs may mix two versions, discard the output and run again; exit code 4'); code = 4
    return code, msgs


def sweep_orphan_tmp(root):
    """remove name.rfa.tmpPID / name.json.tmpPID left by a killed run (PID no longer alive); returns the removed paths"""
    gone = []
    for dp, _, fns in os.walk(root):
        for fn in fns:
            m = re.search(r'\.(?:rfa|json)\.tmp(\d+)$', fn)
            if not m: continue
            try: os.kill(int(m.group(1)), 0); continue      # owner alive (or not ours): leave it
            except ProcessLookupError: pass
            except OSError: continue
            try: os.unlink(os.path.join(dp, fn)); gone.append(os.path.join(dp, fn))
            except OSError: pass
    return gone


_LOCKS = []; _LOCKED = set()


def out_unwritable(out):
    """reason string when --out cannot be created or written (nearest existing ancestor is no writable directory), else None; creates nothing"""
    d = os.path.abspath(out)
    if os.path.lexists(d): return None      # existing --out (dir, file, symlink): the later guards give their own specific message
    while not os.path.lexists(d):
        d = os.path.dirname(d)
    if not os.path.isdir(d): return None      # an ancestor that is a file: the later guard words that
    if not os.access(d, os.W_OK | os.X_OK): return 'cannot write in %s' % d
    return None


def _lock_out(out):
    if out in _LOCKED: return
    _LOCKED.add(out)
    """Advisory lock on --out for the life of the process: two concurrent runs into one folder would overwrite each other's manifest and the first finisher would clear INCOMPLETE under the second."""
    try: import fcntl
    except ImportError: return      # Windows: no flock, skipped
    os.makedirs(out, exist_ok=True); fh = open(os.path.join(out, '.rvtx.lock'), 'a')
    try: fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.stderr.write('rvt-extract: another extraction is already running into %s\n' % out); raise SystemExit(2)
    _LOCKS.append(fh)


def _digest(fn):
    import hashlib
    h = hashlib.sha256(); n = 0
    with open(fn, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c); n += len(c)
    return {'sha256': h.hexdigest(), 'bytes': n}


def _finite(o):
    """non-finite floats become the strings 'NaN' / 'Infinity' / '-Infinity' so the file stays strict JSON"""
    if isinstance(o, float) and (o != o or o in (float('inf'), float('-inf'))): return 'NaN' if o != o else ('Infinity' if o > 0 else '-Infinity')
    if isinstance(o, dict): return {k: _finite(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [_finite(v) for v in o]
    return o


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try: text = json.dumps(data, indent=1, default=str, allow_nan=False)
    except ValueError: text = json.dumps(_finite(data), indent=1, default=str, allow_nan=False)      # NaN/Infinity are not JSON: strict readers (JS, jq) reject the whole manifest
    tmp = path + '.tmp%d' % os.getpid()      # atomic: the manifest is what marks known-bad / error families, never leave it truncated
    try:
        with open(tmp, 'w', encoding='utf-8') as fh: fh.write(text); fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def nested_params_types(B, kn, t):
    """parameters and types of a nested family from its document's ParamElemFamily records and the nested Family record"""
    from .core import eid
    caps = {}; params = []
    for i, b, *_ in B.pd.docs[kn]['R'][:-1]:
        if B.class_of(b) != 'ParamElemFamily': continue
        f = B.dec_loose(b)[1]; d = f['m_pParamDef']['obj']; caps[i] = d['m_caption']
        params.append({'name': d['m_caption'], 'project_id': i, 'instance': bool(f.get('m_instanceParam')), 'spec': ((d.get('m_specTypeId') or {}).get('m_typeId') if isinstance(d.get('m_specTypeId'), dict) else None) or None, 'read_only': bool(d.get('m_readOnly'))})
    types = []; pt = t.get('m_pFamilyTypes')
    for ty in (pt['obj']['m_pairs'] if pt and pt.get('obj') else []):
        vals = {}
        for e in ty['params'].get('m_params', []):
            nm = manifest.param_name(e['m_paramId'], caps)
            v = e['m_str'] if e.get('m_str') else {'element_id': eid(e['m_elemId'])} if eid(e.get('m_elemId', 0xFFFFFFFF)) not in (0xFFFFFFFF, 0xFFFFFFFFFFFFFFFF) else e['m_value'] if e.get('m_value') else e.get('m_int', 0)
            vals[nm] = {'value': v, 'instance': bool(e.get('m_instance'))}
        types.append({'name': ty['name'], 'values': vals})
    return sorted(params, key=lambda q: q['name']), types


def mem_warning(size, avail, lowmem):
    """Heuristic (one measured sample: 28 MB rvt peaked at 1.9 GB RSS, ~67x): warn when available memory is below 80x the file size. A native allocation failure aborts with rc 134 and no message."""
    if avail is None or size * 80 <= avail: return None
    return 'warning: %.0f MB source, %.0f MB memory available (about 80x the file size is needed); the read may abort with "memory allocation failed" (rc 134)%s' % (size / 1e6, avail / 1e6, '' if lowmem else ', try --low-memory (families only)')

def mem_available():
    try:
        for l in open('/proc/meminfo'):
            if l.startswith('MemAvailable:'): return int(l.split()[1]) * 1024
    except OSError: pass
    return None

_OUT_DIR = [None]


def safe_stdio():
    """under LANG=C (cron, systemd) stdout/stderr are ASCII and printing a CJK family name raised UnicodeEncodeError in the middle of a run: never fail on a log line"""
    for st in (sys.stdout, sys.stderr):
        try: st.reconfigure(errors='backslashreplace')
        except Exception: pass


def main(argv=None):
    safe_stdio()
    try:
        return _main(argv)
    except MemoryError:
        sys.stderr.write('rvt-extract: out of memory while reading the project (about 80x the file size is needed); try --low-memory (families only) or a host with more memory. Any output folder is incomplete (families/INCOMPLETE stays if present)\n'); return 6
    except KeyboardInterrupt:
        # Ctrl-C mid-run: no traceback; families/INCOMPLETE (written at start) stays, a half-written rfa is only ever a tmp file
        sys.stderr.write('rvt-extract: interrupted; the output folder is incomplete (families/INCOMPLETE stays), do not use it\n'); return 130
    except ValueError as e:
        # truncated / corrupt source: fail loudly, cleanly, nothing marked ok
        sys.stderr.write('rvt-extract: cannot read source: %s\n' % e); return 2
    except OSError as e:
        import errno
        if e.errno == errno.ENAMETOOLONG:
            sys.stderr.write('rvt-extract: a path is too long for this filesystem (%s); nothing usable written, choose a shorter --out\n' % e.filename); return 2
        if e.errno not in (errno.ENOSPC, errno.EFBIG, errno.EDQUOT, errno.EROFS, errno.EIO, errno.EACCES): raise
        # disk full / quota / size cap / read-only medium while writing output: loud, specific code, partial output is not a finished extraction
        try:      # the run may have cleared the marker before the failing write: put it back so the message is true
            if _OUT_DIR[0]: open(os.path.join(_OUT_DIR[0], safepath.INCOMPLETE), 'w').write('write failed (%s); output unusable\n' % e)
        except OSError: pass
        sys.stderr.write('rvt-extract: cannot write output (%s); the output folder is incomplete (families/INCOMPLETE stays), do not use it\n' % e); return 5
    except (TypeError, AttributeError) as e:
        if 'unexpected keyword argument' not in str(e) and 'has no attribute' not in str(e): raise
        sys.stderr.write('rvt-extract: the research library in RVT_RESEARCH (%s) does not match this version of rvt-extract (%s); use a matching checkout, or drop --low-memory\n' % (os.environ.get('RVT_RESEARCH', '~/rvt-research'), e)); return 2


def _main(argv=None):
    ap = argparse.ArgumentParser(prog='rvt-extract', description='Extract families and other content from a Revit project without Revit.')
    ap.add_argument('rvt', nargs='?'); ap.add_argument('--out', default=None, help='output folder')
    ap.add_argument('--only', default=None, help='comma list of output types (see --list-kinds): ' + ','.join(KINDS))
    ap.add_argument('--no-rfa', action='store_true', help='families: only the manifest, do not assemble .rfa files')
    ap.add_argument('--experimental', action='store_true', help='also write .rfa for Revit 2016 files (not validated)')
    ap.add_argument('--low-memory', action='store_true', help='families only: decode just the classes family lifting needs (100+ MB projects fit in a few GB)')
    ap.add_argument('--match', default=None, help='families: only those whose name or category matches this regular expression (case-insensitive)')
    ap.add_argument('--list', action='store_true', help='print what the file contains and exit')
    ap.add_argument('--list-kinds', action='store_true', help='print the output types and exit')
    a = ap.parse_args(argv)
    if a.out and not a.list:
        why_ = out_unwritable(a.out)
        if why_: print('ERROR: --out %s: %s; nothing written' % (a.out, why_), file=sys.stderr); return 2
    if a.match:
        try: re.compile(a.match)
        except re.error as ex: print('ERROR: --match is not a valid regular expression (%s); nothing written' % ex, file=sys.stderr); return 2
    if a.list_kinds:
        for k in KINDS: print('%-20s %s' % (k, HELP.get(k, '')))
        return 0
    if not a.rvt: ap.error('rvt file required')
    if a.out and not a.list:
        ro, rr = os.path.realpath(a.out), os.path.realpath(a.rvt)
        if os.path.islink(a.out.rstrip('/')) and not os.path.isdir(a.out): ap.error('--out is a symlink that does not lead to a directory: %s' % a.out)
        if os.path.isfile(ro): ap.error('--out must be a directory, not an existing file: %s' % a.out)
        if ro == rr: ap.error('--out must not be the input file')
        anc = os.path.dirname(ro)
        while anc and not os.path.exists(anc) and anc != os.path.dirname(anc): anc = os.path.dirname(anc)
        if anc and os.path.exists(anc) and not os.path.isdir(anc): ap.error('--out is below an existing file (%s); nothing written' % os.path.basename(anc))
    only = [k.strip() for k in a.only.split(',')] if a.only else KINDS
    bad = [k for k in only if k not in KINDS]
    if bad: ap.error('unknown output type(s): %s' % ','.join(bad))
    t0 = time.time()
    if not os.path.exists(a.rvt):
        print('ERROR: %s does not exist; nothing written' % a.rvt, file=sys.stderr); return 2
    if not stat.S_ISREG(os.stat(a.rvt).st_mode) and not os.path.isdir(a.rvt):
        print('ERROR: %s is not a regular file (pipe, device or socket); nothing written' % a.rvt, file=sys.stderr); return 2
    fp0 = _fingerprint(a.rvt)
    st0 = os.stat(a.rvt); sig0 = (st0.st_size, st0.st_mtime_ns)      # a save into the source while we read it would give a torn read: compare again at the end
    w_ = mem_warning(st0.st_size, mem_available(), a.low_memory)
    if w_: print(w_, file=sys.stderr)
    try:
        prj = core.Project(a.rvt, lowmem=a.low_memory and only == ['families'])
    except Exception as ex:
        if type(ex).__module__.startswith('olefile') or isinstance(ex, (OSError, struct.error)):
            print('ERROR: cannot read %s as a Revit project (%s: %s); nothing written' % (a.rvt, type(ex).__name__, ex), file=sys.stderr); return 2
        raise
    log = []
    src_damaged = source_damage(a.rvt, getattr(prj, 'x', None))      # {partition: damaged gzip members}: some families may fail or be incomplete because of this, not because they lack content
    if src_damaged:
        if '(damage check failed)' in src_damaged:
            msg = 'WARNING: the damage check could not run (%s); the source is NOT known to be damaged, usually the research tree lacks rvt2text.damaged_members (use a matching RVT_RESEARCH)' % src_damaged['(damage check failed)']
        else:
            msg = 'WARNING: source has damaged gzip member(s) %s; families that fail below may be victims of this damage' % dict(src_damaged)
        log.append(msg); print(msg, file=sys.stderr)
    res = {}
    if 'families' in only:
        docs, st = core.scan_family_docs(prj)
        ents = []
        for fr in sorted(prj.families(), key=lambda r: r['fields'].get('m_name') or ''):
            if fr['fields'].get('m_name') and (not a.match or re.search(a.match, fr['fields']['m_name'] + ' ' + (manifest.family_entry(prj, fr, docs.get(fr['id']))['category'] or ''), re.I)): ents.append(manifest.family_entry(prj, fr, docs.get(fr['id'])))
        res['families'] = ents
        w_ = family_source_warning(a.rvt, len(ents))
        if w_: log.append(w_); print(w_, file=sys.stderr)
        if a.list or not a.out:
            for e in ents: print('%-28s %-50s types=%-3d params=%-3d records=%d' % (e['category'], e['name'], len(e['types']), len(e['parameters']), e['embedded_records']))
    if 'families' in only and a.out and not a.no_rfa and not a.list:
        from . import rfa as RFA
        pre_rfa = set(safepath.stale_rfa(a.out, []))      # .rfa already in --out before this run: any of them rewritten below was silently replaced
        pd = RFA.ProjectDocs(prj); B = RFA.Builder(pd); byid = {e['family_id']: e for e in res['families']}; namer = safepath.Namer()
        ncp = 0; _lock_out(a.out); safepath.mark_incomplete(a.out); _OUT_DIR[0] = a.out      # marker stays until the final manifest is written: a killed run is recognisable
        for fr in prj.families():
            e = byid.get(fr['id'])
            if e is None: continue
            if not e['embedded_doc']:
                e['rfa'] = {'status': 'no_embedded_doc', 'note': 'the project holds no family document for this family (curtain panel/mullion, in-place element, system family); nothing to extract'}; continue
            ncp += 1
            if True: write_json(os.path.join(a.out, 'families', 'manifest.json'), res['families'])      # checkpoint: a killed run (OOM) still leaves a manifest next to the files it wrote
            old_fmt = str(pd.fmt).isdigit() and int(pd.fmt) < 2024
            if pre2017_refused(pd.fmt, a.experimental):
                e['rfa'] = {'status': 'skipped', 'validation': VALIDATION['older'] + '; use --experimental to write anyway'}; continue
            try:
                B.build(fr)
                cat_, stem_ = safepath.rfa_target(a.out, e['category'], e['name']); d = os.path.join(a.out, 'families', cat_); os.makedirs(d, exist_ok=True); fn = os.path.join(d, namer.take(d, stem_, '.rfa'))
                B.write(fn, e['name'], e['category']); B.last_trees = None; gc.collect(); nd = B.nested_docs(B.k); nest = bool(nd); e['rfa'] = {'nested': nest, 'nested_depth': B.nested_depth(B.k) if nest else 0, 'nested_families': B.nested_names(B.k) if nd else [], 'file': os.path.relpath(fn, a.out), 'status': 'written', 'validation': (VALIDATION.get(str(pd.fmt), (VALIDATION['older'] if int(pd.fmt) < 2017 else VALIDATION['old']) if old_fmt else 'experimental: this Revit format is not validated yet (see RESULTS.md)'))}; knownbad.mark(e['rfa'], pd.fmt, e['category'], e['name'], a.experimental); e['rfa'].update(_digest(fn)); getattr(B, 'risk', None) and e['rfa'].setdefault('risk_note', B.risk)
            except Exception as ex:
                e['rfa'] = {'status': 'error', 'error': '%s: %s' % (type(ex).__name__, ex)}; log.append('%s: rfa failed: %s' % (e['name'], ex))
                if os.environ.get('RVTX_TB'): import traceback; traceback.print_exc()
        # families that exist only as nested documents inside other families (not loaded in the project itself): extract them standalone too
        if not (pre2017_refused(pd.fmt, a.experimental)):
            have = {e['content_doc_guid'] for e in res['families'] if e.get('content_doc_guid')}; todo = [(fr['id'], B.pd.family_doc_index(fr), e['name']) for fr in prj.families() for e in [byid.get(fr['id'])] if e and e['embedded_doc'] and e.get('rfa', {}).get('status') == 'written']
            seen = set()
            while todo:
                _, k, parent = todo.pop()
                for i, b, *_ in pd.docs[k]['R'][:-1]:
                    if B.class_of(b) != 'Family': continue
                    t = B.dec_loose(b)[1]; fd = t.get('m_oFamDoc')
                    if not (isinstance(fd, dict) and 'obj' in fd and t.get('m_name')): continue
                    g_ = fd['obj']['m_contentDocGUID']['m_guid']
                    if g_ in have or g_ in seen: continue
                    seen.add(g_); kn_ = B.pd.family_doc_index({'fields': t})
                    if kn_: todo.append((i, kn_, t['m_name']))
                    if a.match and not re.search(a.match, t['m_name'], re.I): continue
                    cat = manifest.category_name(t['m_categoryId']); ne = {'family_id': i, 'name': t['m_name'], 'category': cat, 'category_id': manifest.sgn(t['m_categoryId']), 'origin': 'nested in ' + parent, 'content_doc_guid': g_, 'embedded_doc': True, 'embedded_records': len(pd.docs[kn_]['H']) - 1 if kn_ else 0, 'types': [], 'parameters': []}
                    try: ne['parameters'], ne['types'] = nested_params_types(B, kn_, t)
                    except Exception as ex: log.append('%s: nested manifest failed: %s' % (t['m_name'], ex))
                    try:
                        B.build({'id': i, 'fields': t})
                        cat_, stem_ = safepath.rfa_target(a.out, cat, t['m_name']); d = os.path.join(a.out, 'families', cat_); os.makedirs(d, exist_ok=True); fn = os.path.join(d, namer.take(d, stem_, '.rfa'))
                        B.write(fn, t['m_name'], cat); B.last_trees = None; gc.collect(); nd = B.nested_docs(B.k)
                        ne['rfa'] = {'nested': bool(nd), 'nested_depth': B.nested_depth(B.k) if nd else 0, 'nested_families': B.nested_names(B.k) if nd else [], 'file': os.path.relpath(fn, a.out), 'status': 'written', 'validation': 'standalone copy of a family nested inside "%s"; ' % parent + (VALIDATION.get(str(pd.fmt)) or 'experimental')}; knownbad.mark(ne['rfa'], pd.fmt, cat, t['m_name'], a.experimental); ne['rfa'].update(_digest(fn)); getattr(B, 'risk', None) and ne['rfa'].setdefault('risk_note', B.risk)
                    except Exception as ex:
                        ne['rfa'] = {'status': 'error', 'error': '%s: %s' % (type(ex).__name__, ex)}; log.append('%s: nested rfa failed: %s' % (t['m_name'], ex))
                    res['families'].append(ne)
    for k in only:
        if k == 'families': continue
        try:
            fn = items.KINDS.get(k)
            data, fl = fn(prj) if fn else files.KINDS[k](a.rvt)
            res[k] = (data, fl)
        except Exception as e:
            log.append('%s: FAILED %s: %s' % (k, type(e).__name__, e)); res[k] = ([], [])
    summary = {k: (len(v) if k == 'families' else len(v[0]) if hasattr(v[0], '__len__') else 1) for k, v in res.items()}
    print('; '.join('%s=%s' % kv for kv in summary.items()) + ' (%.1fs)' % (time.time() - t0), file=sys.stderr)
    for l in log: print(l, file=sys.stderr)
    if a.list or not a.out: return 0
    _lock_out(a.out); os.makedirs(a.out, exist_ok=True); sweep_orphan_tmp(a.out)
    man = {'source': os.path.abspath(a.rvt), 'outputs': summary, 'errors': log}
    if src_damaged: man['source_damaged'] = dict(src_damaged)
    if 'families' in res:
        man['families'] = res['families']
        if any(k != '(damage check failed)' for k in src_damaged):      # a check that could not run proves nothing: no per-family damage claim
            for e in res['families']:
                r = e.get('rfa') or {}
                if r.get('status') == 'error': r['likely_cause'] = 'source_damaged'
                elif r.get('status') == 'written': r['from_damaged_source'] = True      # lifted, but the project file had damaged members: not proven identical to an undamaged lift      # the failure text alone (e.g. 'no embedded document') hides that the project file itself is damaged
        write_json(os.path.join(a.out, 'families', 'manifest.json'), res['families']); safepath.clear_incomplete(a.out)
        stale = safepath.stale_rfa(a.out, res['families'])
        bad = known_bad_files(res['families'])
        if bad:
            man['known_bad_rfa'] = bad
            msg = 'WARNING: %d written .rfa are on the known-bad list (Revit rejects them): %s; see rfa.known_bad in the manifest' % (len(bad), '; '.join(bad[:5]) + (' ...' if len(bad) > 5 else '')); log.append(msg); print(msg, file=sys.stderr)
        over = sorted(locals().get('pre_rfa', set()) & {os.path.normpath((e.get('rfa') or {}).get('file', '')) for e in res['families'] if e.get('rfa')})
        if over:
            man['overwritten_rfa'] = over
            msg = 'WARNING: %d .rfa file(s) from an earlier run in %s were overwritten by this run; use an empty --out' % (len(over), a.out); log.append(msg); print(msg, file=sys.stderr)
        if stale:      # leftovers of an earlier run in the same --out: not in this manifest, so never trust them as this run's output
            man['stale_rfa_not_in_manifest'] = stale
            msg = 'WARNING: %d .rfa file(s) in %s are not in this run\'s manifest (left over from an earlier run); use an empty --out' % (len(stale), a.out); log.append(msg); print(msg, file=sys.stderr)
        import csv
        for e in res['families']:      # type catalogue (Revit family type catalog .txt: ,Param##type##unit headers, one row per type); only named, non-element-id values
            if not e['types']: continue
            cols = sorted({k for t in e['types'] for k, v in t['values'].items() if not k.startswith('Param(') and not isinstance(v['value'], dict) and not v.get('instance')})
            spec = {q['name']: (q.get('spec') or '') for q in e['parameters']}
            CT = {'length': '##length##feet', 'number': '##number##general', 'angle': '##angle##radians', 'area': '##area##squarefeet', 'volume': '##volume##cubicfeet'}
            ctype = lambda c: next((v for k, v in CT.items() if ':%s-' % k in spec.get(c, '')), '##other##')      # values are Revit internal units: feet, radians
            rf = (e.get('rfa') or {}).get('file')      # Revit looks for the catalog next to the .rfa with the same base name
            base = os.path.join(a.out, os.path.splitext(rf)[0]) if rf else os.path.join(a.out, 'families', safepath.safe_name(e['category']), safepath.safe_name(e['name']))
            os.makedirs(os.path.dirname(base), exist_ok=True)
            with open(base + '.txt', 'w', encoding='utf-8', errors='replace') as fh:
                fh.write(','.join([''] + [catalog_cell(c) + ctype(c) for c in cols]) + '\n')
                for t in e['types']: fh.write(','.join([catalog_cell(t['name'])] + [catalog_cell(t['values'].get(c, {}).get('value', '')) for c in cols]) + '\n')
        import csv
        write_families_csv(os.path.join(a.out, 'families', 'families.csv'), res['families'])
    for k, v in res.items():
        if k == 'families': continue
        data, fl = v
        write_json(os.path.join(a.out, k, k + '.json'), data)
        for rel, b in fl:
            fp = os.path.join(a.out, k, rel); os.makedirs(os.path.dirname(fp), exist_ok=True); open(fp, 'wb').write(b)
    write_json(os.path.join(a.out, 'manifest.json'), man)
    open(os.path.join(a.out, 'extract.log'), 'w', encoding='utf-8', errors='replace').write('\n'.join(log) + '\n')
    st1 = os.stat(a.rvt)
    changed = (st1.st_size, st1.st_mtime_ns) != sig0
    if not changed and fp0 is not None and _fingerprint(a.rvt) != fp0:
        changed = True; log.append('source content changed during the run with size and mtime restored')
    if not changed and not src_damaged:      # size+mtime can be restored by an in-place edit: when families fail en masse, re-check the content
        _fam = res.get('families', []); _emb = [e for e in _fam if e.get('embedded_doc')]
        if _emb and sum(1 for e in _emb if (e.get('rfa') or {}).get('status') == 'error') * 10 > len(_emb):
            _d2 = source_damage(a.rvt, getattr(prj, 'x', None))
            if _d2 and set(_d2) != {'(damage check failed)'}:
                changed = True; log.append('source now has damaged gzip member(s) %s that the start check did not see: modified during the run' % dict(_d2))
    if changed:
        man['source_changed_during_run'] = True; write_json(os.path.join(a.out, 'manifest.json'), man)
        safepath.mark_incomplete(a.out)      # outputs may mix two source versions: a folder that looks finished must not be trusted
    code, msgs = exit_status(changed, src_damaged, res.get('families', []))
    for m_ in msgs: print(m_, file=sys.stderr)
    return code
