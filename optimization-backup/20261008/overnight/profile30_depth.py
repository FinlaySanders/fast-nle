from pathlib import Path
import os,subprocess,json,time
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'profile30-depth';d.mkdir()
base={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUF_','PUFFER_')) and k not in ('LD_LIBRARY_PATH','LD_PRELOAD','NETHACKOPTIONS')}
rows=[]
for workload,name,end,measure in [('depth','env00254.trace',2068,384)]:
 warm=end-measure-128;path=old/(workload+'-record-v2')/name
 env=dict(base,NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',NH_DISC_SWAP='1' if workload=='depth' else '0',LD_LIBRARY_PATH=str(r/'pgo20-debug/variant'))
 cmd=['valgrind','--tool=callgrind','--instr-atstart=no','--callgrind-out-file='+str(d/workload),str(old/'harness-v3'/workload/'replay_vec'),'time','1',str(warm),str(measure),str(path)]
 print('START',workload,warm,measure,flush=True);t=time.time();p=subprocess.run(cmd,env=env,capture_output=True,text=True)
 row=dict(workload=workload,command=cmd,rc=p.returncode,seconds=time.time()-t,stdout=p.stdout,stderr=p.stderr,note='Measured window remains within first episode; listed maxdepth is episode maximum, not guaranteed constant depth in window');rows.append(row);(d/'results.json').write_text(json.dumps(rows,indent=2));assert p.returncode==0
 a=subprocess.run(['callgrind_annotate','--auto=yes','--inclusive=no','--threshold=85',str(d/(workload+'.1'))],capture_output=True,text=True);(d/(workload+'-annotated.txt')).write_text(a.stdout+a.stderr);print('DONE',workload,flush=True)
