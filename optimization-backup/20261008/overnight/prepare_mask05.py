from pathlib import Path
import subprocess
r=Path(__file__).parent;s=r/'engine-source';backup=r/'mask05-before';backup.mkdir()
for f in ['src/monmove.c','include/hack.h']:
 p=s/f;q=backup/f;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
p=s/'include/hack.h';t=p.read_text();t=t.replace('unsigned long generation; int index, fallback;', 'unsigned long generation; int index, fallback; unsigned int mask; int base, lx, hx, ly, hy;');p.write_text(t)
p=s/'src/monmove.c';t=p.read_text().replace('cursor->index = 0;','cursor->index = 0;\n        cursor->mask = 0;',1)
needle='''        __m128i xl = _mm_set1_epi16((short) lx), xh = _mm_set1_epi16((short) hx);'''
replacement='''        if (cursor->mask && cursor->lx == lx && cursor->hx == hx
            && cursor->ly == ly && cursor->hy == hy) {
            int bit = __builtin_ctz(cursor->mask);
            int i = cursor->base + bit / 2;
            cursor->mask &= ~(3U << bit);
            cursor->index = i + 1;
            return nh_fobj_ptr[i];
        }
        cursor->mask = 0;
        __m128i xl = _mm_set1_epi16((short) lx), xh = _mm_set1_epi16((short) hx);'''
assert needle in t;t=t.replace(needle,replacement,1)
needle='''                i += __builtin_ctz(mask) / 2;
                cursor->index = i + 1;'''
replacement='''                int bit = __builtin_ctz(mask);
                cursor->base = i;
                cursor->mask = mask & ~(3U << bit);
                cursor->lx = lx; cursor->hx = hx;
                cursor->ly = ly; cursor->hy = hy;
                i += bit / 2;
                cursor->index = i + 1;'''
assert needle in t;t=t.replace(needle,replacement,1)
t=t.replace('#endif\n    while (cursor->index < nh_fobj_count)', '#endif\n    cursor->mask = 0;\n    while (cursor->index < nh_fobj_count)',1)
p.write_text(t)
with (r/'mask05.patch').open('wb') as f:
 for name in ['include/hack.h','src/monmove.c']:
  f.write(subprocess.run(['diff','-u',str(backup/name),str(s/name)],capture_output=True).stdout)
