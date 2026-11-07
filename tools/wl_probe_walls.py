import sys,os,collections
sys.path.insert(0,os.path.expanduser('~/rvt-research/write-lab'))
import rvtgen
g=rvtgen.Gen(sys.argv[1])
ws=[i for i in g.e.m.ids if g.e.trace(i)[2]['class']=='SWall']
print('walls',len(ws),'W',g.W)
c=collections.Counter()
rows=[]
for i in ws[:int(sys.argv[2]) if len(sys.argv)>2 else 400]:
    T=g.template(i); c[len(T['rec'])]+=1; rows.append((i,len(T['rec'])))
print(c.most_common(8)); print(rows[:5])
