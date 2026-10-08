from pathlib import Path
import os,subprocess,shutil,difflib
r=Path(__file__).parent;old=r/'pool83-control-source';s=r/'wait98-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/pufferl.cu';before=p.read_text()
needle='    cudaSetDevice(hypers.gpu_id);'
assert before.count(needle)==1
replacement=needle+"""
    if (const char* wait_mode = getenv("PUF_CUDA_WAIT")) {
        unsigned int flags = 0, actual = 0;
        assert(cudaGetDeviceFlags(&flags) == cudaSuccess);
        unsigned int policy = !strcmp(wait_mode, "blocking") ? cudaDeviceScheduleBlockingSync
            : !strcmp(wait_mode, "yield") ? cudaDeviceScheduleYield : cudaDeviceScheduleSpin;
        assert(cudaSetDeviceFlags((flags & ~cudaDeviceScheduleMask) | policy) == cudaSuccess);
        assert(cudaGetDeviceFlags(&actual) == cudaSuccess);
        assert((actual & cudaDeviceScheduleMask) == policy);
        fprintf(stderr, "CUDA_WAIT_POLICY mode=%s flags=%u\\n", wait_mode, actual);
    }
"""
after=before.replace(needle,replacement);p.write_text(after)
(r/'wait98.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/pufferl.cu',tofile='b/src/pufferl.cu')))
with (r/'wait98-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_pool'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_POOL -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('POOL87_BUILD_COMPLETE',flush=True)
