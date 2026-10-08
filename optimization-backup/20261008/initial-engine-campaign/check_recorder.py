from pathlib import Path
import os,subprocess,json,re
r=Path(__file__).resolve().parent;cmd=json.loads((r/'smoke-command.json').read_text())
env=os.environ.copy();env.update(NH_DISC_SWAP='1',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'lib'),OMP_NUM_THREADS='4')
env.pop('NH_PERF_RECORD',None)
rows=[]
for name,exe,record in [('original',r/'puffer-baseline',False),('recorder-off',r/'source/puffer',False),('recorder-on',r/'source/puffer',True)]:
 extra={}
 if record:
  out=r/'recorder-comparison-traces';out.mkdir(exist_ok=False);extra['NH_PERF_RECORD']=str(out)
 with (r/('recorder-check-'+name+'.log')).open('w') as f:p=subprocess.run([str(exe),*cmd[1:]],cwd=r/'source',env=dict(env,**extra),stdout=f,stderr=subprocess.STDOUT)
 text=(r/('recorder-check-'+name+'.log')).read_text();match=re.search(r'CUDA_EVAL[^\n]+',text)
 rows.append(dict(name=name,rc=p.returncode,result=match[0] if match else None));print(rows[-1],flush=True)
 (r/'recorder-check.json').write_text(json.dumps(rows,indent=2))
 if p.returncode:raise SystemExit(p.returncode)
assert len({x['result'] for x in rows})==1,'aggregate outcomes differ'
print('AGGREGATES_IDENTICAL (not a per-step equivalence proof)',flush=True)
