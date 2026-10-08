def patch(s):
 a='#include <stddef.h>';assert s.count(a)==1;s=s.replace(a,a+'\n#if defined(__SSE2__)\n#include <emmintrin.h>\n#endif')
 a='''        for (int cell = 0; cell < NH_GRID; cell++) {
            int g = env->glyphs[cell];'''
 b='''        int cell = 0;
#if defined(__SSE2__)
        for (; cell + 8 <= NH_GRID; cell += 8) {
            __m128i gs = _mm_loadu_si128((const __m128i*)(env->glyphs + cell));
            __m128i old = _mm_loadu_si128((const __m128i*)(env->obj_mem + cell));
            __m128i floor_mask = _mm_and_si128(_mm_cmpgt_epi16(gs, _mm_set1_epi16(NETHACK_GLYPH_CMAP_OFF - 1)),
                _mm_cmpgt_epi16(_mm_set1_epi16(NETHACK_GLYPH_CMAP_OFF + 96), gs));
            __m128i item_mask = _mm_and_si128(_mm_cmpgt_epi16(gs, _mm_set1_epi16(NETHACK_GLYPH_OBJ_LO - 1)),
                _mm_cmpgt_epi16(_mm_set1_epi16(NETHACK_GLYPH_OBJ_HI), gs));
            __m128i corpse_mask = _mm_and_si128(_mm_cmpgt_epi16(gs, _mm_set1_epi16(NETHACK_GLYPH_BODY_OFF - 1)),
                _mm_cmpgt_epi16(_mm_set1_epi16(NETHACK_GLYPH_BODY_HI), gs));
            __m128i clear_mask = _mm_or_si128(floor_mask, _mm_or_si128(item_mask, corpse_mask));
            __m128i nv = _mm_or_si128(_mm_andnot_si128(clear_mask, old),
                _mm_or_si128(_mm_and_si128(item_mask, _mm_sub_epi16(gs, _mm_set1_epi16(NETHACK_GLYPH_OBJ_LO - 1))),
                _mm_and_si128(corpse_mask, _mm_sub_epi16(gs, _mm_set1_epi16(NETHACK_GLYPH_BODY_OFF - 454)))));
            _mm_storeu_si128((__m128i*)(env->obj_mem + cell), nv);
            unsigned mm = (unsigned)_mm_movemask_epi8(_mm_and_si128(_mm_cmpgt_epi16(gs, _mm_set1_epi16(-1)),
                _mm_cmpgt_epi16(_mm_set1_epi16(NETHACK_GLYPH_BODY_OFF), gs)));
            while (mm && nmon < 256) {
                int bit = __builtin_ctz(mm), pos = cell + bit / 2;
                if (pos != hero_cell) { mon_cell[nmon] = pos; mon_g[nmon++] = env->glyphs[pos]; }
                mm &= ~(3u << (bit & ~1));
            }
            unsigned im = (unsigned)(~_mm_movemask_epi8(_mm_cmpeq_epi16(nv, _mm_setzero_si128()))) & 65535u;
            while (im && nit < 256) {
                int bit = __builtin_ctz(im);
                it_cell[nit++] = cell + bit / 2;
                im &= ~(3u << (bit & ~1));
            }
        }
#endif
        for (; cell < NH_GRID; cell++) {
            int g = env->glyphs[cell];'''
 assert s.count(a)==1;return s.replace(a,b)
