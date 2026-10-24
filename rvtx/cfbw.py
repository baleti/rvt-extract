"""Minimal Compound File Binary (v4, 4096-byte sectors) writer with the fixed directory layout Revit uses for .rfa files (own analysis)."""
import struct
END, FREE, FATS = 0xFFFFFFFE, 0xFFFFFFFF, 0xFFFFFFFD
NO = 0xFFFFFFFF
# index: (path, type, color, left, right, child)   (1 storage, 2 stream, 5 root); links are directory indexes
RFA_DIR = [('', 5, 0, -1, -1, 1), ('Formats', 1, 1, 3, 4, 16), ('RevitPreview4.0', 2, 1, 7, 6, -1), ('Global', 1, 1, -1, -1, 12), ('Partitions', 1, 0, 5, 2, 9),
           ('Contents', 2, 1, -1, 8, -1), ('TransmissionData', 2, 0, -1, -1, -1), ('BasicFileInfo', 2, 0, -1, -1, -1), ('PartAtom', 2, 0, -1, -1, -1),
           ('Partitions/0', 2, 1, -1, -1, -1), ('Global/DocumentIncrementTable', 2, 1, 13, -1, -1), ('Global/History', 2, 1, 15, 14, -1),
           ('Global/PartitionTable', 2, 1, 11, 10, -1), ('Global/ContentDocuments', 2, 0, -1, -1, -1), ('Global/ElemTable', 2, 0, -1, -1, -1),
           ('Global/Latest', 2, 0, -1, -1, -1), ('Formats/Latest', 2, 1, -1, -1, -1)]
SS, MSS, CUTOFF = 4096, 64, 4096
_CLSID_ROOT = b'\x00' * 16


def _dirent(name, typ, color, left, right, child, start, size):
    nm = name.encode('utf-16le') + b'\0\0'
    b = bytearray(128); b[:len(nm)] = nm; struct.pack_into('<H', b, 64, len(nm) if name else 0)
    b[66] = typ; b[67] = color
    struct.pack_into('<III', b, 68, left & 0xFFFFFFFF if left >= 0 else NO, right & 0xFFFFFFFF if right >= 0 else NO, child & 0xFFFFFFFF if child >= 0 else NO)
    struct.pack_into('<I', b, 116, start); struct.pack_into('<Q', b, 120, size)
    return bytes(b)


def write_rfa(streams, part='Partitions/0'):
    """streams: {path: bytes} with the 13 rfa stream paths -> CFB file bytes; part = name of the partition stream"""
    ents = [(part if e[0] == 'Partitions/0' else e[0],) + tuple(e[1:]) for e in RFA_DIR]
    streams = {(part if k == 'Partitions/0' else k): v for k, v in streams.items()}
    for p in streams:
        assert any(e[0] == p for e in ents), 'unexpected stream ' + p
    mini = bytearray(); minifat = []; big = []
    start = {}; size = {}
    for i, e in enumerate(ents):
        if e[1] != 2: continue
        d = streams[e[0]]; size[i] = len(d)
        if len(d) == 0: start[i] = END
        elif len(d) < CUTOFF:
            n = (len(d) + MSS - 1) // MSS; start[i] = len(mini) // MSS
            mini += d + b'\0' * (n * MSS - len(d)); minifat += list(range(start[i] + 1, start[i] + n)) + [END]
        else: big.append(i)
    sectors = []; fat = []

    def alloc(data):
        n = (len(data) + SS - 1) // SS; s = len(fat)
        fat.extend(list(range(s + 1, s + n)) + [END] if n else [])
        pad = data + b'\0' * (n * SS - len(data))
        for k in range(n): sectors.append(pad[k * SS:(k + 1) * SS])
        return s if n else END
    for i in big: start[i] = alloc(streams[ents[i][0]])
    rootstart = alloc(bytes(mini)) if mini else END
    mfd = b''.join(struct.pack('<I', x) for x in minifat); mfstart = alloc(mfd) if minifat else END; nmf = (len(mfd) + SS - 1) // SS
    db = bytearray()
    for i, e in enumerate(ents):
        if e[1] == 5: db += _dirent('Root Entry', 5, 0, -1, -1, e[5], rootstart, len(mini)); continue
        name = e[0].split('/')[-1]
        db += _dirent(name, e[1], e[2], e[3], e[4], e[5], start.get(i, 0) if e[1] == 2 else 0, size.get(i, 0))
    while len(db) % SS: db += _dirent('', 0, 0, -1, -1, -1, 0, 0)
    dstart = alloc(bytes(db)); ndir = len(db) // SS
    per = SS // 4; nfat = 1
    while (len(fat) + nfat + per - 1) // per > nfat: nfat += 1
    assert nfat <= 109
    fatstart = len(fat); fat += [FATS] * nfat; fat += [FREE] * (nfat * per - len(fat))
    fb = struct.pack('<%dI' % len(fat), *fat)
    for k in range(nfat): sectors.append(fb[k * SS:(k + 1) * SS])
    h = bytearray(512)
    h[:8] = bytes.fromhex('d0cf11e0a1b11ae1'); struct.pack_into('<HHHHH', h, 24, 0x3e, 4, 0xFFFE, 12, 6)
    struct.pack_into('<IIIIIIIII', h, 40, ndir, nfat, dstart, 0, CUTOFF, mfstart, nmf, END, 0)
    ids = list(range(fatstart, fatstart + nfat)) + [FREE] * (109 - nfat)
    struct.pack_into('<109I', h, 76, *ids)
    return bytes(h) + b'\0' * (SS - 512) + b''.join(sectors)
