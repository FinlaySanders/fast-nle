from pathlib import Path
import os,subprocess,json
r=Path(__file__).resolve().parent;out=r/'score-balanced-v2';out.mkdir(exist_ok=False)
rows=json.loads((r/'score-timing-selected.json').read_text());assert len(rows)==32 and all(Path(x['path']).name!='env00457.trace' for x in rows)
env=os.environ.copy();env.update(NH_DISC_SWAP='0',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'engine-baseline/build'),NH_PERF_AUGMENT=str(out))
cmd=[str(r/'harness-v3/score/replay_vec'),'verify','24','0','1000000',*[x['path'] for x in rows]]
(r/'score-balanced-augment-command.json').write_text(json.dumps(cmd,indent=2))
p=subprocess.run(cmd,env=env);print('RETURN',p.returncode,flush=True)
if p.returncode:raise SystemExit(p.returncode)
(out/'VERIFIED_ORIGINAL').write_text('Only the original preselected32 timing streams verified; full512 score corpus has the preserved baseline failure documented in BASELINE_MESSAGE_BUG.md.\n')
