from pathlib import Path
import difflib
r=Path(__file__).parent;p=r/'engine-source/src/mon.c';old=p.read_text();start=old.index('int\nmovemon()');end=old.index('\n}',start);part=old[start:end];a='        nmtmp = mtmp->nmon;';assert part.count(a)==1
b='''        nmtmp = mtmp->nmon;
#if defined(__GNUC__)
        if (nmtmp) {
            __builtin_prefetch(nmtmp, 0, 3);
            __builtin_prefetch((const char *) nmtmp + 64, 0, 3);
        }
#endif'''
new=old[:start]+part.replace(a,b)+old[end:];backup=r/'prefetch46-before-mon.c';assert not backup.exists();backup.write_text(old);p.write_text(new);(r/'prefetch46.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/src/mon.c',tofile='b/src/mon.c')))
