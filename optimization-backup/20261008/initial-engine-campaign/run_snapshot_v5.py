from pathlib import Path
import os,select,subprocess,json,hashlib,time
from check_settings_v5 import read as settings_read
r=Path(__file__).resolve().parent;root=r/'harness-v5'
pid=int((r/'late512-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
rows=[];e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS','NVCC_EXTRA')}
e.update(NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'lib'),NH_ZT_MASK='0',CUDA_VISIBLE_DEVICES='0')
def run(label,cmd,cwd=None,extra=None):
 log=root/(label+'.log');start=time.time()
 with log.open('w') as f:p=subprocess.run(cmd,cwd=cwd,env=dict(e,**(extra or {})),stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(label=label,cmd=cmd,rc=p.returncode,seconds=time.time()-start,log=str(log)));(root/'results.json').write_text(json.dumps(rows,indent=2));print(label,p.returncode,flush=True)
 assert p.returncode==0,log.read_text(errors='replace')[-1500:]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
for w in ['depth','score']:
 n=root/w;s=n/'source'
 run(w+'-build',['bash','build.sh','nethack','puffer'],s)
 run(w+'-build-replay',['cc','-O2','-g','-fopenmp','-I'+str(s/'src'),'-I'+str(s/'ocean/nethack'),'-I'+str(r/'engine-baseline/include'),'-I/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include','-I/puffertank/pufferlib/raylib-5.5_linux_amd64/include',str(n/'replay_vec.c'),'-L'+str(r/'lib'),'-Wl,-rpath,'+str(r/'lib'),'-lnethack','-lm','-ldl','-o',str(n/'replay_vec')])
 traces=n/'traces';raw=n/'observations';traces.mkdir();raw.mkdir()
 cmd=json.loads((r/('smoke-command.json' if w=='depth' else 'score-smoke-command.json')).read_text());cmd[0]=str(s/'puffer')
 run(w+'-record',cmd,s,dict(NH_DISC_SWAP='1' if w=='depth' else '0',NH_PERF_RECORD=str(traces),NH_PERF_SNAPSHOTS=str(raw)))
 proof=[]
 # Check new recording did not perturb the original native trajectory.
 for p in sorted(traces.glob('*.trace')):assert sha(p)==sha(r/'harness-v4'/w/'fresh-traces'/p.name)
 for variant,lib in [('baseline',r/'lib'),('candidate03',r/'variants/candidate03')]:
  out=n/('replay-'+variant);out.mkdir()
  run(w+'-replay-'+variant,[str(n/'replay_vec'),'verify','8','0','1000000',*map(str,sorted(traces.glob('*.trace')))],extra=dict(NH_DISC_SWAP='1' if w=='depth' else '0',NH_PERF_SNAPSHOTS=str(out),LD_LIBRARY_PATH=str(lib)))
  for p in sorted(raw.glob('*.obs')):
   assert sha(p)==sha(out/p.name),(w,variant,p.name,'raw field mismatch')
   settings=p.with_suffix('.settings');q=out/settings.name;a=settings_read(settings);b=settings_read(q)
   assert [(x['event'],x['semantic']) for x in a]==[(x['event'],x['semantic']) for x in b]
   # Paths legitimately differ because each env owns a temp directory. Capture
   # them literally; the trace R record verifies expanded options byte-for-byte.
   proof.append(dict(variant=variant,file=p.name,sha256=sha(p),settings_events=len(a)))
 (n/'proof.json').write_text(json.dumps(proof,indent=2))
print('DONE',flush=True)
