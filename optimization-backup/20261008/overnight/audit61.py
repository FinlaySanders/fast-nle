from pathlib import Path
import hashlib,json,subprocess,shutil,difflib
r=Path(__file__).parent;s=r/'pgo61-source';d=r/'pgo61/patch-audit';d.mkdir();p=r/'candidate-through-gold60.patch'
p.write_text((r/'retained-through-track40.patch').read_text()+(r/'gold60.patch').read_text())
# Apply two sequential patches in reverse order, verifying every original source hash.
base=json.loads((r/'engine-source-baseline-hashes.json').read_text());target=json.loads((r/'pgo61-source-manifest.json').read_text())
for name in base:
 q=d/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s/name,q)
for patch in ['gold60.patch','retained-through-track40.patch']:
 subprocess.run(['patch','-R','-p1','--batch','-i',str(r/patch)],cwd=d,check=True,stdout=subprocess.DEVNULL)
assert all(hashlib.sha256((d/n).read_bytes()).hexdigest()==h for n,h in base.items())
for patch in ['retained-through-track40.patch','gold60.patch']:
 subprocess.run(['patch','-p1','--batch','-i',str(r/patch)],cwd=d,check=True,stdout=subprocess.DEVNULL)
assert all(hashlib.sha256((d/n).read_bytes()).hexdigest()==h for n,h in target.items())
# Flatten the two sequential patches for review/application.
flat=[]
for name in base:
 if base[name]==target[name]:continue
 original=d/name
 # baseline engine-source snapshot? reconstruct single file by reverse-applying full patches in a separate work copy below.
q=r/'pgo61/patch-base';shutil.copytree(d,q)
for patch in ['gold60.patch','retained-through-track40.patch']:
 subprocess.run(['patch','-R','-p1','--batch','-i',str(r/patch)],cwd=q,check=True,stdout=subprocess.DEVNULL)
files=[]
for name in base:
 if base[name]!=target[name]:
  files.append(name);flat.extend(difflib.unified_diff((q/name).read_text().splitlines(True),(s/name).read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
p.write_text(''.join(flat))
subprocess.run(['patch','-p1','--batch','-i',str(p)],cwd=q,check=True,stdout=subprocess.DEVNULL)
assert all(hashlib.sha256((q/n).read_bytes()).hexdigest()==h for n,h in target.items())
def symbols(lib):
 text=subprocess.check_output(['nm','-S','--defined-only',str(lib)],text=True)
 return sorted((a[3],a[1],a[2]) for line in text.splitlines() if len(a:=line.split())==4 and a[2] in 'BbDdGgSsCc')
old=symbols(r/'pgo44/variant/libnethack.so');new=symbols(r/'pgo61/variant/libnethack.so');assert old==new,(set(old)^set(new))
result=dict(files=files,reverse_matches_original_baseline=True,forward_matches_frozen_candidate=True,writable_data_symbols_unchanged=True,patch_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(r/'pgo61/patch-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
