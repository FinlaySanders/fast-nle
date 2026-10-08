from pathlib import Path
import subprocess,os
r=Path(__file__).resolve().parent;offsets=r/'score167-refresh-offsets.txt';offsets.write_text('')
env=os.environ.copy();env.update(NH_DISC_SWAP='0',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'engine-baseline/build'))
for mode,key in [('verify','NH_REFRESH_LOG'),('engine-verify','NH_REFRESH_READ')]:
 with (r/('refresh-fixed-'+mode+'.log')).open('w') as f:
  p=subprocess.run([str(r/'score/replay_debug'),mode,'1','0','1000000',str(r/'score-record/env00167.trace')],env=dict(env,**{key:str(offsets)}),stdout=f,stderr=subprocess.STDOUT)
 print(mode,p.returncode,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
print('DONE',flush=True)
