"""wl_add_wall.py SEED OUT TEMPLATE_WALL_ID x0 y0 x1 y1 [height]
Generalised write-lab add: clone an existing wall of the SEED project itself (self-templating, so type/level ids are valid) to a new straight wall.
Uses ~/rvt-research/write-lab (genlib.make_wall, genlib2.registry_update). Experimental."""
import sys,os,struct,json
WL=os.path.expanduser('~/rvt-research/write-lab'); sys.path.insert(0,WL)
import rvtgen,genlib,genlib2
seed,out,tid=sys.argv[1],sys.argv[2],int(sys.argv[3]); x0,y0,x1,y1=map(float,sys.argv[4:8]); H=float(sys.argv[8]) if len(sys.argv)>8 else None
genlib2.YEAR=2024; genlib.FITYEAR=2024
g=rvtgen.Gen(seed); T=g.template(tid); print('tpl rec len',len(T['rec']),flush=True)
L={n:(o,e) for n,o,e,_ in T['log']}
lvl=struct.unpack_from('<Q',T['rec'],L['Element.m_assocLevelId'][0])[0] if 'Element.m_assocLevelId' in L else None
hl={x[0]:x for x in T['hlog']}; mm=struct.unpack_from('<6d',T['hdr'],hl['Outline.m_minmax'][1])
print('level',lvl,'outline',mm,flush=True)
z0=mm[2]; h=H or (mm[5]-mm[2])
et=g._et(); n=struct.unpack_from('<I',et,2)[0]
best=max(range(n),key=lambda k:(struct.unpack_from('<I',et,6+g.RW*k+12)[0],struct.unpack_from('<I',et,6+g.RW*k+8)[0]))
tr=struct.unpack_from('<3I',et,6+g.RW*best+8)
nid=g.nextid; g.nextid+=1
hd,rec,it,row=genlib.make_wall(g,T,nid,lvl,(x0,y0),(x1,y1),h,z0,tr,lvl)
g.new.append((hd,rec,it,nid)); g.rows.append(row)
known=set(g.e.m.ids)
def comp(raw):
    ops=genlib2.registry_update(raw,{tid:[nid]},known); return genlib2.apply_ops(raw,ops)
g.latest_edits=[('Latest',comp)]; g.itag=T['item'][16:18]
g.commit(out); json.dump({'walls':[[nid,x0,y0,x1,y1,h,lvl,z0]],'template':tid},open(out+'.json','w')); print('wrote',out,'new id',nid)
