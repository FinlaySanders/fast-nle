from pathlib import Path
import subprocess,difflib
r=Path(__file__).parent;p=r/'engine-source/src/mon.c';before=p.read_text();assert before==(r/'pgo61-source/src/mon.c').read_text()
needle='            ntyp = TYP_AT(nx, ny);'
assert before.count(needle)==1
after=before.replace(needle,'            __builtin_prefetch(&level.monsters[nx][ny], 0, 1);\n'+needle)
(r/'prefetch95-before-mon.c').write_text(before)
(r/'prefetch95.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/mon.c',tofile='b/src/mon.c')))
p.write_text(after)
try:subprocess.run(['python',str(r/'engine_screen_alloc62.py'),'prefetch95'],check=True)
finally:p.write_text(before)
