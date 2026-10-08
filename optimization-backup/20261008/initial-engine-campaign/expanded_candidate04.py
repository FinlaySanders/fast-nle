from pathlib import Path
import os,select,subprocess,json,time,hashlib
r=Path(__file__).resolve().parent
pid=int((r/'fresh-snapshot-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
assert len(json.loads((r/'fresh-snapshot-results.json').read_text()))==2,'fresh snapshot validation incomplete'
results=[]
env={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')}
def run(w,v,mode,label,paths,warm,steps,threads=8,extra=None):
 lib=r/'engine-baseline/build' if v=='baseline' else r/'variants'/v
 e=dict(env,NH_DISC_SWAP='1' if w=='depth' else '0',NH_ZT_MASK='0',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(lib),OMP_PROC_BIND='true',OMP_PLACES='cores',**(extra or {}))
 cmd=['taskset','-c','0,2,4,6,8,10,12,14',str(r/'harness-v3'/w/'replay_vec'),mode,str(threads),str(warm),str(steps),*map(str,paths)]
 start=time.time();ps=subprocess.check_output(['ps','-eo','pid,ppid,comm,pcpu'],text=True)
 p=subprocess.run(cmd,env=e,capture_output=True,text=True)
 results.append(dict(workload=w,variant=v,mode=mode,label=label,command=cmd,environment={k:e[k] for k in e if k.startswith(('NH_','NLE_','OMP_','NETHACK','LD_LIBRARY'))},library_sha256=hashlib.sha256((lib/'libnethack.so').read_bytes()).hexdigest(),started=start,seconds=time.time()-start,rc=p.returncode,stdout=p.stdout,stderr=p.stderr,processes_before=ps))
 (r/'expanded04-results.json').write_text(json.dumps(results,indent=2));print(w,v,label,p.returncode,p.stdout.strip(),flush=True)
 if p.returncode:raise RuntimeError(label+' '+p.stderr)
# Explicitly verify a prefix of ALL512 score streams, not a substitute for failed full corpus.
corpus=r/'score512-prefix-v2';corpus.mkdir()
paths=sorted((r/'score-record').glob('*.trace'));assert len(paths)==512
run('score','baseline','verify','all512-prefix-augmentation',paths,0,4000,extra={'NH_PERF_AUGMENT':str(corpus)})
(corpus/'VERIFIED_ORIGINAL').write_text('All512 original score streams, first4000 decisions each only. Full score corpus still fails at env457 decision131399. This prefix is for concurrency timing, not a full-score pass.\n')
windows={}
for w in ['depth','score']:
 c=r/'depth-record-v2' if w=='depth' else corpus
 paths=sorted(c.glob('*.trace'));assert len(paths)==512
 run(w,'candidate04','verify','all512-prefix-full-verification',paths,0,4000)
 run(w,'candidate04','engine-verify','all512-prefix-engine-verification',paths,0,4000)
 windows[w]=paths
# Finish checks before timing; no simultaneous other jobs should be queued behind this yet.
for w,paths in windows.items():
 for rep in range(3):
  for phase,v in [('before','baseline'),('candidate','candidate04'),('after','baseline')]:
   run(w,v,'time',f'baseline-vs-candidate04-r{rep}-{phase}',paths,2000,2000)
print('DONE concurrency benchmark; late windows and incremental04 timings remain separate',flush=True)
