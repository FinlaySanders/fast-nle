from pathlib import Path
import subprocess,os,json,time,hashlib
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');out=r/'pgo71-gates';out.mkdir();rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUFFER_','PUF_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',OMP_NUM_THREADS='8')
base=old/'variants/candidate14-lto-local';cand=r/'pgo71/variant'
def run(label,cmd,extra={},allow=False):
 start=time.time();print('START',label,flush=True)
 with (out/(label+'.log')).open('w') as f:p=subprocess.run(list(map(str,cmd)),env=dict(e,**extra),stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(label=label,command=list(map(str,cmd)),rc=p.returncode,seconds=time.time()-start));(out/'results.json').write_text(json.dumps(rows,indent=2));print('DONE',label,p.returncode,flush=True)
 assert allow or p.returncode==0,label
 return (out/(label+'.log')).read_text()
gold=sorted((old/'engine-baseline/tests/goldens').glob('*.golden'));m=[]
for label,lib in [('before',base),('pgo71',cand)]:
 txt=run('golden-'+label,[old/'gates/replay_golden',lib/'libnethack.so',old/'dat',*gold],allow=True);m.append([x for x in txt.splitlines() if 'MISMATCH' in x]);assert rows[-1]['rc']==1 and sum(x.startswith('OK ') for x in txt.splitlines())+len(m[-1])==len(gold)
assert m[0]==m[1] and len(m[0])==15
for w in ['score','depth']:
 paths=sorted((old/'harness-v5'/w/'traces').glob('*.trace'));snap=out/(w+'-snapshots');snap.mkdir()
 run(w+'-raw',[old/'harness-v5'/w/'replay_vec','verify','8','0','1000000',*paths],dict(LD_LIBRARY_PATH=str(cand),NH_DISC_SWAP=str(int(w=='depth')),NH_PERF_SNAPSHOTS=str(snap)))
 for p in (old/'harness-v5'/w/'observations').glob('*.obs'):assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((snap/p.name).read_bytes()).digest(),p.name
 paths=sorted((old/('score-balanced-v2' if w=='score' else 'depth-record-v2')).glob('*.trace'))
 run(w+'-full',[old/'harness-v3'/w/'replay_vec','verify','8','0','1000000',*paths],dict(LD_LIBRARY_PATH=str(cand),NH_DISC_SWAP=str(int(w=='depth'))))
print('GATES COMPLETE: raw historical baseline exceptions unchanged; snapshots and complete selected score/depth corpora pass',flush=True)
