from pathlib import Path
import os,select,subprocess
r=Path(__file__).resolve().parent
pid=int((r/'candidate-01-timing-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
cmd=['cc','-O2','-I'+str(r/'engine-baseline/include'),'-I'+str(r/'engine-baseline/build/include'),str(r/'mkcanon.c'),'-o',str(r/'mkcanon')]
p=subprocess.run(cmd,text=True,capture_output=True);print(p.stdout,p.stderr,flush=True)
if p.returncode:raise SystemExit(p.returncode)
subprocess.run([str(r/'mkcanon'),str(r/'appearance_canon.h')],check=True)
print('GENERATOR_OK',flush=True)
