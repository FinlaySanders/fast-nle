from pathlib import Path
r=Path(__file__).resolve().parent
for w in ['depth','score']:
 src=(r/'scheduling'/w/'replay_static.c').read_text()
 insert='''
#include "env_pool.h"
static Session* replay_sessions;
static int replay_engine, replay_verify;
static void replay_one(void* unused, int i) {
 (void)unused;
 if(replay_engine)engine_step_session(&replay_sessions[i],replay_verify);
 else step_session(&replay_sessions[i]);
}
static void replay_region(EnvPool* pool,int buffer,int lo,int count,int threads) {
#ifdef REPLAY_POOL
 ep_run(pool,buffer,lo,count);
#elif defined(REPLAY_WS)
 int next[256*16];assert(threads<=256);int per=(count+threads-1)/threads;
 for(int w=0;w<threads;w++)next[w*16]=lo+w*per;
#pragma omp parallel num_threads(threads)
 {int id=omp_get_thread_num();for(int k=0;k<threads;k++){int v=(id+k)%threads,hi=lo+(v+1)*per;if(hi>lo+count)hi=lo+count;
 for(;;){int i=__atomic_fetch_add(&next[v*16],1,__ATOMIC_RELAXED);if(i>=hi)break;replay_one(NULL,i);}}}
#else
#pragma omp parallel for num_threads(threads) schedule(static)
 for(int i=lo;i<lo+count;i++)replay_one(NULL,i);
#endif
}
static void replay_rounds(EnvPool* pool,int n,int threads,long rounds) {
#pragma omp parallel num_threads(4)
 {int b=omp_get_thread_num(),lo=b*n/4,hi=(b+1)*n/4;
  for(long t=0;t<rounds;t++) {
   int any=0;for(int i=lo;i<hi;i++)any|=!replay_sessions[i].finished;
   if(!any)break;
   replay_region(pool,b,lo,hi-lo,threads/4);
  }
 }
}
'''
 src=src.replace('int main(int argc,char** argv) {',insert+'\nint main(int argc,char** argv) {')
 needle=' double init_seconds=now()-init_start,warm_start=now();'
 src=src.replace(needle,''' assert(threads>=4 && threads%4==0 && n>=4);
 omp_set_dynamic(0);omp_set_max_active_levels(2);
 replay_sessions=ss;replay_engine=engine;replay_verify=verify;
 EnvPool* pool=NULL;
#ifdef REPLAY_POOL
 pool=ep_create(threads>4?threads-4:1,4,replay_one,NULL);
#endif
'''+needle)
 start=src.index('#pragma omp parallel num_threads(threads)\n {\n  for(long t=0;t<warm;t++)')
 end=src.index(' double warm_seconds=',start)
 src=src[:start]+' replay_rounds(pool,n,threads,warm);\n'+src[end:]
 start=src.index('#pragma omp parallel num_threads(threads) shared(active)')
 end=src.index(' double elapsed=',start)
 src=src[:start]+' replay_rounds(pool,n,threads,measure);\n'+src[end:]
 src=src.replace(' for(int i=0;i<n;i++)close_session(&ss[i]);',' if(pool)ep_destroy(pool);\n for(int i=0;i<n;i++)close_session(&ss[i]);')
 (r/'shared-pool'/w/'replay_buffers.c').write_text(src)
print('Prepared same four-region fixed-action workload for static/WS/pool')
