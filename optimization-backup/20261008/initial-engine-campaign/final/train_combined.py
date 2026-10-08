from pathlib import Path
import os,select,subprocess,json,time,hashlib,re
r=Path('/puffertank/experiments/nethack-perf-20260917');root=r/'tight-loop/campaign2h/training-combined';root.mkdir();rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS','NVCC_EXTRA')};e.update(NETHACKDIR=str(r/'dat'),NH_ZT_MASK='0',CUDA_VISIBLE_DEVICES='0')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(label,cmd,cwd,env):
 t=time.time();log=root/(label+'.log')
 with log.open('w') as f:p=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
 row=dict(label=label,command=cmd,rc=p.returncode,seconds=time.time()-t,log=str(log),stdout=log.read_text(errors='replace'));rows.append(row);(root/'results.json').write_text(json.dumps(rows,indent=2));print(label,p.returncode,flush=True);assert p.returncode==0,row['stdout'][-2000:];return row
for policy in ['depth','score']:
 s=r/('warmtrain' if policy=='depth' else 'warmtrain-score')/'source';env=dict(e,NH_DISC_SWAP='1' if policy=='depth' else '0',OMP_NUM_THREADS='24' if policy=='depth' else '32')

 ckpt=Path('/puffertank/experiments/depth4b-20260916/checkpoints/nethack/depth4b_s901/0000003999989760.bin') if policy=='depth' else Path('/puffertank/pufferlib/resources/nethack/fixwt4b_s705.bin');cksha=sha(ckpt)
 args=json.loads(Path('/puffertank/experiments/depth4b-20260916/manifest.json').read_text())['args'] if policy=='depth' else ['--base.env_name=nethack']
 steps=4194304 if policy=='depth' else 33554432;epochs=64 if policy=='depth' else 128
 for comparison,arms in [('combined',[('before','baseline','static'),('candidate','optimized','ws'),('after','baseline','static')])]:
  for phase,variant,kind in arms:
   label=policy+'-'+comparison+'-'+phase;out=root/label;out.mkdir();proof=out/'loaded.bin';lib=r/'lib' if variant=='baseline' else r/'variants/candidate14-lto-local'
   cmd=[str(s/('puffer_'+kind)),'train','--headless',*args,f'--train.total_timesteps={steps}','--base.seed=901','--base.run_id=perf_warm','--base.eval_episodes=8','--base.eval_agents=8',f'--base.checkpoint_dir={out}/checkpoints',f'--base.log_dir={out}/logs']
   row=run(label,cmd,s,dict(env,LD_LIBRARY_PATH=str(lib),PUF_PERF_START_WEIGHTS=str(ckpt),PUF_PERF_LOADED_PROOF=str(proof)))
   assert sha(proof)==cksha,'loaded weights mismatch';files=list((out/'checkpoints/nethack/perf_warm').glob('*.bin'));assert files and max(int(p.stem) for p in files)>=steps
   intervals=[dict(re.findall(r'(\w+)=([^ ]+)',line)) for line in row['stdout'].splitlines() if line.startswith('PERF_EPOCH ')];assert len(intervals)==epochs
   assert not re.search(r'(?i)(?:^|\s)(?:nan|[+-]?inf)(?:\s|$)',row['stdout'])
   row.update(initial_weights_sha256=cksha,engine_sha256=sha(lib/'libnethack.so'),binary_sha256=sha(s/('puffer_'+kind)),intervals=intervals,later_half_seconds=sum(float(x['seconds']) for x in intervals[epochs//2:]),mean_later_game_turn=sum(float(x['mean_turn']) for x in intervals[epochs//2:])/(epochs//2),max_game_turn=max(int(x['max_turn']) for x in intervals),scope='4B initial policy; fresh optimizer; original PPO/rewards; compare later interval, not claim all games late')
   (root/'results.json').write_text(json.dumps(rows,indent=2))
print('DONE',flush=True)
