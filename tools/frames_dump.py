"""frames_dump.py FILE.rfa : list partition member frames (the 32 B between gzip members)"""
import sys, os, struct, olefile
sys.path.insert(0, os.path.expanduser('~/rvt-research'))
import rvt2text as T
o = olefile.OleFileIO(sys.argv[1])
pn = [y for y in ['/'.join(e) for e in o.listdir(streams=True)] if y.startswith('Partitions/')][0]
data = T.strip_pages(o.openstream(pn).read()); GZ = b'\x1f\x8b\x08'
pos = 0; prev_end = 44; k = 0
print(pn, len(data), data[:44].hex())
while True:
    i = data.find(GZ, pos)
    if i < 0: break
    d = __import__('zlib').decompressobj(-15)
    try: out = d.decompress(data[i + 10:])
    except Exception: pos = i + 4; continue
    end = len(data) - len(d.unused_data) if False else i + 10 + (len(data) - i - 10 - len(d.unused_data))
    fr = data[end:end + 32]
    print(k, 'raw', len(out), 'frame', fr.hex())
    k += 1; pos = end
