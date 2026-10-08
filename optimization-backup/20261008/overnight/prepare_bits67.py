from pathlib import Path
import shutil,difflib
r=Path(__file__).parent;p=r/'engine-source/src/display.c';s=p.read_text()
a='''typedef struct {
    xchar new; /* perhaps move this bit into the rm structure. */
    int glyph;
} gbuf_entry;'''
z='''typedef struct {
    unsigned short new : 1;
    signed short glyph : 15;
} gbuf_entry;
_Static_assert(MAX_GLYPH < 16384, "glyph IDs must fit in signed 15 bits");
_Static_assert(sizeof(gbuf_entry) == 2, "compact screen cell must be 2 bytes");'''
assert s.count(a)==1;shutil.copy2(p,r/'bits67-before-display.c');t=s.replace(a,z);p.write_text(t);(r/'bits67.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='a/src/display.c',tofile='b/src/display.c')))
