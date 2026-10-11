"""PGO build of the stacked candidate (incstack), same recipe as the campaign's rawglyph_pgo."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, time
r = Path('/puffertank/experiments/nethack-compact-state-20261008'); old = Path('/puffertank/experiments/nethack-perf-20260917')
d = r/'engines/incstack_pgo'; s, b, prof = d/'source', d/'build', d/'profiles'
assert not d.exists(); shutil.copytree(r/'engines/incstack/source', s, symlinks=True); prof.mkdir()
env = {k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','CPU_','PUF_','PUFFER_')) and k not in ('LD_LIBRARY_PATH','LD_PRELOAD','NETHACKOPTIONS','CPUPROFILE')}
env.update(NETHACKDIR=str(old/'dat'), NH_ZT_MASK='0', OMP_PROC_BIND='true', OMP_PLACES='cores')
rows=[]
def invoke(label, cmd, extra=None):
    cmd=list(map(str,cmd)); print('START',label,flush=True); t=time.time()
    with (d/(label+'.log')).open('w') as f: rc=subprocess.Popen(cmd,env=dict(env,**(extra or {})),stdout=f,stderr=subprocess.STDOUT).wait(timeout=1800)
    txt=(d/(label+'.log')).read_text(errors='replace'); rows.append(dict(label=label,rc=rc,seconds=time.time()-t)); (d/'results.json').write_text(json.dumps(rows,indent=2))
    print('DONE',label,rc,round(time.time()-t,1),flush=True); assert rc==0, txt[-4000:]; return txt
def build(phase, flags):
    cmd=['cmake','-S',s,'-B',b,'-DCMAKE_BUILD_TYPE=Release','-DNLE_TLS_INITIAL_EXEC=ON','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON','-DCMAKE_C_FLAGS=-fno-semantic-interposition '+flags,'-DCMAKE_CXX_FLAGS=-fno-semantic-interposition '+flags]
    for dep in ['bzip2','deboost_context','pybind11']: cmd.append('-DFETCHCONTENT_SOURCE_DIR_'+dep.upper()+'=/puffertank/pufferlib/vendor/fast-nle/build/_deps/'+dep+'-src')
    invoke(phase+'_configure',cmd); return invoke(phase+'_build',['cmake','--build',b,'--target','nethack','-j8'])
build('generate','-fprofile-generate='+str(prof)+' -fprofile-update=atomic')
(d/'generate').mkdir(); shutil.copy2(b/'libnethack.so', d/'generate/libnethack.so')
for workload in ['score','depth']:
    corpus=old/('score-balanced-v2' if workload=='score' else 'depth-record-v2')
    selected=json.loads((old/(workload+'-timing-selected.json')).read_text())[::4]
    paths=[corpus/Path(x['path']).name for x in selected]; assert len(paths)==8
    invoke(workload+'_profile',['taskset','-c','0,2,4,6,8,10,12,14',old/'harness-v3'/workload/'replay_vec','time','8','20000','10000',*paths],dict(LD_LIBRARY_PATH=str(b),NH_DISC_SWAP=str(int(workload=='depth'))))
files=list(prof.rglob('*.gcda')); assert files
txt=build('use','-fprofile-use='+str(prof)+' -fprofile-correction -Werror=coverage-mismatch'); assert 'coverage-mismatch' not in txt.lower()
(d/'manifest.json').write_text(json.dumps(dict(library_sha256=hashlib.sha256((b/'libnethack.so').read_bytes()).hexdigest(),profile_files=len(files),source_identical_to='incstack'),indent=2))
print('PGO READY',flush=True)
