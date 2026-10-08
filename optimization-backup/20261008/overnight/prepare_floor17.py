from pathlib import Path
import shutil,subprocess,difflib
r=Path(__file__).parent;s=r/'engine-source';b=r/'floor17-before';b.mkdir()
for rel in ['src/monmove.c','tools/globals.def','include/nh_ctx_gen.h','src/nh_ctx_gen.c']:
 p=b/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s/rel,p)
p=s/'tools/globals.def';t=p.read_text();assert 'short | nh_fobj_x' in t;t=t.replace('short | nh_fobj_x','schar | nh_fobj_x').replace('short | nh_fobj_y','schar | nh_fobj_y');p.write_text(t)
p=s/'src/monmove.c';t=p.read_text();start=t.index('#ifdef __SSE2__',t.index('nh_fobj_next(struct'));end=t.index('#endif',start);part=t[start:end]
for a,z in [('eight coordinates','sixteen coordinates'),('lx >= -32768 && hx <= 32767 && ly >= -32768 && hy <= 32767','lx >= -128 && hx <= 127 && ly >= -128 && hy <= 127'),('bit / 2','bit'),('3U << bit','1U << bit'),('_mm_set1_epi16((short)','_mm_set1_epi8((char)'),('cursor->index + 8','cursor->index + 16'),('_mm_cmpgt_epi16','_mm_cmpgt_epi8'),('cursor->index += 8','cursor->index += 16')]:
 assert a in part,a;part=part.replace(a,z)
t=t[:start]+part+t[end:];p.write_text(t)
subprocess.run(['python',str(s/'tools/gen_ctx.py')],check=True,stdout=subprocess.DEVNULL)
out=[]
for p in sorted(b.rglob('*')):
 if p.is_file():
  rel=p.relative_to(b);out.extend(difflib.unified_diff(p.read_text().splitlines(True),(s/rel).read_text().splitlines(True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
(r/'floor17.patch').write_text(''.join(out))
