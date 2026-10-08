from pathlib import Path
import os,select,subprocess,json
r=Path(__file__).parent;s=r/'score/source'
pid=int((r/'depth-record.pid').read_text())
try:
 fd=os.pidfd_open(pid);select.select([fd],[],[]);os.close(fd)
except ProcessLookupError:pass
assert 'CUDA_EVAL' in (r/'depth-record.log').read_text(errors='replace')
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH')}
e.update(NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'lib'),NH_DISC_SWAP='0',OMP_NUM_THREADS='24')
base=[str(s/'puffer'),'eval','--headless','--base.load_model_path=/puffertank/pufferlib/resources/nethack/fixwt4b_s705.bin','--policy.hidden_size=1024','--policy.num_layers=4','--env.multi_role=1','--env.mask_search20=0','--env.mask_run=0','--base.seed=7','--base.async=0','--vec.num_buffers=1']
for label,agents,eps,threads in [('score-smoke',8,16,4),('score-record',512,14000,24)]:
 d=r/label;d.mkdir();cmd=base+[f'--base.eval_agents={agents}',f'--base.eval_episodes={eps}',f'--vec.num_threads={threads}']
 (r/(label+'-command.json')).write_text(json.dumps(cmd,indent=2))
 with (r/(label+'.log')).open('w') as f:
  p=subprocess.Popen(cmd,cwd=s,env=dict(e,NH_PERF_RECORD=str(d)),stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
  (r/(label+'.pid')).write_text(str(p.pid));print('START',label,p.pid,flush=True);rc=p.wait()
 assert rc==0,(label,rc)
 print('DONE',label,flush=True)
(r/'RECORDING_DONE').write_text('depth and score corpora ready\n')
