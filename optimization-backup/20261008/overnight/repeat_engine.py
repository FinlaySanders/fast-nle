from pathlib import Path
import os,subprocess,json,time,re,sys
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');candidate=sys.argv[1];baseline=sys.argv[2] if len(sys.argv)>2 else 'mask05';d=r/(candidate+'-repeat');d.mkdir();rows=[];summary={}
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',OMP_PROC_BIND='true',OMP_PLACES='cores')
for work in ['score','depth']:
 corpus=old/('depth-record-v2' if work=='depth' else 'score-balanced-v2');paths=[str(corpus/Path(x['path']).name) for x in json.loads((old/(work+'-timing-selected.json')).read_text())];vals={}
 for phase,lib in [('before',baseline),('candidate',candidate),('after',baseline)]:
  cmd=['taskset','-c','0,2,4,6,8,10,12,14',str(old/'harness-v3'/work/'replay_vec'),'time','8','20000','20000',*paths];print('START',work,phase,flush=True)
  with (d/(work+'-'+phase+'.log')).open('w') as f:p=subprocess.run(cmd,env=dict(e,LD_LIBRARY_PATH=str(r/lib/'variant'),NH_DISC_SWAP='1' if work=='depth' else '0'),stdout=f,stderr=subprocess.STDOUT)
  text=(d/(work+'-'+phase+'.log')).read_text();assert p.returncode==0,text[-1000:];vals[phase]=float(re.search(r'measured_seconds=([\d.]+)',text)[1]);rows.append(dict(work=work,phase=phase,seconds=vals[phase],command=cmd));(d/'results.json').write_text(json.dumps(rows,indent=2));print('DONE',work,phase,vals[phase],flush=True)
 summary[work]=dict(**vals,gain_percent=100*((vals['before']+vals['after'])/2/vals['candidate']-1),drift_percent=100*(vals['after']/vals['before']-1));(d/'summary.json').write_text(json.dumps(summary,indent=2))
print('REPEAT_COMPLETE',json.dumps(summary),flush=True)
