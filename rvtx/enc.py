"""Encoder mirroring rvt_decode.Dec (own analysis): re-serialises a decoded object tree. Used for Global/Latest (ADocument) editing.
Round trip is the test: encode(decode(x)) == x."""
import struct
import rvtx  # noqa (sys.path)
import rvt_decode as D

EID = D.EID


class Dec2(D.Dec):
    """decoder that remembers the two null pointer forms and the u32 0xffffffff 'null' without tag"""
    def slot(s, b, p, stars, pend, path):
        v = struct.unpack_from('<I', b, p)[0]
        if v == 0: return {'null': 0}, p + 4
        if v != 0xffffffff:
            if (s.backref and v in s.defined) or stars == 3: return {'ref': v}, p + 4
            s.defined.add(v)
        tag = struct.unpack_from('<H', b, p + 4)[0]
        if v == 0xffffffff and not (12 <= tag < 12 + len(s.s.c)): return {'null': 0xffffffff}, p + 4
        if not 12 <= tag < 12 + len(s.s.c): raise D.Desync('pointer tag %d at %d (%s)' % (tag, p, '.'.join(path)))
        slot = {'handle': v, 'ptr': tag}; pend.append((slot, tag)); return slot, p + 6

    def elem(s, b, p, kind, fl, ref, pend, path):
        if kind == 0x0e and (fl & 0xf0) == 0x50 and (fl & 0x0f) and struct.unpack_from('<I', b, p)[0] == 0xffffffff:
            return {'nullset': 1}, p + 4
        if kind == 0x0e and fl == 0x50 and struct.unpack_from('<I', b, p)[0] == 0xffffffff:
            return {'nullset': 1}, p + 4
        return super().elem(b, p, kind, fl, ref, pend, path)


class Enc:
    def __init__(self, schema, idsize):
        self.s = schema; self.W = idsize

    def prim(self, kind, v):
        if kind == 9: return bytes.fromhex(v)
        if kind == 8:
            e = v.encode('utf-16le'); return struct.pack('<I', len(e) // 2) + e
        fmt, sz = D.PRIM[kind]
        if fmt == '<I' and not 0 <= v <= 0xFFFFFFFF: v &= 0xFFFFFFFF      # 4-byte element id formats: the 8-byte sentinel -1 (and negative ids) wrap to ffffffff
        return struct.pack(fmt, v)

    def value(self, f, v, pend, lvl=0):
        types = f['types']; ns = f.get('ns') or [None] * len(types)
        T = types[lvl]; kind = T & 0xff; fl = (T >> 8) & 0xff
        n = ns[lvl] if lvl < len(ns) else None
        ref = f.get('ref') if (lvl == 0 or lvl == len(types) - 1) and 'ref' in f else f.get('ref2')
        if kind == 0x0d:
            out = b'' if (fl & 0x10 and not fl & 0x40) else struct.pack('<I', len(v))
            for x in v: out += self.value(f, x, pend, lvl + 1)
            return out
        if fl & 0x10 and not fl & 0x40:
            return b''.join(self.elem(kind, fl & ~0x10, ref, x, pend) for x in v)
        return self.elem(kind, fl, ref, v, pend)

    def elem(self, kind, fl, ref, v, pend):
        if kind == 0x0e:
            if isinstance(v, dict) and 'nullset' in v: return struct.pack('<I', 0xffffffff)
            if (fl & 0xf0) == 0x50 and (fl & 0x0f):
                return struct.pack('<I', len(v)) + b''.join(self.slot(x, pend) for x in v)
            if fl in (1, 2, 3): return self.slot(v, pend)
            ref = (ref or 0) & 0x7fff
            if fl == 0x50:
                return struct.pack('<I', len(v)) + b''.join(self.struct(ref - 12, x, pend) for x in v)
            return self.struct(ref - 12, v, pend)
        if fl in (0x50, 0x51):
            if kind in (1, 2): return struct.pack('<I', len(v)) + bytes(v)
            return struct.pack('<I', len(v)) + b''.join(self.prim(kind, x) for x in v)
        return self.prim(kind, v)

    def slot(self, v, pend):
        if 'null' in v: return struct.pack('<I', v['null'])
        if 'ref' in v: return struct.pack('<I', v['ref'])
        pend.append(v)
        return struct.pack('<IH', v['handle'], v['ptr'])

    def struct(self, ci, v, pend, top=False):
        c = self.s.c
        chain = self.s.chain(ci)
        if c[ci]['name'] == 'ElementId' and isinstance(v, EID): return self.eid(ci, v.v if hasattr(v, 'v') else int(v))
        out = b''
        for k in chain:
            for f in c[k]['fields']:
                out += self.value(f, v[f['name']], pend)
        return out

    def eid(self, ci, val):
        out = b''
        for k in self.s.chain(ci):
            for f in c_fields(self.s, k):
                T = f['types'][0]; kind = T & 0xff; fl = (T >> 8) & 0xff
                if kind == 0x0e and fl == 0: out += self.eid((f.get('ref') & 0x7fff) - 12, val)
                else: out += self.prim(kind, val)
        return out

    def body(self, tag, tree, fixed_prefix=b''):
        """encode top-level object fixed part + BFS bodies"""
        from collections import deque
        pend = []
        out = bytearray(self.struct(tag - 12, tree, pend, top=True))
        q = deque(pend)
        while q:
            slot = q.popleft(); npend = []
            out += self.struct(slot['ptr'] - 12, slot['obj'], npend); q.extend(npend)
        return bytes(out)


def c_fields(sch, k):
    return sch.c[k]['fields']


def decode_tree(sch, W, data, off, tag, defined=(1,)):
    dec = Dec2(sch, idsize=W); dec.STOP = (); dec.visited = []; dec.err = None; dec.maxh = 1; dec.defined = set(defined)
    v, p, complete = dec.body(data, off, tag, [sch.name(tag)], top=True)
    return v, p, complete
