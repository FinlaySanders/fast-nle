from pathlib import Path
import os,select,subprocess,json,time,hashlib
r=Path(__file__).resolve().parent;root=r/'late512';root.mkdir(exist_ok=True)
pid=int((r/'floor-extended-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
rows=[];bench=[]
env={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS','NVCC_EXTRA')}
env.update(NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'variants/candidate03'),NH_ZT_MASK='0')
def run(label,cmd,extra=None):
 start=time.time();log=root/(label+'.log');e=dict(env,**(extra or {}))
 with log.open('w') as f:p=subprocess.run(cmd,env=e,stdout=f,stderr=subprocess.STDOUT)
 row=dict(label=label,command=cmd,elapsed=time.time()-start,rc=p.returncode,stdout=log.read_text(errors='replace'),log=str(log))
 rows.append(row);(root/'replay-results.json').write_text(json.dumps(rows,indent=2));print(label,p.returncode,flush=True)
 assert p.returncode==0,row['stdout'][-1500:]
 return row
for w in ['depth','score']:
 n=r/'shared-pool'/w;s=n/'source'
 for kind,flag in [('static',''),('ws','-DREPLAY_WS=1'),('pool','-DREPLAY_POOL=1')]:
  run(w+'-build-multi-'+kind,['cc','-O2','-g','-fopenmp','-pthread',*([flag] if flag else []),'-I'+str(r/'shared-pool'),'-I'+str(s/'src'),'-I'+str(s/'ocean/nethack'),'-I'+str(r/'engine-baseline/include'),'-I/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include','-I/puffertank/pufferlib/raylib-5.5_linux_amd64/include',str(root/(w+'.c')),'-L'+str(r/'lib'),'-Wl,-rpath,'+str(r/'lib'),'-lnethack','-lm','-ldl','-o',str(root/(w+'-'+kind))])
 corpus=r/('depth-record-v2' if w=='depth' else 'score-record')
 paths=list(map(str,sorted(corpus.glob('*.trace'))));assert len(paths)==512
 for kind in ['static','ws','pool']:
  run(w+'-verify-multi-'+kind,[str(root/(w+'-'+kind)),'verify','8','0','40000',*paths],dict(NH_DISC_SWAP='1' if w=='depth' else '0'))
for w in ['depth','score']:
 n=r/'shared-pool'/w;corpus=r/('depth-record-v2' if w=='depth' else 'score-record')
 paths=list(map(str,sorted(corpus.glob('*.trace'))));assert len(paths)==512
 for threads,cores in [(8,'0,2,4,6,8,10,12,14'),(32,'0-31')]:
  for old,new in [('static','ws'),('ws','pool')]:
   for rep in range(3):
    for phase,kind in [('before',old),('candidate',new),('after',old)]:
     label=f'{w}-{threads}-{old}-vs-{new}-r{rep}-{phase}'
     row=run(label,['taskset','-c',cores,str(root/(w+'-'+kind)),'time',str(threads),'20000','20000',*paths],dict(NH_DISC_SWAP='1' if w=='depth' else '0',OMP_PROC_BIND='false'))
     bench.append(dict(row,workload=f'{w}-512env-4buffers-{threads}threads-warm20k',variant=kind,mode='time',label=f'{old}-vs-{new}-r{rep}-{phase}',library_sha256=hashlib.sha256((r/'variants/candidate03/libnethack.so').read_bytes()).hexdigest()))
     (root/'replay-timings.json').write_text(json.dumps(bench,indent=2))
print('DONE',flush=True)
