from pathlib import Path
import shutil,difflib
r=Path(__file__).resolve().parent
old=r/'shared-pool/depth/source';dest=r/'warmtrain/source'
def ignore(path,names):return [n for n in names if Path(path)==old and (n.startswith('puffer_') or n=='build')]
shutil.copytree(old,dest,symlinks=True,ignore=ignore)
p=dest/'src/pufferl.cu';before=p.read_text();needle='    PuffeRL* pufferl = create_pufferl(ini, ctx);\n    Selfplay selfplay = {0};';assert before.count(needle)==1
new='''    PuffeRL* pufferl = create_pufferl(ini, ctx);
#ifdef PUF_PERF_LOAD
    const char* perf_weights = getenv("PUF_PERF_START_WEIGHTS");
    const char* perf_proof = getenv("PUF_PERF_LOADED_PROOF");
    assert(perf_weights && perf_proof && !use_selfplay && ctx->world_size == 1);
    pufferl_load_policy(pufferl, 0, perf_weights);
    puf_save_weights(pufferl, perf_proof);
    fprintf(stderr, "PERF_LOADED_WEIGHTS %s saved %s before first rollout\\n", perf_weights, perf_proof);
#endif
    Selfplay selfplay = {0};'''
p.write_text(before.replace(needle,new));(r/'warmtrain/load-hook.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),p.read_text().splitlines(True),fromfile='a/src/pufferl.cu',tofile='b/src/pufferl.cu')))
print('Prepared isolated common checkpoint loading hook; same for static/WS/pool')
