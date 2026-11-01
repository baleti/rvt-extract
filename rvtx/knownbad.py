"""Known-bad registry: .rfa the extractor writes but Revit is known to reject. rvtx/known_bad.tsv rows: year<TAB>category regex<TAB>name regex<TAB>reason ('*' year = any). Empty after the 2026-10-30 sweeps."""
import os, re

PATH = os.path.join(os.path.dirname(__file__), 'known_bad.tsv')


def reason(fmt, category, name, path=PATH):
    if not os.path.exists(path): return None
    for l in open(path, encoding='utf-8'):
        if l.startswith('#') or not l.strip(): continue
        y, cat, nm, why = (l.rstrip('\n').split('\t') + [''] * 4)[:4]
        if y not in ('*', str(fmt)): continue
        if re.search(cat or '.', category or '') and re.search(nm or '.', name or ''): return why or 'known bad'
    return None


def mark(entry, fmt, category, name, experimental=False):
    """Set rfa.known_bad on a written entry; a 2016 file written with --experimental is always marked."""
    why = reason(fmt, category, name) or ('Revit 2016 layout not validated' if str(fmt).isdigit() and int(fmt) < 2017 and experimental else None)
    if why: entry['known_bad'] = why
    return entry


def mark_nested_titleblock(entry, fmt, category, nested):
    """4-byte-id years (2017-2023): every nested Title Block lifted from real projects stalled Revit 2024 on open (13 of 13 checked 2026-11-01; flat title blocks open). Cause not found."""
    try: y = int(fmt)
    except (TypeError, ValueError): return entry
    if nested and y <= 2023 and 'title block' in (category or '').lower() and 'known_bad' not in entry:
        entry['known_bad'] = 'nested title block in a 4-byte-id year: Revit 2024 hangs in OpenDocumentFile (observed 2026-11-01 on 2020-2023 office families; flat title blocks open)'
    return entry
