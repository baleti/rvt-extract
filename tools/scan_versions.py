"""scan_versions.py LIST.tsv OUT.tsv : Revit format, build, workshare flag, size per file (reads only BasicFileInfo). Private data: OUT stays local."""
import sys, re, os, olefile
out = open(sys.argv[2], 'w')
for l in open(sys.argv[1]):
    f = l.rstrip('\n').split('\t')
    if len(f) < 3: continue
    p = f[2]
    try:
        o = olefile.OleFileIO(p); b = o.openstream('BasicFileInfo').read()
        t = b.decode('utf-16le', 'ignore') + b[1:].decode('utf-16le', 'ignore')
        fm = re.search(r'Format: (\d+)', t); ws = re.search(r'Worksharing: ([^\r\n]*)', t); cen = re.search(r'Central Model Path: ([^\r\n]*)', t)
        parts = [x for x in ['/'.join(e) for e in o.listdir(streams=True)] if x.startswith('Partitions/')]
        out.write('\t'.join([f[0], f[1][:10], fm.group(1) if fm else '?', (ws.group(1) if ws else '?').strip(), str(len(parts)), str(o.exists('Global/ContentDocuments')), p]) + '\n')
    except Exception as e:
        out.write('\t'.join([f[0], f[1][:10], 'ERR', str(e)[:40], '', '', p]) + '\n')
    out.flush()
