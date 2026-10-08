from pathlib import Path
import os,subprocess,select,json,time
r=Path(__file__).resolve().parent
pid=int((r/'check-v3.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
assert (r/'score167-v2/VERIFIED').exists(),'v3 validation failed'
for work in ['depth','score']:
 out=r/(work+'-record-v2');out.mkdir(exist_ok=False)
 env=os.environ.copy();env.update(NH_DISC_SWAP='0' if work=='score' else '1',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'engine-baseline/build'),NH_PERF_AUGMENT=str(out))
 cmd=[str(r/'harness-v3'/work/'replay_vec'),'verify','24','0','1000000',*map(str,sorted((r/(work+'-record')).glob('*.trace')))]
 (r/(work+'-augment-command.json')).write_text(json.dumps(cmd,indent=2))
 print('START',work,flush=True);start=time.time()
 with (r/(work+'-augment.log')).open('w') as f:p=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 print('DONE',work,p.returncode,'seconds',time.time()-start,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
 (out/'VERIFIED_ORIGINAL').write_text('All original keys, hashes, rewards and terminal events matched the frozen fresh baseline. Missing refresh events added; original files preserved.\n')
print('ALL_AUGMENTED',flush=True)
