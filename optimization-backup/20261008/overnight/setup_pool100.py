from pathlib import Path
import os,subprocess,shutil,difflib
r=Path(__file__).parent;old=r/'pool83-control-source';s=r/'pool100-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/env_pool.h';before=p.read_text()
after=before.replace('#include <sched.h>','#include <sched.h>\n#include <time.h>\n#include <stdio.h>')
after=after.replace('    int* next;','    int* next;\n    unsigned long long calls, measured, claim_ns, wait_ns, drain_ns, yields;')
needle='static void ep_run(EnvPool* p, int buffer, int start, int count) {'
helper="""static unsigned long long ep_now_ns(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return (unsigned long long)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

"""
after=after.replace(needle,helper+needle)
needle='    ep_claim(p, r, buffer % p->workers);\n    while (__atomic_load_n(&r->done, __ATOMIC_ACQUIRE) < count) sched_yield();'
assert after.count(needle)==1
after=after.replace(needle,"""    int capture = r->calls++ >= 8192;
    unsigned long long t0 = capture ? ep_now_ns() : 0, spins = 0;
    ep_claim(p, r, buffer % p->workers);
    unsigned long long t1 = capture ? ep_now_ns() : 0;
    while (__atomic_load_n(&r->done, __ATOMIC_ACQUIRE) < count) { spins++; sched_yield(); }
    unsigned long long t2 = capture ? ep_now_ns() : 0;""")
needle='    while (r->readers) pthread_cond_wait(&r->quiet, &r->mu);\n    pthread_mutex_unlock(&r->mu);'
assert after.count(needle)==1
after=after.replace(needle,needle+"""
    if (capture) {
        unsigned long long t3 = ep_now_ns();
        r->measured++; r->claim_ns += t1-t0; r->wait_ns += t2-t1;
        r->drain_ns += t3-t2; r->yields += spins;
    }""")
needle='        assert(!p->region[b].active && !p->region[b].readers);'
assert after.count(needle)==1
after=after.replace(needle,needle+"""
        EPRegion* r = &p->region[b];
        fprintf(stderr, "POOL_WAIT buffer=%d calls=%llu measured=%llu claim_ns=%llu wait_ns=%llu drain_ns=%llu yields=%llu\\n", b, r->calls, r->measured, r->claim_ns, r->wait_ns, r->drain_ns, r->yields);""")
p.write_text(after)
(r/'pool100.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/env_pool.h',tofile='b/src/env_pool.h')))
with (r/'pool100-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_pool'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_POOL -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('POOL87_BUILD_COMPLETE',flush=True)
