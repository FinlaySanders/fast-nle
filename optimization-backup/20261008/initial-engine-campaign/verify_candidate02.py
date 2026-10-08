from pathlib import Path
import os,subprocess,json,time
r=Path(__file__).resolve().parent
results=[]
for workload,variant,mode in [('depth','candidate02','verify'),('score','baseline','verify'),('score','candidate02','verify'),('score','candidate02','engine-verify')]:
 selected=json.loads((r/(workload+'-timing-selected.json')).read_text())
 lib=r/'engine-baseline/build' if variant=='baseline' else r/'variants'/variant
 env=os.environ.copy();env.update(NH_DISC_SWAP='0' if workload=='score' else '1',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(lib))
 exe=r/('score/replay_vec' if workload=='score' else 'replay_vec')
 cmd=[str(exe),mode,'8','0','1000000',*[x['path'] for x in selected]]
 log=r/f'{variant}-{workload}-balanced-{mode}.log'
 start=time.time()
 with log.open('w') as f:p=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 result=dict(workload=workload,variant=variant,mode=mode,command=cmd,returncode=p.returncode,seconds=time.time()-start,log=str(log))
 results.append(result);(r/'candidate-02-verification.json').write_text(json.dumps(results,indent=2));print(result,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
print('DONE',flush=True)
