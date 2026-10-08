from pathlib import Path
import os,subprocess,shutil,difflib
r=Path(__file__).parent;old=r/'pool83-control-source';s=r/'pool97-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/env_pool.h';before=p.read_text()
needle='    while (__atomic_load_n(&r->done, __ATOMIC_ACQUIRE) < count) sched_yield();'
assert before.count(needle)==1
replacement="""    unsigned int spins = 0;
    while (__atomic_load_n(&r->done, __ATOMIC_ACQUIRE) < count) {
#if defined(__x86_64__) || defined(__i386__)
        if (++spins < 64) __asm__ __volatile__("pause");
        else { spins = 0; sched_yield(); }
#else
        sched_yield();
#endif
    }"""
after=before.replace(needle,replacement);p.write_text(after)
(r/'pool97.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/env_pool.h',tofile='b/src/env_pool.h')))
with (r/'pool97-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_pool'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_POOL -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('POOL87_BUILD_COMPLETE',flush=True)
