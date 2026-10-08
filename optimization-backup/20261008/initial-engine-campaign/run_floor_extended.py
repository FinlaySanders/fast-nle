from pathlib import Path
import os,select,subprocess,json,time,hashlib,shutil
r=Path(__file__).resolve().parent
pid=int((r/'pool-cas-runner.pid').read_text())
try: fd=os.pidfd_open(pid)
except ProcessLookupError: fd=None
if fd is not None: select.select([fd],[],[]);os.close(fd)
checks=json.loads((r/'floor-validation.json').read_text())
assert checks[-1]['label']=='normal-score-engine-verify' and all(x['rc']==0 for x in checks), 'initial floor gate incomplete/failed'
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')}
e.update(NETHACKDIR=str(r/'dat'),NH_ZT_MASK='0'); rows=[]
def run(label,cmd,extra=None):
 log=r/('floor-extended-'+label+'.log');start=time.time()
 with log.open('w') as f:p=subprocess.run(cmd,env=dict(e,**(extra or {})),stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(label=label,command=cmd,rc=p.returncode,seconds=time.time()-start,log=str(log)));(r/'floor-extended.json').write_text(json.dumps(rows,indent=2));print(label,p.returncode,flush=True)
 assert p.returncode==0,log.read_text(errors='replace')[-2000:]
paths=sorted(map(str,(r/'depth-record-v2').glob('*.trace')))
# Use recorded index names rather than assume the trace extension.
paths=[str(r/'depth-record-v2'/Path(x['path']).name) for x in json.loads((r/'depth-index.json').read_text())]
assert len(paths)==512
for kind in ['diagnostic','normal']:
 run(kind+'-depth512',[str(r/'harness-v3/depth/replay_vec'),'verify','8','0','1000000',*paths],dict(LD_LIBRARY_PATH=str(r/'variants'/('candidate05-'+kind)),NH_DISC_SWAP='1'))
s=r/'engine-floor'; a=r/'engine-floor-stock-view';a.mkdir()
for name in subprocess.check_output(['git','-C',str(s),'ls-files'],text=True).splitlines()+['util/mkcanon.c']:
 src=s/name
 if src.is_file():
  dst=a/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
# Same explicitly documented historical-observation projection used for baseline/03.
shutil.copy2(r/'engine-stock-view/win/rl/winrl.cc',a/'win/rl/winrl.cc')
(r/'floor-stock-view-adapter.diff').write_bytes(subprocess.run(['diff','-u',str(s/'win/rl/winrl.cc'),str(a/'win/rl/winrl.cc')],capture_output=True).stdout)
b=a/'build';cmd=['cmake','-S',str(a),'-B',str(b),'-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DNLE_TLS_INITIAL_EXEC=ON','-DCMAKE_C_FLAGS=-DNLE_FOBJ_VERIFY=1']
for dep in ['bzip2','deboost_context','pybind11']:cmd.append('-DFETCHCONTENT_SOURCE_DIR_'+dep.upper()+'=/puffertank/pufferlib/vendor/fast-nle/build/_deps/'+dep+'-src')
run('adapter-configure',cmd);run('adapter-build',['cmake','--build',str(b),'--target','nethack','-j8'])
lib=str(b/'libnethack.so');dat=str(r/'dat');gold=sorted(map(str,(r/'engine-baseline/tests/goldens').glob('*.golden')));fuzz=sorted(map(str,(r/'fuzz-stock').glob('*.golden')))
assert len(gold)==34 and len(fuzz)==26
for label,exe,args,extra in [('golden','replay_golden',gold,{}),('status','replay_golden',gold,{'NLE_REPLAY_OPTIONS_APPEND':',!status_updates'}),('interleaved','replay_multi',gold,{}),('shuffled','replay_multi',gold,{}),('fuzz','replay_golden',fuzz,{})]:
 cmd=[str(r/'gates'/exe)]+(['--'+label] if exe=='replay_multi' else [])+[lib,dat,*args]
 run('stock-view-'+label,cmd,extra)
print('DONE; stock-view is diagnostic, raw historical mismatch remains; performance pending',flush=True)
