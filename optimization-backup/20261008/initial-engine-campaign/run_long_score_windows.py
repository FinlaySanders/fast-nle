from pathlib import Path
import os,select,subprocess,json,time,hashlib,datetime
r=Path(__file__).resolve().parent;root=r/'long-score-windows';s=r/'harness-v3/score/source'
pid=int((r/'warmtrain-score-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
gates=json.loads((r/'floor-extended.json').read_text());assert gates[-1]['label']=='stock-view-fuzz' and all(x['rc']==0 for x in gates)
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')}
e.update(NETHACKDIR=str(r/'dat'),NH_ZT_MASK='0',NH_DISC_SWAP='0',OMP_PROC_BIND='true',OMP_PLACES='cores');rows=[]
exe=root/'replay_vec';cmd=['cc','-O2','-g','-fopenmp','-I'+str(s/'src'),'-I'+str(s/'ocean/nethack'),'-I'+str(r/'engine-baseline/include'),'-I/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include','-I/puffertank/pufferlib/raylib-5.5_linux_amd64/include',str(root/'replay_vec.c'),'-L'+str(r/'lib'),'-Wl,-rpath,'+str(r/'lib'),'-lnethack','-lm','-ldl','-o',str(exe)]
subprocess.run(cmd,env=e,check=True);(root/'build-command.json').write_text(json.dumps(cmd))
def run(w,v,mode,label):
 lib=r/'variants'/v;cmd=['taskset','-c','0',str(exe),mode,'1',str(w['warmup']),str(w['measured_decisions']),w['path']];start=time.time();p=subprocess.run(cmd,env=dict(e,LD_LIBRARY_PATH=str(lib)),capture_output=True,text=True)
 rows.append(dict(workload='score-long-'+Path(w['path']).stem,variant=v,mode=mode,label=label,window=w,command=cmd,seconds=time.time()-start,rc=p.returncode,stdout=p.stdout,stderr=p.stderr,library_sha256=hashlib.sha256((lib/'libnethack.so').read_bytes()).hexdigest()));(root/'results.json').write_text(json.dumps(rows,indent=2));print(label,v,p.returncode,p.stdout.strip(),flush=True);assert p.returncode==0,p.stderr
for w in json.loads((root/'manifest.json').read_text()):
 for v in ['candidate03','candidate05-normal']:run(w,v,'verify','verify')
 for rep in range(3):
  if time.time()>=datetime.datetime(2026,9,17,17,59,32,tzinfo=datetime.timezone.utc).timestamp():raise SystemExit('deadline before next ABA')
  for phase,v in [('before','candidate03'),('candidate','candidate05-normal'),('after','candidate03')]:run(w,v,'time',f'candidate03-vs-candidate05-normal-r{rep}-{phase}')
print('DONE',flush=True)
