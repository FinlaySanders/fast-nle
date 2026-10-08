#include <stdint.h>
#include <assert.h>
#include "hack.h"
int main(void) {
    struct nh_ctx *ctx[32];
    FILE *f;
    char line[256];
    for (int i=0;i<32;i++) {
        ctx[i]=nh_ctx_new();
        assert(ctx[i]);
        assert(((uintptr_t)ctx[i] & 2097151)==0);
        assert(ctx[i]->g_moves==1);
        ctx[i]->g_moves=1000+i;
    }
    for(int i=0;i<32;i++) assert(ctx[i]->g_moves==1000+i);
    f=fopen("/proc/self/smaps_rollup","r");assert(f);
    while(fgets(line,sizeof(line),f))
        if(!strncmp(line,"Rss:",4)||!strncmp(line,"AnonHugePages:",14)) fputs(line,stdout);
    fclose(f);
    for(int i=0;i<32;i++) nh_ctx_free(ctx[i]);
    for(int i=0;i<128;i++) {
        struct nh_ctx *p=nh_ctx_new();assert(p);assert(p->g_moves==1);nh_ctx_free(p);
    }
    puts("PASS aligned independent contexts and repeated reset/free");
    return 0;
}
