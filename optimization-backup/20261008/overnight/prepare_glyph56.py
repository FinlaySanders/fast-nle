from pathlib import Path
import shutil,difflib
r=Path(__file__).parent;p=r/'engine-source/src/display.c';s=p.read_text();shutil.copy2(p,r/'glyph56-before-display.c')
a='''    int x, y;
    for (y = 0; y < ROWNO; y++)
        for (x = 1; x < COLNO; x++)
            *dst++ = (short) gbuf[y][x].glyph;'''
b='''    int x, y;
    const gbuf_entry (*screen)[COLNO] = gbuf;
    for (y = 0; y < ROWNO; y++)
        for (x = 1; x < COLNO; x++)
            *dst++ = (short) screen[y][x].glyph;'''
assert s.count(a)==1;t=s.replace(a,b);p.write_text(t);(r/'glyph56.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='a/src/display.c',tofile='b/src/display.c')))
