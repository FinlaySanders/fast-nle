from pathlib import Path
import os,subprocess,json,hashlib,time,re,datetime
r=Path(__file__).parent;s=Path('/puffertank/experiments/nethack-workspace-safe-20260917/source');out=r/'pgo61-training';out.mkdir()
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_LIBRARY_PATH','LD_PRELOAD','NETHACKOPTIONS','NVCC_EXTRA')}
ckpt=Path('/puffertank/pufferlib/resources/nethack/fixwt4b_s705.bin');e.update(NETHACKDIR='/puffertank/experiments/nethack-perf-20260917/dat',NH_ZT_MASK='0',NH_DISC_SWAP='0',CUDA_VISIBLE_DEVICES='0',LD_LIBRARY_PATH='/puffertank/experiments/nethack-perf-20260917/variants/candidate14-lto-local',PUF_PERF_START_WEIGHTS=str(ckpt))
phases=[('baseline-before',32,{}),('pgo61',32,{'LD_LIBRARY_PATH':str(r/'pgo61/variant')}),('baseline-after',32,{})]
for label,workers,extra in phases:
 d=out/label;d.mkdir();cmd=[str(s/'puffer_safe'),'train','--headless','--base.env_name=nethack','--train.total_timesteps=8388608','--vec.num_threads='+str(workers),'--base.seed=901','--base.run_id=screen','--base.eval_episodes=8','--base.eval_agents=8','--base.checkpoint_dir='+str(d/'checkpoints'),'--base.log_dir='+str(d/'logs')]
 env=dict(e,OMP_NUM_THREADS=str(workers),PUF_PERF_LOADED_PROOF=str(d/'loaded.bin'),**extra)
 print('START',label,flush=True);start=time.time()
 with (d/'log').open('w') as f:
  p=subprocess.Popen(cmd,cwd=s,env=env,stdout=f,stderr=subprocess.STDOUT);(r/'active-process.json').write_text(json.dumps(dict(pid=p.pid,command=cmd,label=label,started=time.time()),indent=2));rc=p.wait()
 import numpy as np
 for weight in (d/'checkpoints').rglob('*.bin'):
  assert np.isfinite(np.fromfile(weight,dtype=np.float32)).all(),str(weight)
 txt=(d/'log').read_text(errors='replace');epochs=[dict(re.findall(r'(\w+)=([^\s]+)',line)) for line in re.findall(r'PERF_EPOCH [^\n]+',txt)]
 assert rc==0 and [int(x['epoch']) for x in epochs]==list(range(32)),(label,rc)
 assert hashlib.sha256((d/'loaded.bin').read_bytes()).digest()==hashlib.sha256(ckpt.read_bytes()).digest()
 assert not re.search(r'(?i)(?<!\w)(nan|[+-]?inf)(?!\w)',txt)
 selected=epochs[16:31];seconds=sum(float(x['seconds']) for x in selected)
 result=dict(candidate=label,workers=workers,environment_overrides=extra,command=cmd,seconds=seconds,steps=15*262144,sps=15*262144/seconds,mean_turn=sum(float(x['mean_turn']) for x in selected)/15,epochs=epochs,wall_seconds=time.time()-start,correctness='completed, finite weights/log, loaded checkpoint hash verified; engine correctness audited separately',decision='screen only; agent must confirm before retaining')
 (d/'result.json').write_text(json.dumps(result,indent=2))
 with (r/'ledger.jsonl').open('a') as f:f.write(json.dumps(dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),**{k:v for k,v in result.items() if k!='epochs'}))+'\n')
 print('DONE',label,'seconds',seconds,'mean_turn',result['mean_turn'],flush=True)
print('SCREEN_COMPLETE; adaptive agent review required',flush=True)
