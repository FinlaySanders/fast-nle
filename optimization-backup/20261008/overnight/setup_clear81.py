from pathlib import Path
import sys,shutil,os,subprocess
r=Path(__file__).parent;label=sys.argv[1];s=r/(label+'-rollout-source');old=r/'buffers42-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
(s/'ocean').mkdir()
for p in (old/'ocean').iterdir():
 if p.name=='nethack':shutil.copytree(p,s/'ocean/nethack')
 else:(s/'ocean'/p.name).symlink_to(p.resolve(),target_is_directory=p.is_dir())
p=s/'ocean/nethack/nethack.h';t=p.read_text();needle='if (env->obj_mem[cell]) env->obj_mem[cell] = 0;';assert t.count(needle)==1;t=t.replace(needle,'env->obj_mem[cell] = 0;');p.write_text(t)
with (r/(label+'-rollout-build.log')).open('w') as f:subprocess.run(['./build.sh','nethack','puffer_rollout'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_WS -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('ROLLOUT BUILD COMPLETE',flush=True)
