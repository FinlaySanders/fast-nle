from pathlib import Path
import os,subprocess,select,json,time,hashlib
r=Path(__file__).resolve().parent
pid=int((r/'augment-all.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
for w in ['depth','score']:assert (r/(w+'-record-v2/VERIFIED_ORIGINAL')).exists(),w+' augmentation failed'
results=[]
def run(w,variant,mode,label,warm,measure,pin=False):
 src=json.loads((r/(w+'-timing-selected.json')).read_text())
 paths=[str(r/(w+'-record-v2')/Path(x['path']).name) for x in src]
 lib=r/'engine-baseline/build' if variant=='baseline' else r/'variants'/variant
 env=os.environ.copy();env.update(NH_DISC_SWAP='0' if w=='score' else '1',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(lib),OMP_PROC_BIND='true',OMP_PLACES='cores')
 cmd=[str(r/'harness-v3'/w/'replay_vec'),mode,'8',str(warm),str(measure),*paths]
 if pin:cmd=['taskset','-c','0,2,4,6,8,10,12,14',*cmd]
 ps=subprocess.check_output(['ps','-eo','pid,ppid,comm,pcpu'],text=True)
 start=time.time();p=subprocess.run(cmd,env=env,capture_output=True,text=True)
 record=dict(workload=w,variant=variant,mode=mode,label=label,started=start,seconds=time.time()-start,rc=p.returncode,command=cmd,stdout=p.stdout,stderr=p.stderr,processes_before=ps,library_sha256=hashlib.sha256((lib/'libnethack.so').read_bytes()).hexdigest())
 results.append(record);(r/'v3-validation-timings.json').write_text(json.dumps(results,indent=2));print(w,variant,label,p.returncode,p.stdout.strip(),flush=True)
 if p.returncode:raise RuntimeError('failure: '+label+' '+p.stderr)
for w in ['depth','score']:
 for v in ['baseline','candidate02','candidate03']:run(w,v,'engine-verify','complete-engine-check',0,1000000)
for w in ['depth','score']:
 for old,new in [('candidate01','candidate02'),('candidate02','candidate03'),('baseline','candidate03')]:
  for rep in range(3):
   for phase,v in [('before',old),('candidate',new),('after',old)]:
    run(w,v,'time',f'{old}-vs-{new}-r{rep}-{phase}',20000,20000,True)
print('DONE',flush=True)
