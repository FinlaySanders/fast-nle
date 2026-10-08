from pathlib import Path
import subprocess,shutil,json,hashlib,difflib
r=Path(__file__).resolve().parent;root=r/'patch-review';rows=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for w in ['depth','score']:
 base=r/('source' if w=='depth' else 'score/source')/'src/pufferl.cu';dest=root/('scheduler-'+w);(dest/'src').mkdir(parents=True)
 shutil.copy2(base,dest/'src/pufferl.cu');before=sha(base)
 for kind,patchdir,reference in [('ws',r/'scheduling'/w,r/'scheduling'/w/'source/src'),('pool',r/'shared-pool'/w,r/'shared-pool'/w/'source/src')]:
  patch=patchdir/('native-'+kind+'.patch');export=root/(w+'-'+kind+'.patch');shutil.copy2(patch,export)
  if kind=='pool':
   helper=r/'shared-pool/env_pool.h';t=helper.read_text();extra='diff --git a/src/env_pool.h b/src/env_pool.h\nnew file mode 100644\n'+''.join(difflib.unified_diff([],t.splitlines(True),fromfile='/dev/null',tofile='b/src/env_pool.h'))
   export.write_text(export.read_text()+extra)
  subprocess.run(['git','apply','--check',str(export)],cwd=dest,check=True);subprocess.run(['git','apply',str(export)],cwd=dest,check=True)
  assert (dest/'src/pufferl.cu').read_bytes()==(reference/'pufferl.cu').read_bytes(),(w,kind)
  if kind=='pool':assert (dest/'src/env_pool.h').read_bytes()==(reference/'env_pool.h').read_bytes()
  rows.append(dict(workload=w,scheduler=kind,base_trainer_sha256=before,patch=str(export),patch_sha256=sha(export),result_trainer_sha256=sha(dest/'src/pufferl.cu'),build_define='PUF_ENV_'+kind.upper(),scope='pool patch applies after WS; header included. Syntax/source proof, not performance acceptance'))
  before=sha(dest/'src/pufferl.cu')
(root/'scheduler-manifest.json').write_text(json.dumps(rows,indent=2));print('PASS: both policy trainer patches reproduce frozen WS and pool sources')
