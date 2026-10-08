from pathlib import Path
import subprocess
r=Path(__file__).parent;d=r/'pool106-fastgate';d.mkdir()
subprocess.run(['cc','-O2','-pthread','-I'+str(r/'pool106-source/src'),str(r/'pool83-gates/stress.c'),'-o',str(d/'stress')],check=True)
with (d/'log').open('w') as f:subprocess.run([str(d/'stress')],stdout=f,stderr=subprocess.STDOUT,check=True)
print((d/'log').read_text(),flush=True)
