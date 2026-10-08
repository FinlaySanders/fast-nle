"""Incremental04 plus explicitly indexed late-episode comparisons."""
from pathlib import Path
import os,select,subprocess,json,time,hashlib
r=Path(__file__).resolve().parent
pid=int((r/'expanded04-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
assert 'DONE concurrency benchmark' in (r/'expanded04-runner.log').read_text(),'expanded benchmark incomplete'
results=[]
env={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')}
def run(w,v,mode,label,paths,warm,steps,threads=8,window=None):
 lib=r/'engine-baseline/build' if v=='baseline' else r/'variants'/v
 e=dict(env,NH_DISC_SWAP='1' if w=='depth' else '0',NH_ZT_MASK='0',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(lib),OMP_PROC_BIND='true',OMP_PLACES='cores')
 cmd=['taskset','-c','0,2,4,6,8,10,12,14' if threads==8 else '0',str(r/'harness-v3'/w/'replay_vec'),mode,str(threads),str(warm),str(steps),*map(str,paths)]
 start=time.time();ps=subprocess.check_output(['ps','-eo','pid,ppid,comm,pcpu'],text=True);p=subprocess.run(cmd,env=e,capture_output=True,text=True)
 work=w if window is None else w+'-late-'+Path(paths[0]).stem
 results.append(dict(workload=work,variant=v,mode=mode,label=label,window=window,command=cmd,library_sha256=hashlib.sha256((lib/'libnethack.so').read_bytes()).hexdigest(),started=start,seconds=time.time()-start,rc=p.returncode,stdout=p.stdout,stderr=p.stderr,processes_before=ps))
 (r/'candidate04-window-results.json').write_text(json.dumps(results,indent=2));print(work,v,label,p.returncode,p.stdout.strip(),flush=True)
 if p.returncode:raise RuntimeError(label+' '+p.stderr)
for w in ['depth','score']:
 corpus=r/('depth-record-v2' if w=='depth' else 'score-balanced-v2')
 paths=[corpus/Path(x['path']).name for x in json.loads((r/(w+'-timing-selected.json')).read_text())]
 for rep in range(3):
  for phase,v in [('before','candidate03'),('candidate','candidate04'),('after','candidate03')]:
   run(w,v,'time',f'candidate03-vs-candidate04-r{rep}-{phase}',paths,20000,20000)
# Full backend replay executes omitted legacy refreshes itself. No engine-only use of NHPERF1.
for window in json.loads((r/'late-window-manifest.json').read_text()):
 w=window['workload'];paths=[Path(window['path'])];warm=window['warmup'];steps=window['measured_decisions']
 for v in ['baseline','candidate04']:run(w,v,'verify','late-window-verification',paths,warm,steps,1,window)
 for rep in range(3):
  for phase,v in [('before','baseline'),('candidate','candidate04'),('after','baseline')]:
   run(w,v,'time',f'baseline-vs-candidate04-r{rep}-{phase}',paths,warm,steps,1,window)
print('DONE',flush=True)
