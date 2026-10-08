from pathlib import Path
import os,select,subprocess,json,time,hashlib,re
r=Path(__file__).resolve().parent;root=r/'warmtrain';s=root/'source'
pid=int((r/'pthread-replay-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
assert (r/'pthread-replay-runner.log').read_text().rstrip().endswith('DONE'),'replay prerequisite failed'
rows=[];e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS','NVCC_EXTRA')}
e.update(NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'variants/candidate03'),NH_ZT_MASK='0',CUDA_VISIBLE_DEVICES='0',NH_DISC_SWAP='1',OMP_NUM_THREADS='24',PUF_POOL_WORKERS='12')
def run(label,cmd,extra=None):
 start=time.time();log=root/(label+'.log')
 with log.open('w') as f:p=subprocess.run(cmd,cwd=s,env=dict(e,**(extra or {})),stdout=f,stderr=subprocess.STDOUT,timeout=1800)
 row=dict(label=label,command=cmd,elapsed=time.time()-start,rc=p.returncode,stdout=log.read_text(errors='replace'),log=str(log))
 rows.append(row);(root/'results.json').write_text(json.dumps(rows,indent=2));print(label,p.returncode,flush=True)
 assert p.returncode==0,row['stdout'][-2000:]
 return row
for kind,flag in [('static',''),('ws','-DPUF_ENV_WS=1'),('pool','-DPUF_ENV_POOL=1')]:
 run('build-'+kind,['bash','build.sh','nethack','puffer_'+kind],{'NVCC_EXTRA':'-DPUF_PERF_LOAD=1 '+flag})
ckpt=Path('/puffertank/experiments/depth4b-20260916/checkpoints/nethack/depth4b_s901/0000003999989760.bin');cksha=hashlib.sha256(ckpt.read_bytes()).hexdigest()
args=json.loads(Path('/puffertank/experiments/depth4b-20260916/manifest.json').read_text())['args']
# Same archived hyperparameters/rewards for every arm. Start with proven4B weights,
# fresh optimizer, and compare later intervals separately from total process wall.
for old,new in [('static','ws'),('ws','pool')]:
 for rep in range(3):
  for phase,kind in [('before',old),('candidate',new),('after',old)]:
   label=f'{old}-vs-{new}-r{rep}-{phase}';out=root/label;out.mkdir();proof=out/'loaded.bin'
   cmd=[str(s/('puffer_'+kind)),'train','--headless',*args,'--train.total_timesteps=4194304','--base.seed=900','--base.run_id=perf_warm','--base.eval_episodes=8','--base.eval_agents=8',f'--base.checkpoint_dir={out}/checkpoints',f'--base.log_dir={out}/logs']
   row=run(label,cmd,dict(PUF_PERF_START_WEIGHTS=str(ckpt),PUF_PERF_LOADED_PROOF=str(proof)))
   assert hashlib.sha256(proof.read_bytes()).hexdigest()==cksha,'initial weights not identical'
   files=list((out/'checkpoints/nethack/perf_warm').glob('*.bin'));assert files and max(int(p.stem) for p in files)>=4194304
   assert not re.search(r'(?i)(?:^|\s)(?:nan|[+-]?inf)(?:\s|$)',row['stdout'])
   intervals=[]
   for line in row['stdout'].splitlines():
    if line.startswith('PERF_EPOCH '):intervals.append(dict(re.findall(r'(\w+)=([^ ]+)',line)))
   assert len(intervals)==64,(label,len(intervals))
   row.update(initial_weights_sha256=cksha,intervals=intervals,late_half_seconds=sum(float(x['seconds']) for x in intervals[32:]),scope='4B weights, fresh optimizer, original PPO. Later half excludes first2Msteps; report observed game turns, not assume late game.')
   (root/'results.json').write_text(json.dumps(rows,indent=2))
print('DONE',flush=True)
