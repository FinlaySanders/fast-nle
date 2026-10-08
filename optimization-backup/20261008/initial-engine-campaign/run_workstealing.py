from pathlib import Path
import os,select,subprocess,json,time,hashlib,re
r=Path(__file__).resolve().parent
pid=int((r/'candidate04-live-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
# Prior jobs need to be terminal for uncontended measurements; failures remain visible.
rows=[]
env={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS','NVCC_EXTRA')}
env.update(NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'variants/candidate03'),NH_ZT_MASK='0',CUDA_VISIBLE_DEVICES='0')
def run(label,cmd,cwd=None,extra=None):
 start=time.time();log=r/'scheduling'/(label+'.log');e=dict(env,**(extra or {}))
 ps=subprocess.check_output(['ps','-eo','pid,ppid,comm,pcpu'],text=True)
 with log.open('w') as f:p=subprocess.run(cmd,cwd=cwd,env=e,stdout=f,stderr=subprocess.STDOUT)
 text=log.read_text(errors='replace');row=dict(label=label,command=cmd,elapsed=time.time()-start,rc=p.returncode,log=str(log),stdout=text,processes_before=ps)
 rows.append(row);(r/'scheduling/results.json').write_text(json.dumps(rows,indent=2));print(label,p.returncode,flush=True)
 if p.returncode:raise RuntimeError(label+' failed: '+text[-2000:])
 return row
for w in ['depth','score']:
 n=r/'scheduling'/w;s=n/'source'
 for kind in ['static','ws']:
  run(w+'-build-replay-'+kind,['cc','-O2','-g','-fopenmp','-I'+str(s/'src'),'-I'+str(s/'ocean/nethack'),'-I'+str(r/'engine-baseline/include'),'-I/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include','-I/puffertank/pufferlib/raylib-5.5_linux_amd64/include',str(n/('replay_'+kind+'.c')),'-L'+str(r/'lib'),'-Wl,-rpath,'+str(r/'lib'),'-lnethack','-lm','-ldl','-o',str(n/('replay_'+kind))])
  run(w+'-build-native-'+kind,['bash','build.sh','nethack','puffer_'+kind],s,{'NVCC_EXTRA':'-DPUF_ENV_WS=1' if kind=='ws' else ''})
 # Raw policy inference equivalence vs original fixed recording; eight envs, one buffer.
 out=n/'ws-live';out.mkdir();traces=out/'traces';raw=out/'observations';traces.mkdir();raw.mkdir()
 cmd=json.loads((r/('smoke-command.json' if w=='depth' else 'score-smoke-command.json')).read_text());cmd[0]=str(s/'puffer_ws')
 run(w+'-native-verify',cmd,s,dict(NH_DISC_SWAP='1' if w=='depth' else '0',NH_PERF_RECORD=str(traces),NH_PERF_SNAPSHOTS=str(raw),OMP_NUM_THREADS='4'))
 def sha(p):
  h=hashlib.sha256()
  with p.open('rb') as f:
   while b:=f.read(1048576):h.update(b)
  return h.hexdigest()
 proof=[]
 for folder,ref in [(traces,r/'harness-v4'/w/'fresh-traces'),(raw,r/'harness-v4'/w/'fresh-observations')]:
  for p in sorted(folder.iterdir()):
   h=sha(p);assert h==sha(ref/p.name),(w,p.name,'work-stealing changed trajectory');proof.append(dict(path=str(p),sha256=h))
 (n/'native-proof.json').write_text(json.dumps(proof,indent=2))
 corpus=r/('depth-record-v2' if w=='depth' else 'score-balanced-v2')
 paths=[str(corpus/Path(x['path']).name) for x in json.loads((r/(w+'-timing-selected.json')).read_text())]
 for kind in ['static','ws']:
  run(w+'-replay-verify-'+kind,[str(n/('replay_'+kind)),'verify','8','0','1000000',*paths],extra={'NH_DISC_SWAP':'1' if w=='depth' else '0'})
# Same backend/engine for both scheduler binaries; startup+warmup excluded by replay harness.
bench=[]
for w in ['depth','score']:
 n=r/'scheduling'/w;corpus=r/'depth-record-v2' if w=='depth' else r/'score512-prefix-v2'
 paths=list(map(str,sorted(corpus.glob('*.trace'))));assert len(paths)==512
 for threads,cores in [(8,'0,2,4,6,8,10,12,14'),(32,'0-31')]:
  for rep in range(3):
   for phase,kind in [('before','static'),('candidate','ws'),('after','static')]:
    label=f'{w}-{threads}-static-vs-ws-r{rep}-{phase}'
    row=run(label,['taskset','-c',cores,str(n/('replay_'+kind)),'time',str(threads),'2000','2000',*paths],extra={'NH_DISC_SWAP':'1' if w=='depth' else '0','OMP_PROC_BIND':'true','OMP_PLACES':'cores'})
    bench.append(dict(row,workload=f'{w}-{threads}threads',variant=kind,mode='time',label=f'static-vs-ws-r{rep}-{phase}',library_sha256=sha(r/'variants/candidate03/libnethack.so')))
    (r/'scheduling/timings.json').write_text(json.dumps(bench,indent=2))
# Real training wall time, not the possibly misleading panel SPS. Three ABA repeats.
args=json.loads(Path('/puffertank/experiments/depth4b-20260916/manifest.json').read_text())['args']
ckpt='/puffertank/experiments/depth4b-20260916/checkpoints/nethack/depth4b_s901/0000003999989760.bin'
s=r/'scheduling/depth/source'
for rep in range(3):
 for phase,kind in [('before','static'),('candidate','ws'),('after','static')]:
  label=f'train-r{rep}-{phase}';out=r/'scheduling'/label;out.mkdir()
  cmd=[str(s/('puffer_'+kind)),'train','--headless',*args,'--train.total_timesteps=1048576','--base.seed=900','--base.run_id=perf_smoke','--base.eval_episodes=8','--base.eval_agents=8',f'--base.load_model_path={ckpt}',f'--base.checkpoint_dir={out}/checkpoints',f'--base.log_dir={out}/logs']
  row=run(label,cmd,s,dict(NH_DISC_SWAP='1',OMP_NUM_THREADS='24'))
  files=list((out/'checkpoints/nethack/perf_smoke').glob('*.bin'));assert files and max(int(p.stem) for p in files)>=983040
  assert not re.search(r'(?i)(?:^|\s)(?:nan|[+-]?inf)(?:\s|$)',row['stdout'])
print('DONE',flush=True)
