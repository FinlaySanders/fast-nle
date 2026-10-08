from pathlib import Path
import os,select,subprocess,json,time,hashlib,shutil
r=Path(__file__).resolve().parent
pid=int((r/'build-validate-v4.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
# Also wait directly for the timing process if the snapshot job failed early.
try:fd=os.pidfd_open(756641)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
results=[]
def run(name,cmd,env=None):
 start=time.time()
 with (r/('candidate04-'+name+'.log')).open('w') as f:p=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 results.append(dict(name=name,command=cmd,returncode=p.returncode,seconds=time.time()-start));(r/'candidate04-validation.json').write_text(json.dumps(results,indent=2));print(name,p.returncode,flush=True)
 if p.returncode:raise RuntimeError(name+' failed')
run('build',['cmake','--build',str(r/'engine-candidate/build'),'--target','nethack','-j','8'])
v=r/'variants/candidate04';v.mkdir()
shutil.copy2(r/'engine-candidate/build/libnethack.so',v/'libnethack.so')
(v/'sha256').write_text(hashlib.sha256((v/'libnethack.so').read_bytes()).hexdigest()+'\n')
(v/'incremental.patch').write_bytes((r/'proposed-nonobject-fastpath.patch').read_bytes())
(v/'combined.patch').write_bytes(subprocess.check_output(['git','-C',str(r/'engine-candidate'),'diff']))
# Include untracked build generator separately; git diff alone omits it.
shutil.copy2(r/'engine-candidate/util/mkcanon.c',v/'mkcanon.c')
env={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')}
run('globals',[str(r/'engine-candidate/tools/check_no_globals.sh'),str(v/'libnethack.so')],env)
for w in ['depth','score']:
 corpus=r/('depth-record-v2' if w=='depth' else 'score-balanced-v2')
 selected=json.loads((r/(w+'-timing-selected.json')).read_text())
 paths=[str(corpus/Path(x['path']).name) for x in selected]
 e=dict(env,NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(v),NH_DISC_SWAP='1' if w=='depth' else '0',NH_ZT_MASK='0')
 for mode in ['verify','engine-verify']:
  run(w+'-'+mode,[str(r/'harness-v3'/w/'replay_vec'),mode,'8','0','1000000',*paths],e)
run('depth512',[str(r/'harness-v3/depth/replay_vec'),'verify','24','0','1000000',*map(str,sorted((r/'depth-record-v2').glob('*.trace')))],dict(env,NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(v),NH_DISC_SWAP='1',NH_ZT_MASK='0'))
print('DONE; performance acceptance remains pending',flush=True)
