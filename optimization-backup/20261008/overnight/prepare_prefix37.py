from pathlib import Path
import shutil
r=Path(__file__).parent;p=r/'engine-source/src/monmove.c';shutil.copy2(p,r/'prefix37-before-monmove.c');s=p.read_text();a=s.index('static void\nnh_fobj_build(void)');b=s.index('\nstruct obj *\nnh_fobj_next',a)
s=s[:a]+'''static void
nh_fobj_build(void)
{
    struct obj *o;
    int n = 0, c, word;
    nh_fobj_spatial = 0;
    for (o = fobj; o; o = o->nobj) {
        if (n == 2048) { nh_fobj_count = -1; nh_fobj_valid = 1; return; }
        nh_fobj_ptr[n] = o;
        nh_fobj_x[n] = o->ox; nh_fobj_y[n] = o->oy;
        n++;
    }
    if (n >= 128) {
        nh_fobj_spatial = 1;
        memset(nh_fobj_px, 0, sizeof(nh_fobj_px));
        memset(nh_fobj_py, 0, sizeof(nh_fobj_py));
        for (c = 0; c < n; c++) {
            int x = nh_fobj_x[c], y = nh_fobj_y[c];
            if (x < 0 || x >= COLNO || y < 0 || y >= ROWNO) {
                nh_fobj_spatial = 0;
                break;
            }
            nh_fobj_px[x + 1][c / 64] |= 1ULL << (c % 64);
            nh_fobj_py[y + 1][c / 64] |= 1ULL << (c % 64);
        }
        if (nh_fobj_spatial) {
            for (c = 1; c <= COLNO; c++)
                for (word = 0; word < (n + 63) / 64; word++)
                    nh_fobj_px[c][word] |= nh_fobj_px[c - 1][word];
            for (c = 1; c <= ROWNO; c++)
                for (word = 0; word < (n + 63) / 64; word++)
                    nh_fobj_py[c][word] |= nh_fobj_py[c - 1][word];
        }
    }
    nh_fobj_count = n; nh_fobj_valid = 1;
}
''' +s[b:]
s=s.replace('if (xl > xh || yl > yh) return (struct obj *) 0;', 'if (xl > xh || yl > yh) { cursor->mask = 0; cursor->index = nh_fobj_count; return (struct obj *) 0; }')
p.write_text(s)
