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
