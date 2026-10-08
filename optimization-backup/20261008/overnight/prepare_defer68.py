from pathlib import Path
import shutil,difflib
r=Path(__file__).parent;p=r/'engine-source/src/mon.c';s=p.read_text()
a='                boolean checkobj = OBJ_AT(nx, ny);\n';b='                if (checkobj) {';assert s.count(a)==1 and s.count(b)==1
shutil.copy2(p,r/'defer68-before-mon.c');t=s.replace(a,'').replace(b,'                if (OBJ_AT(nx, ny)) {');p.write_text(t);(r/'defer68.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='a/src/mon.c',tofile='b/src/mon.c')))
