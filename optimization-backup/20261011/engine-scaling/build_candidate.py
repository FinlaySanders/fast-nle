# Build an isolated engine candidate from the retained source (movement_object_presence) into the
# compact-state engines/ tree so check.py gates work unchanged. Usage: build_candidate.py <name> [patch.diff]
from pathlib import Path
import subprocess,json,time,shutil,sys
CS=Path('/puffertank/experiments/nethack-compact-state-20261008'); base=CS/'engines/movement_object_presence/source'
def build(name,patch=None):
    d=CS/'engines'/name; s=d/'source'; b=d/'build'; d.mkdir(parents=True,exist_ok=True)
    if not s.exists():
        shutil.copytree(base,s,symlinks=True)
        if patch: subprocess.run(['patch','-p1','-d',str(s),'-i',str(Path(patch).resolve())],check=True)
    with (d/'changes.patch').open('w') as f: subprocess.run(['diff','-ru',str(base),str(s)],stdout=f)
    import os; flags='-fno-semantic-interposition '+os.environ.get('BUILD_EXTRA_CFLAGS','')
    cmd=['cmake','-S',str(s),'-B',str(b),'-DCMAKE_BUILD_TYPE=Release','-DNLE_TLS_INITIAL_EXEC=ON','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON','-DCMAKE_C_FLAGS='+flags,'-DCMAKE_CXX_FLAGS='+flags]
    for dep in ['bzip2','deboost_context','pybind11']: cmd+=['-DFETCHCONTENT_SOURCE_DIR_'+dep.upper()+'=/puffertank/pufferlib/vendor/fast-nle/build/_deps/'+dep+'-src']
    (d/'command.json').write_text(json.dumps(cmd,indent=2)); t0=time.time(); print('BUILD',name,flush=True)
    with (d/'build.log').open('w') as f:
        subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
        subprocess.run(['cmake','--build',str(b),'--target','nethack','-j8'],stdout=f,stderr=subprocess.STDOUT,check=True)
    print('BUILT',name,round(time.time()-t0,1),'s ->',b/'libnethack.so',flush=True); return b
if __name__=='__main__': build(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else None)
