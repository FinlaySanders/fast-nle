from pathlib import Path
import shutil,difflib,subprocess
r=Path(__file__).parent;s=r/'engine-source';b=r/'glyph57-before';b.mkdir();rels=['src/display.c','tools/globals.def','include/nh_ctx_gen.h','src/nh_ctx_gen.c']
for rel in rels:
 p=b/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s/rel,p)
p=s/'tools/globals.def';p.write_text(p.read_text()+'\nglobal | cold | short | nh_glyph_plane | [ROWNO * (COLNO - 1)] | 0\n')
p=s/'src/display.c';t=p.read_text();a='        gbuf[y][x].glyph = glyph;';assert t.count(a)==1;t=t.replace(a,a+'\n        nh_glyph_plane[y * (COLNO - 1) + x - 1] = (short) glyph;')
a='''    reset_glyph_bbox();
}
''';start=t.index('void\nclear_glyph_buffer()');end=t.index(a,start);t=t[:end]+'''    for (y = 0; y < ROWNO * (COLNO - 1); y++)
        nh_glyph_plane[y] = (short) nul_gbuf.glyph;
'''+t[end:]
a='''    int x, y;
    for (y = 0; y < ROWNO; y++)
        for (x = 1; x < COLNO; x++)
            *dst++ = (short) gbuf[y][x].glyph;'''
z='''#ifdef NLE_GLYPH_VERIFY
    int x, y;
    for (y = 0; y < ROWNO; y++)
        for (x = 1; x < COLNO; x++)
            if (nh_glyph_plane[y * (COLNO - 1) + x - 1] != (short) gbuf[y][x].glyph)
                panic("glyph plane mismatch at %d,%d", x, y);
#endif
    memcpy(dst, nh_glyph_plane, sizeof nh_glyph_plane);'''
assert t.count(a)==1;t=t.replace(a,z);p.write_text(t)
subprocess.run(['python',str(s/'tools/gen_ctx.py')],check=True,stdout=subprocess.DEVNULL)
out=[]
for rel in rels:out.extend(difflib.unified_diff((b/rel).read_text().splitlines(True),(s/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
(r/'glyph57.patch').write_text(''.join(out))
