import sys,struct
sys.path.insert(0,'~/rvt-research/write-lab'); sys.path.insert(0,'~/rvt-research')
import cfb, rvtw, wlpart, olefile, fmt_parser as fp
from rvtfmt import inflate_stream
def load(path, W=8):
    c=cfb.CFB(open(path,'rb').read()); st=c.streams()
    pn=[k for k in st if k.startswith('Partitions/')][0]
    P=wlpart.Partition(rvtw.Stream(st[pn].data)); joined=b''.join(bytes(m['raw']) for m in P.mem)
    o=olefile.OleFileIO(path); cls,_=fp.parse(inflate_stream(o.openstream('Formats/Latest').read())[1])
    return P, joined, cls
def walk_hdr(joined, p, W=8):
    """walk records of the form A(4) id(W) L(4) body(L); yields (pos, A, id, L, tag)"""
    out=[]
    while p+8+W+4<=len(joined):
        A,=struct.unpack_from('<I',joined,p); idv=int.from_bytes(joined[p+4:p+4+W],'little'); L,=struct.unpack_from('<I',joined,p+4+W)
        if L>2_000_000 or p+8+W+L>len(joined): break
        tag=struct.unpack_from('<H',joined,p+8+W)[0] if L>=2 else None
        out.append((p,A,idv,L,tag)); p+=8+W+L
    return out

def chain(joined, W=8, start=0, limit=None):
    """walk [id W][L u32][body L] records joined by A=4 bytes (A == previous L); returns list of (pos_of_id, A, id, L, tag)"""
    out=[]; p=start; A=None
    while p+W+4<=len(joined):
        idv=int.from_bytes(joined[p:p+W],'little'); L,=struct.unpack_from('<I',joined,p+W)
        if p+W+4+L>len(joined): break
        tag=struct.unpack_from('<H',joined,p+W+4)[0] if L>=2 else None
        out.append((p,A,idv,L,tag))
        nxt=p+W+4+L+4
        if nxt+W+4>len(joined): break
        A2,=struct.unpack_from('<I',joined,p+W+4+L)
        if A2!=L: out.append((p+W+4+L,'CHAINBREAK',A2,L,None)); break
        A=A2; p=nxt
    return out

def all_items(j, W=8):
    """full item list of the joined payload: dict(region, pos(of A or id for first), A_pos, id, L, kind). Regions: H (hs 16), R (hs 20), Z (hs 20)."""
    items=[]; p=0
    # H: first record has no A field in payload
    first=True; prevL=None
    while True:
        idv=int.from_bytes(j[p:p+W],'little'); L,=struct.unpack_from('<I',j,p+W)
        items.append(dict(region='H',apos=None if first else p-4,pos=p,id=idv,L=L,end=p+W+4+L)); first=False
        if idv==(1<<(8*W))-1: p=p+W+4+L; break
        p=p+W+4+L+4
    # R and Z: [A4][id][stamp4][L][body]; terminator = id -1, L=0
    for reg in ('R','Z'):
        while True:
            A,=struct.unpack_from('<I',j,p); idv=int.from_bytes(j[p+4:p+4+W],'little'); st,L=struct.unpack_from('<II',j,p+4+W)
            items.append(dict(region=reg,apos=p,pos=p+4,id=idv,L=L,end=p+4+W+8+L,A=A,stamp=st))
            p=p+4+W+8+L
            if idv==(1<<(8*W))-1: break
    return items, p
