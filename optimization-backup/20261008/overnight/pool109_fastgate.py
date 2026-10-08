from pathlib import Path
import subprocess
r=Path(__file__).parent;d=r/'pool109-fastgate';d.mkdir()
subprocess.run(['cc','-O2','-pthread','-I'+str(r/'pool109-source/src'),str(r/'pool83-gates/stress.c'),'-o',str(d/'stress')],check=True)
with (d/'log').open('w') as f:subprocess.run([str(d/'stress')],stdout=f,stderr=subprocess.STDOUT,check=True)
print((d/'log').read_text(),flush=True)

# The original stress varies count every round; also exercise cached order reuse.
t=(r/'pool83-gates/stress.c').read_text()
a='int n = (round * 17 + s->b) % (WIDTH + 1);'
b='int n = round % 41 == 0 ? 0 : ((round / 32) * 17 + s->b) % (WIDTH + 1);'
assert t.count(a)==1
(d/'steady.c').write_text(t.replace(a,b))
subprocess.run(['cc','-O2','-pthread','-I'+str(r/'pool109-source/src'),str(d/'steady.c'),'-o',str(d/'steady')],check=True)
with (d/'steady.log').open('w') as f:subprocess.run([str(d/'steady')],stdout=f,stderr=subprocess.STDOUT,check=True)
print('STEADY-ORDER:',(d/'steady.log').read_text(),flush=True)
