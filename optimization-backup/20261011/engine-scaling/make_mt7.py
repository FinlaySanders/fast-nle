# mt7 = <base> + byte coordinates in the floor-object index: the SSE box filter rejects 16 objects per iteration instead of 8,
# same index order, same first-match semantics; arrays halve (2 KB each).
import shutil,subprocess,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'mt6'
dst=CS/'mt7/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('tools/globals.def',"global | cold | short | nh_fobj_x | [2048] | 0\nglobal | cold | short | nh_fobj_y | [2048] | 0\n","global | cold | schar | nh_fobj_x | [2048] | 0\nglobal | cold | schar | nh_fobj_y | [2048] | 0\n")
rep('src/monmove.c',"""    /* Reject eight coordinates at once; the first matching entry still wins. */
    if (lx >= -32768 && hx <= 32767 && ly >= -32768 && hy <= 32767
        && lx <= hx && ly <= hy) {
        if (cursor->mask && cursor->lx == lx && cursor->hx == hx
            && cursor->ly == ly && cursor->hy == hy) {
            int bit = __builtin_ctz(cursor->mask);
            int i = cursor->base + bit / 2;
            cursor->mask &= ~(3U << bit);
            cursor->index = i + 1;
            return nh_fobj_ptr[i];
        }
        cursor->mask = 0;
        __m128i xl = _mm_set1_epi16((short) lx), xh = _mm_set1_epi16((short) hx);
        __m128i yl = _mm_set1_epi16((short) ly), yh = _mm_set1_epi16((short) hy);
        while (cursor->index + 8 <= nh_fobj_lo + nh_fobj_count) {
            int i = cursor->index;
            __m128i x = _mm_loadu_si128((const __m128i *) (nh_fobj_x + i));
            __m128i y = _mm_loadu_si128((const __m128i *) (nh_fobj_y + i));
            __m128i reject = _mm_or_si128(
                _mm_or_si128(_mm_cmpgt_epi16(xl, x), _mm_cmpgt_epi16(x, xh)),
                _mm_or_si128(_mm_cmpgt_epi16(yl, y), _mm_cmpgt_epi16(y, yh)));
            unsigned int mask = (~(unsigned int) _mm_movemask_epi8(reject)) & 65535U;
            if (mask) {
                int bit = __builtin_ctz(mask);
                cursor->base = i;
                cursor->mask = mask & ~(3U << bit);
                cursor->lx = lx; cursor->hx = hx;
                cursor->ly = ly; cursor->hy = hy;
                i += bit / 2;
                cursor->index = i + 1;
                return nh_fobj_ptr[i];
            }
            cursor->index += 8;
        }
    }""","""    /* Reject sixteen byte coordinates at once; the first matching entry still wins. */
    if (lx >= -128 && hx <= 127 && ly >= -128 && hy <= 127
        && lx <= hx && ly <= hy) {
        if (cursor->mask && cursor->lx == lx && cursor->hx == hx
            && cursor->ly == ly && cursor->hy == hy) {
            int bit = __builtin_ctz(cursor->mask);
            int i = cursor->base + bit;
            cursor->mask &= ~(1U << bit);
            cursor->index = i + 1;
            return nh_fobj_ptr[i];
        }
        cursor->mask = 0;
        __m128i xl = _mm_set1_epi8((char) lx), xh = _mm_set1_epi8((char) hx);
        __m128i yl = _mm_set1_epi8((char) ly), yh = _mm_set1_epi8((char) hy);
        while (cursor->index + 16 <= nh_fobj_lo + nh_fobj_count) {
            int i = cursor->index;
            __m128i x = _mm_loadu_si128((const __m128i *) (nh_fobj_x + i));
            __m128i y = _mm_loadu_si128((const __m128i *) (nh_fobj_y + i));
            __m128i reject = _mm_or_si128(
                _mm_or_si128(_mm_cmpgt_epi8(xl, x), _mm_cmpgt_epi8(x, xh)),
                _mm_or_si128(_mm_cmpgt_epi8(yl, y), _mm_cmpgt_epi8(y, yh)));
            unsigned int mask = (~(unsigned int) _mm_movemask_epi8(reject)) & 65535U;
            if (mask) {
                int bit = __builtin_ctz(mask);
                cursor->base = i;
                cursor->mask = mask & ~(1U << bit);
                cursor->lx = lx; cursor->hx = hx;
                cursor->ly = ly; cursor->hy = hy;
                i += bit;
                cursor->index = i + 1;
                return nh_fobj_ptr[i];
            }
            cursor->index += 16;
        }
    }""")
out=subprocess.run(['python3','tools/gen_ctx.py'],cwd=dst,capture_output=True,text=True); assert out.returncode==0, out.stderr[:300]
print('mt7 source ready (base', BASE+')')
