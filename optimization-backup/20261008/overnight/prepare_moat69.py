from pathlib import Path
import shutil,difflib
r=Path(__file__).parent;p=r/'engine-source/include/hack.h';s=p.read_text()
a='''    ltyp = levl[x][y].typ;
    if (!Is_juiblex_level(&u.uz)'''
z='''    ltyp = nh_typ_plane[x][y];
#ifdef NLE_MOAT_VERIFY
    if (ltyp != levl[x][y].typ)
        panic("moat terrain cache mismatch at %d,%d", x, y);
#endif
    if (!Is_juiblex_level(&u.uz)'''
assert s.count(a)==1;shutil.copy2(p,r/'moat69-before-hack.h');t=s.replace(a,z);p.write_text(t);(r/'moat69.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='a/include/hack.h',tofile='b/include/hack.h')))
