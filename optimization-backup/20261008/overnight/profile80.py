from pathlib import Path
import os,subprocess,json,time,shutil
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'profile80';d.mkdir();e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUF_','PUFFER_')) and k not in ('LD_LIBRARY_PATH','LD_PRELOAD','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',NH_DISC_SWAP='1',LD_LIBRARY_PATH=str(r/'profile63/variant'));n=old/'harness-v3/depth';s=n/'source';rows=[]
cmd=['cc','-O3','-g','-fopenmp','-I'+str(s/'src'),'-I'+str(s/'ocean/nethack'),'-I'+str(old/'engine-baseline/include'),'-I/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include','-I/puffertank/pufferlib/raylib-5.5_linux_amd64/include',str(n/'replay_vec.c'),'-L'+str(old/'lib'),'-Wl,-rpath,'+str(old/'lib'),'-lnethack','-lm','-ldl','-o',str(d/'replay_vec')]
for phase,cmd in [('build',cmd),('verify',[str(d/'replay_vec'),'verify','1','45700','512',str(old/'depth-record-v2/env00199.trace')]),('profile',['valgrind','--tool=callgrind','--cache-sim=yes','--instr-atstart=no','--callgrind-out-file='+str(d/'deep'),str(d/'replay_vec'),'time','1','45700','512',str(old/'depth-record-v2/env00199.trace')])]:
 print('START',phase,flush=True);t=time.time()
 with (d/(phase+'.log')).open('w') as f:p=subprocess.run(cmd,env=e,stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(phase=phase,command=cmd,seconds=time.time()-t,rc=p.returncode));(d/'results.json').write_text(json.dumps(rows,indent=2));assert p.returncode==0,(d/(phase+'.log')).read_text()[-1000:];print('DONE',phase,flush=True)
for event in ['Ir','D1mr']:
 with (d/(event+'.txt')).open('w') as f:subprocess.run(['callgrind_annotate','--auto=yes','--inclusive=no','--threshold=95','--sort='+event,str(d/'deep.1')],stdout=f,stderr=subprocess.STDOUT,check=True)
print('PROFILE80_COMPLETE',flush=True)
