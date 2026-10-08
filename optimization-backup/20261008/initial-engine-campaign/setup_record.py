from pathlib import Path
r=Path(__file__).parent;s=r/'source/ocean/nethack'
p=s/'nethack.h';t=p.read_text();t=t.replace('    int num_agents;','    int num_agents;\n    FILE* trace_file;\n    int trace_mode; // 0 off, 1 record, 2 verify, 3 timed replay\n    unsigned long trace_events;\n',1)
t=t.replace('#include "macros.h"','#include "perf_trace.h"\n#include "macros.h"',1)
t=t.replace('    env->ctx = nle_start(&env->obs, NULL, &env->settings);','    trace_start(env);\n    env->ctx = nle_start(&env->obs, NULL, &env->settings);\n    trace_engine(env, \'S\');',1)
t=t.replace('    nle_obs_refresh(env->ctx, &env->obs); // full fill:',"    nle_obs_refresh(env->ctx, &env->obs); trace_engine(env, 'F'); // full fill:")
t=t.replace('    if (!env->obs.done) nle_obs_refresh(env->ctx, &env->obs);',"    if (!env->obs.done) { nle_obs_refresh(env->ctx, &env->obs); trace_engine(env, 'F'); }")
t=t.replace('    int verb = (int)env->agents[0].actions[0];',"    trace_action(env);\n    int verb = (int)env->agents[0].actions[0];",1)
t=t.replace('static void nethack_add_log(Nethack* env, int how) {',"static void nethack_add_log(Nethack* env, int how) {\n    trace_end(env, how);",1)
# pack calls at reset and at policy step only
assert t.count('        nethack_pack_obs(env);')==1
t=t.replace('        nethack_pack_obs(env);',"        nethack_pack_obs(env); trace_policy(env);",1)
t=t.replace('    nethack_pack_obs(env);\n}\n\nvoid puf_reset',"    nethack_pack_obs(env); trace_policy(env);\n}\n\nvoid puf_reset",1)
t=t.replace('    env->agents[0].terminals[0] = done ? 1.0f : 0.0f;',"    env->agents[0].terminals[0] = done ? 1.0f : 0.0f; trace_reward(env);",1)
t=t.replace('void puf_close(Nethack* env) {','void puf_close(Nethack* env) {\n    if (env->trace_file) { fclose(env->trace_file); env->trace_file=NULL; }',1)
p.write_text(t)
p=s/'macros.h';t=p.read_text().replace('    env->ctx = nle_step(env->ctx, &env->obs);',"    trace_key(env);\n    env->ctx = nle_step(env->ctx, &env->obs);\n    trace_engine(env, 'K');",1);p.write_text(t)
