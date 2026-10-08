from pathlib import Path
import shutil,subprocess,difflib
r=Path(__file__).parent;s=r/'engine-source';b=r/'prefix36-before';b.mkdir()
for rel in ['src/monmove.c','tools/globals.def','include/nh_ctx_gen.h','src/nh_ctx_gen.c']:
 p=b/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s/rel,p)
p=s/'tools/globals.def';t=p.read_text();needle='global | cold | int | nh_fobj_count | | 0';assert t.count(needle)==1;t=t.replace(needle,needle+'\nglobal | cold | int | nh_fobj_spatial | | 0\nglobal | cold | unsigned long long | nh_fobj_px | [COLNO+1][32] | 0\nglobal | cold | unsigned long long | nh_fobj_py | [ROWNO+1][32] | 0');p.write_text(t)
p=s/'src/monmove.c';t=p.read_text();a='''    int n = 0;
    for (o = fobj; o; o = o->nobj) {''';z='''    int n = 0, c, word;
    nh_fobj_spatial = 1;
    memset(nh_fobj_px, 0, sizeof(nh_fobj_px));
    memset(nh_fobj_py, 0, sizeof(nh_fobj_py));
    for (o = fobj; o; o = o->nobj) {''';assert t.count(a)==1;t=t.replace(a,z)
a='''        nh_fobj_x[n] = o->ox; nh_fobj_y[n] = o->oy;
        n++;''';z='''        nh_fobj_x[n] = o->ox; nh_fobj_y[n] = o->oy;
        if (o->ox >= 0 && o->ox < COLNO && o->oy >= 0 && o->oy < ROWNO) {
            nh_fobj_px[o->ox + 1][n / 64] |= 1ULL << (n % 64);
            nh_fobj_py[o->oy + 1][n / 64] |= 1ULL << (n % 64);
        } else nh_fobj_spatial = 0;
        n++;''';assert t.count(a)==1;t=t.replace(a,z)
a='''    nh_fobj_count = n; nh_fobj_valid = 1;
}''';z='''    if (nh_fobj_spatial) {
        for (c = 1; c <= COLNO; c++)
            for (word = 0; word < (n + 63) / 64; word++)
                nh_fobj_px[c][word] |= nh_fobj_px[c - 1][word];
        for (c = 1; c <= ROWNO; c++)
            for (word = 0; word < (n + 63) / 64; word++)
                nh_fobj_py[c][word] |= nh_fobj_py[c - 1][word];
    }
    nh_fobj_count = n; nh_fobj_valid = 1;
}''';assert t.count(a)==1;t=t.replace(a,z)
start=t.index('#ifdef __SSE2__',t.index('nh_fobj_next(struct'))
insert='''#if defined(__GNUC__)
    if (nh_fobj_spatial) {
        int xl = max(lx, 0), xh = min(hx, COLNO - 1);
        int yl = max(ly, 0), yh = min(hy, ROWNO - 1);
        if (xl > xh || yl > yh) return (struct obj *) 0;
        cursor->mask = 0;
        while (cursor->index < nh_fobj_count) {
            int word = cursor->index / 64;
            unsigned long long mask =
                (nh_fobj_px[xh + 1][word] ^ nh_fobj_px[xl][word])
                & (nh_fobj_py[yh + 1][word] ^ nh_fobj_py[yl][word]);
            mask &= ~0ULL << (cursor->index % 64);
            if (mask) {
                int i = word * 64 + __builtin_ctzll(mask);
                cursor->index = i + 1;
                return nh_fobj_ptr[i];
            }
            cursor->index = (word + 1) * 64;
        }
        return (struct obj *) 0;
    }
#endif
''';t=t[:start]+insert+t[start:];p.write_text(t)
subprocess.run(['python',str(s/'tools/gen_ctx.py')],check=True,stdout=subprocess.DEVNULL)
out=[]
for p in sorted(b.rglob('*')):
 if p.is_file():
  rel=p.relative_to(b);out.extend(difflib.unified_diff(p.read_text().splitlines(True),(s/rel).read_text().splitlines(True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
(r/'prefix36.patch').write_text(''.join(out))
