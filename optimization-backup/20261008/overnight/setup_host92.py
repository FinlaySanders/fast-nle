from pathlib import Path
import os,subprocess,shutil,difflib
r=Path(__file__).parent;old=r/'pool83-control-source';s=r/'host92-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
with (r/'host92-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_pool'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_POOL -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER -Xcompiler=-O3'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('POOL87_BUILD_COMPLETE',flush=True)
