from pathlib import Path
import os,subprocess,shutil,difflib
r=Path(__file__).parent;old=r/'pool83-control-source';s=r/'pool106-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/env_pool.h';before=p.read_text();after=before
needle='    int workers, buffers, stop;'
assert after.count(needle)==1;after=after.replace(needle,'    int workers, buffers, stop, sleepers;')
needle='        while (!p->stop && epoch == p->epoch) pthread_cond_wait(&p->ready, &p->mu);'
replacement='        while (!p->stop && epoch == p->epoch) {\n            p->sleepers++;\n            pthread_cond_wait(&p->ready, &p->mu);\n            p->sleepers--;\n        }'
assert after.count(needle)==1;after=after.replace(needle,replacement)
needle='    p->epoch++; pthread_cond_broadcast(&p->ready);'
replacement='    p->epoch++; if (p->sleepers) pthread_cond_broadcast(&p->ready);'
assert after.count(needle)==1;after=after.replace(needle,replacement)

p.write_text(after);(r/'pool106.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/env_pool.h',tofile='b/src/env_pool.h')))
with (r/'pool106-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_pool'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_POOL -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('POOL106_BUILD_COMPLETE',flush=True)
