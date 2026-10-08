from pathlib import Path
import shutil,subprocess,difflib
r=Path(__file__).parent;s=r/'engine-source';b=r/'track40-before';b.mkdir()
for rel in ['src/track.c','tools/globals.def','include/nh_ctx_gen.h','src/nh_ctx_gen.c']:
 p=b/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s/rel,p)
p=s/'tools/globals.def';p.write_text(p.read_text()+'\nglobal | cold | unsigned char | nh_track_near | [COLNO][ROWNO] | 0\n')
p=s/'src/track.c';t=p.read_text();t=t.replace('    utcnt = utpnt = 0;', '    utcnt = utpnt = 0;\n    memset(nh_track_near, 0, sizeof(nh_track_near));')
needle='/* add to track */';insert='''static void
nh_track_adjust(coord *position, int delta)
{
    int x, y;
    for (x = max(0, position->x - 1); x <= min(COLNO - 1, position->x + 1); x++)
        for (y = max(0, position->y - 1); y <= min(ROWNO - 1, position->y + 1); y++)
            nh_track_near[x][y] += delta;
}

''';assert t.count(needle)==1;t=t.replace(needle,insert+needle)
a='''    if (utcnt < UTSZ)
        utcnt++;
    if (utpnt == UTSZ)
        utpnt = 0;''';z='''    int full = (utcnt == UTSZ);
    if (utcnt < UTSZ)
        utcnt++;
    if (utpnt == UTSZ)
        utpnt = 0;
    if (full)
        nh_track_adjust(&utrack[utpnt], -1);''';assert t.count(a)==1;t=t.replace(a,z)
t=t.replace('    utpnt++;', '    nh_track_adjust(&utrack[utpnt], 1);\n    utpnt++;')
a='''    cnt = utcnt;
    for (tc''';z='''    if (x >= 0 && x < COLNO && y >= 0 && y < ROWNO && !nh_track_near[x][y])
        return (coord *) 0;
    cnt = utcnt;
    for (tc''';assert t.count(a)==1;t=t.replace(a,z);p.write_text(t)
subprocess.run(['python',str(s/'tools/gen_ctx.py')],check=True,stdout=subprocess.DEVNULL)
out=[]
for p in sorted(b.rglob('*')):
 if p.is_file():
  rel=p.relative_to(b);out.extend(difflib.unified_diff(p.read_text().splitlines(True),(s/rel).read_text().splitlines(True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
(r/'track40.patch').write_text(''.join(out))
