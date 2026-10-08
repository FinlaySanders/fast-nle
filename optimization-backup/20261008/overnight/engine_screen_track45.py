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
run('track-build',['cc','-O2','-DNH_TLS_INITIAL_EXEC','-I'+str(s/'include'),'-I'+str(b/'include'),str(r/'track44_test.c'),'-L'+str(v),'-Wl,-rpath,'+str(v),'-lnethack','-o',str(d/'track-test')])
run('track-test',[str(d/'track-test')])
for workload in ['score','depth']:
 corpus=old/('depth-record-v2' if workload=='depth' else 'score-balanced-v2');paths=[str(corpus/Path(x['path']).name) for x in json.loads((old/(workload+'-timing-selected.json')).read_text())]
 for mode,phase,folder in [('verify','verify',v),('time','before',r/'track40/variant'),('time','candidate',v),('time','after',r/'track40/variant')]:
  cmd=['taskset','-c','0,2,4,6,8,10,12,14',str(old/'harness-v3'/workload/'replay_vec'),mode,'8','20000','20000',*paths]
  run(workload+'-'+phase,cmd,dict(LD_LIBRARY_PATH=str(folder),NH_DISC_SWAP='1' if workload=='depth' else '0'))
summary={}
for workload in ['score','depth']:
 vals={}
 for phase in ['before','candidate','after']:
  row=next(x for x in rows if x['label']==workload+'-'+phase);vals[phase]=float(re.search(r'measured_seconds=([\d.]+)',row['output'])[1])
 summary[workload]=dict(**vals,gain_percent=100*((vals['before']+vals['after'])/2/vals['candidate']-1),drift_percent=100*(vals['after']/vals['before']-1))
(d/'summary.json').write_text(json.dumps(summary,indent=2))
with (r/'ledger.jsonl').open('a') as f:f.write(json.dumps(dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate=label,correctness='32 score +32 depth exact prefix replay passed',results=summary,decision='screen only; agent review/repeat required'))+'\n')
print('ENGINE_SCREEN_COMPLETE',json.dumps(summary),flush=True)
