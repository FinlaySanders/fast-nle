from pathlib import Path
import os,subprocess,json,time
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'pgo08-profile';d.mkdir();w=json.loads((old/'score-profile-window.json').read_text())
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','PUF_','PUFFER_')) and k not in ('LD_LIBRARY_PATH','LD_PRELOAD','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',NH_DISC_SWAP='0',LD_LIBRARY_PATH=str(r/'pgo08/variant'))
cmd=['valgrind','--tool=callgrind','--instr-atstart=no','--cache-sim=yes','--branch-sim=yes','--callgrind-out-file='+str(d/'score'),str(old/'score/replay_vec'),'time','1',str(w['warmup']),str(w['measure']),w['path']];t=time.time()
p=subprocess.run(cmd,env=e,capture_output=True,text=True);(d/'result.json').write_text(json.dumps(dict(command=cmd,rc=p.returncode,seconds=time.time()-t,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0
p=subprocess.run(['callgrind_annotate','--auto=no','--inclusive=no','--threshold=90',str(d/'score.1')],capture_output=True,text=True);(d/'annotated.txt').write_text(p.stdout+p.stderr);print('PROFILE COMPLETE',flush=True)
