from pathlib import Path
r=Path(__file__).resolve().parent
replacement='''typedef struct {
 EnvPool* pool;int n,threads,stop;long rounds;
 pthread_barrier_t begin,end;
 pthread_t submitters[4];
} ReplayDriver;
typedef struct {ReplayDriver* d;int buffer;} ReplayArg;
static ReplayDriver driver;
static ReplayArg submit_args[4];
static void* replay_submitter(void* arg) {
 ReplayArg* a=(ReplayArg*)arg;ReplayDriver* d=a->d;int b=a->buffer;
 int lo=b*d->n/4,hi=(b+1)*d->n/4;
 for(;;) {
  pthread_barrier_wait(&d->begin);
  if(d->stop)break;
  for(long t=0;t<d->rounds;t++) {
   int any=0;for(int i=lo;i<hi;i++)any|=!replay_sessions[i].finished;
   if(!any)break;
   replay_region(d->pool,b,lo,hi-lo,d->threads/4);
  }
  pthread_barrier_wait(&d->end);
 }
 return NULL;
}
static void replay_driver_start(EnvPool* pool,int n,int threads) {
 driver.pool=pool;driver.n=n;driver.threads=threads;
 pthread_barrier_init(&driver.begin,NULL,5);pthread_barrier_init(&driver.end,NULL,5);
 for(int b=0;b<4;b++) {
  submit_args[b]=(ReplayArg){&driver,b};
  assert(!pthread_create(&driver.submitters[b],NULL,replay_submitter,&submit_args[b]));
 }
}
static void replay_rounds(EnvPool* pool,int n,int threads,long rounds) {
 (void)pool;(void)n;(void)threads;
 driver.rounds=rounds;
 pthread_barrier_wait(&driver.begin);pthread_barrier_wait(&driver.end);
}
static void replay_driver_stop(void) {
 driver.stop=1;pthread_barrier_wait(&driver.begin);
 for(int b=0;b<4;b++)pthread_join(driver.submitters[b],NULL);
 pthread_barrier_destroy(&driver.begin);pthread_barrier_destroy(&driver.end);
}
'''
for w in ['depth','score']:
 p=r/'shared-pool'/w/'replay_buffers.c';s=p.read_text()
 start=s.index('static void replay_rounds(');end=s.index('\nint main(',start)
 s=s[:start]+replacement+s[end:]
 s=s.replace(' double init_seconds=now()-init_start,warm_start=now();',' replay_driver_start(pool,n,threads);\n double init_seconds=now()-init_start,warm_start=now();')
 s=s.replace(' if(pool)ep_destroy(pool);',' replay_driver_stop();\n if(pool)ep_destroy(pool);')
 (r/'shared-pool'/w/'replay_pthreads.c').write_text(s)
# Preserve the rejected nested-OMP experiment; new outputs and binaries.
script=(r/'run_multibuffer_replay.py').read_text()
a=script.index("pid=int((r/'four-buffer-diagnostic.pid')")
b=script.index('rows=[];bench=[]',a)
script=script[:a]+script[b:]
script=script.replace("root=r/'shared-pool'","root=r/'pthread-replay';root.mkdir(exist_ok=True)")
script=script.replace("n=root/w;s=n/'source'","n=r/'shared-pool'/w;s=n/'source'")
script=script.replace("'-I'+str(root)","'-I'+str(r/'shared-pool')")
script=script.replace("n/'replay_buffers.c'","n/'replay_pthreads.c'")
script=script.replace("n=root/w;corpus=","n=r/'shared-pool'/w;corpus=")
script=script.replace("('replay_'+kind)","('replay_pthread_'+kind)")
(r/'run_pthread_replay.py').write_text(script)
print('Persistent pthread submitters prepared; nested OpenMP timings rejected as unrepresentative')
