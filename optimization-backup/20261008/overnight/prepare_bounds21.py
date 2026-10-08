from pathlib import Path
import difflib
r=Path(__file__).parent;p=r/'engine-source/src/monmove.c';old=p.read_text();a='                if (xx >= lmx && xx <= oomx && yy >= lmy && yy <= oomy) {';z='                { /* nh_fobj_next already checked these live bounds. */';assert old.count(a)==1;new=old.replace(a,z);(r/'bounds21-before-monmove.c').write_text(old);p.write_text(new);(r/'bounds21.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/src/monmove.c',tofile='b/src/monmove.c')))
