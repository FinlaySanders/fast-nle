from pathlib import Path
import os,select,subprocess,json
r=Path(__file__).resolve().parent
pid=int((r/'candidate-01-timing-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
w=json.loads((r/'score-profile-window.json').read_text())
env=os.environ.copy();env.update(NH_DISC_SWAP='0',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'engine-baseline/build'))
cmd=['valgrind','--tool=callgrind','--instr-atstart=no','--collect-jumps=yes','--callgrind-out-file='+str(r/'score-late.callgrind'),str(r/'score/replay_vec'),'time','1',str(w['warmup']),str(w['measure']),w['path']]
(r/'score-profile-command.json').write_text(json.dumps(cmd,indent=2))
p=subprocess.run(cmd,env=env);print('PROFILE_DONE',p.returncode,flush=True)
