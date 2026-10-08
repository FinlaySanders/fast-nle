from pathlib import Path
import difflib
r=Path(__file__).parent;p=r/'engine-source/src/monmove.c';old=p.read_text();new=old.replace('        cursor->mask = 0;\n        cursor->fallback = nh_fobj_count < 0;', '        cursor->mask = 0;\n        cursor->base = -1;\n        cursor->fallback = nh_fobj_count < 0;')
a='''        if (cursor->mask && cursor->lx == lx && cursor->hx == hx
            && cursor->ly == ly && cursor->hy == hy) {
            int bit = __builtin_ctz(cursor->mask);
            int i = cursor->base + bit / 2;
            cursor->mask &= ~(3U << bit);
            cursor->index = i + 1;
            return nh_fobj_ptr[i];
        }
        cursor->mask = 0;'''
z='''        if (cursor->base >= 0 && cursor->lx == lx && cursor->hx == hx
            && cursor->ly == ly && cursor->hy == hy) {
            if (cursor->mask) {
                int bit = __builtin_ctz(cursor->mask);
                int i = cursor->base + bit / 2;
                cursor->mask &= ~(3U << bit);
                cursor->index = i + 1;
                return nh_fobj_ptr[i];
            }
            if (cursor->index < cursor->base + 8)
                cursor->index = cursor->base + 8;
        }
        cursor->mask = 0;
        cursor->base = -1;'''
assert new.count(a)==1;new=new.replace(a,z);a='''#endif
    cursor->mask = 0;
    while (cursor->index < nh_fobj_count)''';z='''#endif
    cursor->mask = 0;
    cursor->base = -1;
    while (cursor->index < nh_fobj_count)''';assert new.count(a)==1;new=new.replace(a,z)
(r/'cursor25-before-monmove.c').write_text(old);p.write_text(new);(r/'cursor25.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/src/monmove.c',tofile='b/src/monmove.c')))
