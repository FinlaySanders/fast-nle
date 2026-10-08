from pathlib import Path
import struct,mmap,json,sys
r=Path(sys.argv[1]);heads=int(sys.argv[2]);out=Path(sys.argv[3])
sizes={'R':32792,'S':8,'k':4,'K':8,'F':8,'A':heads*4,'O':8,'W':8,'E':48}
rows=[]
for p in sorted(r.glob('*.trace')):
 with p.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as m:
  assert m[:7]==b'NHPERF1';i=60;n=len(m);counts={k:0 for k in sizes};episodes=[];epstart=60;stepstart=0
  while i<n:
   k=chr(m[i]);sz=sizes[k];assert i+1+sz<=n,(p,i,k)
   if k=='R':epstart=i;stepstart=counts['A']
   if k=='E':
    score,turn,depth,xp,how,length=struct.unpack_from('<6q',m,i+1)
    episodes.append(dict(score=score,turn=turn,depth=depth,xp=xp,how=how,length=length,start_offset=epstart,end_offset=i+1+sz,start_decision=stepstart,end_decision=counts['A']))
   counts[k]+=1;i+=1+sz
  rows.append(dict(path=str(p),bytes=n,events=counts,episodes=episodes,max_depth=max((e['depth'] for e in episodes),default=0),max_score=max((e['score'] for e in episodes),default=0)))
 print(p.name,'steps',counts['A'],'episodes',len(episodes),flush=True)
out.write_text(json.dumps(rows,indent=2));print('DONE files',len(rows),flush=True)
