from pathlib import Path
import shutil,subprocess,os
r=Path(__file__).parent;old=r/'rollout11-source';s=r/'affinity13-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/pufferl.cu';t=p.read_text();start=t.index('static void* vec_thread_main(');needle='    int buf = a->buf;';idx=t.index(needle,start);add='''
    assert(vec->buffers == 4 && vec->num_workers == 8);
    cpu_set_t affinity;
    CPU_ZERO(&affinity);
    for (int k=0;k<4;k++) {CPU_SET(4*buf+k,&affinity);CPU_SET(16+4*buf+k,&affinity);}
    assert(pthread_setaffinity_np(pthread_self(),sizeof(affinity),&affinity)==0);
''';t=t[:idx]+t[idx:].replace(needle,needle+add,1);t='#include <sched.h>\n'+t;p.write_text(t)
(r/'affinity13.patch').write_bytes(subprocess.run(['diff','-u','--label','a/src/pufferl.cu','--label','b/src/pufferl.cu',str(old/'src/pufferl.cu'),str(p)],capture_output=True).stdout)
with (r/'affinity13-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_affinity'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_WS -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('AFFINITY_BUILD_COMPLETE',flush=True)
