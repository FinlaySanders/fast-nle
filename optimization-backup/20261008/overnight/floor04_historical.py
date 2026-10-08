from pathlib import Path
import os,subprocess,json,time,shutil
r=Path('/puffertank/experiments/nethack-perf-20260917');root=Path('/puffertank/experiments/nethack-overnight-20260917/floor04-historical');root.mkdir();s=Path('/puffertank/experiments/nethack-overnight-20260917/engine-source');a=root/'source';a.mkdir();rows=[]
for name in set(subprocess.check_output(['git','-C',str(r/'engine-baseline'),'ls-files'],text=True).splitlines()+['util/mkcanon.c']):
 p=s/name
 if p.is_file():
  q=a/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
shutil.copy2(r/'engine-stock-view/win/rl/winrl.cc',a/'win/rl/winrl.cc')
(root/'adapter.diff').write_bytes(subprocess.run(['diff','-u',str(s/'win/rl/winrl.cc'),str(a/'win/rl/winrl.cc')],capture_output=True).stdout)
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUF_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')}
def run(label,cmd,extra=None):
 t=time.time();log=root/(label+'.log')
 with log.open('w') as f:p=subprocess.run(cmd,env=dict(e,**(extra or {})),stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(label=label,command=cmd,rc=p.returncode,seconds=time.time()-t,log=str(log)));(root/'results.json').write_text(json.dumps(rows,indent=2));print(label,p.returncode,flush=True);assert p.returncode==0,log.read_text()[-2000:]
b=a/'build';cmd=['cmake','-S',str(a),'-B',str(b),'-DCMAKE_BUILD_TYPE=Release','-DNLE_TLS_INITIAL_EXEC=ON','-DCMAKE_C_FLAGS=-DNLE_FOBJ_VERIFY=1 -fno-semantic-interposition','-DCMAKE_CXX_FLAGS=-fno-semantic-interposition','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON']
for dep in ['bzip2','deboost_context','pybind11']:cmd.append('-DFETCHCONTENT_SOURCE_DIR_'+dep.upper()+'=/puffertank/pufferlib/vendor/fast-nle/build/_deps/'+dep+'-src')
run('configure',cmd);run('build',['cmake','--build',str(b),'--target','nethack','-j8'])
lib=str(b/'libnethack.so');dat=str(r/'dat');gold=sorted(map(str,(r/'engine-baseline/tests/goldens').glob('*.golden')));fuzz=sorted(map(str,(r/'fuzz-stock').glob('*.golden')))
for label,exe,args,extra in [('golden','replay_golden',gold,{}),('status','replay_golden',gold,{'NLE_REPLAY_OPTIONS_APPEND':',!status_updates'}),('interleaved','replay_multi',gold,{}),('shuffled','replay_multi',gold,{}),('fuzz','replay_golden',fuzz,{})]:
 cmd=[str(r/'gates'/exe)]+(['--'+label] if exe=='replay_multi' else [])+[lib,dat,*args];run(label,cmd,extra)
print('DONE: explicit historical-view diagnostic, not raw exporter proof',flush=True)
