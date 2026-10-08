from pathlib import Path
import os,subprocess,json,time,hashlib
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'profile110';d.mkdir();e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUF_','PUFFER_')) and k not in ('LD_LIBRARY_PATH','LD_PRELOAD','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',NH_DISC_SWAP='0',LD_LIBRARY_PATH=str(r/'profile63/variant'))
m=json.loads((r/'pgo61-source-manifest.json').read_text());assert all(hashlib.sha256((r/'engine-source'/p).read_bytes()).hexdigest()==h for p,h in m.items())
rows=[]
for phase in ['verify','profile']:
 cmd=[str(old/'harness-v3/score/replay_vec'),'verify' if phase=='verify' else 'time','1','62000','512',str(old/'score-record/env00040.trace')]
 if phase=='profile':cmd=['valgrind','--tool=callgrind','--cache-sim=yes','--instr-atstart=no','--callgrind-out-file='+str(d/'deep'),*cmd]
 print('START',phase,flush=True);t=time.time()
 with (d/(phase+'.log')).open('w') as f:p=subprocess.run(cmd,env=e,stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(phase=phase,command=cmd,seconds=time.time()-t,rc=p.returncode));(d/'results.json').write_text(json.dumps(rows,indent=2));assert p.returncode==0,(d/(phase+'.log')).read_text()[-1200:];print('DONE',phase,(d/(phase+'.log')).read_text()[-700:],flush=True)
for event in ['Ir','D1mr']:
 with (d/(event+'.txt')).open('w') as f:subprocess.run(['callgrind_annotate','--auto=yes','--inclusive=no','--threshold=95','--sort='+event,str(d/'deep.1')],stdout=f,stderr=subprocess.STDOUT,check=True)
print('PROFILE110_COMPLETE',flush=True)
