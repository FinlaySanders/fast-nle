from pathlib import Path
import os,subprocess,json,time
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'alloc94-gates';d.mkdir();rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_LIBRARY_PATH','LD_PRELOAD','NETHACKOPTIONS')}
e.update(NETHACKDIR=str(old/'dat'),LD_LIBRARY_PATH=str(r/'pgo61/variant'),LD_PRELOAD='/lib/x86_64-linux-gnu/libtcmalloc_minimal.so.4',NH_ZT_MASK='0')
for w in ['score','depth']:
 paths=sorted((old/('score-balanced-v2' if w=='score' else 'depth-record-v2')).glob('*.trace'));cmd=[str(r/'pool83-gates'/w/'replay_pool'),'verify','28','0','1000000',*map(str,paths)];start=time.time();print('START',w,flush=True)
 with (d/(w+'.log')).open('w') as f:p=subprocess.Popen(cmd,env=dict(e,NH_DISC_SWAP='1' if w=='depth' else '0'),stdout=f,stderr=subprocess.STDOUT);_,status,usage=os.wait4(p.pid,0);p.returncode=os.waitstatus_to_exitcode(status)
 t=(d/(w+'.log')).read_text(errors='replace');row=dict(workload=w,command=cmd,rc=p.returncode,wall_seconds=time.time()-start,peak_rss_kb=usage.ru_maxrss,output=t[-3000:]);rows.append(row);(d/'results.json').write_text(json.dumps(rows,indent=2));print('DONE',w,p.returncode,t[-600:],flush=True);assert p.returncode==0
print('ALLOC94_FULL_REPLAY_COMPLETE',flush=True)
