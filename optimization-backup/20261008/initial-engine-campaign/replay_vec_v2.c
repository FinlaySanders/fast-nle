#define _GNU_SOURCE
#include <time.h>
#include <omp.h>
#include <sys/resource.h>
#include <sys/mman.h>
#include <valgrind/callgrind.h>
#include "source/ocean/nethack/nethack.h"
typedef struct {Nethack* e;void* data;size_t bytes;long steps,turns,keys,measure_offset;int finished;} Session;
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static Session load_session(const char* path,int verify) {
 Session s={0};FILE* disk=fopen(path,"rb");assert(disk);fseek(disk,0,SEEK_END);s.bytes=ftell(disk);rewind(disk);
 s.data=mmap(NULL,s.bytes,PROT_READ,MAP_PRIVATE,fileno(disk),0);assert(s.data!=MAP_FAILED);fclose(disk);
 FILE* f=fmemopen(s.data,s.bytes,"rb");assert(f);TraceHeader h;assert(fread(&h,1,sizeof(h),f)==sizeof(h));assert(!memcmp(h.magic,"NHPERF1",7));
 Nethack* e=(Nethack*)calloc(1,sizeof(Nethack));s.e=e;e->rng=h.rng;
 e->agents[0].observations=(unsigned char*)calloc(OBS_SIZE,1);e->agents[0].actions=(float*)calloc(NUM_ATNS,sizeof(float));
 e->agents[0].rewards=(float*)calloc(1,sizeof(float));e->agents[0].terminals=(float*)calloc(1,sizeof(float));
 int sizes[]=ACT_SIZES,n=0;for(int i=0;i<NUM_ATNS;i++)n+=sizes[i];e->agents[0].action_mask=(unsigned char*)calloc(n,1);
 init(e);memcpy(&e->gold_coef,h.cfg,sizeof(h.cfg));e->trace_file=f;e->trace_mode=verify?2:3;
 nethack_sync_buffers(e);nethack_do_reset(e);return s;
}
static int step_session(Session* s) {
 if(s->finished)return 0;Nethack* e=s->e;FILE* f=e->trace_file;
 int kind=fgetc(f);if(kind==EOF){s->finished=1;return 0;}assert(kind=='A');
 long off=ftell(f)-1;assert(fread(e->agents[0].actions,sizeof(float),NUM_ATNS,f)==NUM_ATNS);fseek(f,off,SEEK_SET);
 long before=e->blstats[NLE_BL_TIME];puf_step(e);long after=e->blstats[NLE_BL_TIME];if(after>before)s->turns+=after-before;s->steps++;return 1;
}
static int engine_step_session(Session* s,int verify) {
 if(s->finished)return 0;Nethack* e=s->e;FILE* f=e->trace_file;
 int kind=fgetc(f);if(kind==EOF){s->finished=1;return 0;}assert(kind=='A');
 assert(fread(e->agents[0].actions,sizeof(float),NUM_ATNS,f)==NUM_ATNS);
 long before=e->blstats[NLE_BL_TIME];
 while(1) {
  kind=fgetc(f);assert(kind!=EOF);
  if(kind=='k') {
   int key;assert(fread(&key,1,sizeof(key),f)==sizeof(key));e->obs.action=key;
   e->ctx=nle_step(e->ctx,&e->obs);trace_engine(e,'K');s->keys++;
  } else if(kind=='F') {
   ungetc(kind,f);nle_obs_refresh(e->ctx,&e->obs);trace_engine(e,'F');
  } else if(kind=='W') {
   float rw[2];assert(fread(rw,1,sizeof(rw),f)==sizeof(rw));
   if(!e->obs.done){short path[2*NETHACK_PATH_MAX];nle_path_drain(e->ctx,path,NETHACK_PATH_MAX);}
  } else if(kind=='E') {long x[6];assert(fread(x,1,sizeof(x),f)==sizeof(x));}
  else if(kind=='R') {
   TraceStart st;assert(fread(&st,1,sizeof(st),f)==sizeof(st));
   if(e->ctx)nle_end(e->ctx);e->ctx=NULL;nethack_bind_obs(e);e->obs.how_done=-2;
   e->seed=st.seed;e->settings.initial_seeds.seeds[0]=st.seed;
   e->settings.initial_seeds.seeds[1]=st.seed^0x9E3779B97F4A7C15UL;
   e->settings.initial_seeds.use_init_seeds=true;e->settings.time_seed=st.seed;e->settings.time_seed_is_set=true;
   e->settings.spawn_monsters=st.spawn;e->settings.underfoot_glyphs=st.underfoot;e->settings.fix_moon_phase=st.moon;
   char path[2048];snprintf(path,sizeof(path),"%s/trace-options",e->vardir);FILE* rc=fopen(path,"w");assert(rc);
   size_t n=strnlen(st.options,sizeof(st.options));assert(fwrite(st.options,1,n,rc)==n);fclose(rc);
   snprintf(e->settings.options,sizeof(e->settings.options),"@%s",path);
   e->ctx=nle_start(&e->obs,NULL,&e->settings);trace_engine(e,'S');
  } else if(kind=='O') {uint64_t h;assert(fread(&h,1,sizeof(h),f)==sizeof(h));break;}
  else {fprintf(stderr,"unexpected engine event %c\n",kind);abort();}
 }
 long after=e->blstats[NLE_BL_TIME];if(after>before)s->turns+=after-before;s->steps++;return 1;
}
static long measured_keys(Session *s) {
 const unsigned char *p=(const unsigned char*)s->data+s->measure_offset;
 const unsigned char *end=(const unsigned char*)s->data+ftell(s->e->trace_file);
 long keys=0;
 while(p<end) {
  unsigned char kind=*p++;size_t bytes=0;
  switch(kind) {
   case 'R':bytes=sizeof(TraceStart);break;
   case 'S':case 'K':case 'F':case 'O':bytes=sizeof(uint64_t);break;
   case 'k':bytes=sizeof(int);keys++;break;
   case 'A':bytes=NUM_ATNS*sizeof(float);break;
   case 'W':bytes=2*sizeof(float);break;
   case 'E':bytes=6*sizeof(long);break;
   default:fprintf(stderr,"bad event in key accounting: %u\n",kind);abort();
  }
  assert((size_t)(end-p)>=bytes);p+=bytes;
 }
 assert(p==end);return keys;
}
static void close_session(Session* s){Nethack* e=s->e;puf_close(e);free(e->agents[0].observations);free(e->agents[0].actions);free(e->agents[0].rewards);free(e->agents[0].terminals);free(e->agents[0].action_mask);free(e);munmap(s->data,s->bytes);}
int main(int argc,char** argv) {
 if(argc<6){fprintf(stderr,"usage: replay_vec verify|time|engine-verify|engine-time threads warmup_steps measured_steps trace...\n");return 2;}
 int engine=!strncmp(argv[1],"engine-",7);
 int verify=!strcmp(argv[1],"verify")||!strcmp(argv[1],"engine-verify"),threads=atoi(argv[2]),n=argc-5;long warm=atol(argv[3]),measure=atol(argv[4]);
 assert(threads>0 && warm>=0 && measure>0);
 Session* ss=(Session*)calloc(n,sizeof(Session));double init_start=now();
 // First env initialises process-constant caches before worker threads start.
 ss[0]=load_session(argv[5],verify);
#pragma omp parallel for num_threads(threads) schedule(static)
 for(int i=1;i<n;i++)ss[i]=load_session(argv[5+i],verify);
 double init_seconds=now()-init_start,warm_start=now();
#pragma omp parallel num_threads(threads)
 {
  for(long t=0;t<warm;t++) {
#pragma omp for schedule(static)
   for(int i=0;i<n;i++)(engine?engine_step_session(&ss[i],verify):step_session(&ss[i]));
  }
 }
 double warm_seconds=now()-warm_start;long before_steps=0,before_turns=0;
 for(int i=0;i<n;i++){before_steps+=ss[i].steps;before_turns+=ss[i].turns;ss[i].measure_offset=ftell(ss[i].e->trace_file);}
 CALLGRIND_ZERO_STATS;CALLGRIND_START_INSTRUMENTATION;
 double start=now();int active=1;
#pragma omp parallel num_threads(threads) shared(active)
 {
  for(long t=0;t<measure;t++) {
#pragma omp single
   active=0;
#pragma omp for schedule(static) reduction(+:active)
   for(int i=0;i<n;i++)active+=(engine?engine_step_session(&ss[i],verify):step_session(&ss[i]));
   int keep_going=active;
#pragma omp barrier
   if(!keep_going)break;
  }
 }
 double elapsed=now()-start;CALLGRIND_STOP_INSTRUMENTATION;CALLGRIND_DUMP_STATS;
 long steps=0,turns=0;int finished=0;for(int i=0;i<n;i++){steps+=ss[i].steps;turns+=ss[i].turns;finished+=ss[i].finished;}
 long keys=0;for(int i=0;i<n;i++)keys+=measured_keys(&ss[i]);
 struct rusage ru;getrusage(RUSAGE_SELF,&ru);
 printf("RESULT mode=%s envs=%d threads=%d warmup=%ld limit=%ld init_seconds=%.6f warmup_seconds=%.6f measured_seconds=%.6f measured_steps=%ld positive_turn_advances=%ld sps=%.2f measured_keys=%ld keys_per_second=%.2f maxrss_kb=%ld completed_streams=%d total_steps=%ld\n",argv[1],n,threads,warm,measure,init_seconds,warm_seconds,elapsed,steps-before_steps,turns-before_turns,(steps-before_steps)/elapsed,keys,keys/elapsed,ru.ru_maxrss,finished,steps);
 for(int i=0;i<n;i++)close_session(&ss[i]);free(ss);return 0;
}
