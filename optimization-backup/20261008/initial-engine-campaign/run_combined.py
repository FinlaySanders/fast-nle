"""Direct combined-engine/scheduler comparison. Run only after candidate selection and queue drain."""
from pathlib import Path
import argparse,os,subprocess,json,time,hashlib,re
r=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--engine',choices=['candidate03','candidate05-normal'],required=True);p.add_argument('--scheduler',choices=['ws','pool'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=a.output.resolve();root.mkdir();rows=[];bench=[]
base=r/'engine-baseline/build';candidate=r/'variants'/a.engine
for lib in [base,candidate]:assert (lib/'libnethack.so').is_file()
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS','NVCC_EXTRA')}
e.update(NETHACKDIR=str(r/'dat'),NH_ZT_MASK='0',CUDA_VISIBLE_DEVICES='0',OMP_NUM_THREADS='24',PUF_POOL_WORKERS='12')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
manifest=dict(engine=a.engine,scheduler=a.scheduler,baseline_engine_sha256=sha(base/'libnethack.so'),candidate_engine_sha256=sha(candidate/'libnethack.so'),scope='Direct combined comparison; no multiplication of separate speedups')
(root/'manifest.json').write_text(json.dumps(manifest,indent=2))
def run(label,cmd,extra=None,cwd=None):
 log=root/(label+'.log');start=time.time()
 with log.open('w') as f:q=subprocess.run(cmd,env=dict(e,**(extra or {})),cwd=cwd,stdout=f,stderr=subprocess.STDOUT)
 row=dict(label=label,command=cmd,elapsed=time.time()-start,rc=q.returncode,stdout=log.read_text(errors='replace'),log=str(log));rows.append(row);(root/'results.json').write_text(json.dumps(rows,indent=2));print(label,q.returncode,flush=True)
 assert q.returncode==0,row['stdout'][-2000:]
 return row
for w in ['depth','score']:
 swap='1' if w=='depth' else '0';corpus=r/('depth-record-v2' if w=='depth' else 'score-record');paths=sorted(map(str,corpus.glob('*.trace')));assert len(paths)==512
 for label,kind,lib in [('baseline','static',base),('combined',a.scheduler,candidate)]:
  exe=r/'late512'/(w+'-'+kind);assert exe.is_file()
  run(w+'-verify-'+label,[str(exe),'verify','8','0','40000',*paths],dict(LD_LIBRARY_PATH=str(lib),NH_DISC_SWAP=swap))
 for rep in range(3):
  for phase,kind,lib in [('before','static',base),('candidate',a.scheduler,candidate),('after','static',base)]:
   row=run(f'{w}-r{rep}-{phase}',['taskset','-c','0,2,4,6,8,10,12,14',str(r/'late512'/(w+'-'+kind)),'time','8','20000','20000',*paths],dict(LD_LIBRARY_PATH=str(lib),NH_DISC_SWAP=swap,OMP_PROC_BIND='false'))
   bench.append(dict(row,workload=w+'-combined-512env-8cores',variant='combined' if phase=='candidate' else 'baseline',mode='time',library_sha256=sha(lib/'libnethack.so')));(root/'timings.json').write_text(json.dumps(bench,indent=2))
 # Native one-buffer inference: frozen actions and raw observations must match.
 s=r/'shared-pool'/w/'source'
 run(w+'-build-native',['bash','build.sh','nethack','puffer_combined'],dict(NVCC_EXTRA='-DPUF_ENV_'+('WS' if a.scheduler=='ws' else 'POOL')+'=1'),s)
 out=root/(w+'-native');out.mkdir();traces=out/'traces';raw=out/'observations';traces.mkdir();raw.mkdir()
 cmd=json.loads((r/('smoke-command.json' if w=='depth' else 'score-smoke-command.json')).read_text());cmd[0]=str(s/'puffer_combined')
 run(w+'-native',cmd,dict(LD_LIBRARY_PATH=str(candidate),NH_DISC_SWAP=swap,NH_PERF_RECORD=str(traces),NH_PERF_SNAPSHOTS=str(raw),OMP_NUM_THREADS='4'),s)
 for folder,reference in [(traces,r/'harness-v4'/w/'fresh-traces'),(raw,r/'harness-v4'/w/'fresh-observations')]:
  files=sorted(folder.iterdir());assert len(files)==8,(w,folder,len(files))
  assert {x.name for x in files}=={x.name for x in reference.iterdir()}
  for x in files:assert sha(x)==sha(reference/x.name),(w,x.name,'native mismatch')
 # This does not claim graph-enabled multi-buffer bitwise inference determinism.
args=json.loads(Path('/puffertank/experiments/depth4b-20260916/manifest.json').read_text())['args'];weights=Path('/puffertank/experiments/depth4b-20260916/checkpoints/nethack/depth4b_s901/0000003999989760.bin');digest=sha(weights);s=r/'warmtrain/source'
for rep in range(3):
 for phase,kind,lib in [('before','static',base),('candidate',a.scheduler,candidate),('after','static',base)]:
  label=f'train-r{rep}-{phase}';out=root/label;out.mkdir();proof=out/'loaded.bin'
  cmd=[str(s/('puffer_'+kind)),'train','--headless',*args,'--train.total_timesteps=4194304','--base.seed=900','--base.run_id=perf_combined','--base.eval_episodes=8','--base.eval_agents=8',f'--base.checkpoint_dir={out}/checkpoints',f'--base.log_dir={out}/logs']
  row=run(label,cmd,dict(LD_LIBRARY_PATH=str(lib),NH_DISC_SWAP='1',PUF_PERF_START_WEIGHTS=str(weights),PUF_PERF_LOADED_PROOF=str(proof)),s)
  assert sha(proof)==digest
  checkpoints=list((out/'checkpoints/nethack/perf_combined').glob('*.bin'));assert checkpoints and max(int(x.stem) for x in checkpoints)>=4194304
  assert not re.search(r'(?i)(?:^|\s)(?:nan|[+-]?inf)(?:\s|$)',row['stdout'])
  intervals=[dict(re.findall(r'(\w+)=([^ ]+)',line)) for line in row['stdout'].splitlines() if line.startswith('PERF_EPOCH ')];assert len(intervals)==64
  row.update(initial_weights_sha256=digest,intervals=intervals,late_half_seconds=sum(float(x['seconds']) for x in intervals[32:]));(root/'results.json').write_text(json.dumps(rows,indent=2))
assert sha(base/'libnethack.so')==manifest['baseline_engine_sha256'] and sha(candidate/'libnethack.so')==manifest['candidate_engine_sha256']
print('DONE direct combined replay, native one-buffer parity and loaded-policy training',flush=True)
