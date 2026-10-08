from pathlib import Path
import subprocess,json,hashlib,shutil
r=Path(__file__).parent;d=r/'pgo38';d.mkdir();m=json.loads((r/'pgo20-source-manifest.json').read_text());assert all(hashlib.sha256((r/'engine-source'/p).read_bytes()).hexdigest()==h for p,h in m.items())
rows=json.loads((r/'pgo20/results.json').read_text());cmd=next(x['command'] for x in rows if x['label']=='use-configure');cmd=[x+' -fprofile-partial-training' if x.startswith(('-DCMAKE_C_FLAGS=','-DCMAKE_CXX_FLAGS=')) else x for x in cmd];commands=[]
for label,command in [('configure',cmd),('build',['cmake','--build',str(r/'pgo20/build'),'--target','nethack','-j8'])]:
 print('START',label,flush=True)
 with (d/(label+'.log')).open('w') as f:p=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
 commands.append(dict(label=label,command=command,rc=p.returncode));(d/'commands.json').write_text(json.dumps(commands,indent=2));assert p.returncode==0
v=d/'variant';v.mkdir();shutil.copy2(r/'pgo20/build/libnethack.so',v/'libnethack.so');(d/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256((v/'libnethack.so').read_bytes()).hexdigest(),source_manifest='pgo20-source-manifest.json',profile_manifest='pgo20/profile-manifest.json',change='-fprofile-partial-training; identical source and original matching profiles; no new profiles collected'),indent=2));print('BUILD COMPLETE',flush=True)
