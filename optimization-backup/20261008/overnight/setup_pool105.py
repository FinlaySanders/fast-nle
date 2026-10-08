from pathlib import Path
import os,subprocess,shutil,difflib
r=Path(__file__).parent;old=r/'pool83-control-source';s=r/'pool105-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/env_pool.h';before=p.read_text();after=before
needle='    int active, readers, start, count, done;\n    int* next;'
replacement='    int active, readers, start, count;\n    int* next;\n    int done __attribute__((aligned(64)));'
assert after.count(needle)==1;after=after.replace(needle,replacement)
needle='    p->region = (EPRegion*)calloc(buffers, sizeof(*p->region));'
replacement='    if (posix_memalign((void**)&p->region, 64, buffers * sizeof(*p->region))) abort();\n    memset(p->region, 0, buffers * sizeof(*p->region));'
assert after.count(needle)==1;after=after.replace(needle,replacement).replace('#include <stdlib.h>','#include <stdlib.h>\n#include <string.h>')
p.write_text(after);(r/'pool105.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/env_pool.h',tofile='b/src/env_pool.h')))
with (r/'pool105-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_pool'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_POOL -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('POOL105_BUILD_COMPLETE',flush=True)
