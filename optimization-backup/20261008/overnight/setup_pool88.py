from pathlib import Path
import os,subprocess,shutil,difflib
r=Path(__file__).parent;old=r/'pool83-control-source';s=r/'pool88-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/env_pool.h';before=p.read_text()
needle='static void ep_claim(EnvPool* p, EPRegion* r, int id) {\n'
assert before.count(needle)==1
after=before.replace(needle,needle+'    int completed = 0;\n')
needle='            __atomic_fetch_add(&r->done, 1, __ATOMIC_RELEASE);'
assert after.count(needle)==1
after=after.replace(needle,'            completed++;')
needle='\n}\n\nstatic void* ep_worker'
assert after.count(needle)==1
after=after.replace(needle,'\n    if (completed) __atomic_fetch_add(&r->done, completed, __ATOMIC_RELEASE);'+needle)
p.write_text(after)
(r/'pool88.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/env_pool.h',tofile='b/src/env_pool.h')))
with (r/'pool88-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_pool'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_POOL -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('POOL87_BUILD_COMPLETE',flush=True)
