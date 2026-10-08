from pathlib import Path
import subprocess
r=Path(__file__).parent;p=r/'engine-source/src/monmove.c';b=r/'scary06-before.c';assert not b.exists();b.write_bytes(p.read_bytes());s=p.read_text();needle='''    /* creatures who are directly resistant to magical scaring:''';replacement='''    if ((x || y) && !OBJ_AT(x, y) && !IS_ALTAR(TYP_AT(x, y))
        && (u.ux != x || u.uy != y)
        && (!Displaced || mtmp->mux != x || mtmp->muy != y))
        return FALSE;

    /* creatures who are directly resistant to magical scaring:''';assert s.count(needle)==1;s=s.replace(needle,replacement);p.write_text(s);(r/'scary06.patch').write_bytes(subprocess.run(['diff','-u',str(b),str(p)],capture_output=True).stdout)
