from pathlib import Path
import difflib
r=Path(__file__).parent;p=r/'engine-source/src/monmove.c';old=p.read_text();a='''            register int pctload =
                (curr_mon_load(mtmp) * 100) / max_mon_load(mtmp);''';b='''            int scaled_load = curr_mon_load(mtmp) * 100;
            long long load_capacity = max_mon_load(mtmp);''';assert old.count(a)==1
new=old.replace(a,b)
a2='                int pctload = (curr_mon_load(mtmp) * 100) / max_mon_load(mtmp);'
b2='                int scaled_load = curr_mon_load(mtmp) * 100;\n                long long load_capacity = max_mon_load(mtmp);'
assert new.count(a2)==1;new=new.replace(a2,b2)
for limit in [95,85,75,50]:new=new.replace('pctload < '+str(limit),'scaled_load < '+str(limit)+' * load_capacity')
assert 'pctload' not in new
backup=r/'load47-before-monmove.c';assert not backup.exists();backup.write_text(old);p.write_text(new);(r/'load47.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/src/monmove.c',tofile='b/src/monmove.c')))
