from pathlib import Path
import difflib
r=Path(__file__).parent;p=r/'engine-source/src/monmove.c';old=p.read_text();anchor='''        __m128i xl = _mm_set1_epi16((short) lx), xh = _mm_set1_epi16((short) hx);''';assert old.count(anchor)==1
block='''#ifdef __AVX2__
        __m256i axl = _mm256_set1_epi16((short) lx), axh = _mm256_set1_epi16((short) hx);
        __m256i ayl = _mm256_set1_epi16((short) ly), ayh = _mm256_set1_epi16((short) hy);
        while (cursor->index + 16 <= nh_fobj_count) {
            int i = cursor->index;
            __m256i x = _mm256_loadu_si256((const __m256i *) (nh_fobj_x + i));
            __m256i y = _mm256_loadu_si256((const __m256i *) (nh_fobj_y + i));
            __m256i reject = _mm256_or_si256(
                _mm256_or_si256(_mm256_cmpgt_epi16(axl, x), _mm256_cmpgt_epi16(x, axh)),
                _mm256_or_si256(_mm256_cmpgt_epi16(ayl, y), _mm256_cmpgt_epi16(y, ayh)));
            unsigned int mask = ~(unsigned int) _mm256_movemask_epi8(reject);
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
            cursor->index += 16;
        }
#endif
'''
new='#ifdef __AVX2__\n#include <immintrin.h>\n#endif\n'+old.replace(anchor,block+anchor)
b=r/'avx48-before-monmove.c';assert not b.exists();b.write_text(old);p.write_text(new);(r/'avx48.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/src/monmove.c',tofile='b/src/monmove.c')))
