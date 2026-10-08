from pathlib import Path
import shutil,subprocess,os,difflib
r=Path(__file__).parent;s=r/'events73-source';old=r/'buffers42-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/pufferl.cu';original=p.read_text();start=original.index('static void* vec_thread_main(');end=original.index('\nstatic ',start+1);part=original[start:end];assert part.count('cudaEventRecord(')==5 and part.count('cudaEventElapsedTime(')==4
part=part.replace('    float ms = 0.0f;','    float ms = 0.0f;\n    const bool bench_timing = getenv("PUF_BENCH_NO_TIMING_EVENTS") == NULL;')
lines=[]
for line in part.splitlines(True):
 if 'cudaEventRecord(' in line or 'cudaEventElapsedTime(' in line:
  line=line[:len(line)-len(line.lstrip())]+'if (bench_timing) '+line.lstrip()
 lines.append(line)
t=original[:start]+''.join(lines)+original[end:];p.write_text(t);(r/'events73.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),t.splitlines(True),fromfile='a/src/pufferl.cu',tofile='b/src/pufferl.cu')))
with (r/'events73-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_events'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_WS -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('EVENTS73 BUILT; benchmark-only toggle suppresses timing metrics, not production-ready',flush=True)
