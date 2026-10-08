from pathlib import Path
import os,subprocess,json,time,re
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'buffers41';d.mkdir();rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',LD_LIBRARY_PATH=str(r/'pgo20/variant'),OMP_PROC_BIND='false')
for w in ['score','depth']:
 corpus=old/('score-record' if w=='score' else 'depth-record-v2');paths=sorted(map(str,corpus.glob('*.trace')))
 for mode,label,buffers in [('verify','verify2',2),('verify','verify8',8),('time','before',4),('time','buffers2',2),('time','buffers8',8),('time','after',4)]:
  cmd=['taskset','-c','0-31',str(r/'buffers39'/(w+'-'+str(buffers))),mode,'32','20000','5000',*paths];print('START',w,label,flush=True);t=time.time();p=subprocess.run(cmd,env=dict(e,NH_DISC_SWAP=str(int(w=='depth'))),capture_output=True,text=True);row=dict(label=w+'-'+label,command=cmd,rc=p.returncode,seconds=time.time()-t,stdout=p.stdout,stderr=p.stderr);rows.append(row);(d/'results.json').write_text(json.dumps(rows,indent=2));print('DONE',w,label,p.returncode,p.stdout[-500:],flush=True);assert p.returncode==0,p.stderr[-1000:]
summary={}
for w in ['score','depth']:
 vals={phase:float(re.search(r'measured_seconds=([\d.]+)',next(x['stdout'] for x in rows if x['label']==w+'-'+phase))[1]) for phase in ['before','buffers2','buffers8','after']};base=(vals['before']+vals['after'])/2;summary[w]=dict(**vals,gain2_percent=100*(base/vals['buffers2']-1),gain8_percent=100*(base/vals['buffers8']-1),drift_percent=100*(vals['after']/vals['before']-1))
(d/'summary.json').write_text(json.dumps(summary,indent=2));print('COMPLETE',summary,flush=True)
