from pathlib import Path
import os,subprocess,json,time,datetime
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'chunks02';d.mkdir();rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',LD_LIBRARY_PATH=str(old/'variants/candidate14-lto-local'),OMP_PROC_BIND='false')
for workload in ['score','depth']:
 text=(old/'late512'/(workload+'.c')).read_text();a='for(;;){int i=__atomic_fetch_add(&next[v*16],1,__ATOMIC_RELAXED);if(i>=hi)break;replay_one(NULL,i);}'
 b='for(;;){int i=__atomic_fetch_add(&next[v*16],REPLAY_CHUNK,__ATOMIC_RELAXED);if(i>=hi)break;int stop=i+REPLAY_CHUNK;if(stop>hi)stop=hi;for(;i<stop;i++)replay_one(NULL,i);}'
 assert a in text;text=text.replace(a,b);src=d/(workload+'.c');src.write_text(text)
 for chunk in [1,2,4,8]:
  s=old/'shared-pool'/workload/'source';cmd=['cc','-O2','-g','-fopenmp','-pthread','-DREPLAY_WS=1','-DREPLAY_CHUNK='+str(chunk),'-I'+str(old/'shared-pool'),'-I'+str(s/'src'),'-I'+str(s/'ocean/nethack'),'-I'+str(old/'engine-baseline/include'),'-I/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include','-I/puffertank/pufferlib/raylib-5.5_linux_amd64/include',str(src),'-L'+str(old/'lib'),'-Wl,-rpath,'+str(old/'lib'),'-lnethack','-lm','-ldl','-o',str(d/f'{workload}-{chunk}')]
  with (d/f'build-{workload}-{chunk}.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
for workload in ['score','depth']:
 corpus=old/('depth-record-v2' if workload=='depth' else 'score-record');paths=[str(corpus/Path(x['path']).name) for x in json.loads((old/(workload+'-timing-selected.json')).read_text())]
 # Identical recorded actions; verify full prefix before measuring each new scheduler.
 cases=[('verify',k) for k in [1,2,4,8]]+[('time',k) for k in [1,2,4,8,1]]
 for index,(mode,k) in enumerate(cases):
  label=f'{workload}-{index}-{mode}-chunk{k}';cmd=['taskset','-c','0,2,4,6,8,10,12,14',str(d/f'{workload}-{k}'),mode,'8','20000','20000',*paths]
  print('START',label,flush=True);t=time.time();p=subprocess.run(cmd,env=dict(e,NH_DISC_SWAP='1' if workload=='depth' else '0'),capture_output=True,text=True);row=dict(label=label,workload=workload,mode=mode,chunk=k,command=cmd,rc=p.returncode,wall_seconds=time.time()-t,stdout=p.stdout,stderr=p.stderr);rows.append(row);(d/'results.json').write_text(json.dumps(rows,indent=2));(d/(label+'.log')).write_text(p.stdout+p.stderr);print('DONE',label,p.returncode,p.stdout[-900:],flush=True)
  if p.returncode:
   with (r/'ledger.jsonl').open('a') as f:f.write(json.dumps(dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate='chunks02',decision='stop on verification/run failure',detail=row))+'\n')
   raise RuntimeError(label)
print('CHUNKS_SCREEN_COMPLETE; agent must assess drift and choose repeats',flush=True)
