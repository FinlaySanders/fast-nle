from pathlib import Path
import os,select,subprocess,json,time,hashlib,re,shutil
r=Path(__file__).resolve().parent;root=r/'shared-pool-cas'
pid=int((r/'late512-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
prior=json.loads((r/'late512/replay-timings.json').read_text());assert len(prior)==72 and all(x['rc']==0 for x in prior),'late512 prerequisite failed'
rows=[];bench=[];e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS','NVCC_EXTRA')}
e.update(NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'variants/candidate03'),NH_ZT_MASK='0',CUDA_VISIBLE_DEVICES='0')
def run(label,cmd,cwd=None,extra=None):
 log=root/(label+'.log');start=time.time()
 with log.open('w') as f:p=subprocess.run(cmd,cwd=cwd,env=dict(e,**(extra or {})),stdout=f,stderr=subprocess.STDOUT)
 row=dict(label=label,command=cmd,rc=p.returncode,seconds=time.time()-start,stdout=log.read_text(errors='replace'),log=str(log));rows.append(row);(root/'results.json').write_text(json.dumps(rows,indent=2));print(label,p.returncode,flush=True)
 if p.returncode and label.startswith('stress-tsan') and 'ThreadSanitizer: unexpected memory mapping' in row['stdout']: return row
 assert p.returncode==0,row['stdout'][-2000:]
 return row
for name,flags in [('regular',[]),('asan',['-fsanitize=address,undefined']),('tsan',['-fsanitize=thread'])]:
 run('build-stress-'+name,['cc','-O1','-g','-pthread',*flags,str(root/'stress.c'),'-o',str(root/('stress-'+name))])
 if name=='tsan':
  for attempt in range(5):
   result=run('stress-tsan-attempt'+str(attempt),[str(root/'stress-tsan')])
   if result['rc']==0:break
  assert result['rc']==0,'TSAN runtime never initialized; do not count unsupported runtime as pass'
 else:run('stress-'+name,[str(root/('stress-'+name))])
for w in ['depth','score']:
 s=r/'shared-pool'/w/'source'
 run(w+'-build',['cc','-O2','-g','-fopenmp','-pthread','-DREPLAY_POOL=1','-I'+str(root),'-I'+str(s/'src'),'-I'+str(s/'ocean/nethack'),'-I'+str(r/'engine-baseline/include'),'-I/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include','-I/puffertank/pufferlib/raylib-5.5_linux_amd64/include',str(r/'late512'/(w+'.c')),'-L'+str(r/'lib'),'-Wl,-rpath,'+str(r/'lib'),'-lnethack','-lm','-ldl','-o',str(root/(w+'-cas'))])
 corpus=r/('depth-record-v2' if w=='depth' else 'score-record');paths=list(map(str,sorted(corpus.glob('*.trace'))));assert len(paths)==512
 run(w+'-verify',[str(root/(w+'-cas')),'verify','8','0','40000',*paths],extra={'NH_DISC_SWAP':'1' if w=='depth' else '0'})
 for threads,cores in [(8,'0,2,4,6,8,10,12,14'),(32,'0-31')]:
  for rep in range(3):
   for phase,kind in [('before','pool'),('candidate','cas'),('after','pool')]:
    binary=r/'late512'/(w+'-pool') if kind=='pool' else root/(w+'-cas')
    row=run(f'{w}-{threads}-r{rep}-{phase}',['taskset','-c',cores,str(binary),'time',str(threads),'20000','20000',*paths],extra=dict(NH_DISC_SWAP='1' if w=='depth' else '0',OMP_PROC_BIND='false'))
    bench.append(dict(row,workload=f'{w}-512env-{threads}threads',variant=kind,mode='time',label=f'pool-vs-cas-r{rep}-{phase}'))
    (root/'timings.json').write_text(json.dumps(bench,indent=2))
# Same native/training source as original warmtrain; replace only claim function.
old=r/'warmtrain/source';dest=root/'source'
def ignore(path,names):return [n for n in names if Path(path)==old and (n.startswith('puffer_') or n=='build')]
shutil.copytree(old,dest,symlinks=True,ignore=ignore);shutil.copy2(root/'env_pool.h',dest/'src/env_pool.h')
run('native-build',['bash','build.sh','nethack','puffer_pool_cas'],dest,{'NVCC_EXTRA':'-DPUF_PERF_LOAD=1 -DPUF_ENV_POOL=1'})
tr=root/'native-traces';tr.mkdir();cmd=json.loads((r/'smoke-command.json').read_text());cmd[0]=str(dest/'puffer_pool_cas')
run('native-verify',cmd,dest,dict(NH_DISC_SWAP='1',NH_PERF_RECORD=str(tr),PUF_POOL_WORKERS='4'))
for p in tr.glob('*.trace'):assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((r/'harness-v4/depth/fresh-traces'/p.name).read_bytes()).digest()
ckpt=Path('/puffertank/experiments/depth4b-20260916/checkpoints/nethack/depth4b_s901/0000003999989760.bin');cksha=hashlib.sha256(ckpt.read_bytes()).hexdigest();args=json.loads(Path('/puffertank/experiments/depth4b-20260916/manifest.json').read_text())['args']
for rep in range(3):
 for phase,kind in [('before','pool'),('candidate','cas'),('after','pool')]:
  label=f'train-r{rep}-{phase}';out=root/label;out.mkdir();proof=out/'loaded.bin'
  binary=r/'warmtrain/source/puffer_pool' if kind=='pool' else dest/'puffer_pool_cas'
  cmd=[str(binary),'train','--headless',*args,'--train.total_timesteps=4194304','--base.seed=900','--base.run_id=perf_warm','--base.eval_episodes=8','--base.eval_agents=8',f'--base.checkpoint_dir={out}/checkpoints',f'--base.log_dir={out}/logs']
  row=run(label,cmd,dest,dict(NH_DISC_SWAP='1',OMP_NUM_THREADS='24',PUF_POOL_WORKERS='12',PUF_PERF_START_WEIGHTS=str(ckpt),PUF_PERF_LOADED_PROOF=str(proof)))
  assert hashlib.sha256(proof.read_bytes()).hexdigest()==cksha
  assert (out/'checkpoints/nethack/perf_warm/0000000004194304.bin').exists()
  assert not re.search(r'(?i)(?:^|\s)(?:nan|[+-]?inf)(?:\s|$)',row['stdout'])
print('DONE',flush=True)
