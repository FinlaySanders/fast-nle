from pathlib import Path
import os,subprocess,json,time,hashlib,sys,datetime,re,shutil
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');label=sys.argv[1];extra=sys.argv[2] if len(sys.argv)>2 else '';s=r/'engine-source';d=r/label;d.mkdir();b=d/'build';v=d/'variant';v.mkdir();rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',OMP_PROC_BIND='true',OMP_PLACES='cores')
def run(name,cmd,env=None):
 print('START',name,flush=True);t=time.time()
 with (d/(name+'.log')).open('w') as f:
  p=subprocess.Popen(cmd,env=dict(e,**(env or {})),stdout=f,stderr=subprocess.STDOUT);(d/'process.json').write_text(json.dumps(dict(pid=p.pid,command=cmd)));rc=p.wait()
 text=(d/(name+'.log')).read_text(errors='replace');row=dict(label=name,command=cmd,rc=rc,seconds=time.time()-t,output=text[-16000:]);rows.append(row);(d/'results.json').write_text(json.dumps(rows,indent=2));print('DONE',name,rc,text[-900:],flush=True)
 if rc:raise RuntimeError(name)
 return row
flags='-fno-semantic-interposition '+extra
cmd=['cmake','-S',str(s),'-B',str(b),'-DCMAKE_BUILD_TYPE=Release','-DNLE_TLS_INITIAL_EXEC=ON','-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON','-DCMAKE_C_FLAGS='+flags,'-DCMAKE_CXX_FLAGS='+flags]
for dep in ['bzip2','deboost_context','pybind11']:cmd.append('-DFETCHCONTENT_SOURCE_DIR_'+dep.upper()+'=/puffertank/pufferlib/vendor/fast-nle/build/_deps/'+dep+'-src')
run('configure',cmd);run('build',['cmake','--build',str(b),'--target','nethack','-j8']);shutil.copy2(b/'libnethack.so',v/'libnethack.so')
(d/'manifest.json').write_text(json.dumps(dict(flags=flags,source=str(s),library_sha256=hashlib.sha256((v/'libnethack.so').read_bytes()).hexdigest()),indent=2))
