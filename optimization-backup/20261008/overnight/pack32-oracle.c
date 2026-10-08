#include <emmintrin.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
#define NH_GRID 1659
#define NETHACK_GLYPH_CMAP_OFF 2359
#define NETHACK_GLYPH_OBJ_LO 1906
#define NETHACK_GLYPH_OBJ_HI 2359
#define NETHACK_GLYPH_BODY_OFF 1144
#define NETHACK_GLYPH_BODY_HI 1525
typedef struct {short glyphs[NH_GRID];unsigned short obj_mem[NH_GRID];} Env;
typedef struct {int mon_cell[256],mon_g[256],it_cell[256],nmon,nit;} Out;
static void scalar(Env*env,Out*out,long hero_cell){int *mon_cell=out->mon_cell,*mon_g=out->mon_g,*it_cell=out->it_cell;int nmon=0,nit=0;
        for (int cell = 0; cell < NH_GRID; cell++) {
            int g = env->glyphs[cell];
            if (g >= NETHACK_GLYPH_CMAP_OFF && g < NETHACK_GLYPH_CMAP_OFF + 96) {
                if (env->obj_mem[cell]) env->obj_mem[cell] = 0; // bare floor shown: no object here
            } else if (g >= NETHACK_GLYPH_OBJ_LO && g < NETHACK_GLYPH_OBJ_HI) {
                unsigned short nv = (unsigned short)(g - NETHACK_GLYPH_OBJ_LO + 1);
                if (env->obj_mem[cell] != nv) env->obj_mem[cell] = nv;
            } else if (g >= NETHACK_GLYPH_BODY_OFF && g < NETHACK_GLYPH_BODY_HI) {
                unsigned short nv = (unsigned short)(g - NETHACK_GLYPH_BODY_OFF + 454);
                if (env->obj_mem[cell] != nv) env->obj_mem[cell] = nv;
            } else if (g >= 0 && g < NETHACK_GLYPH_BODY_OFF && cell != hero_cell
                       && nmon < 256) { // monsters, pets and detected alike
                mon_cell[nmon] = cell; mon_g[nmon] = g; nmon++;
                // monster on top: obj_mem stays as last seen
            }
            if (env->obj_mem[cell] && nit < 256) it_cell[nit++] = cell;
        }
out->nmon=nmon;out->nit=nit;}
static void vector(Env*env,Out*out,long hero_cell){int *mon_cell=out->mon_cell,*mon_g=out->mon_g,*it_cell=out->it_cell;int nmon=0,nit=0;
        int scan_cell = 0;
#ifdef __SSE2__
        for (; scan_cell + 8 <= NH_GRID; scan_cell += 8) {
            __m128i gs = _mm_loadu_si128((const __m128i*)(env->glyphs + scan_cell));
            __m128i oldmem = _mm_loadu_si128((const __m128i*)(env->obj_mem + scan_cell));
            __m128i cm = _mm_and_si128(
                _mm_cmpgt_epi16(gs, _mm_set1_epi16(NETHACK_GLYPH_CMAP_OFF - 1)),
                _mm_cmpgt_epi16(_mm_set1_epi16(NETHACK_GLYPH_CMAP_OFF + 96), gs));
            __m128i om = _mm_and_si128(
                _mm_cmpgt_epi16(gs, _mm_set1_epi16(NETHACK_GLYPH_OBJ_LO - 1)),
                _mm_cmpgt_epi16(_mm_set1_epi16(NETHACK_GLYPH_OBJ_HI), gs));
            __m128i bm = _mm_and_si128(
                _mm_cmpgt_epi16(gs, _mm_set1_epi16(NETHACK_GLYPH_BODY_OFF - 1)),
                _mm_cmpgt_epi16(_mm_set1_epi16(NETHACK_GLYPH_BODY_HI), gs));
            __m128i mem = _mm_or_si128(
                _mm_andnot_si128(_mm_or_si128(cm, _mm_or_si128(om, bm)), oldmem),
                _mm_or_si128(
                    _mm_and_si128(om, _mm_sub_epi16(gs, _mm_set1_epi16(NETHACK_GLYPH_OBJ_LO - 1))),
                    _mm_and_si128(bm, _mm_sub_epi16(gs, _mm_set1_epi16(NETHACK_GLYPH_BODY_OFF - 454)))));
            _mm_storeu_si128((__m128i*)(env->obj_mem + scan_cell), mem);
            unsigned monsters = (unsigned)_mm_movemask_epi8(_mm_and_si128(
                _mm_cmpgt_epi16(gs, _mm_set1_epi16(-1)),
                _mm_cmpgt_epi16(_mm_set1_epi16(NETHACK_GLYPH_BODY_OFF), gs)));
            while (monsters && nmon < 256) {
                int lane = __builtin_ctz(monsters) / 2;
                int cell = scan_cell + lane;
                monsters &= ~(3u << (2 * lane));
                if (cell != hero_cell) {
                    mon_cell[nmon] = cell;
                    mon_g[nmon++] = env->glyphs[cell];
                }
            }
            unsigned items = (unsigned)_mm_movemask_epi8(_mm_cmpeq_epi16(mem, _mm_setzero_si128())) ^ 65535u;
            while (items && nit < 256) {
                int lane = __builtin_ctz(items) / 2;
                it_cell[nit++] = scan_cell + lane;
                items &= ~(3u << (2 * lane));
            }
        }
#endif
        for (int cell = scan_cell; cell < NH_GRID; cell++) {
            int g = env->glyphs[cell];
            if (g >= NETHACK_GLYPH_CMAP_OFF && g < NETHACK_GLYPH_CMAP_OFF + 96) {
                if (env->obj_mem[cell]) env->obj_mem[cell] = 0; // bare floor shown: no object here
            } else if (g >= NETHACK_GLYPH_OBJ_LO && g < NETHACK_GLYPH_OBJ_HI) {
                unsigned short nv = (unsigned short)(g - NETHACK_GLYPH_OBJ_LO + 1);
                if (env->obj_mem[cell] != nv) env->obj_mem[cell] = nv;
            } else if (g >= NETHACK_GLYPH_BODY_OFF && g < NETHACK_GLYPH_BODY_HI) {
                unsigned short nv = (unsigned short)(g - NETHACK_GLYPH_BODY_OFF + 454);
                if (env->obj_mem[cell] != nv) env->obj_mem[cell] = nv;
            } else if (g >= 0 && g < NETHACK_GLYPH_BODY_OFF && cell != hero_cell
                       && nmon < 256) { // monsters, pets and detected alike
                mon_cell[nmon] = cell; mon_g[nmon] = g; nmon++;
                // monster on top: obj_mem stays as last seen
            }
            if (env->obj_mem[cell] && nit < 256) it_cell[nit++] = cell;
        }
out->nmon=nmon;out->nit=nit;}
static uint32_t state=93;static uint32_t rng(void){state^=state<<13;state^=state>>17;state^=state<<5;return state;}
int main(void){Env a,b;Out x,y;for(int trial=0;trial<4096;trial++){for(int i=0;i<NH_GRID;i++){unsigned v=rng();a.glyphs[i]=(short)(trial%4==0?v:trial%4==1?v%6000:trial%4==2?2359+v%96:v%1144);a.obj_mem[i]=(unsigned short)(rng()%2?rng():0);}b=a;memset(&x,0,sizeof(x));memset(&y,0,sizeof(y));long hero=(long)(rng()%(NH_GRID+2))-1;scalar(&a,&x,hero);vector(&b,&y,hero);assert(!memcmp(a.obj_mem,b.obj_mem,sizeof(a.obj_mem)));assert(!memcmp(&x,&y,sizeof(x)));}puts("4096 randomized complete-grid memory and ordered token comparisons passed");}
