"""Record raw observations during fresh vec inference, then reproduce without inference."""
from pathlib import Path
import os,select,subprocess,json,shutil,hashlib
r=Path(__file__).resolve().parent
pid=int((r/'candidate04-runner.pid').read_text())
try:fd=os.pidfd_open(pid)
except ProcessLookupError:fd=None
if fd is not None:select.select([fd],[],[]);os.close(fd)
assert len(json.loads((r/'v4-snapshot-checks.json').read_text()))==2,'v4 smoke not complete'
results=[]
for w in ['depth','score']:
 n=r/'harness-v4'/w;s=n/'source';original=r/('source' if w=='depth' else 'score/source')
 shutil.copy2(original/'build.sh',s/'build.sh');shutil.copytree(original/'config',s/'config')
 for name in ['resources','raylib-5.5_linux_amd64']:(s/name).symlink_to((original/name).resolve(),target_is_directory=True)
 v=s/'vendor/fast-nle';v.mkdir(parents=True)
 for name in ['src','include']:(v/name).symlink_to(r/'engine-baseline'/name,target_is_directory=True)
 (v/'build').mkdir();(v/'build/libnethack.so').symlink_to(r/'lib/libnethack.so')
 (v/'build/_deps').symlink_to(r/'engine-baseline/build/_deps',target_is_directory=True)
 with (n/'trainer-build.log').open('w') as f:p=subprocess.run(['bash','build.sh','nethack'],cwd=s,stdout=f,stderr=subprocess.STDOUT)
 assert p.returncode==0,'trainer build '+w
 cmd=json.loads((r/('smoke-command.json' if w=='depth' else 'score-smoke-command.json')).read_text());cmd[0]=str(s/'puffer')
 env={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')}
 env.update(NH_DISC_SWAP='1' if w=='depth' else '0',NH_ZT_MASK='0',NETHACKDIR=str(r/'dat'),LD_LIBRARY_PATH=str(r/'lib'),OMP_NUM_THREADS='4')
 traces=n/'fresh-traces';raw=n/'fresh-observations';traces.mkdir();raw.mkdir()
 with (n/'fresh-record.log').open('w') as f:p=subprocess.run(cmd,cwd=s,env=dict(env,NH_PERF_RECORD=str(traces),NH_PERF_SNAPSHOTS=str(raw)),stdout=f,stderr=subprocess.STDOUT)
 assert p.returncode==0,'record '+w
 row=dict(workload=w,record_command=cmd,comparisons=[])
 for label,lib in [('baseline',r/'lib'),('candidate04',r/'variants/candidate04')]:
  out=n/('fresh-replay-'+label);out.mkdir()
  replay=[str(n/'replay_vec'),'verify','4','0','1000000',*map(str,sorted(traces.glob('*.trace')))]
  with (n/('fresh-replay-'+label+'.log')).open('w') as f:p=subprocess.run(replay,env=dict(env,LD_LIBRARY_PATH=str(lib),NH_PERF_SNAPSHOTS=str(out)),stdout=f,stderr=subprocess.STDOUT)
  assert p.returncode==0,'replay '+w+' '+label
  hashes=[]
  for orig in sorted(raw.glob('*.obs')):
   def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
     while b:=f.read(1048576):h.update(b)
    return h.hexdigest()
   h=sha(orig);assert h==sha(out/orig.name),(w,label,orig.name,'raw observation mismatch')
   hashes.append(dict(file=orig.name,bytes=orig.stat().st_size,sha256=h))
  assert len(hashes)==8
  row['comparisons'].append(dict(label=label,command=replay,observations=hashes))
 results.append(row);(r/'fresh-snapshot-results.json').write_text(json.dumps(results,indent=2));print(w,'PASS fresh inference vs baseline/candidate raw replay',flush=True)
print('DONE',flush=True)
