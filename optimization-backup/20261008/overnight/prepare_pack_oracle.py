from pathlib import Path
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917/harness-v3/score/source/ocean/nethack/nethack.h');scalar=old.read_text();a=scalar.index('        for (int cell = 0; cell < NH_GRID; cell++) {');b=scalar.index('        // lean token block',a);scalar=scalar[a:b]
simd=(r/'pack32/score/source/ocean/nethack/nethack.h').read_text();a=simd.index('        int scan_cell = 0;');b=simd.index('        // lean token block',a);simd=simd[a:b]
head='''#include <emmintrin.h>
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
'''
def fn(name,body):return 'static void '+name+'(Env*env,Out*out,long hero_cell){int *mon_cell=out->mon_cell,*mon_g=out->mon_g,*it_cell=out->it_cell;int nmon=0,nit=0;\n'+body+'out->nmon=nmon;out->nit=nit;}\n'
main='''static uint32_t state=93;static uint32_t rng(void){state^=state<<13;state^=state>>17;state^=state<<5;return state;}
int main(void){Env a,b;Out x,y;for(int trial=0;trial<4096;trial++){for(int i=0;i<NH_GRID;i++){unsigned v=rng();a.glyphs[i]=(short)(trial%4==0?v:trial%4==1?v%6000:trial%4==2?2359+v%96:v%1144);a.obj_mem[i]=(unsigned short)(rng()%2?rng():0);}b=a;memset(&x,0,sizeof(x));memset(&y,0,sizeof(y));long hero=(long)(rng()%(NH_GRID+2))-1;scalar(&a,&x,hero);vector(&b,&y,hero);assert(!memcmp(a.obj_mem,b.obj_mem,sizeof(a.obj_mem)));assert(!memcmp(&x,&y,sizeof(x)));}puts("4096 randomized complete-grid memory and ordered token comparisons passed");}
'''
(r/'pack32-oracle.c').write_text(head+fn('scalar',scalar)+fn('vector',simd)+main)
