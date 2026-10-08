from pathlib import Path
import os,subprocess,shutil,difflib
r=Path(__file__).parent;old=r/'buffers42-source'
for label in ['pool83-control','pool83-central']:
 s=r/(label+'-source');s.mkdir()
 for name in ['src','config']:shutil.copytree(old/name,s/name)
 shutil.copy2(old/'build.sh',s/'build.sh')
 for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
 if label=='pool83-central':
  p=s/'src/env_pool.h';text=p.read_text();a=text.index('    for (int k = 0;',text.index('static void ep_claim'));b=text.index('\n}\n\nstatic void* ep_worker',a)
  changed=text[:a]+'''    (void)id;
    for (;;) {
        int offset = __atomic_fetch_add(&r->next[0], 1, __ATOMIC_RELAXED);
        if (offset >= r->count) break;
        p->step(p->context, r->start + offset);
        __atomic_fetch_add(&r->done, 1, __ATOMIC_RELEASE);
    }'''+text[b:];p.write_text(changed)
  (r/'pool83.patch').write_text(''.join(difflib.unified_diff(text.splitlines(True),changed.splitlines(True),fromfile='a/src/env_pool.h',tofile='b/src/env_pool.h')))
 print('BUILD',label,flush=True)
 with (r/(label+'-build.log')).open('w') as f:subprocess.run(['./build.sh','nethack','puffer_pool'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_POOL -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('POOL83_BUILD_COMPLETE',flush=True)
