from pathlib import Path
import shutil,subprocess,os
r=Path(__file__).parent;s=r/'buffers42-source';old=r/'rollout11-source';s.mkdir()
for name in ['src','config']:shutil.copytree(old/name,s/name)
shutil.copy2(old/'build.sh',s/'build.sh')
for name in ['ocean','resources','vendor','raylib-5.5_linux_amd64']:(s/name).symlink_to((old/name).resolve(),target_is_directory=True)
p=s/'src/pufferl.cu';t=p.read_text();a='__global__ void rng_init(curandStatePhilox4_32_10_t* states, uint64_t seed, int n)';assert t.count(a)==1;t=t.replace(a,a[:-1]+', int offset, int reference_agents)')
a='        curand_init(seed, idx, 0, &states[idx]);';b='''        if (reference_agents > 0) {
            int global_agent = offset + idx;
            curand_init(seed + global_agent / reference_agents,
                        global_agent % reference_agents, 0, &states[idx]);
        } else curand_init(seed, idx, 0, &states[idx]);''';assert t.count(a)==1;t=t.replace(a,b)
a='    // Per-buffer persistent RNG states';t=t.replace(a,'''    int benchmark_reference_agents = getenv("PUF_BENCH_REFERENCE_AGENTS") ? atoi(getenv("PUF_BENCH_REFERENCE_AGENTS")) : 0;
'''+a)
a='''            pufferl->rng_states[i], pufferl->seed + i, agents_per_buf);''';b='''            pufferl->rng_states[i], pufferl->seed + (benchmark_reference_agents ? 0 : i), agents_per_buf,
            i * agents_per_buf, benchmark_reference_agents);''';assert t.count(a)==1;t=t.replace(a,b)
a='    // Post-create initialization';b='''    if (const char* proof = getenv("PUF_BENCH_RNG_PROOF")) {
        size_t bytes = agents_per_buf * sizeof(curandStatePhilox4_32_10_t);
        void* host = malloc(bytes); assert(host);
        FILE* file = fopen(proof, "wb"); assert(file);
        for (int i = 0; i < num_buffers; i++) {
            cudaError_t rc = cudaMemcpy(host, pufferl->rng_states[i], bytes, cudaMemcpyDeviceToHost);
            assert(rc == cudaSuccess); assert(fwrite(host, 1, bytes, file) == bytes);
        }
        assert(fclose(file) == 0); free(host);
    }

'''+a;assert t.count(a)==1;t=t.replace(a,b)
a='''            fprintf(stderr,"ROLLOUT_BLOCK block=%d''';b='''            uint64_t digest = 1469598103934665603ULL;
            for(int i=0;i<p->vec->size;i++) {
                const unsigned char* obs=(const unsigned char*)p->vec->envs[i].agents[0].observations;
                for(int j=0;j<OBS_SIZE;j++){digest^=obs[j];digest*=1099511628211ULL;}
            }
            fprintf(stderr,"ROLLOUT_OBS block=%d hash=%016llx\\n",bench_block,(unsigned long long)digest);
'''+a;assert t.count(a)==1;t=t.replace(a,b);p.write_text(t)
with (r/'buffers42-build.log').open('w') as f:subprocess.run(['./build.sh','nethack','puffer_rollout'],cwd=s,env=dict(os.environ,NVCC_EXTRA='-DPUF_ENV_WS -DPUF_PERF_LOAD -DPUF_HEAD_SAMPLER'),stdout=f,stderr=subprocess.STDOUT,check=True)
print('BUILD COMPLETE',flush=True)
