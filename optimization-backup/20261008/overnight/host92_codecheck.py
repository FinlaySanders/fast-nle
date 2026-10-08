from pathlib import Path
import hashlib,subprocess,json
r=Path(__file__).parent;d=r/'host92-codecheck';d.mkdir();hashes={}
for label,src in [('baseline',r/'pool83-control-source'),('candidate',r/'host92-source')]:
 out=d/(label+'.fatbin')
 subprocess.run(['objcopy','--dump-section','.nv_fatbin='+str(out),str(src/'puffer_pool')],check=True)
 hashes[label]=hashlib.sha256(out.read_bytes()).hexdigest()
files={str(p.relative_to(r/'pool83-control-source')):hashlib.sha256(p.read_bytes()).hexdigest() for area in ['src','config'] for p in (r/'pool83-control-source'/area).rglob('*') if p.is_file()}
changed=[p for p,h in files.items() if hashlib.sha256((r/'host92-source'/p).read_bytes()).hexdigest()!=h]
result=dict(device_fatbin_sha256=hashes,source_changes=changed)
(d/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
assert not changed and hashes['baseline']==hashes['candidate'],'GPU image or source changed; review before timing'
