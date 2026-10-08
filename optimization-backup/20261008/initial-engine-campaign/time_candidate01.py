import os,select,subprocess,json,hashlib,time
from pathlib import Path
r=Path(__file__).resolve().parent
for pid in (740816,742058,742059):
 try: fd=os.pidfd_open(pid)
 except ProcessLookupError: continue
 select.select([fd],[],[]);os.close(fd)
for name in ('candidate-01-depth-engine-verify.log','candidate-01-score32-verify.log'):
 if 'RESULT mode=' not in (r/name).read_text(): raise RuntimeError('verification did not pass: '+name)
rows=[]
for workload in ('depth','score'):
 data=json.loads((r/(workload+'-index.json')).read_text())
 # Mix high scores, deep episodes, and ordinary env streams; preserve complete history.
 ranked=sorted(data,key=lambda x:x['max_score'],reverse=True)[:12]+sorted(data,key=lambda x:x['max_depth'],reverse=True)[:12]+data[::32]
 chosen=[];seen=set()
 for x in ranked:
  if x['path'] not in seen: chosen.append(x);seen.add(x['path'])
 chosen=chosen[:32]
 (r/(workload+'-timing-selected.json')).write_text(json.dumps(chosen,indent=2))
 exe=r/('score/replay_vec' if workload=='score' else 'replay_vec')
 for repeat in range(3):
  for phase,variant in (('before','baseline'),('candidate','candidate'),('after','baseline')):
   env=os.environ.copy();env.update(NH_DISC_SWAP='0' if workload=='score' else '1',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/('engine-'+variant)/'build'),OMP_PROC_BIND='true',OMP_PLACES='cores')
   cmd=['taskset','-c','0,2,4,6,8,10,12,14',str(exe),'time','8','20000','20000',*[x['path'] for x in chosen]]
   started=time.time();p=subprocess.run(cmd,env=env,text=True,capture_output=True)
   record=dict(workload=workload,repeat=repeat,phase=phase,variant=variant,command=cmd,started=started,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,library_sha256=hashlib.sha256((r/('engine-'+variant)/'build/libnethack.so').read_bytes()).hexdigest())
   rows.append(record);(r/'candidate-01-timings.json').write_text(json.dumps(rows,indent=2))
   print(workload,repeat,phase,p.returncode,p.stdout.strip(),flush=True)
   if p.returncode:raise RuntimeError('timing failed')
print('DONE',flush=True)
