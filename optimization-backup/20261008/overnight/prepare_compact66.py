from pathlib import Path
import shutil,difflib
r=Path(__file__).parent;p=r/'engine-source/src/display.c';s=p.read_text()
a='''typedef struct {
    xchar new; /* perhaps move this bit into the rm structure. */
    int glyph;
} gbuf_entry;'''
z='''typedef struct {
    xchar new; /* perhaps move this bit into the rm structure. */
    short glyph;
} gbuf_entry;
_Static_assert(MAX_GLYPH < 32767, "glyph IDs must fit in signed short");'''
assert s.count(a)==1;shutil.copy2(p,r/'compact66-before-display.c');t=s.replace(a,z);p.write_text(t);(r/'compact66.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='a/src/display.c',tofile='b/src/display.c')))
