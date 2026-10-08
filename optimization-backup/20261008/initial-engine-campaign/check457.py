from pathlib import Path
import subprocess,os,json
r=Path(__file__).resolve().parent
jobs=[('original-lib-v2',r/'score/replay_vec_v2',r/'lib'),('fresh-lib-v2',r/'score/replay_vec_v2',r/'engine-baseline/build'),('original-lib-v3',r/'harness-v3/score/replay_vec',r/'lib'),('fresh-lib-v3',r/'harness-v3/score/replay_vec',r/'engine-baseline/build')]
results=[]
for name,exe,lib in jobs:
 env=os.environ.copy();env.update(NH_DISC_SWAP='0',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(lib));env.pop('NH_PERF_AUGMENT',None)
 with (r/('check457-'+name+'.log')).open('w') as f:p=subprocess.run([str(exe),'verify','1','0','1000000',str(r/'score-record/env00457.trace')],env=env,stdout=f,stderr=subprocess.STDOUT)
 results.append({'name':name,'rc':p.returncode});(r/'check457.json').write_text(json.dumps(results,indent=2));print(name,p.returncode,flush=True)
print('DONE',flush=True)
