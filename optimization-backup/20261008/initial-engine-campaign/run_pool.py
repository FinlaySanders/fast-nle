from pathlib import Path
import os,select,subprocess,json,time,hashlib,re
r=Path(__file__).resolve().parent;root=r/'shared-pool'
pid=int((r/'workstealing-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
assert (r/'workstealing-runner.log').read_text().rstrip().endswith('DONE'), 'WS prerequisite did not finish successfully'
rows=[]
env={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS','NVCC_EXTRA')}
env.update(NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'variants/candidate03'),NH_ZT_MASK='0',CUDA_VISIBLE_DEVICES='0')
def run(label,cmd,cwd=None,extra=None,required=True):
 start=time.time();log=root/(label+'.log');e=dict(env,**(extra or {}))
 ps=subprocess.check_output(['ps','-eo','pid,ppid,comm,pcpu'],text=True)
 with log.open('w') as f:p=subprocess.run(cmd,cwd=cwd,env=e,stdout=f,stderr=subprocess.STDOUT,timeout=1800)
 text=log.read_text(errors='replace');row=dict(label=label,command=cmd,elapsed=time.time()-start,rc=p.returncode,log=str(log),stdout=text,processes_before=ps)
 rows.append(row);(root/'results.json').write_text(json.dumps(rows,indent=2));print(label,p.returncode,flush=True)
 if required and p.returncode:raise RuntimeError(label+' failed: '+text[-2000:])
 return row
for kind,flags in [('regular',[]),('asan',['-fsanitize=address,undefined']),('tsan',['-fsanitize=thread'])]:
 exe=root/('stress-'+kind)
 run('build-stress-'+kind,['cc','-O1','-g','-pthread',*flags,str(root/'stress.c'),'-o',str(exe)])
 row=run('stress-'+kind,[str(exe)],required=kind!='tsan')
 if row['rc'] and kind=='tsan':
  assert 'unexpected memory mapping' in row['stdout'], 'TSAN reported a real failure; stop'
  print('TSAN unavailable: runtime memory-mapping error, not a pass',flush=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
for w in ['depth','score']:
 s=root/w/'source'
 run(w+'-build-native-pool',['bash','build.sh','nethack','puffer_pool'],s,{'NVCC_EXTRA':'-DPUF_ENV_POOL=1'})
 base=json.loads((r/('smoke-command.json' if w=='depth' else 'score-smoke-command.json')).read_text())
 for buffers in [1,4]:
  proofs={}
  for kind in ['ws','pool']:
   out=root/w/f'live-{buffers}-{kind}';out.mkdir();traces=out/'traces';raw=out/'observations';traces.mkdir();raw.mkdir()
   binary=(r/'scheduling'/w/'source/puffer_ws') if kind=='ws' else s/'puffer_pool'
   cmd=[str(binary),*[x for x in base[1:] if not x.startswith(('--vec.num_buffers=','--vec.num_threads='))],f'--vec.num_buffers={buffers}','--vec.num_threads=8']
   run(w+f'-native-{buffers}-{kind}',cmd,s,dict(NH_DISC_SWAP='1' if w=='depth' else '0',NH_PERF_RECORD=str(traces),NH_PERF_SNAPSHOTS=str(raw),OMP_NUM_THREADS='8',PUF_POOL_WORKERS='4'))
   proofs[kind]={str(p.relative_to(out)):sha(p) for folder in [traces,raw] for p in sorted(folder.iterdir())}
  assert proofs['ws']==proofs['pool'],(w,buffers,'pool changed trajectory')
  (root/w/f'proof-{buffers}.json').write_text(json.dumps(proofs,indent=2))
args=json.loads(Path('/puffertank/experiments/depth4b-20260916/manifest.json').read_text())['args']
ckpt='/puffertank/experiments/depth4b-20260916/checkpoints/nethack/depth4b_s901/0000003999989760.bin'
s=root/'depth/source'
for rep in range(3):
 for phase,kind in [('before','ws'),('candidate','pool'),('after','ws')]:
  label=f'train-r{rep}-{phase}';out=root/label;out.mkdir()
  binary=r/'scheduling/depth/source/puffer_ws' if kind=='ws' else s/'puffer_pool'
  cmd=[str(binary),'train','--headless',*args,'--train.total_timesteps=1048576','--base.seed=900','--base.run_id=perf_smoke','--base.eval_episodes=8','--base.eval_agents=8',f'--base.load_model_path={ckpt}',f'--base.checkpoint_dir={out}/checkpoints',f'--base.log_dir={out}/logs']
  row=run(label,cmd,s,dict(NH_DISC_SWAP='1',OMP_NUM_THREADS='24',PUF_POOL_WORKERS='12'))
  files=list((out/'checkpoints/nethack/perf_smoke').glob('*.bin'));assert files and max(int(p.stem) for p in files)>=983040
  assert not re.search(r'(?i)(?:^|\s)(?:nan|[+-]?inf)(?:\s|$)',row['stdout'])
print('DONE',flush=True)
