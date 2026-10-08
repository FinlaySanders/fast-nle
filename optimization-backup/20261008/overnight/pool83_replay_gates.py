from pathlib import Path
import subprocess,os,json,time,shutil,hashlib
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'pool83-gates';rows=json.loads((d/'results.json').read_text());src=r/'pool83-control-source/src'
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUF_','PUFFER_')) and k not in ('LD_LIBRARY_PATH','LD_PRELOAD','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),LD_LIBRARY_PATH=str(r/'pgo61/variant'),NH_ZT_MASK='0')
def run(label,cmd,extra={}):
 print('START',label,flush=True);start=time.time()
 with (d/(label+'.log')).open('w') as f:p=subprocess.run(list(map(str,cmd)),env=dict(e,**extra),stdout=f,stderr=subprocess.STDOUT)
 row=dict(label=label,command=list(map(str,cmd)),rc=p.returncode,seconds=time.time()-start,tail=(d/(label+'.log')).read_text(errors='replace')[-1600:]);rows.append(row);(d/'results.json').write_text(json.dumps(rows,indent=2));print('DONE',label,p.returncode,row['tail'][-300:],flush=True);assert p.returncode==0,row['tail']
s=(old/'shared-pool/stress.c').read_text().replace('generation < 12','generation < 15').replace('ep_create(1 + generation % 8,','ep_create(generation < 12 ? 1 + generation % 8 : 20 + (generation-12)*4,').replace('48000','60000');(d/'stress.c').write_text(s)
for w in ['score','depth']:
 n=d/w;n.mkdir();(n/'source').symlink_to(old/'harness-v3'/w/'source',target_is_directory=True);shutil.copy2(old/'shared-pool'/w/'replay_pthreads.c',n/'replay_pthreads.c')
 cmd=['cc','-O2','-g','-fopenmp','-pthread','-DREPLAY_POOL=1','-I'+str(src),'-I'+str(n/'source/src'),'-I'+str(n/'source/ocean/nethack'),'-I'+str(old/'engine-baseline/include'),'-I/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include','-I/puffertank/pufferlib/raylib-5.5_linux_amd64/include',n/'replay_pthreads.c','-L'+str(old/'lib'),'-Wl,-rpath,'+str(old/'lib'),'-lnethack','-lm','-ldl','-o',n/'replay_pool'];run(w+'-build',cmd)
 paths=sorted((old/('score-balanced-v2' if w=='score' else 'depth-record-v2')).glob('*.trace'))
 run(w+'-full',[n/'replay_pool','verify','24','0','1000000',*paths],dict(NH_DISC_SWAP='1' if w=='depth' else '0'))
print('POOL83_GATES_COMPLETE',flush=True)
