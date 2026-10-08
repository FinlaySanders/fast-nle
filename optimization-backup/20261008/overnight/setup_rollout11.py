from pathlib import Path
import shutil,os,subprocess
r=Path(__file__).parent;s=r/'rollout11-source';old=Path('/puffertank/experiments/nethack-workspace-safe-20260917/source');s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/pufferl.cu';text=p.read_text();start=text.index('static EvalResult eval_loop(');end=text.index('\n}',start)+2;part=text[start:end]
part=part.replace('    double last_dash = 0;', '''    int bench_blocks = getenv("PUF_ROLLOUT_BLOCKS") ? atoi(getenv("PUF_ROLLOUT_BLOCKS")) : 0;
    int bench_block = 0;
    if (bench_blocks) {assert(getenv("PUF_PERF_LOADED_PROOF"));puf_save_weights(p,getenv("PUF_PERF_LOADED_PROOF"));}
    double last_dash = 0;''')
part=part.replace('        rollouts(p);', '''        double bench_start = wall_clock();
        rollouts(p);
        if (bench_blocks) {
            double seconds = wall_clock()-bench_start;
            long turns=0,max_turn=0;int mature=0;
            for(int i=0;i<p->vec->size;i++){long t=p->vec->envs[i].blstats[NLE_BL_TIME];turns+=t;if(t>max_turn)max_turn=t;mature+=t>=10000;}
            fprintf(stderr,"ROLLOUT_BLOCK block=%d steps=%ld seconds=%.9f mean_turn=%.2f max_turn=%ld over10k=%d envs=%d\\n",bench_block,p->global_step,seconds,(double)turns/p->vec->size,max_turn,mature,p->vec->size);
            if(++bench_block==bench_blocks)return result;
        }''');p.write_text(text[:start]+part+text[end:])
with (r/'rollout11-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_rollout'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_WS -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('ROLLOUT BUILD COMPLETE',flush=True)
