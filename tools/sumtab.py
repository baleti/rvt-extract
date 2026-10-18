import json,glob,sys,os
rows=[]
for f in sorted(glob.glob(os.path.expanduser('~/src/rvt-extract/out/studyx/*/summary.json'))):
    s=json.load(open(f)); rows.append(s)
print('%-8s %-5s %6s %5s %5s %5s %6s %6s %5s %s'%('id','fmt','MB','fams','doc','inpl','rfaOK','rfaERR','rssMB','fail'))
for s in rows:
    k=s.get('kinds',{}); kf=[n for n,v in k.items() if not v.get('ok')]
    print('%-8s %-5s %6d %5s %5s %5s %6s %6s %5s %s %s'%(s['id'],s.get('format','?'),s['size']//2**20,s.get('families','-'),s.get('with_doc','-'),s.get('in_place','-'),s.get('rfa_written','-'),s.get('rfa_errors','-'),s.get('maxrss_mb','-'),[n for n,v in s['steps'].items() if not v['ok']],kf or ''))
