from pathlib import Path
import shutil,difflib
r=Path(__file__).parent;p=r/'engine-source/include/hack.h';s=p.read_text()
a='''    if (!Is_juiblex_level(&u.uz)
        && (ltyp == MOAT
            || (ltyp == DRAWBRIDGE_UP
                && (levl[x][y].drawbridgemask & DB_UNDER) == DB_MOAT)))'''
z='''    if ((ltyp == MOAT
         || (ltyp == DRAWBRIDGE_UP
             && (levl[x][y].drawbridgemask & DB_UNDER) == DB_MOAT))
        && !Is_juiblex_level(&u.uz))'''
assert s.count(a)==1;shutil.copy2(p,r/'moat70-before-hack.h');t=s.replace(a,z);p.write_text(t);(r/'moat70.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='a/include/hack.h',tofile='b/include/hack.h')))
