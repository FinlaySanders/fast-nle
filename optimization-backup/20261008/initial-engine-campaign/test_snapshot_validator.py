"""Small format-level checks: payload corruption, missing and duplicate events."""
from pathlib import Path
import tempfile,subprocess,struct,json
r=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='nh-snapshot-format-') as d:
 d=Path(d);t=d/'case.trace';s=d/'case.obs'
 fields=[bytes([i])*i for i in range(15)]
 h=14695981039346656037
 for b in b''.join(fields):h=((h^b)*1099511628211)&((1<<64)-1)
 rec=struct.pack('<Qc',0,b'S')+b''.join(struct.pack('<I',len(x))+x for x in fields+[b''])
 t.write_bytes(b'NHPERF2\0'+bytes(52)+b'S'+struct.pack('<Q',h)+b'F'+struct.pack('<Q',h))
 good=b'NHOBS001'+rec
 cases={'valid_prefix':(good,True),'corrupt_payload':(good[:-1]+bytes([good[-1]^1]),False),'truncated_payload':(good[:-1],False),'duplicate':(good+rec,False),'missing_first_event':(b'NHOBS001'+struct.pack('<Qc',1,b'F')+rec[9:],False)}
 results=[]
 for name,(blob,ok) in cases.items():
  s.write_bytes(blob);p=subprocess.run(['python',str(r/'check_snapshots.py'),str(t),str(s),'--heads','21'],capture_output=True,text=True)
  assert (p.returncode==0)==ok,(name,p.stdout,p.stderr)
  results.append({'case':name,'expected_accept':ok,'returncode':p.returncode})
(r/'snapshot-format-checks.json').write_text(json.dumps(results,indent=2));print('PASS: valid prefix accepted; corruption, truncation, duplicates, missing event rejected')
