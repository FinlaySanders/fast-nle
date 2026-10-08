from pathlib import Path
import difflib
r=Path(__file__).parent;p=r/'engine-source/src/monmove.c';s=p.read_text();(r/'appar77-before-monmove.c').write_text(s)
a='    set_apparxy(mtmp);';b='    if (mtmp->mux != u.ux || mtmp->muy != u.uy)\n        set_apparxy(mtmp);';assert s.count(a)==2;s=s.replace(a,b);p.write_text(s)
(r/'appar77.patch').write_text(''.join(difflib.unified_diff((r/'appar77-before-monmove.c').read_text().splitlines(True),s.splitlines(True),fromfile='a/src/monmove.c',tofile='b/src/monmove.c')))
