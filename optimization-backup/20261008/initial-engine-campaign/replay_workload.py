#!/usr/bin/env python3
"""Reproduce a frozen policy workload without inference; preserve command/results."""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
r=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('workload',choices=['depth','score'])
p.add_argument('mode',choices=['verify','engine-verify','time','engine-time'])
p.add_argument('--library',type=Path,required=True)
p.add_argument('--corpus',type=Path,help='Explicit complete-format corpus directory; its verification scope is copied into the result')
p.add_argument('--selection',choices=['balanced','all','late'],default='balanced')
p.add_argument('--threads',type=int,default=8)
p.add_argument('--cores',default='0,2,4,6,8,10,12,14')
p.add_argument('--warmup',type=int)
p.add_argument('--steps',type=int)
p.add_argument('--dat',type=Path,default=r/'dat')
p.add_argument('--output',type=Path)
a=p.parse_args();lib=a.library.resolve();corpus=a.corpus.resolve() if a.corpus else r/(a.workload+'-record-v2')
if lib.name!='libnethack.so' or not lib.is_file():p.error('--library must name an existing libnethack.so')
if not (corpus/'VERIFIED_ORIGINAL').is_file():p.error('complete verified corpus is not available yet')
if a.threads<1 or (a.steps is not None and a.steps<1) or (a.warmup is not None and a.warmup<0):p.error('invalid thread/step count')
late=None
if a.selection=='balanced':
 rows=json.loads((r/(a.workload+'-timing-selected.json')).read_text());paths=[corpus/Path(x['path']).name for x in rows]
elif a.selection=='all':
 paths=sorted(corpus.glob('*.trace'))
 if len(paths)!=512:p.error('--selection all requires all512 environment streams')
else:
 rows=json.loads((r/(a.workload+'-index.json')).read_text())
 field='score' if a.workload=='score' else 'depth'
 row,late=max(((row,e) for row in rows for e in row['episodes']),key=lambda x:(x[1][field],x[1]['turn']))
 paths=[corpus/Path(row['path']).name]
if any(not path.is_file() for path in paths):p.error('selected stream is absent from this corpus')
verify=a.mode.endswith('verify')
steps=a.steps if a.steps is not None else (min(512,late['length']) if late else (1000000 if verify else 20000))
warmup=a.warmup if a.warmup is not None else (max(late['start_decision'],late['end_decision']-steps) if late else (0 if verify else 20000))
exe=r/'harness-v3'/a.workload/'replay_vec'
env=os.environ.copy()
for key in list(env):
 if key.startswith(('NH_','NLE_','OMP_')) or key in ('LD_PRELOAD','NETHACKOPTIONS'):env.pop(key)
env.update(NH_DISC_SWAP='0' if a.workload=='score' else '1',NH_ZT_MASK='0',NETHACKDIR=str(a.dat.resolve()),LD_LIBRARY_PATH=str(lib.parent),OMP_PROC_BIND='true',OMP_PLACES='cores')
cmd=['taskset','-c',a.cores,str(exe),a.mode,str(a.threads),str(warmup),str(steps),*map(str,paths)]
out=a.output or r/'runs'/f'{time.time_ns()}-{a.workload}-{a.mode}.json';out.parent.mkdir(parents=True,exist_ok=True)
record=dict(corpus=str(corpus),corpus_verification_scope=(corpus/'VERIFIED_ORIGINAL').read_text(),command=cmd,workload=a.workload,mode=a.mode,selection=a.selection,late_episode=late,library=str(lib),library_sha256=hashlib.sha256(lib.read_bytes()).hexdigest(),harness_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),environment={k:env[k] for k in ['NH_DISC_SWAP','NH_ZT_MASK','NETHACKDIR','LD_LIBRARY_PATH','OMP_PROC_BIND','OMP_PLACES']},started=time.time())
# Reserve the output path before starting so an existing result cannot be overwritten.
with out.open('x') as f:json.dump(record,f,indent=2)
q=subprocess.run(cmd,env=env,capture_output=True,text=True)
record.update(returncode=q.returncode,elapsed=time.time()-record['started'],stdout=q.stdout,stderr=q.stderr)
out.write_text(json.dumps(record,indent=2));print(q.stdout,end='');print(q.stderr,end='');print('Result:',out)
raise SystemExit(q.returncode)
