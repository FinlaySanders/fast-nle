from pathlib import Path
from collections import Counter
import os,subprocess,json
r=Path(__file__).parent;d=r/'affinity13-proof';d.mkdir();s=r/'affinity13-source';e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_LIBRARY_PATH','LD_PRELOAD','NETHACKOPTIONS')};e.update(NETHACKDIR='/puffertank/experiments/nethack-perf-20260917/dat',NH_DISC_SWAP='0',NH_ZT_MASK='0',CUDA_VISIBLE_DEVICES='0',OMP_NUM_THREADS='32',LD_LIBRARY_PATH=str(r/'pgo08/variant'),PUF_ROLLOUT_BLOCKS='2',PUF_PERF_LOADED_PROOF=str(d/'loaded.bin'))
cmd=[str(s/'puffer_affinity'),'eval','--headless','--load-model-path=/puffertank/pufferlib/resources/nethack/fixwt4b_s705.bin','--base.eval_agents=512','--vec.num_buffers=4','--vec.num_threads=32','--base.eval_episodes=1000000000','--base.seed=901'];p=subprocess.Popen(cmd,cwd=s,env=e,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);masks=None
with (d/'log').open('w') as f:
 for line in p.stdout:
  f.write(line)
  if 'ROLLOUT_BLOCK block=0 ' in line:
   masks=Counter(next(l.split(':',1)[1].strip() for l in q.read_text().splitlines() if l.startswith('Cpus_allowed_list:')) for q in Path('/proc',str(p.pid),'task').glob('*/status'))
rc=p.wait();assert rc==0 and masks
(d/'proof.json').write_text(json.dumps(dict(command=cmd,thread_affinity_counts=dict(masks)),indent=2));print(dict(masks),flush=True)
for mask in ['0-3,16-19','4-7,20-23','8-11,24-27','12-15,28-31']:assert masks[mask]==8,(mask,masks)
print('AFFINITY_INHERITANCE_VERIFIED',flush=True)
