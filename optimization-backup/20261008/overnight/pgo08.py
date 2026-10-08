from pathlib import Path
import os,subprocess,json,time,hashlib,shutil,sys,re,datetime
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'pgo08';d.mkdir();b=d/'build';v=d/'variant';v.mkdir();prof=d/'profiles';prof.mkdir();rows=[];source=r/'engine-source';baseline=Path(sys.argv[1])
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',OMP_PROC_BIND='true',OMP_PLACES='cores')
def run(name,cmd,extra={}):
 print('START',name,flush=True);t=time.time()
 with (d/(name+'.log')).open('w') as f:p=subprocess.run(list(map(str,cmd)),env=dict(e,**extra),stdout=f,stderr=subprocess.STDOUT)
 txt=(d/(name+'.log')).read_text(errors='replace');row=dict(label=name,command=list(map(str,cmd)),rc=p.returncode,seconds=time.time()-t,output=txt[-5000:]);rows.append(row);(d/'results.json').write_text(json.dumps(rows,indent=2));print('DONE',name,p.returncode,flush=True);assert p.returncode==0,txt[-2000:];return row
def build(phase,flags):
 cmd=['cmake','-S',str(source),'-B',str(b),'-DCMAKE_BUILD_TYPE=Release','-DNLE_TLS_INITIAL_EXEC=ON','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON','-DCMAKE_C_FLAGS=-fno-semantic-interposition '+flags,'-DCMAKE_CXX_FLAGS=-fno-semantic-interposition '+flags]
 for dep in ['bzip2','deboost_context','pybind11']:cmd.append('-DFETCHCONTENT_SOURCE_DIR_'+dep.upper()+'=/puffertank/pufferlib/vendor/fast-nle/build/_deps/'+dep+'-src')
 run(phase+'-configure',cmd);run(phase+'-build',['cmake','--build',b,'--target','nethack','-j8'])
build('generate','-fprofile-generate='+str(prof)+' -fprofile-update=atomic')
for w in ['score','depth']:
 corpus=old/('score-balanced-v2' if w=='score' else 'depth-record-v2');paths=[str(corpus/Path(x['path']).name) for x in json.loads((old/(w+'-timing-selected.json')).read_text())][::4]
 run(w+'-profile',[old/'harness-v3'/w/'replay_vec','time','8','20000','10000',*paths],dict(LD_LIBRARY_PATH=str(b),NH_DISC_SWAP=str(int(w=='depth'))))
files=list(prof.rglob('*.gcda'));assert files;print('PROFILE_FILES',len(files),flush=True)
(d/'profile-manifest.json').write_text(json.dumps({str(p.relative_to(prof)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2))
build('use','-fprofile-use='+str(prof)+' -fprofile-correction -Werror=coverage-mismatch')
shutil.copy2(b/'libnethack.so',v/'libnethack.so')
(d/'manifest.json').write_text(json.dumps(dict(baseline=str(baseline),library_sha256=hashlib.sha256((v/'libnethack.so').read_bytes()).hexdigest(),profile_files=len(files)),indent=2))
for w in ['score','depth']:
 corpus=old/('score-balanced-v2' if w=='score' else 'depth-record-v2');paths=[str(corpus/Path(x['path']).name) for x in json.loads((old/(w+'-timing-selected.json')).read_text())]
 for mode,phase,lib in [('verify','verify',v),('time','before',baseline),('time','candidate',v),('time','after',baseline)]:
  run(w+'-'+phase,['taskset','-c','0,2,4,6,8,10,12,14',old/'harness-v3'/w/'replay_vec',mode,'8','20000','20000',*paths],dict(LD_LIBRARY_PATH=str(lib),NH_DISC_SWAP=str(int(w=='depth'))))
summary={}
for w in ['score','depth']:
 vals={p:float(re.search(r'measured_seconds=([\d.]+)',next(x for x in rows if x['label']==w+'-'+p)['output'])[1]) for p in ['before','candidate','after']};summary[w]=dict(**vals,gain_percent=((vals['before']+vals['after'])/2/vals['candidate']-1)*100,drift_percent=(vals['after']/vals['before']-1)*100)
(d/'summary.json').write_text(json.dumps(summary,indent=2));print('PGO_SCREEN_COMPLETE',json.dumps(summary),flush=True)
