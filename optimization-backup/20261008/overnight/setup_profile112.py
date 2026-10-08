from pathlib import Path
import shutil,subprocess,os,difflib
r=Path(__file__).parent;old=r/'pool83-control-source';s=r/'profile112-source';s.mkdir()
for n in ['src','config']:shutil.copytree(old/n,s/n)
shutil.copy2(old/'build.sh',s/'build.sh')
for n in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/n).symlink_to((old/n).resolve(),target_is_directory=True)
p=s/'src/env_pool.h';a=p.read_text();b=a.replace('#include <pthread.h>','#include <pthread.h>\n#include <nvtx3/nvToolsExt.h>')
for x,y in [
('            ep_claim(p, r, w->id);','            nvtxRangePushA("pool.worker_work");\n            ep_claim(p, r, w->id);\n            nvtxRangePop();'),
('    ep_claim(p, r, buffer % p->workers);','    nvtxRangePushA("pool.submitter_work");\n    ep_claim(p, r, buffer % p->workers);\n    nvtxRangePop();'),
('    while (__atomic_load_n(&r->done, __ATOMIC_ACQUIRE) < count) sched_yield();','    nvtxRangePushA("pool.tail_wait");\n    while (__atomic_load_n(&r->done, __ATOMIC_ACQUIRE) < count) sched_yield();\n    nvtxRangePop();'),
('    while (r->readers) pthread_cond_wait(&r->quiet, &r->mu);','    nvtxRangePushA("pool.reader_drain");\n    while (r->readers) pthread_cond_wait(&r->quiet, &r->mu);\n    nvtxRangePop();')]:
 assert b.count(x)==1,x;b=b.replace(x,y)
p.write_text(b)
p=s/'src/pufferl.cu';a=p.read_text();start=a.index('static void* vec_thread_main(');end=a.index('// Fresh episodes',start);t=a[start:end]
for x,y in [
('            cudaEventRecord(ev[MODEL_START], stream);','            nvtxRangePushA("rollout.gpu_submit");\n            cudaEventRecord(ev[MODEL_START], stream);'),
('            cudaStreamSynchronize(stream);','            nvtxRangePop();\n            nvtxRangePushA("rollout.gpu_wait");\n            cudaStreamSynchronize(stream);\n            nvtxRangePop();'),
('            ep_run(vec->env_pool, buf, env_start, env_count);','            nvtxRangePushA("rollout.env");\n            ep_run(vec->env_pool, buf, env_start, env_count);\n            nvtxRangePop();'),
('            cudaEventRecord(ev[H2D_START], stream);','            nvtxRangePushA("rollout.upload");\n            cudaEventRecord(ev[H2D_START], stream);'),
('            cudaEventRecord(ev[H2D_END], stream);','            cudaEventRecord(ev[H2D_END], stream);\n            nvtxRangePop();')]:
 assert t.count(x)==1,x;t=t.replace(x,y)
p.write_text(a[:start]+t+a[end:])
with (r/'profile112-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_profile'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_POOL -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('PROFILE112_BUILD_COMPLETE',flush=True)
