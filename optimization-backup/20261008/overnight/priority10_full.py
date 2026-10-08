from pathlib import Path
import os,subprocess,json,time,re
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'priority10-full';d.mkdir();rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',LD_LIBRARY_PATH=str(r/'pgo08/variant'),OMP_PROC_BIND='false')
for w in ['score','depth']:
 corpus=old/('score-record' if w=='score' else 'depth-record-v2');paths=sorted(map(str,corpus.glob('*.trace')))[:512]
 for mode,label,exe in [('verify','verify','priority'),('time','before','baseline'),('time','candidate','priority'),('time','after','baseline')]:
  cmd=[str(r/'priority10'/(w+'-'+exe)),mode,'32','20000','20000',*paths];print('START',w,label,flush=True);start=time.time();p=subprocess.run(cmd,env=dict(e,NH_DISC_SWAP=str(int(w=='depth'))),capture_output=True,text=True);row=dict(label=w+'-'+label,command=cmd,rc=p.returncode,seconds=time.time()-start,stdout=p.stdout,stderr=p.stderr);rows.append(row);(d/'results.json').write_text(json.dumps(rows,indent=2));print('DONE',w,label,p.returncode,p.stdout[-500:],flush=True);assert p.returncode==0,p.stderr[-1000:]
summary={}
for w in ['score','depth']:
 vals={p:float(re.search(r'measured_seconds=([\d.]+)',next(x for x in rows if x['label']==w+'-'+p)['stdout'])[1]) for p in ['before','candidate','after']};summary[w]=dict(**vals,gain_percent=((vals['before']+vals['after'])/2/vals['candidate']-1)*100,drift_percent=(vals['after']/vals['before']-1)*100)
(d/'summary.json').write_text(json.dumps(summary,indent=2));print('PRIORITY_COMPLETE',summary,flush=True)
