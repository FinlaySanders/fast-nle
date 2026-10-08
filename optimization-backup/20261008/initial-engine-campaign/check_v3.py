from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent;out=r/'score167-v2';out.mkdir(exist_ok=True)
env=os.environ.copy();env.update(NH_DISC_SWAP='0',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'engine-baseline/build'))
exe=r/'harness-v3/score/replay_vec'
jobs=[('augment', 'verify',r/'score-record/env00167.trace',{'NH_PERF_AUGMENT':str(out)}),('full','verify',out/'env00167.trace',{}),('engine','engine-verify',out/'env00167.trace',{})]
for name,mode,path,extra in jobs:
 with (r/('v3-check-'+name+'.log')).open('w') as f:p=subprocess.run([str(exe),mode,'1','0','1000000',str(path)],env=dict(env,**extra),stdout=f,stderr=subprocess.STDOUT)
 print(name,p.returncode,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
(out/'VERIFIED').write_text('full baseline replay, augmented full replay and engine-only replay pass\n');print('DONE',flush=True)
