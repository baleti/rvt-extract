import sys,os,collections,pickle
sys.path.insert(0,'~/rvt-research')
import rvt_xcache as X
p=sys.argv[1]
x=X.get_x(p)
print(type(x), list(x.keys())[:30])
for k,v in x.items():
    try: print(k, len(v))
    except: print(k, v)
pickle.dump(x,open(sys.argv[2],'wb'))
