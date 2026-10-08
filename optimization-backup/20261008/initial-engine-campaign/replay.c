#define _GNU_SOURCE
#include <time.h>
#include <omp.h>
#include "source/ocean/nethack/nethack.h"
static double now(void) {struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static long replay(const char* path,int verify,double* seconds,long* turns) {
    FILE* disk=fopen(path,"rb");assert(disk);fseek(disk,0,SEEK_END);long bytes=ftell(disk);rewind(disk);
    char* data=(char*)malloc(bytes);assert(fread(data,1,bytes,disk)==(size_t)bytes);fclose(disk);
    FILE* f=fmemopen(data,bytes,"rb");assert(f);
    TraceHeader h;assert(fread(&h,1,sizeof(h),f)==sizeof(h));assert(!memcmp(h.magic,"NHPERF1",7));
    Nethack* e=(Nethack*)calloc(1,sizeof(Nethack));e->rng=h.rng;
    e->agents[0].observations=(unsigned char*)calloc(OBS_SIZE,1);
    e->agents[0].actions=(float*)calloc(NUM_ATNS,sizeof(float));
    e->agents[0].rewards=(float*)calloc(1,sizeof(float));e->agents[0].terminals=(float*)calloc(1,sizeof(float));
    int sizes[]=ACT_SIZES,n=0;for(int i=0;i<NUM_ATNS;i++)n+=sizes[i];
    e->agents[0].action_mask=(unsigned char*)calloc(n,1);
    init(e);memcpy(&e->gold_coef,h.cfg,sizeof(h.cfg));e->trace_file=f;e->trace_mode=verify?2:3;
    nethack_sync_buffers(e);nethack_do_reset(e);
    double start=now();long steps=0,advance=0;
    while(1) {
        int kind=fgetc(f);if(kind==EOF)break;ungetc(kind,f);
        assert(kind=='A');long off=ftell(f);fgetc(f);
        assert(fread(e->agents[0].actions,sizeof(float),NUM_ATNS,f)==NUM_ATNS);fseek(f,off,SEEK_SET);
        long before=e->blstats[NLE_BL_TIME];
        puf_step(e);long after=e->blstats[NLE_BL_TIME];if(after>before)advance+=after-before;
        steps++;
    }
    *seconds=now()-start;*turns=advance;
    puf_close(e);free(e->agents[0].observations);free(e->agents[0].actions);free(e->agents[0].rewards);free(e->agents[0].terminals);free(e->agents[0].action_mask);free(e);free(data);
    return steps;
}
int main(int argc,char** argv) {
    if(argc<4){fprintf(stderr,"usage: replay verify|time threads trace...\n");return 2;}
    int verify=!strcmp(argv[1],"verify"),threads=atoi(argv[2]);
    // Initialise function-local process constants on one thread before parallel work.
    double sec;long turns;long first=replay(argv[3],verify,&sec,&turns);
    printf("FIRST steps=%ld turns=%ld step_seconds=%.6f\n",first,turns,sec);
    double begin=now(),total_seconds=0;long total_steps=0,total_turns=0;
#pragma omp parallel for num_threads(threads) reduction(+:total_steps,total_turns,total_seconds) schedule(dynamic,1)
    for(int i=3;i<argc;i++) {double s;long t;long n=replay(argv[i],verify,&s,&t);total_steps+=n;total_turns+=t;total_seconds+=s;}
    printf("DONE mode=%s files=%d threads=%d steps=%ld turns=%ld wall_seconds=%.6f summed_step_seconds=%.6f\n",argv[1],argc-3,threads,total_steps,total_turns,now()-begin,total_seconds);
}
