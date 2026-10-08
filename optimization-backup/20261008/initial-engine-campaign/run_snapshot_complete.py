from pathlib import Path
import os,select,subprocess,json,time,hashlib
from check_settings_v5 import read as settings_read
r=Path(__file__).resolve().parent
pid=int((r/'candidate05-timing-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
root=r/'snapshot-complete';root.mkdir();rows=[]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b)
 return h.hexdigest()
for w,heads in [('depth',21),('score',20)]:
 n=r/'harness-v5'/w;traces=n/'traces';raw=n/'observations'
 ts=sorted(traces.glob('*.trace'));obs=sorted(raw.glob('*.obs'));sets=sorted(raw.glob('*.settings'))
 assert len(ts)==len(obs)==len(sets)==8,(w,len(ts),len(obs),len(sets))
 assert {p.stem for p in ts}=={p.stem for p in obs}=={p.stem for p in sets}
 proof=json.loads((n/'proof.json').read_text());assert len(proof)==16
 for p in obs:
  assert p.read_bytes()[:8]==b'NHOBS002'
  cmd=['python',str(r/'check_snapshots_complete.py'),str(traces/(p.stem+'.trace')),str(p),'--heads',str(heads)]
  start=time.time();out=subprocess.run(cmd,capture_output=True,text=True)
  row=dict(workload=w,file=p.name,command=cmd,seconds=time.time()-start,returncode=out.returncode,stdout=out.stdout,stderr=out.stderr)
  rows.append(row);(root/'results.json').write_text(json.dumps(rows,indent=2));print(w,p.name,out.returncode,flush=True)
  assert out.returncode==0,out.stderr
  digest=sha(p);a=settings_read(p.with_suffix('.settings'))
  for variant in ['baseline','candidate03']:
   q=n/('replay-'+variant)/p.name;assert sha(q)==digest
   b=settings_read(q.with_suffix('.settings'));assert [(x['event'],x['semantic']) for x in a]==[(x['event'],x['semantic']) for x in b]
   matching=[x for x in proof if x['variant']==variant and x['file']==p.name];assert len(matching)==1 and matching[0]['sha256']==digest
  row.update(sha256=digest,settings_events=len(a),whole_file_replay_variants=['baseline','candidate03'])
  (root/'results.json').write_text(json.dumps(rows,indent=2))
print('DONE: complete native observation coverage and exact baseline/candidate03 replay, both policies',flush=True)
