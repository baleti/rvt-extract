"""lift_chunks.py PROJECT OUTDIR NAMESFILE [N] : lift families in chunks of N names, one process per chunk (bounds memory on remote-host)"""
import sys, subprocess, os
proj, out, nf = sys.argv[1:4]; n = int(sys.argv[4]) if len(sys.argv) > 4 else 12
names = [l.rstrip('\n') for l in open(nf) if l.strip()]
here = os.path.dirname(os.path.realpath(__file__))
for k in range(0, len(names), n):
    chunk = names[k:k + n]
    subprocess.run(['systemd-run', '--user', '--scope', '-q', '-p', 'MemoryMax=3G', '-p', 'MemorySwapMax=0', 'nice', '-n', '19', sys.executable, os.path.join(here, 'lift_all.py'), proj, out] + [c.replace(',', '\\,') for c in chunk], stdout=open(out + '.log', 'a'), stderr=subprocess.STDOUT)
print('done')
