#define _GNU_SOURCE
#include <time.h>
#include <omp.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <valgrind/callgrind.h>
#include "source/ocean/nethack/nethack.h"
#include "env_pool.h"
static Env* envs;
static float* actions[4];
static int env_count, buffers=4, apb, single=-1, sampling, measured;
static long ticks[4];
static long* samples;
static double* work;
static uint64_t* advances;
static double now(void) { struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9; }
static uint64_t hash_bytes(uint64_t h,const void* ptr,size_t n) {const unsigned char* p=ptr;for(size_t j=0;j<n;j++){h^=p[j];h*=1099511628211ULL;}return h;}
static void step_one(void* unused,int i) {
 Env* e=envs+i;int b=i/apb,original=single>=0?single:(b*128+i%apb%128);
 int stream=original/128,slot=original%128;
 memcpy(e->agents[0].actions,actions[stream]+((size_t)ticks[b]*128+slot)*NUM_ATNS,NUM_ATNS*sizeof(float));
 *e->agents[0].rewards=0;*e->agents[0].terminals=0;
 long before=e->blstats[NLE_BL_TIME];
 int sample=measured && sampling && ticks[b]%64==0;double start=sample?now():0;
 puf_step(e);
 if(sample){work[i]+=now()-start;samples[i]++;}
 long after=e->blstats[NLE_BL_TIME];if(measured && after>before)advances[i]+=after-before;
}
static void rounds(EnvPool* pool,long begin,long count) {
#pragma omp parallel num_threads(buffers)
 {int b=omp_get_thread_num();for(long t=begin;t<begin+count;t++) {ticks[b]=t;if(pool)ep_run(pool,b,b*apb,apb);else for(int i=b*apb;i<(b+1)*apb;i++)step_one(NULL,i);}}
}
int main(int argc,char**argv) {
 if(argc<6){fprintf(stderr,"replay envs workers warm steps action_dir [single_env]\n");return 2;}
 env_count=atoi(argv[1]);int workers=atoi(argv[2]);long warm=atol(argv[3]),steps=atol(argv[4]);
 if(argc>6){single=atoi(argv[6]);env_count=1;buffers=1;}
 assert(env_count%buffers==0);apb=env_count/buffers;
 sampling=getenv("CPU_SAMPLE")!=NULL;
 omp_set_dynamic(0);omp_set_max_active_levels(2);
 for(int b=0;b<4;b++){char path[4096];snprintf(path,sizeof(path),"%s/buf%d.bin",argv[5],b);int fd=open(path,O_RDONLY);assert(fd>=0);struct stat st;assert(fstat(fd,&st)==0);assert(st.st_size>=(warm+steps)*128*NUM_ATNS*sizeof(float));actions[b]=mmap(NULL,st.st_size,PROT_READ,MAP_PRIVATE,fd,0);assert(actions[b]!=MAP_FAILED);close(fd);}
 envs=calloc(env_count,sizeof(Env));work=calloc(env_count,sizeof(double));samples=calloc(env_count,sizeof(long));advances=calloc(env_count,sizeof(uint64_t));
 Dict kwargs={0};
 dict_set(&kwargs,"gold_coef",0.0530697852);dict_set(&kwargs,"score_coef",0.00148907036);dict_set(&kwargs,"exp_coef",0.0912783295);dict_set(&kwargs,"descent_coef",1);dict_set(&kwargs,"floor_coef",0.126026332);dict_set(&kwargs,"xp_coef",1);dict_set(&kwargs,"scout_coef",0.00686222408);dict_set(&kwargs,"death_penalty",-0.472198129);dict_set(&kwargs,"mask_search20",0);dict_set(&kwargs,"mask_run",0);dict_set(&kwargs,"multi_role",1);
 int sizes[]=ACT_SIZES,mask_size=0;for(int h=0;h<NUM_ATNS;h++)mask_size+=sizes[h];
 double start=now();
 for(int i=0;i<env_count;i++){Env*e=envs+i;e->rng=single>=0?single:(i/apb*128+i%apb%128);puf_init(e,&kwargs);Agent*a=e->agents;a->observations=calloc(OBS_SIZE,1);a->actions=calloc(NUM_ATNS,sizeof(float));a->rewards=calloc(1,sizeof(float));a->terminals=calloc(1,sizeof(float));a->action_mask=calloc(mask_size,1);puf_reset(e);}
 EnvPool*pool=workers>0?ep_create(workers,buffers,step_one,NULL):NULL;
 double initialized=now();rounds(pool,0,warm);double warmed=now();
 measured=1;CALLGRIND_ZERO_STATS;CALLGRIND_START_INSTRUMENTATION;
 rounds(pool,warm,steps);double stopped=now();CALLGRIND_STOP_INSTRUMENTATION;CALLGRIND_DUMP_STATS;
 uint64_t hash=1469598103934665603ULL;long turns=0;uint64_t world_steps=0;
 for(int b=0;b<buffers;b++)for(int i=b*apb;i<(b+1)*apb;i++){if(i%apb<128)hash=hash_bytes(hash,envs[i].agents[0].observations,OBS_SIZE);else assert(memcmp(envs[i].agents[0].observations,envs[b*apb+i%128].agents[0].observations,OBS_SIZE)==0);turns+=envs[i].blstats[NLE_BL_TIME];world_steps+=advances[i];}
 printf("RESULT envs=%d workers=%d warm=%ld steps=%ld init=%.6f warm_seconds=%.6f seconds=%.6f sps=%.2f obs=%016lx age=%.2f turns=%lu\n",env_count,workers,warm,steps,initialized-start,warmed-initialized,stopped-warmed,env_count*steps/(stopped-warmed),hash,(double)turns/env_count,world_steps);
 if(sampling)for(int i=0;i<env_count;i++)printf("ENV id=%d seed=%u samples=%ld seconds=%.9f turn=%ld depth=%ld\n",i,envs[i].rng,samples[i],work[i],envs[i].blstats[NLE_BL_TIME],envs[i].blstats[NLE_BL_DEPTH]);
 if(pool)ep_destroy(pool);
 for(int i=0;i<env_count;i++){Env*e=envs+i;puf_close(e);free(e->agents[0].observations);free(e->agents[0].actions);free(e->agents[0].rewards);free(e->agents[0].terminals);free(e->agents[0].action_mask);}free(envs);return 0;
}
