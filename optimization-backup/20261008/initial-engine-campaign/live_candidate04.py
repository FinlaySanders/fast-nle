"""Integration checks for candidate04; not a claim that it is the final accepted engine."""
from pathlib import Path
import os,select,subprocess,json,hashlib,re
r=Path(__file__).resolve().parent
pid=int((r/'candidate04-windows-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
assert (r/'candidate04-windows-runner.log').read_text().rstrip().endswith('DONE'),'window benchmarks failed'
env={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')}
env.update(NETHACKDIR=str(r/'dat'),NH_ZT_MASK='0',CUDA_VISIBLE_DEVICES='0')
results=[]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
for w in ['depth','score']:
 n=r/'harness-v4'/w;s=n/'source';out=n/'candidate-live';out.mkdir();traces=out/'traces';raw=out/'observations';traces.mkdir();raw.mkdir()
 cmd=json.loads((r/('smoke-command.json' if w=='depth' else 'score-smoke-command.json')).read_text());cmd[0]=str(s/'puffer')
 e=dict(env,NH_DISC_SWAP='1' if w=='depth' else '0',LD_LIBRARY_PATH=str(r/'variants/candidate04'),OMP_NUM_THREADS='4',NH_PERF_RECORD=str(traces),NH_PERF_SNAPSHOTS=str(raw))
 with (out/'run.log').open('w') as f:p=subprocess.run(cmd,cwd=s,env=e,stdout=f,stderr=subprocess.STDOUT)
 assert p.returncode==0,(w,p.returncode)
 files=[]
 for folder,ref in [(traces,n/'fresh-traces'),(raw,n/'fresh-observations')]:
  for x in sorted(folder.iterdir()):
   h=sha(x);assert h==sha(ref/x.name),(w,x.name,'live candidate differs from frozen baseline inference')
   files.append(dict(path=str(x),sha256=h,bytes=x.stat().st_size))
 results.append(dict(kind='live-eval',workload=w,command=cmd,files=files));(r/'candidate04-integration.json').write_text(json.dumps(results,indent=2));print(w,'live inference exact',flush=True)
# Preserve archived depth PPO/reward/vector settings, changing budget/output and loading frozen policy.
args=json.loads(Path('/puffertank/experiments/depth4b-20260916/manifest.json').read_text())['args']
ckpt='/puffertank/experiments/depth4b-20260916/checkpoints/nethack/depth4b_s901/0000003999989760.bin'
for v in ['baseline','candidate04']:
 out=r/('training-smoke-'+v);out.mkdir();s=r/'harness-v4/depth/source';lib=r/'lib' if v=='baseline' else r/'variants'/v
 cmd=[str(s/'puffer'),'train','--headless',*args,'--train.total_timesteps=524288','--base.seed=900','--base.run_id=perf_smoke','--base.eval_episodes=8','--base.eval_agents=8',f'--base.load_model_path={ckpt}',f'--base.checkpoint_dir={out}/checkpoints',f'--base.log_dir={out}/logs']
 e=dict(env,NH_DISC_SWAP='1',LD_LIBRARY_PATH=str(lib),OMP_NUM_THREADS='24')
 with (out/'run.log').open('w') as f:p=subprocess.run(cmd,cwd=s,env=e,stdout=f,stderr=subprocess.STDOUT)
 assert p.returncode==0,(v,'training failed',p.returncode)
 files=sorted((out/'checkpoints/nethack/perf_smoke').glob('*.bin'));assert files,'no checkpoint'
 final=max(files,key=lambda p:int(p.stem));assert int(final.stem)>=458752,('insufficient training',final)
 log=(out/'run.log').read_text(errors='replace');assert not re.search(r'(?i)(?:^|\s)(?:nan|[+-]?inf)(?:\s|$)',log),'non-finite printed metric'
 results.append(dict(kind='short-training',variant=v,command=cmd,checkpoint=str(final),sha256=sha(final),checkpoint_step=int(final.stem),returncode=p.returncode));(r/'candidate04-integration.json').write_text(json.dumps(results,indent=2));print(v,'short training passed',flush=True)
print('DONE',flush=True)
