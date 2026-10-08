from pathlib import Path
import subprocess,tarfile,io,difflib,json,hashlib,re
r=Path(__file__).resolve().parent;out=r/'patch-review';out.mkdir(exist_ok=True)
base=subprocess.check_output(['git','-C',str(r/'engine-baseline'),'rev-parse','HEAD'],text=True).strip();assert base.startswith('e7f656856')
archive=subprocess.check_output(['git','-C',str(r/'engine-baseline'),'archive',base]);results=[]
p02=(r/'variants/candidate02/changes.patch').read_text();prefix='puffertank/experiments/nethack-perf-20260917/engine-candidate/'
p02=p02.replace('a/'+prefix,'a/').replace('b/'+prefix,'b/')
p03=p02+(r/'candidate-03-money.patch').read_text()
mk=(r/'variants/candidate05-normal/mkcanon.c').read_text();newfile='diff --git a/util/mkcanon.c b/util/mkcanon.c\nnew file mode 100644\n'+''.join(difflib.unified_diff([],mk.splitlines(True),fromfile='/dev/null',tofile='b/util/mkcanon.c'))
p05=(r/'variants/candidate05-normal/combined.patch').read_text()+newfile
for name,patch in [('candidate03',p03),('candidate05',p05)]:
 path=out/(name+'.patch');path.write_text(patch);dest=out/name;dest.mkdir()
 with tarfile.open(fileobj=io.BytesIO(archive)) as t:t.extractall(dest,filter='data')
 subprocess.run(['git','apply','--check',str(path)],cwd=dest,check=True)
 subprocess.run(['git','apply',str(path)],cwd=dest,check=True)
 touched=re.findall(r'^diff --git a/(\S+) b/',patch,re.M);files={}
 for f in touched:
  p=dest/f
  reference=r/'engine-floor'/f
  if name=='candidate03' and f=='src/monmove.c':reference=r/'engine-stock-view'/f
  assert p.read_bytes()==reference.read_bytes(),(name,f,'source differs')
  files[f]=hashlib.sha256(p.read_bytes()).hexdigest()
 results.append(dict(candidate=name,base_commit=base,patch=str(path),patch_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),applies_cleanly=True,source_matches=True,files=files,scope='Patch application/source proof only; acceptance depends on separate correctness and timing results'))
(out/'manifest.json').write_text(json.dumps(results,indent=2));print(json.dumps([{k:v for k,v in x.items() if k!='files'} for x in results],indent=2))
