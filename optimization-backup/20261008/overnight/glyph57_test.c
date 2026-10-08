#include <stdint.h>
#include <assert.h>
#include "hack.h"
int main(void) {
    struct nh_ctx *ctx[4];
    short expected[4][ROWNO*(COLNO-1)] = {{0}}, got[ROWNO*(COLNO-1)];
    uint32_t rng = 173;
    unsigned checks=0;
    for (int i=0;i<4;i++) ctx[i]=nh_ctx_new();
    for (int k=0;k<40000;k++) {
        int which = k%4;
        nh_cur=ctx[which];
        if (k < 4 || k%337==0) {
            clear_glyph_buffer();
            for(int j=0;j<ROWNO*(COLNO-1);j++) expected[which][j]=cmap_to_glyph(S_stone);
        } else {
            rng=rng*1664525U+1013904223U;
            int x=1+(rng%(COLNO-1));
            rng=rng*1664525U+1013904223U;
            int y=rng%ROWNO;
            rng=rng*1664525U+1013904223U;
            int g=rng%MAX_GLYPH;
            show_glyph(x,y,g);
            expected[which][y*(COLNO-1)+x-1]=(short)g;
            show_glyph(0,y,g); /* ignored sentinel column */
        }
        nle_copy_glyphs(got);
        for(int j=0;j<ROWNO*(COLNO-1);j++) { assert(got[j]==expected[which][j]); checks++; }
    }
    for(int i=0;i<4;i++) nh_ctx_free(ctx[i]);
    nh_cur=0;
    printf("PASS %u glyph comparisons across interleaved contexts and clears\n",checks);
    return 0;
}
