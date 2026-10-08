from pathlib import Path
import os,subprocess,json,time,re
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'buffers39';d.mkdir();rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',LD_LIBRARY_PATH=str(r/'pgo20/variant'),OMP_PROC_BIND='false')
for w in ['score','depth']:
 s=(old/'late512'/(w+'.c')).read_text();s='#ifndef REPLAY_BUFFERS\n#define REPLAY_BUFFERS 4\n#endif\n'+s
 for a,b in [('submitters[4]','submitters[REPLAY_BUFFERS]'),('submit_args[4]','submit_args[REPLAY_BUFFERS]'),('d->n/4','d->n/REPLAY_BUFFERS'),('d->threads/4','d->threads/REPLAY_BUFFERS'),('b<4','b<REPLAY_BUFFERS'),('NULL,5','NULL,REPLAY_BUFFERS+1'),('threads>=4 && threads%4==0 && n>=4','threads>=REPLAY_BUFFERS && threads%REPLAY_BUFFERS==0 && n>=REPLAY_BUFFERS && n%REPLAY_BUFFERS==0')]:
  assert a in s,a;s=s.replace(a,b)
 src=d/(w+'.c');src.write_text(s)
 for buffers in [2,4,8]:
  tree=old/'shared-pool'/w/'source';cmd=['cc','-O2','-g','-fopenmp','-pthread','-DREPLAY_WS=1','-DREPLAY_BUFFERS='+str(buffers),'-I'+str(old/'shared-pool'),'-I'+str(tree/'src'),'-I'+str(tree/'ocean/nethack'),'-I'+str(old/'engine-baseline/include'),'-I/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include','-I/puffertank/pufferlib/raylib-5.5_linux_amd64/include',str(src),'-L'+str(old/'lib'),'-Wl,-rpath,'+str(old/'lib'),'-lnethack','-lm','-ldl','-o',str(d/(w+'-'+str(buffers)))]
  with (d/('build-'+w+'-'+str(buffers)+'.log')).open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
for w in ['score','depth']:
 corpus=old/('score-record' if w=='score' else 'depth-record-v2');paths=sorted(map(str,corpus.glob('*.trace')))[:128]
 for mode,label,buffers in [('verify','verify2',2),('verify','verify8',8),('time','before',4),('time','buffers2',2),('time','buffers8',8),('time','after',4)]:
  cmd=['taskset','-c','0,2,4,6,8,10,12,14',str(d/(w+'-'+str(buffers))),mode,'8','20000','5000',*paths];print('START',w,label,flush=True);t=time.time();p=subprocess.run(cmd,env=dict(e,NH_DISC_SWAP=str(int(w=='depth'))),capture_output=True,text=True);row=dict(label=w+'-'+label,command=cmd,rc=p.returncode,seconds=time.time()-t,stdout=p.stdout,stderr=p.stderr);rows.append(row);(d/'results.json').write_text(json.dumps(rows,indent=2));print('DONE',w,label,p.returncode,p.stdout[-500:],flush=True);assert p.returncode==0,p.stderr[-1000:]
summary={}
for w in ['score','depth']:
 vals={phase:float(re.search(r'measured_seconds=([\d.]+)',next(x['stdout'] for x in rows if x['label']==w+'-'+phase))[1]) for phase in ['before','buffers2','buffers8','after']};base=(vals['before']+vals['after'])/2;summary[w]=dict(**vals,gain2_percent=100*(base/vals['buffers2']-1),gain8_percent=100*(base/vals['buffers8']-1),drift_percent=100*(vals['after']/vals['before']-1))
(d/'summary.json').write_text(json.dumps(summary,indent=2));print('COMPLETE',summary,flush=True)
