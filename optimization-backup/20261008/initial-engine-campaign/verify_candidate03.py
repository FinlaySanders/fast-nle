from pathlib import Path
import os,select,subprocess,json,time
r=Path(__file__).resolve().parent
pid=int((r/'candidate-03-stock-view-build.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
if '[100%] Built target nethack' not in (r/'candidate-03-stock-view-build.log').read_text():raise RuntimeError('adapter build failed')
env={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')}
lib=str(r/'engine-stock-view/build/libnethack.so');dat=str(r/'dat')
gold=list(map(str,sorted((r/'engine-baseline/tests/goldens').glob('*.golden'))));fuzz=list(map(str,sorted((r/'fuzz-stock').glob('*.golden'))));assert len(gold)==34 and len(fuzz)==26
jobs=[('globals',[str(r/'engine-candidate/tools/check_no_globals.sh'),str(r/'variants/candidate03/libnethack.so')],{}),('stock-view-golden',[str(r/'gates/replay_golden'),lib,dat,*gold],{}),('stock-view-status',[str(r/'gates/replay_golden'),lib,dat,*gold],{'NLE_REPLAY_OPTIONS_APPEND':',!status_updates'}),('stock-view-interleaved',[str(r/'gates/replay_multi'),'--interleaved',lib,dat,*gold],{}),('stock-view-shuffled',[str(r/'gates/replay_multi'),'--shuffled',lib,dat,*gold],{}),('stock-view-fuzz',[str(r/'gates/replay_golden'),lib,dat,*fuzz],{})]
for w in ['depth','score']:
 data=json.loads((r/(w+'-timing-selected.json')).read_text());exe=r/('score/replay_vec_v2' if w=='score' else 'replay_vec_v2')
 jobs.append((w+'-balanced',[str(exe),'verify','8','0','1000000',*[x['path'] for x in data]],dict(NH_DISC_SWAP='0' if w=='score' else '1',NETHACKDIR=dat,LD_LIBRARY_PATH=str(r/'variants/candidate03'))))
results=[]
for name,cmd,extra in jobs:
 start=time.time()
 with (r/('candidate03-'+name+'.log')).open('w') as f:p=subprocess.run(cmd,env=dict(env,**extra),stdout=f,stderr=subprocess.STDOUT)
 results.append(dict(name=name,rc=p.returncode,seconds=time.time()-start,command=cmd));(r/'candidate-03-verification.json').write_text(json.dumps(results,indent=2));print(name,p.returncode,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
print('DONE',flush=True)
