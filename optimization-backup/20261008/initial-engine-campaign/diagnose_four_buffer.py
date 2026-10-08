from pathlib import Path
import os,subprocess,json,hashlib
r=Path(__file__).resolve().parent;root=r/'shared-pool/depth';rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS','NVCC_EXTRA')}
e.update(NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'variants/candidate03'),NH_ZT_MASK='0',CUDA_VISIBLE_DEVICES='0',NH_DISC_SWAP='1',OMP_NUM_THREADS='8',PUF_POOL_WORKERS='4')
base=next(x['command'] for x in json.loads((r/'shared-pool/results.json').read_text()) if x['label']=='depth-native-4-ws')
for kind in ['ws-a','ws-b','pool']:
 out=root/('no-graphs-'+kind);out.mkdir();tr=out/'traces';tr.mkdir()
 cmd=list(base);cmd.append('--base.cudagraphs=-1')
 if kind=='pool':cmd[0]=str(root/'source/puffer_pool')
 with (out/'log').open('w') as f:p=subprocess.run(cmd,cwd=root/'source',env=dict(e,NH_PERF_RECORD=str(tr)),stdout=f,stderr=subprocess.STDOUT)
 assert p.returncode==0
 hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in tr.iterdir()}
 rows.append(dict(kind=kind,rc=p.returncode,hashes=hashes,command=cmd));(root/'no-graphs-results.json').write_text(json.dumps(rows,indent=2));print(kind,flush=True)
print('baseline repeat identical',rows[0]['hashes']==rows[1]['hashes']);print('pool identical',rows[0]['hashes']==rows[2]['hashes'])
