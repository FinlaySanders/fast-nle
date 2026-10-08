from pathlib import Path
import subprocess,os,json,struct
r=Path(__file__).resolve().parent;root=r/'shared-pool/depth';out=root/'live-4-ws-repeat';out.mkdir();tr=out/'traces';tr.mkdir()
row=next(x for x in json.loads((r/'shared-pool/results.json').read_text()) if x['label']=='depth-native-4-ws')
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS','NVCC_EXTRA')}
e.update(NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'variants/candidate03'),NH_ZT_MASK='0',CUDA_VISIBLE_DEVICES='0',NH_DISC_SWAP='1',NH_PERF_RECORD=str(tr),OMP_NUM_THREADS='8')
with (out/'log').open('w') as f:p=subprocess.run(row['command'],cwd=root/'source',env=e,stdout=f,stderr=subprocess.STDOUT)
assert p.returncode==0
sizes={'R':32792,'S':8,'k':4,'K':8,'F':8,'A':84,'O':8,'W':8,'E':48};rows=[]
for a in sorted((root/'live-4-ws/traces').iterdir()):
 x=a.read_bytes();y=(tr/a.name).read_bytes();i=60;ev=0;act=0;diff=None
 while i<min(len(x),len(y)):
  k=chr(x[i]);n=1+sizes[k]
  if x[i:i+n]!=y[i:i+n]:diff=dict(event=ev,decisions=act,kind=k,offset=i);break
  act+=k=='A';ev+=1;i+=n
 rows.append(dict(env=a.name,same=x==y,first_difference=diff,lengths=[len(x),len(y)]))
(root/'four-buffer-ws-self-comparison.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
