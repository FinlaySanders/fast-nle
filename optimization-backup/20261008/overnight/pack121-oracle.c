#include <stdint.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
#include <emmintrin.h>
#define N 1659
static uint32_t rng=123;
static unsigned rnd(void){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
static void scan(const short*g,unsigned short*m,int*mc,int*mg,int*ic,int*nmon,int*nit,int hero,int simd){
*nmon=*nit=0;
int cell = 0; if(simd) {
#if defined(__SSE2__)
        for (; cell + 8 <= N; cell += 8) {
            __m128i gs = _mm_loadu_si128((const __m128i*)(g + cell));
            __m128i old = _mm_loadu_si128((const __m128i*)(m + cell));
            __m128i floor_mask = _mm_and_si128(_mm_cmpgt_epi16(gs, _mm_set1_epi16(2359 - 1)),
                _mm_cmpgt_epi16(_mm_set1_epi16(2359 + 96), gs));
            __m128i item_mask = _mm_and_si128(_mm_cmpgt_epi16(gs, _mm_set1_epi16(1906 - 1)),
                _mm_cmpgt_epi16(_mm_set1_epi16(2359), gs));
            __m128i corpse_mask = _mm_and_si128(_mm_cmpgt_epi16(gs, _mm_set1_epi16(1144 - 1)),
                _mm_cmpgt_epi16(_mm_set1_epi16(1526), gs));
            __m128i clear_mask = _mm_or_si128(floor_mask, _mm_or_si128(item_mask, corpse_mask));
            __m128i nv = _mm_or_si128(_mm_andnot_si128(clear_mask, old),
                _mm_or_si128(_mm_and_si128(item_mask, _mm_sub_epi16(gs, _mm_set1_epi16(1906 - 1))),
                _mm_and_si128(corpse_mask, _mm_sub_epi16(gs, _mm_set1_epi16(1144 - 454)))));
            _mm_storeu_si128((__m128i*)(m + cell), nv);
            unsigned mm = (unsigned)_mm_movemask_epi8(_mm_and_si128(_mm_cmpgt_epi16(gs, _mm_set1_epi16(-1)),
                _mm_cmpgt_epi16(_mm_set1_epi16(1144), gs)));
            while (mm && (*nmon) < 256) {
                int bit = __builtin_ctz(mm), pos = cell + bit / 2;
                if (pos != hero) { mc[(*nmon)] = pos; mg[(*nmon)++] = g[pos]; }
                mm &= ~(3u << (bit & ~1));
            }
            unsigned im = (unsigned)(~_mm_movemask_epi8(_mm_cmpeq_epi16(nv, _mm_setzero_si128()))) & 65535u;
            while (im && (*nit) < 256) {
                int bit = __builtin_ctz(im);
                ic[(*nit)++] = cell + bit / 2;
                im &= ~(3u << (bit & ~1));
            }
        }
#endif
}
for(;cell<N;cell++){
 int v=g[cell];if(v>=2359&&v<2455)m[cell]=0;
 else if(v>=1906&&v<2359)m[cell]=(unsigned short)(v-1906+1);
 else if(v>=1144&&v<1526)m[cell]=(unsigned short)(v-1144+454);
 else if(v>=0&&v<1144&&cell!=hero&&*nmon<256){mc[*nmon]=cell;mg[(*nmon)++]=v;}
 if(m[cell]&&*nit<256)ic[(*nit)++]=cell;
}}
int main(void){short g[N];unsigned short a[N],b[N];int ac[256],ag[256],ai[256],bc[256],bg[256],bi[256],an,ain,bn,bin;
for(int trial=0;trial<20000;trial++){for(int i=0;i<N;i++){unsigned v=rnd();g[i]=trial%3==0?(short)v:trial%3==1?(short)(2359+v%96):(short)(v%4?2359+v%96:v%6000);a[i]=b[i]=(unsigned short)rnd();}int hero=(int)(rnd()%(N+1))-1;scan(g,a,ac,ag,ai,&an,&ain,hero,0);scan(g,b,bc,bg,bi,&bn,&bin,hero,1);assert(an==bn&&ain==bin);assert(!memcmp(a,b,sizeof a));assert(!memcmp(ac,bc,an*sizeof(int)));assert(!memcmp(ag,bg,an*sizeof(int)));assert(!memcmp(ai,bi,ain*sizeof(int)));}puts("PASS 20000 maps/33180000 signed16 glyphs, memory and ordered capped lists");}
