from pathlib import Path
import difflib
r=Path(__file__).parent;p=r/'engine-source/src/mthrowu.c';s=p.read_text();(r/'line75-before-mthrowu.c').write_text(s)
a='''    ignore_boulders = (throws_rocks(mtmp->data)
                       || m_carrying(mtmp, WAN_STRIKING));'''
b='''    /* Preserve the direction outputs even for a rejected firing line. */
    tbx = mtmp->mux - mtmp->mx;
    tby = mtmp->muy - mtmp->my;
    if ((!tbx && !tby)
        || (tbx && tby && abs(tbx) != abs(tby))
        || abs(tbx) >= BOLT_LIM || abs(tby) >= BOLT_LIM)
        return FALSE;

    ignore_boulders = (throws_rocks(mtmp->data)
                       || m_carrying(mtmp, WAN_STRIKING));'''
assert s.count(a)==1;s=s.replace(a,b);p.write_text(s)
(r/'line75.patch').write_text(''.join(difflib.unified_diff((r/'line75-before-mthrowu.c').read_text().splitlines(True),s.splitlines(True),fromfile='a/src/mthrowu.c',tofile='b/src/mthrowu.c')))
