from pathlib import Path
import shutil,subprocess,os
r=Path(__file__).parent;old=r/'rollout11-source';s=r/'pause12-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/pufferl.cu';t=p.read_text();needle='// CPU worker handshake.';repl='''static inline void cpu_spin_pause(void) {
#if defined(__x86_64__) || defined(__i386__)
    __asm__ __volatile__("pause");
#endif
}

// CPU worker handshake.''';assert needle in t;t=t.replace(needle,repl,1)
needle='while (__atomic_load_n(state, __ATOMIC_SEQ_CST) != BUF_WAITING) {}';assert t.count(needle)==2;t=t.replace(needle,'while (__atomic_load_n(state, __ATOMIC_SEQ_CST) != BUF_WAITING) {cpu_spin_pause();}')
needle='while (__atomic_load_n(state, __ATOMIC_SEQ_CST) != BUF_RUNNING) {';assert t.count(needle)==1;t=t.replace(needle,needle+'\n            cpu_spin_pause();');p.write_text(t)
(r/'pause12.patch').write_bytes(subprocess.run(['diff','-u','--label','a/src/pufferl.cu','--label','b/src/pufferl.cu',str(old/'src/pufferl.cu'),str(p)],capture_output=True).stdout)
with (r/'pause12-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_pause'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_WS -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('PAUSE_BUILD_COMPLETE',flush=True)
