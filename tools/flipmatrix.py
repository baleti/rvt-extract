#!/usr/bin/env python3
"""Repeatable bit-flip matrix: extract a control, then copies with one 16-byte run
flipped at given percent offsets; report rc, source_damaged, written/error counts and
how many written rfa differ from the control (masking the per-run streams).
Use on Autodesk samples or synthetic data only.
usage: flipmatrix.py SAMPLE.rvt WORKDIR [pct,pct,...]   (needs a fresh WORKDIR)"""
import sys, os, json, shutil, subprocess, hashlib, glob
import olefile
MASK = {'BasicFileInfo', 'DocumentIncrementTable', 'History', 'PartAtom'}
ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def digest(rfa):
    h = hashlib.sha256()
    ole = olefile.OleFileIO(rfa)
    for s in sorted(ole.listdir(streams=True), key=lambda p: '/'.join(p)):
        if s[-1] in MASK or s[0] in MASK:
            continue
        h.update('/'.join(s).encode()); h.update(ole.openstream(s).read())
    ole.close()
    return h.hexdigest()

def run(src, out):
    p = subprocess.run([sys.executable, os.path.join(ROOT, 'bin/rvt-extract'), '--only', 'families',
                        '--out', out, src], capture_output=True, text=True)
    man = json.load(open(os.path.join(out, 'manifest.json'))) if os.path.exists(os.path.join(out, 'manifest.json')) else {}
    return p.returncode, man

def rfas(out):
    return {os.path.basename(f): digest(f) for f in glob.glob(os.path.join(out, '**', '*.rfa'), recursive=True)}

def main():
    src, work = sys.argv[1], sys.argv[2]
    pcts = [int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else '5,20,40,60,80').split(',')]
    os.makedirs(work)
    rc, man = run(src, os.path.join(work, 'control'))
    ctl = rfas(os.path.join(work, 'control'))
    print('pct\trc\tsource_damaged\trfa\twrong_vs_control\t(wrong must be 0)')
    print(f'ctl\t{rc}\t{bool(man.get("source_damaged"))}\t{len(ctl)}\t0')
    data = open(src, 'rb').read()
    for p in pcts:
        d = os.path.join(work, f'f{p}'); os.makedirs(d)
        s = os.path.join(d, 'in.rvt'); b = bytearray(data)
        o = len(b) * p // 100
        for i in range(o, o + 16): b[i] ^= 0xFF
        open(s, 'wb').write(b)
        rc, man = run(s, os.path.join(d, 'out')); got = rfas(os.path.join(d, 'out'))
        wrong = sum(1 for k, v in got.items() if ctl.get(k) != v)
        print(f'{p}\t{rc}\t{bool(man.get("source_damaged"))}\t{len(got)}\t{wrong}')
        os.remove(s)
main()
