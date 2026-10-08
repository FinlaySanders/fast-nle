from pathlib import Path
import subprocess,os,json
r=Path(__file__).parent
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH')}
for mode in ['interleaved','shuffled']:
 cmd=[str(r/'gates/replay_multi'),'--'+mode,str(r/'engine-stock-view/build/libnethack.so'),str(r/'dat'),*[str(p) for p in sorted((r/'engine-baseline/tests/goldens').glob('*.golden'))]]
 with (r/('stock-view-'+mode+'.log')).open('w') as out:p=subprocess.run(cmd,env=e,stdout=out,stderr=subprocess.STDOUT)
 print(mode,p.returncode,flush=True)
