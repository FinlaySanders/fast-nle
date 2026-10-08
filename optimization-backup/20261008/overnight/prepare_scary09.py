from pathlib import Path
import subprocess
r=Path(__file__).parent;s=r/'engine-source';backup=r/'scary09-before';backup.mkdir()
for name in ['src/monmove.c','src/mon.c','include/extern.h']:
 p=s/name;q=backup/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
p=s/'src/monmove.c';t=p.read_text();needle='''    /* should this still be true for defiled/molochian altars? */''';repl='''    return nh_onscary_tile(x, y, mtmp);
}

boolean
nh_onscary_tile(int x, int y, struct monst *mtmp)
{
    /* should this still be true for defiled/molochian altars? */''';assert t.count(needle)==1;p.write_text(t.replace(needle,repl))
p=s/'include/extern.h';t=p.read_text();needle='E boolean FDECL(onscary, (int, int, struct monst *));';assert needle in t;p.write_text(t.replace(needle,needle+'\nE boolean FDECL(nh_onscary_tile, (int, int, struct monst *));'))
p=s/'src/mon.c';t=p.read_text();a=t.index('int mfndpos(');z=t.index('\n}',a);part=t[a:z];needle='boolean poisongas_ok, in_poisongas;';assert needle in part;part=part.replace(needle,needle+'\n    boolean can_scare = onscary(0, 0, mon);');needle='if (onscary(dispx, dispy, mon))';assert needle in part;part=part.replace(needle,'if (can_scare && nh_onscary_tile(dispx, dispy, mon))');p.write_text(t[:a]+part+t[z:])
with (r/'scary09.patch').open('wb') as f:
 for name in ['src/monmove.c','src/mon.c','include/extern.h']:f.write(subprocess.run(['diff','-u','--label','a/'+name,'--label','b/'+name,str(backup/name),str(s/name)],capture_output=True).stdout)
