from pathlib import Path
import os,subprocess,json,time
r=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'tight-loop/campaign2h';rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUF_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')};e.update(NETHACKDIR=str(r/'dat'),NH_ZT_MASK='0',LD_LIBRARY_PATH=str(r/'variants/candidate14-lto-local'),OMP_PROC_BIND='false')
for name in ['depth','score']:
 corpus=r/('depth-record-v2' if name=='depth' else 'score-record');paths=[str(corpus/Path(x['path']).name) for x in json.loads((r/(name+'-index.json')).read_text())]
 for mode,label,kind in [('verify','verify-static','static'),('verify','verify-ws','ws'),('time','before','static'),('time','candidate','ws'),('time','after','static')]:
  cmd=['taskset','-c','0,2,4,6,8,10,12,14',str(r/'late512'/(name+'-'+kind)),mode,'8','20000','20000',*paths];t=time.time();p=subprocess.run(cmd,env=dict(e,NH_DISC_SWAP='1' if name=='depth' else '0',LD_LIBRARY_PATH=str(r/'lib' if kind=='static' else r/'variants/candidate14-lto-local')),capture_output=True,text=True);rows.append(dict(label=name+'-'+label,command=cmd,rc=p.returncode,seconds=time.time()-t,stdout=p.stdout,stderr=p.stderr));(d/'combined512-results.json').write_text(json.dumps(rows,indent=2));print(name,label,p.returncode,p.stdout[-1000:],flush=True);assert p.returncode==0,p.stderr
print('DONE',flush=True)
