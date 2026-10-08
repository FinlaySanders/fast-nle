from pathlib import Path
import subprocess,json,re
r=Path('/puffertank/experiments/nethack-perf-20260917');out=Path('/puffertank/experiments/nethack-overnight-20260917/pgo08-global-audit');out.mkdir(exist_ok=True);base=r/'variants/candidate08-release/libnethack.so';new=Path('/puffertank/experiments/nethack-overnight-20260917/pgo08/variant/libnethack.so')
def inventory(lib):
 s=subprocess.check_output(['objdump','-t',str(lib)],text=True);rows=[]
 for line in s.splitlines():
  p=line.split()
  if len(p)>=6 and p[-3] in ('.data','.bss','*COM*'):rows.append(dict(name=p[-1],size=int(p[-2],16),section=p[-3],address=int(p[0],16)))
 return rows
b=inventory(base);n=inventory(new);allowed={x.split()[0] for x in (r/'engine-glyph-simd/tools/global_whitelist.txt').read_text().splitlines() if x.strip() and not x.startswith('#')};proof=[]
for x in n:
 name=x['name']
 if name in allowed or re.match(r'^completed\.[0-9]+$',name):continue
 canonical=re.sub(r'\.lto_priv\.[0-9]+$','',name)
 matches=[z for z in b if z['name']==canonical and z['size']==x['size'] and z['section']==x['section']]
 if canonical!=name and canonical in allowed and matches:proof.append(dict(symbol=x,canonical=canonical,matching_baseline=matches));continue
 if name=='DW.ref.__gcc_personality_v0':
  relocs=subprocess.check_output(['readelf','-rW',str(new)],text=True);lines=[l for l in relocs.splitlines() if l.split() and l.split()[0].lstrip('0')==format(x['address'],'x')]
  assert x['size']==8 and len(lines)==1 and '__gcc_personality_v0' in lines[0],(x,lines)
  proof.append(dict(symbol=x,kind='GCC-generated EH personality reference',relocation=lines[0]));continue
 raise AssertionError(('unexplained writable symbol',x))
assert len(proof)==6,len(proof) # PGO leaves six renamed/toolchain symbols, all individually checked above.
(out/'proof.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2));print('All six differences individually explained; profile-use introduces no unexplained writable symbols.')
