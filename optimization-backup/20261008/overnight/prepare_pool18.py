from pathlib import Path
import difflib
r=Path(__file__).parent;p=r/'engine-source/src/mon.c';old=p.read_text();a='if ((is_pool(nx, ny) == wantpool || poolok)';z='if ((poolok || is_pool(nx, ny) == wantpool)';assert old.count(a)==1;new=old.replace(a,z);(r/'pool18-before-mon.c').write_text(old);p.write_text(new);(r/'pool18.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/src/mon.c',tofile='b/src/mon.c')))
