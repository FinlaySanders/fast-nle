from pathlib import Path
import shutil,difflib,json
r=Path(__file__).resolve().parent
native_old='''            #pragma omp parallel for schedule(static) num_threads(vec->num_workers)
            for (int i = env_start; i < env_start + env_count; i++) {
                puf_step(&envs[i]);
            }'''
native_new='''#ifdef PUF_ENV_WS
            {
                int nw = vec->num_workers;
                if (nw > 256) nw = 256;
                int next[256 * 16];
                int per = (env_count + nw - 1) / nw;
                for (int w = 0; w < nw; w++) next[w * 16] = env_start + w * per;
                #pragma omp parallel num_threads(nw)
                {
                    int worker = omp_get_thread_num();
                    for (int k = 0; k < nw; k++) {
                        int victim = (worker + k) % nw;
                        int end = env_start + (victim + 1) * per;
                        if (end > env_start + env_count) end = env_start + env_count;
                        for (;;) {
                            int i = __atomic_fetch_add(&next[victim * 16], 1, __ATOMIC_RELAXED);
                            if (i >= end) break;
                            puf_step(&envs[i]);
                        }
                    }
                }
            }
#else
'''+native_old+'''
#endif'''
for w in ['depth','score']:
 old=r/'harness-v4'/w;new=r/'scheduling'/w
 shutil.copytree(old/'source',new/'source',symlinks=True,ignore=shutil.ignore_patterns('puffer','build'))
 src=new/'source/src';original=src.resolve();assert src.is_symlink();src.unlink();shutil.copytree(original,src)
 p=src/'pufferl.cu';before=p.read_text();assert before.count(native_old)==1;p.write_text(before.replace(native_old,native_new))
 (new/'native-ws.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),p.read_text().splitlines(True),fromfile='a/src/pufferl.cu',tofile='b/src/pufferl.cu')))
 # Create a replay-only scheduler, keeping the engine and policy backend fixed.
 text=(r/'harness-v3'/w/'replay_vec.c').read_text()
 text=text.replace(' Session* ss=(Session*)calloc(n,sizeof(Session));',' int* ws_next=(int*)calloc(threads*16,sizeof(int));\n Session* ss=(Session*)calloc(n,sizeof(Session));')
 warm='''#pragma omp for schedule(static)
   for(int i=0;i<n;i++)(engine?engine_step_session(&ss[i],verify):step_session(&ss[i]));'''
 warmws='''#pragma omp single
   { int nw=omp_get_num_threads(),per=(n+nw-1)/nw;for(int w=0;w<nw;w++)ws_next[w*16]=w*per; }
   { int nw=omp_get_num_threads(),per=(n+nw-1)/nw,id=omp_get_thread_num();
     for(int k=0;k<nw;k++){int v=(id+k)%nw,end=(v+1)*per;if(end>n)end=n;
       for(;;){int i=__atomic_fetch_add(&ws_next[v*16],1,__ATOMIC_RELAXED);if(i>=end)break;
         (engine?engine_step_session(&ss[i],verify):step_session(&ss[i]));}}
   }
#pragma omp barrier'''
 assert warm in text;text=text.replace(warm,warmws)
 measured='''#pragma omp single
   active=0;
#pragma omp for schedule(static) reduction(+:active)
   for(int i=0;i<n;i++)active+=(engine?engine_step_session(&ss[i],verify):step_session(&ss[i]));'''
 measuredws='''#pragma omp single
   { active=0;int nw=omp_get_num_threads(),per=(n+nw-1)/nw;for(int w=0;w<nw;w++)ws_next[w*16]=w*per; }
   { int local=0,nw=omp_get_num_threads(),per=(n+nw-1)/nw,id=omp_get_thread_num();
     for(int k=0;k<nw;k++){int v=(id+k)%nw,end=(v+1)*per;if(end>n)end=n;
       for(;;){int i=__atomic_fetch_add(&ws_next[v*16],1,__ATOMIC_RELAXED);if(i>=end)break;
         local+=(engine?engine_step_session(&ss[i],verify):step_session(&ss[i]));}}
#pragma omp atomic update
     active+=local;
   }
#pragma omp barrier'''
 assert measured in text;text=text.replace(measured,measuredws).replace('free(ss);return 0;','free(ss);free(ws_next);return 0;')
 (new/'replay_ws.c').write_text(text)
print('Prepared isolated work-stealing sources; no build started.')
