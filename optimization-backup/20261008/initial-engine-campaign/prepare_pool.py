from pathlib import Path
import shutil,difflib
r=Path(__file__).resolve().parent
for w in ['depth','score']:
 old=r/'scheduling'/w/'source'; dest=r/'shared-pool'/w/'source'
 def ignore(path,names):
  return [n for n in names if (Path(path)==old and (n.startswith('puffer_') or n=='build'))]
 shutil.copytree(old,dest,symlinks=True,ignore=ignore)
 p=dest/'src/pufferl.cu';assert not p.is_symlink();before=p.read_text();s=before
 s=s.replace('#include <pthread.h>','#include <pthread.h>\n#ifdef PUF_ENV_POOL\n#include "env_pool.h"\n#endif',1)
 needle='    int* worker_state;';assert s.count(needle)==1
 s=s.replace(needle,needle+'\n#ifdef PUF_ENV_POOL\n    EnvPool* env_pool;\n#endif')
 needle='static void* vec_thread_main(void* arg) {';assert s.count(needle)==1
 s=s.replace(needle,'#ifdef PUF_ENV_POOL\nstatic void pool_env_step(void* context, int i) { puf_step(&((Env*)context)[i]); }\n#endif\n\n'+needle)
 needle='#ifdef PUF_ENV_WS';assert s.count(needle)==1
 s=s.replace(needle,'#ifdef PUF_ENV_POOL\n            ep_run(vec->env_pool, buf, env_start, env_count);\n#elif defined(PUF_ENV_WS)')
 needle='    env_restart(p);\n    for (int i = 0; i < vec->buffers; i++) {';assert s.count(needle)==1
 s=s.replace(needle,'''    env_restart(p);
#ifdef PUF_ENV_POOL
    int workers = vec->num_workers * vec->buffers - 12;
    const char* pool_workers = getenv("PUF_POOL_WORKERS");
    if (pool_workers) workers = atoi(pool_workers);
    if (workers < 1) workers = 1;
    vec->env_pool = ep_create(workers, vec->buffers, pool_env_step, vec->envs);
#endif
    for (int i = 0; i < vec->buffers; i++) {''')
 needle='        pthread_join(vec->threads[i], NULL);\n    }';assert s.count(needle)==1
 s=s.replace(needle,needle+'\n#ifdef PUF_ENV_POOL\n    ep_destroy(vec->env_pool);\n    vec->env_pool = NULL;\n#endif')
 p.write_text(s);shutil.copy2(r/'shared-pool/env_pool.h',dest/'src/env_pool.h')
 (r/'shared-pool'/w/'native-pool.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile='a/src/pufferl.cu',tofile='b/src/pufferl.cu')))
print('Prepared separate per-VecEnv shared pool, unchanged WS comparison sources')
