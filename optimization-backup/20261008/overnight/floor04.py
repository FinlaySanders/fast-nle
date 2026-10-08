from pathlib import Path
import subprocess,os,json,time
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'floor04-diagnostic';d.mkdir();s=r/'engine-source';b=d/'build';rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',OMP_PROC_BIND='true',OMP_PLACES='cores')
def run(label,cmd,extra=None):
 print('START',label,flush=True)
 with (d/(label+'.log')).open('w') as f:
  p=subprocess.Popen(cmd,env=dict(e,**(extra or {})),stdout=f,stderr=subprocess.STDOUT);(d/'process.json').write_text(json.dumps(dict(pid=p.pid,command=cmd)));rc=p.wait()
 txt=(d/(label+'.log')).read_text(errors='replace');rows.append(dict(label=label,rc=rc,command=cmd,output=txt[-8000:]));(d/'results.json').write_text(json.dumps(rows,indent=2));print('DONE',label,rc,txt[-700:],flush=True);assert rc==0,label
flags='-fno-semantic-interposition -DNLE_FOBJ_VERIFY';cmd=['cmake','-S',str(s),'-B',str(b),'-DCMAKE_BUILD_TYPE=Release','-DNLE_TLS_INITIAL_EXEC=ON','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON','-DCMAKE_C_FLAGS='+flags,'-DCMAKE_CXX_FLAGS='+flags]
for dep in ['bzip2','deboost_context','pybind11']:cmd.append('-DFETCHCONTENT_SOURCE_DIR_'+dep.upper()+'=/puffertank/pufferlib/vendor/fast-nle/build/_deps/'+dep+'-src')
run('configure',cmd);run('build',['cmake','--build',str(b),'--target','nethack','-j8'])
for w in ['score','depth']:
 corpus=old/('score-balanced-v2' if w=='score' else 'depth-record-v2');selected=json.loads((old/(w+'-timing-selected.json')).read_text());paths=[str(corpus/Path(selected[i]['path']).name) for i in [0,8,16,24]]
 run(w+'-index-verify',[str(old/'harness-v3'/w/'replay_vec'),'verify','4','20000','2000',*paths],dict(LD_LIBRARY_PATH=str(b),NH_DISC_SWAP='0' if w=='score' else '1'))
print('INDEX_GATE_PASS',flush=True)
subprocess.run(['python',str(r/'engine_screen.py'),'floor04'],check=True)
