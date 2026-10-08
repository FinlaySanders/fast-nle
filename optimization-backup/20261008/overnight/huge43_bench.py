from pathlib import Path
import os,subprocess,json,time,re
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'huge43-512';d.mkdir();rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',OMP_PROC_BIND='false')
for w in ['score','depth']:
 corpus=old/('score-record' if w=='score' else 'depth-record-v2');paths=sorted(map(str,corpus.glob('*.trace')));assert len(paths)==512
 for mode,label,library in [('verify','verify','huge43'),('time','before','track40'),('time','candidate','huge43'),('time','after','track40')]:
  cmd=['taskset','-c','0-31',str(r/'buffers39'/(w+'-4')),mode,'32','20000','5000',*paths];print('START',w,label,flush=True);t=time.time()
  log=d/(w+'-'+label+'.log')
  with log.open('w') as f:
   p=subprocess.Popen(cmd,env=dict(e,LD_LIBRARY_PATH=str(r/library/'variant'),NH_DISC_SWAP=str(int(w=='depth'))),stdout=f,stderr=subprocess.STDOUT)
   (d/'active.json').write_text(json.dumps(dict(pid=p.pid,workload=w,phase=label,library=library,command=cmd)));rc=p.wait()
  txt=log.read_text();row=dict(label=w+'-'+label,command=cmd,rc=rc,seconds=time.time()-t,stdout=txt);rows.append(row);(d/'results.json').write_text(json.dumps(rows,indent=2));print('DONE',w,label,rc,txt[-500:],flush=True);assert rc==0,txt[-1000:]
summary={}
for w in ['score','depth']:
 vals={phase:float(re.search(r'measured_seconds=([\d.]+)',next(x['stdout'] for x in rows if x['label']==w+'-'+phase))[1]) for phase in ['before','candidate','after']};base=(vals['before']+vals['after'])/2;summary[w]=dict(**vals,gain_percent=100*(base/vals['candidate']-1),drift_percent=100*(vals['after']/vals['before']-1),maxrss_kb={phase:int(re.search(r'maxrss_kb=(\d+)',next(x['stdout'] for x in rows if x['label']==w+'-'+phase))[1]) for phase in vals})
(d/'summary.json').write_text(json.dumps(summary,indent=2));print('COMPLETE',summary,flush=True)
