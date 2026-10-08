from pathlib import Path
import os,select,subprocess,json,time,hashlib,shutil
r=Path(__file__).resolve().parent;s=r/'engine-floor'
pid=int((r/'warmtrain-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
# Independent engine work can proceed after the preceding job terminates, even
# if its own failed gate stopped it. Keep that failure in its original logs.
rows=[];e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS','NVCC_EXTRA')}
e.update(NETHACKDIR=str(r/'dat'),NH_ZT_MASK='0')
def run(label,cmd,env=None):
 start=time.time();log=r/('floor-'+label+'.log')
 with log.open('w') as f:p=subprocess.run(cmd,env=dict(e,**(env or {})),stdout=f,stderr=subprocess.STDOUT)
 row=dict(label=label,command=cmd,rc=p.returncode,seconds=time.time()-start,log=str(log));rows.append(row);(r/'floor-validation.json').write_text(json.dumps(rows,indent=2));print(label,p.returncode,flush=True)
 assert p.returncode==0,log.read_text(errors='replace')[-2500:]
for kind in ['diagnostic','normal']:
 b=s/('build-'+kind)
 args=['cmake','-S',str(s),'-B',str(b),'-DCMAKE_BUILD_TYPE=RelWithDebInfo','-DNLE_TLS_INITIAL_EXEC=ON']
 for dep in ['bzip2','deboost_context','pybind11']:args.append('-DFETCHCONTENT_SOURCE_DIR_'+dep.upper()+'=/puffertank/pufferlib/vendor/fast-nle/build/_deps/'+dep+'-src')
 if kind=='diagnostic':args.append('-DCMAKE_C_FLAGS=-DNLE_FOBJ_VERIFY=1')
 run('configure-'+kind,args);run('build-'+kind,['cmake','--build',str(b),'--target','nethack','-j8'])
 v=r/'variants'/('candidate05-'+kind);v.mkdir();shutil.copy2(b/'libnethack.so',v/'libnethack.so');(v/'sha256').write_text(hashlib.sha256((v/'libnethack.so').read_bytes()).hexdigest()+'\n')
 (v/'combined.patch').write_bytes(subprocess.check_output(['git','-C',str(s),'diff']));shutil.copy2(s/'util/mkcanon.c',v/'mkcanon.c')
 run('globals-'+kind,[str(s/'tools/check_no_globals.sh'),str(v/'libnethack.so')])
 exe=r/('floor-cursor-'+kind)
 run('build-cursor-'+kind,['cc','-O2','-g','-DNH_TLS_INITIAL_EXEC','-I'+str(s/'include'),'-I'+str(b/'include'),str(r/'floor_cursor_test.c'),'-L'+str(v),'-Wl,-rpath,'+str(v),'-lnethack','-o',str(exe)])
 run('cursor-'+kind,[str(exe)],dict(LD_LIBRARY_PATH=str(v)))
 for w in ['depth','score']:
  corpus=r/('depth-record-v2' if w=='depth' else 'score-balanced-v2');paths=[str(corpus/Path(x['path']).name) for x in json.loads((r/(w+'-timing-selected.json')).read_text())]
  for mode in ['verify','engine-verify']:
   run(kind+'-'+w+'-'+mode,[str(r/'harness-v3'/w/'replay_vec'),mode,'8','0','1000000',*paths],dict(LD_LIBRARY_PATH=str(v),NH_DISC_SWAP='1' if w=='depth' else '0'))
print('DONE; broader historical/fuzz and timings still required',flush=True)
