from pathlib import Path
import os,subprocess,shutil,difflib
r=Path(__file__).parent;old=r/'pool83-control-source';s=r/'pool91-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/env_pool.h';before=p.read_text()
needle='    EnvPool* p = w->pool;'
assert before.count(needle)==1
replacement=needle+"""
    const char* pin = getenv("PUF_POOL_PHYSICAL");
    if (pin && atoi(pin)) {
        assert(p->workers == 24);
        cpu_set_t cpus; CPU_ZERO(&cpus);
        CPU_SET(w->id < 8 ? 2*w->id : w->id+8, &cpus);
        if (pthread_setaffinity_np(pthread_self(), sizeof(cpus), &cpus)) abort();
    }
"""
after=before.replace(needle,replacement);p.write_text(after)
(r/'pool91.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/env_pool.h',tofile='b/src/env_pool.h')))
with (r/'pool91-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_pool'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_POOL -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('POOL87_BUILD_COMPLETE',flush=True)
