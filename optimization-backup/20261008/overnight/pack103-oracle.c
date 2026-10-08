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
for(int cell=0;cell<N;cell++){
 if(simd&&cell+8<=N){__m128i gs=_mm_loadu_si128((const __m128i*)(g+cell));__m128i a=_mm_cmpgt_epi16(gs,_mm_set1_epi16(2358));__m128i b=_mm_cmpgt_epi16(_mm_set1_epi16(2455),gs);if(_mm_movemask_epi8(_mm_and_si128(a,b))==65535){_mm_storeu_si128((__m128i*)(m+cell),_mm_setzero_si128());cell+=7;continue;}}
 int v=g[cell];if(v>=2359&&v<2455)m[cell]=0;
 else if(v>=1906&&v<2359)m[cell]=(unsigned short)(v-1906+1);
 else if(v>=1144&&v<1526)m[cell]=(unsigned short)(v-1144+454);
 else if(v>=0&&v<1144&&cell!=hero&&*nmon<256){mc[*nmon]=cell;mg[(*nmon)++]=v;}
 if(m[cell]&&*nit<256)ic[(*nit)++]=cell;
}}
int main(void){short g[N];unsigned short a[N],b[N];int ac[256],ag[256],ai[256],bc[256],bg[256],bi[256],an,ain,bn,bin;
for(int trial=0;trial<20000;trial++){for(int i=0;i<N;i++){unsigned v=rnd();g[i]=trial%3==0?(short)v:trial%3==1?(short)(2359+v%96):(short)(v%4?2359+v%96:v%6000);a[i]=b[i]=(unsigned short)rnd();}int hero=(int)(rnd()%(N+1))-1;scan(g,a,ac,ag,ai,&an,&ain,hero,0);scan(g,b,bc,bg,bi,&bn,&bin,hero,1);assert(an==bn&&ain==bin);assert(!memcmp(a,b,sizeof a));assert(!memcmp(ac,bc,an*sizeof(int)));assert(!memcmp(ag,bg,an*sizeof(int)));assert(!memcmp(ai,bi,ain*sizeof(int)));}puts("PASS 20000 maps/33180000 signed16 glyphs, memory and ordered capped lists");}
