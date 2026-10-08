from pathlib import Path
import os,subprocess,shutil,difflib
r=Path(__file__).parent;old=r/'pool83-control-source';s=r/'pool101-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/env_pool.h';before=p.read_text()
needle='static void* ep_worker(void* arg) {'
helper="""static int ep_help_one(EnvPool* p, int own) {
    for (int b = 1; b < p->buffers; b++) {
        EPRegion* r = &p->region[(own+b) % p->buffers];
        pthread_mutex_lock(&r->mu);
        int active = r->active;
        if (active) r->readers++;
        pthread_mutex_unlock(&r->mu);
        if (!active) continue;
        int worked = 0;
        for (int k = 0; k < p->workers; k++) {
            int home = (own+k) % p->workers;
            int seen = __atomic_load_n(&r->next[home*16], __ATOMIC_RELAXED);
            if (home + seen*p->workers >= r->count) continue;
            int n = __atomic_fetch_add(&r->next[home*16], 1, __ATOMIC_RELAXED);
            int offset = home + n*p->workers;
            if (offset >= r->count) continue;
            p->step(p->context, r->start+offset);
            __atomic_fetch_add(&r->done, 1, __ATOMIC_RELEASE);
            worked = 1; break;
        }
        pthread_mutex_lock(&r->mu);
        if (--r->readers == 0) pthread_cond_signal(&r->quiet);
        pthread_mutex_unlock(&r->mu);
        if (worked) return 1;
    }
    return 0;
}

"""
assert before.count(needle)==1
after=before.replace(needle,helper+needle)
needle='    while (__atomic_load_n(&r->done, __ATOMIC_ACQUIRE) < count) sched_yield();'
assert after.count(needle)==1
after=after.replace(needle,"""    unsigned int polls = 0;
    while (__atomic_load_n(&r->done, __ATOMIC_ACQUIRE) < count) {
        if ((polls++ & 63) == 0 && ep_help_one(p, buffer)) continue;
        sched_yield();
    }""")
p.write_text(after)
(r/'pool101.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/env_pool.h',tofile='b/src/env_pool.h')))
with (r/'pool101-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_pool'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_POOL -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('POOL87_BUILD_COMPLETE',flush=True)
