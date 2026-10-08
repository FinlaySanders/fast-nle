from pathlib import Path
import os,subprocess,json,sys
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');candidate=sys.argv[1];d=r/(candidate+'-verify');d.mkdir();rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0')
for w in ['score','depth']:
 corpus=old/('depth-record-v2' if w=='depth' else 'score-balanced-v2');paths=[str(corpus/Path(x['path']).name) for x in json.loads((old/(w+'-timing-selected.json')).read_text())];cmd=[str(old/'harness-v3'/w/'replay_vec'),'verify','8','20000','20000',*paths]
 print('START',w,flush=True)
 with (d/(w+'.log')).open('w') as f:p=subprocess.run(cmd,env=dict(e,LD_LIBRARY_PATH=str(r/candidate/'variant'),NH_DISC_SWAP=str(int(w=='depth'))),stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(workload=w,rc=p.returncode,command=cmd));(d/'results.json').write_text(json.dumps(rows,indent=2));assert p.returncode==0,(d/(w+'.log')).read_text()[-1000:];print('PASS',w,flush=True)
