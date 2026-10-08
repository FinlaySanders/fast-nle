from pathlib import Path
import os,subprocess,shutil,difflib
r=Path(__file__).parent;old=r/'pool83-control-source';s=r/'pool109-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/env_pool.h';before=p.read_text();after=before
replacements=[('#include <sched.h>','#include <sched.h>\n#include <time.h>\n#include <stdint.h>\n#include <string.h>\ntypedef struct { uint64_t cost; int offset; } EPCost;\nstatic int ep_cost_order(const void* av, const void* bv) {\n    const EPCost* a = (const EPCost*)av; const EPCost* b = (const EPCost*)bv;\n    if (a->cost != b->cost) return a->cost > b->cost ? -1 : 1;\n    return a->offset - b->offset;\n}\nstatic uint64_t ep_now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec*1000000000ull+t.tv_nsec; }'),
('    int* next;','    int* next;\n    int capacity, sampled;\n    unsigned int round;\n    uint64_t* costs;\n    EPCost* order;'),
('            p->step(p->context, r->start + offset);','            offset = r->order[offset].offset;\n            uint64_t started = r->sampled ? ep_now() : 0;\n            p->step(p->context, r->start + offset);\n            if (r->sampled) r->costs[offset] = (r->costs[offset] + ep_now() - started) / 2;'),
('    r->start = start; r->count = count;','''    if (count > r->capacity) {
        free(r->costs); free(r->order);
        r->costs = (uint64_t*)calloc(count, sizeof(*r->costs));
        r->order = (EPCost*)calloc(count, sizeof(*r->order));
        assert(r->costs && r->order); r->capacity = count;
    }
    r->sampled = !(r->round++ & 15u);
    if (r->sampled || count != r->count || start != r->start) {
        if (start != r->start && count) memset(r->costs, 0, count * sizeof(*r->costs));
        for (int i = 0; i < count; i++) { r->order[i].cost = r->costs[i]; r->order[i].offset = i; }
        if (count > 1) qsort(r->order, count, sizeof(*r->order), ep_cost_order);
    }
    r->start = start; r->count = count;'''),
('        free(p->region[b].next);','        free(p->region[b].next);\n        free(p->region[b].costs); free(p->region[b].order);')]
for a,b in replacements:
 assert after.count(a)==1,a
 after=after.replace(a,b)
p.write_text(after);(r/'pool109.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/env_pool.h',tofile='b/src/env_pool.h')))
with (r/'pool109-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_pool'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_POOL -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('POOL109_BUILD_COMPLETE',flush=True)
