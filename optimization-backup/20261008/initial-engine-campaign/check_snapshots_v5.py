"""Validate every snapshot against its numbered trace hash; allow a trace prefix."""
import argparse,struct,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('snapshots',type=Path);p.add_argument('--heads',type=int,required=True);a=p.parse_args()
def exact(f,n):
 b=f.read(n)
 if len(b)!=n:raise ValueError('truncated input')
 return b
sizes={'R':32792,'k':4,'K':8,'S':8,'F':8,'A':4*a.heads,'O':8,'W':8,'E':48}
with a.trace.open('rb') as t,a.snapshots.open('rb') as s:
 assert exact(t,60)[:7]==b'NHPERF2'
 magic=exact(s,8);assert magic in (b'NHOBS001',b'NHOBS002');engine_fields=24 if magic==b'NHOBS002' else 16
 event=0;count=0;payload=0;counts={}
 while True:
  record=s.read(9)
  if not record:break
  assert len(record)==9
  target,kind=struct.unpack('<Qc',record);kind=kind.decode();assert kind in 'SKFO'
  assert target>=event,('duplicate or out-of-order event',target,event)
  while event<=target:
   tk=exact(t,1).decode();data=exact(t,sizes[tk]);event+=1
   if event-1==target:
    assert tk==kind,(event-1,tk,kind)
    expected=struct.unpack('<Q',data)[0]
   else:
    assert tk not in 'SKFO',('missing snapshot',event-1,tk)
  h=14695981039346656037
  for field in range(2 if kind=='O' else engine_fields):
   n=struct.unpack('<I',exact(s,4))[0];assert n<10000000
   b=exact(s,n);payload+=n
   if kind=='O' or field<15:
    for x in b:h=((h^x)*1099511628211)&0xffffffffffffffff
  assert h==expected,('hash mismatch',target,kind,h,expected)
  counts[kind]=counts.get(kind,0)+1;count+=1
 assert count>0
print(json.dumps(dict(snapshots=count,fields_bytes=payload,kinds=counts,last_event=event-1,scope='all snapshots in file; trace may have an unrecorded suffix')))
