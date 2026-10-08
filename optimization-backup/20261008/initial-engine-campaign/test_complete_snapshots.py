from pathlib import Path
import struct,subprocess,json
r=Path(__file__).resolve().parent;d=r/'snapshot-completeness-tests';d.mkdir(exist_ok=True)
def hash_bytes(b):
 h=14695981039346656037
 for x in b:h=((h^x)*1099511628211)&0xffffffffffffffff
 return h
def obs(event,kind,fields):return struct.pack('<Qc',event,kind)+b''.join(struct.pack('<I',len(x))+x for x in fields)
f=[b'']*24
for k,n in {13:4,14:4,16:4,17:1,18:1}.items():f[k]=b'\0'*n
pol=[b'abcd',b'efgh'];header=b'NHPERF2'+b'\0'*53
srec=b'S'+struct.pack('<Q',hash_bytes(b''.join(f[:15])))
orec=b'O'+struct.pack('<Q',hash_bytes(b''.join(pol)))
t=header+srec+orec;full=b'NHOBS002'+obs(0,b'S',f)+obs(1,b'O',pol)
(d/'input.trace').write_bytes(t)
rows=[]
for name,blob,rc in [('complete',full,0),('missing-suffix',b'NHOBS002'+obs(0,b'S',f),1),('duplicate',full+obs(1,b'O',pol),1),('truncated',full[:-1],1),('empty',b'NHOBS002',1)]:
 p=d/(name+'.obs');p.write_bytes(blob)
 out=subprocess.run(['python',str(r/'check_snapshots_complete.py'),str(d/'input.trace'),str(p),'--heads','21'],text=True,capture_output=True)
 assert (out.returncode==0)==(rc==0),(name,out.stdout,out.stderr)
 rows.append(dict(name=name,returncode=out.returncode,stdout=out.stdout,stderr=out.stderr))
(d/'results.json').write_text(json.dumps(rows,indent=2));print('PASS: complete accepted; missing suffix, duplicate, truncation and empty rejected')
