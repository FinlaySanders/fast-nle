from pathlib import Path
import shutil,difflib
r=Path(__file__).parent;s=r/'engine-source';b=r/'alloc62-before';b.mkdir()
changes={
 'include/monst.h':('#define newmonst() (struct monst *) alloc(sizeof (struct monst))','#define newmonst() (struct monst *) nh_mon_alloc(sizeof (struct monst))'),
 'include/extern.h':('E char *FDECL(fmt_ptr, (const genericptr));','E long *FDECL(nh_mon_alloc, (unsigned int));\nE char *FDECL(fmt_ptr, (const genericptr));'),
 'src/alloc.c':('#ifdef HAS_PTR_FMT','long *\nnh_mon_alloc(unsigned int lth)\n{\n    void *ptr = aligned_alloc(64, ((size_t) lth + 63) & ~(size_t) 63);\n    if (!ptr)\n        panic("Monster allocation failure; cannot get %u bytes", lth);\n    return (long *) ptr;\n}\n\n#ifdef HAS_PTR_FMT')}
patch=[]
for name,(old,new) in changes.items():
 p=s/name;t=p.read_text();assert t.count(old)==1,name
 q=b/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 u=t.replace(old,new)
 if name=='src/alloc.c':u=u.replace('#include \"config.h\"','#include \"config.h\"\n#include <stdlib.h>')
 p.write_text(u);patch.extend(difflib.unified_diff(t.splitlines(True),u.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
(r/'alloc62.patch').write_text(''.join(patch))
print('Applied allocation alignment only: structure/save layout unchanged, free-compatible C11 allocation')
