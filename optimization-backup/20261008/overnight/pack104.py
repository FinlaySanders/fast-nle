from pathlib import Path
import os,shutil,subprocess,json,time,re
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'pack104';d.mkdir();rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_LIBRARY_PATH','LD_PRELOAD','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),LD_LIBRARY_PATH=str(r/'pgo61/variant'),NH_ZT_MASK='0',OMP_PROC_BIND='true',OMP_PLACES='cores')
def run(name,cmd,env):
 print('START',name,flush=True);t=time.time()
 with (d/(name+'.log')).open('w') as f:p=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 out=(d/(name+'.log')).read_text();rows.append(dict(name=name,cmd=cmd,rc=p.returncode,seconds=time.time()-t,output=out[-5000:]));(d/'results.json').write_text(json.dumps(rows,indent=2));print('DONE',name,p.returncode,out[-500:],flush=True);assert p.returncode==0
for w in ['score','depth']:
 src=old/'harness-v3'/w;n=d/w;shutil.copytree(src,n,ignore=shutil.ignore_patterns('replay_vec','*.log'));p=n/'source/ocean/nethack/nethack.h';s=p.read_text()
 from patch_pack104 import patch
 p.write_text(patch(s))
 sdir=n/'source';cmd=['cc','-O2','-g','-fopenmp','-I'+str(sdir/'src'),'-I'+str(sdir/'ocean/nethack'),'-I'+str(old/'engine-baseline/include'),'-I/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include','-I/puffertank/pufferlib/raylib-5.5_linux_amd64/include',str(n/'replay_vec.c'),'-L'+str(old/'lib'),'-Wl,-rpath,'+str(old/'lib'),'-lnethack','-lm','-ldl','-o',str(n/'replay_vec')];run(w+'-build',cmd,e)
for w in ['score','depth']:
 corpus=old/('score-balanced-v2' if w=='score' else 'depth-record-v2');paths=[str(corpus/Path(x['path']).name) for x in json.loads((old/(w+'-timing-selected.json')).read_text())];env=dict(e,NH_DISC_SWAP='1' if w=='depth' else '0')
 for phase,mode,exe in [('verify','verify',d/w/'replay_vec'),('before','time',old/'harness-v3'/w/'replay_vec'),('candidate','time',d/w/'replay_vec'),('after','time',old/'harness-v3'/w/'replay_vec')]:run(w+'-'+phase,['taskset','-c','0,2,4,6,8,10,12,14',str(exe),mode,'8','20000','20000',*paths],env)
summary={}
for w in ['score','depth']:
 vals={phase:float(re.search(r'measured_seconds=([\d.]+)',next(x['output'] for x in rows if x['name']==w+'-'+phase))[1]) for phase in ['before','candidate','after']};summary[w]=dict(**vals,gain_percent=100*((vals['before']+vals['after'])/2/vals['candidate']-1),drift_percent=100*(vals['after']/vals['before']-1))
(d/'summary.json').write_text(json.dumps(summary,indent=2));print('COMPLETE',summary,flush=True)
