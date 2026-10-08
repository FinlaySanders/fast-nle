from pathlib import Path
import os,subprocess,json,time,re
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'profile50';d.mkdir();rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUF_','PUFFER_')) and k not in ('LD_LIBRARY_PATH','LD_PRELOAD','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',NH_DISC_SWAP='0',LD_LIBRARY_PATH=str(r/'profile49/variant'))
for warm in [20000,25000,28000]:
 label=str(warm);cmd=['valgrind','--tool=callgrind','--instr-atstart=no','--callgrind-out-file='+str(d/label),str(old/'score/replay_vec'),'time','1',str(warm),'512',str(old/'score-record/env00020.trace')];print('START',warm,flush=True);t=time.time();p=subprocess.run(cmd,env=e,capture_output=True,text=True);row=dict(warmup=warm,measure=512,command=cmd,rc=p.returncode,seconds=time.time()-t,stdout=p.stdout,stderr=p.stderr);rows.append(row);(d/'results.json').write_text(json.dumps(rows,indent=2));assert p.returncode==0,p.stderr[-1000:]
 a=subprocess.run(['callgrind_annotate','--auto=yes','--inclusive=no','--threshold=95',str(d/(label+'.1'))],capture_output=True,text=True);(d/(label+'-annotated.txt')).write_text(a.stdout+a.stderr);print('DONE',warm,p.stdout[-500:],flush=True)
print('PROFILE_WINDOWS_COMPLETE',flush=True)
