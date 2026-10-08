def patch(s):
 needle='#include <stddef.h>'
 assert s.count(needle)==1
 s=s.replace(needle,needle+'\n#if defined(__SSE2__)\n#include <emmintrin.h>\n#endif')
 needle='        for (int cell = 0; cell < NH_GRID; cell++) {\n            int g = env->glyphs[cell];'
 assert s.count(needle)==1
 replacement='''        for (int cell = 0; cell < NH_GRID; cell++) {
#if defined(__SSE2__)
            if (cell + 8 <= NH_GRID) {
                __m128i gs = _mm_loadu_si128((const __m128i*)(env->glyphs + cell));
                __m128i above = _mm_cmpgt_epi16(gs, _mm_set1_epi16(NETHACK_GLYPH_CMAP_OFF - 1));
                __m128i below = _mm_cmpgt_epi16(_mm_set1_epi16(NETHACK_GLYPH_CMAP_OFF + 96), gs);
                if (_mm_movemask_epi8(_mm_and_si128(above, below)) == 65535) {
                    _mm_storeu_si128((__m128i*)(env->obj_mem + cell), _mm_setzero_si128());
                    cell += 7;
                    continue;
                }
            }
#endif
            int g = env->glyphs[cell];'''
 return s.replace(needle,replacement)
