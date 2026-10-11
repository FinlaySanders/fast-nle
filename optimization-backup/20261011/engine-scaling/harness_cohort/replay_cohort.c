/* replay_cohort: cohort-synchronous scheduler over the recorded-action workload (same init/hash as replay.c).
 * Worker w owns, in every buffer b, the games {b*apb + w + n*W}; a cohort is one (worker, buffer) set.
 * Knobs (env): COHORT_A   cohorts a worker alternates between (1..buffers; buffers = today's interleaving)
 *              COHORT_K   consecutive ticks per cohort visit (burst; >1 ignores latency within the burst)
 *              COHORT_LAT_US  emulated inference latency: a cohort's next tick starts no earlier than LAT after its last one;
 *                             a worker with no ready cohort sleeps until the earliest one is ready
 *              COHORT_PIN  pin worker w to cpu w
 * Per-game action order is unchanged, so the final observation hash must equal replay.c's. */
#define _GNU_SOURCE
#include <time.h>
#include <pthread.h>
#include <sched.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include "source/ocean/nethack/nethack.h"
static Env* envs;
static float* actions[4];
static int env_count, buffers=4, apb, W, A=4, K=1, PIN=0;
static long LAT_NS=0;
static uint64_t* advances; static double* busy; static double* idle_t; static int measured;
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static uint64_t hash_bytes(uint64_t h,const void* ptr,size_t n){const unsigned char* p=ptr;for(size_t j=0;j<n;j++){h^=p[j];h*=1099511628211ULL;}return h;}
static void step_game(int i,long t){
 Env* e=envs+i;int b=i/apb,slot=i%apb%128;
 memcpy(e->agents[0].actions,actions[b]+((size_t)t*128+slot)*NUM_ATNS,NUM_ATNS*sizeof(float));
 *e->agents[0].rewards=0;*e->agents[0].terminals=0;
 long before=e->blstats[NLE_BL_TIME];
 puf_step(e);
 long after=e->blstats[NLE_BL_TIME];if(measured&&after>before)advances[i]+=after-before;
}
typedef struct{int w;long begin,end;}WorkerArg;
static void sleep_until(double t){double d=t-now();if(d<=0)return;struct timespec ts={(time_t)d,(long)((d-(time_t)d)*1e9)};nanosleep(&ts,NULL);}
static void* worker(void* arg){
 WorkerArg* wa=arg;int w=wa->w;
 if(PIN){cpu_set_t cs;CPU_ZERO(&cs);CPU_SET(w%sysconf(_SC_NPROCESSORS_ONLN),&cs);sched_setaffinity(0,sizeof cs,&cs);}
 long tick[4];double ready[4];
 /* process the buffers in groups of A: the group's cohorts alternate until they finish the window */
 for(int g=0;g<buffers;g+=A){
  int n=A<buffers-g?A:buffers-g;
  for(int c=0;c<n;c++){tick[c]=wa->begin;ready[c]=0;}
  for(;;){
   int best=-1;double bestready=0;int remaining=0;
   for(int c=0;c<n;c++){if(tick[c]>=wa->end)continue;remaining++;if(best<0||ready[c]<bestready){best=c;bestready=ready[c];}}
   if(!remaining)break;
   /* prefer a ready cohort in round-robin order; otherwise wait for the earliest */
   double t0=now();
   if(bestready>t0){if(measured)idle_t[w]+=bestready-t0;sleep_until(bestready);}
   int b=g+best;double s=now();
   for(int k=0;k<K&&tick[best]<wa->end;k++){
    for(int i=b*apb+w;i<(b+1)*apb;i+=W)step_game(i,tick[best]);
    tick[best]++;
   }
   double e=now();if(measured)busy[w]+=e-s;ready[best]=e+LAT_NS*1e-9;
  }
 }
 return NULL;
}
static void run_window(long begin,long end){
 pthread_t th[256];WorkerArg wa[256];
 for(int w=0;w<W;w++){wa[w].w=w;wa[w].begin=begin;wa[w].end=end;pthread_create(&th[w],NULL,worker,&wa[w]);}
 for(int w=0;w<W;w++)pthread_join(th[w],NULL);
}
int main(int argc,char**argv){
 if(argc<6){fprintf(stderr,"replay_cohort envs workers warm steps action_dir\n");return 2;}
 env_count=atoi(argv[1]);W=atoi(argv[2]);long warm=atol(argv[3]),steps=atol(argv[4]);
 if(getenv("COHORT_A"))A=atoi(getenv("COHORT_A"));if(getenv("COHORT_K"))K=atoi(getenv("COHORT_K"));
 if(getenv("COHORT_LAT_US"))LAT_NS=atol(getenv("COHORT_LAT_US"))*1000L;if(getenv("COHORT_PIN"))PIN=atoi(getenv("COHORT_PIN"));
 assert(env_count%buffers==0);apb=env_count/buffers;assert(A>=1&&A<=buffers&&K>=1&&W>=1&&W<=256);
 for(int b=0;b<4;b++){char path[4096];snprintf(path,sizeof(path),"%s/buf%d.bin",argv[5],b);int fd=open(path,O_RDONLY);assert(fd>=0);struct stat st;assert(fstat(fd,&st)==0);assert(st.st_size>=(warm+steps)*128*NUM_ATNS*sizeof(float));actions[b]=mmap(NULL,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);assert(actions[b]!=MAP_FAILED);close(fd);}
 envs=calloc(env_count,sizeof(Env));advances=calloc(env_count,sizeof(uint64_t));busy=calloc(W,sizeof(double));idle_t=calloc(W,sizeof(double));
 Dict kwargs={0};
 dict_set(&kwargs,"gold_coef",0.0530697852);dict_set(&kwargs,"score_coef",0.00148907036);dict_set(&kwargs,"exp_coef",0.0912783295);dict_set(&kwargs,"descent_coef",1);dict_set(&kwargs,"floor_coef",0.126026332);dict_set(&kwargs,"xp_coef",1);dict_set(&kwargs,"scout_coef",0.00686222408);dict_set(&kwargs,"death_penalty",-0.472198129);dict_set(&kwargs,"mask_search20",0);dict_set(&kwargs,"mask_run",0);dict_set(&kwargs,"multi_role",1);
 int sizes[]=ACT_SIZES,mask_size=0;for(int h=0;h<NUM_ATNS;h++)mask_size+=sizes[h];
 double start=now();
 for(int i=0;i<env_count;i++){Env*e=envs+i;e->rng=(i/apb*128+i%apb%128);puf_init(e,&kwargs);Agent*a=e->agents;a->observations=calloc(OBS_SIZE,1);a->actions=calloc(NUM_ATNS,sizeof(float));a->rewards=calloc(1,sizeof(float));a->terminals=calloc(1,sizeof(float));a->action_mask=calloc(mask_size,1);puf_reset(e);}
 double initialized=now();
 { int a0=A,k0=K;long l0=LAT_NS; A=buffers;K=1;LAT_NS=0; run_window(0,warm); A=a0;K=k0;LAT_NS=l0; } /* warm with today's interleaving */
 double warmed=now();measured=1;
 run_window(warm,warm+steps);double stopped=now();
 uint64_t hash=1469598103934665603ULL;long turns=0;uint64_t world_steps=0;
 for(int b=0;b<buffers;b++)for(int i=b*apb;i<(b+1)*apb;i++){if(i%apb<128)hash=hash_bytes(hash,envs[i].agents[0].observations,OBS_SIZE);else assert(memcmp(envs[i].agents[0].observations,envs[b*apb+i%128].agents[0].observations,OBS_SIZE)==0);turns+=envs[i].blstats[NLE_BL_TIME];world_steps+=advances[i];}
 double tb=0,ti=0,maxb=0;for(int w=0;w<W;w++){tb+=busy[w];ti+=idle_t[w];if(busy[w]>maxb)maxb=busy[w];}
 printf("RESULT envs=%d workers=%d A=%d K=%d lat_us=%ld pin=%d warm=%ld steps=%ld warm_seconds=%.3f seconds=%.3f sps=%.2f busy_sps=%.2f busy_mean=%.3f busy_max=%.3f idle_mean=%.3f obs=%016lx age=%.2f turns=%lu\n",
  env_count,W,A,K,LAT_NS/1000,PIN,warm,steps,warmed-initialized,stopped-warmed,env_count*steps/(stopped-warmed),env_count*steps/(tb/W),tb/W,maxb,ti/W,hash,(double)turns/env_count,world_steps);
 for(int i=0;i<env_count;i++){Env*e=envs+i;puf_close(e);free(e->agents[0].observations);free(e->agents[0].actions);free(e->agents[0].rewards);free(e->agents[0].terminals);free(e->agents[0].action_mask);}free(envs);return 0;
}
