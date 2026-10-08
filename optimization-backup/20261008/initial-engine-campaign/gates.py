from pathlib import Path
import subprocess,os,json,time
r=Path(__file__).parent;s=r/'engine-baseline';b=r/'gates';b.mkdir(exist_ok=True)
inc='/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include'
for n in ['replay_golden','replay_multi']:
 cmd=['cc','-O2','-I'+str(s/'include'),'-I'+inc,str(s/'tests'/ (n+'.c')),'-ldl','-lpthread','-o',str(b/n)]
 subprocess.run(cmd,check=True)
lib=str(r/'lib/libnethack.so');dat=str(r/'dat');gold=[str(p) for p in sorted((s/'tests/goldens').glob('*.golden'))]
jobs=[('globals',[str(s/'tools/check_no_globals.sh'),lib],{}),('golden',[str(b/'replay_golden'),lib,dat,*gold],{}),('interleaved',[str(b/'replay_multi'),'--interleaved',lib,dat,*gold],{}),('shuffled',[str(b/'replay_multi'),'--shuffled',lib,dat,*gold],{}),('status',[str(b/'replay_golden'),lib,dat,*gold],{'NLE_REPLAY_OPTIONS_APPEND':',!status_updates'})]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')}
results=[]
for name,cmd,extra in jobs:
 t=time.time()
 with (b/(name+'.log')).open('w') as out:q=subprocess.run(cmd,cwd=s,env=dict(e,**extra),stdout=out,stderr=subprocess.STDOUT)
 results.append(dict(name=name,rc=q.returncode,seconds=time.time()-t));print(results[-1],flush=True)
 (b/'results.json').write_text(json.dumps(results,indent=2))
(b/'DONE').write_text('finished; see result codes\n')
