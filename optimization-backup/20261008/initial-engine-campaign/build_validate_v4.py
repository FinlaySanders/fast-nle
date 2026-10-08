from pathlib import Path
import os,select,subprocess,json
r=Path(__file__).resolve().parent
# Capture a pidfd now so PID reuse cannot trigger a new wait.
try: fd=os.pidfd_open(756641)
except ProcessLookupError: fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
results=[]
for w,heads in [('depth',21),('score',20)]:
 n=r/'harness-v4'/w
 cmd=['cc','-O2','-g','-fopenmp','-I'+str(n/'source/src'),'-I'+str(n/'source/ocean/nethack'),'-I'+str(r/'engine-baseline/include'),'-I/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include','-I/puffertank/pufferlib/raylib-5.5_linux_amd64/include',str(n/'replay_vec.c'),'-L'+str(r/'lib'),'-Wl,-rpath,'+str(r/'lib'),'-lnethack','-lm','-ldl','-o',str(n/'replay_vec')]
 p=subprocess.run(cmd,capture_output=True,text=True);(n/'build.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
 corpus=r/('depth-record-v2' if w=='depth' else 'score-balanced-v2');trace=sorted(corpus.glob('*.trace'))[0]
 out=n/'snapshot-smoke';out.mkdir()
 env={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_')) and k not in ('LD_PRELOAD','NETHACKOPTIONS')}
 env.update(NH_PERF_SNAPSHOTS=str(out),NH_DISC_SWAP='1' if w=='depth' else '0',NH_ZT_MASK='0',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'lib'))
 cmd=[str(n/'replay_vec'),'verify','1','0','128',str(trace)]
 p=subprocess.run(cmd,env=env,capture_output=True,text=True);assert p.returncode==0,p.stderr
 check=subprocess.run(['python',str(r/'check_snapshots.py'),str(trace),str(next(out.glob('*.obs'))),'--heads',str(heads)],capture_output=True,text=True);assert check.returncode==0,check.stderr
 results.append(dict(workload=w,command=cmd,stdout=p.stdout,validation=json.loads(check.stdout)))
 (r/'v4-snapshot-checks.json').write_text(json.dumps(results,indent=2));print(w,check.stdout,flush=True)
print('DONE',flush=True)
