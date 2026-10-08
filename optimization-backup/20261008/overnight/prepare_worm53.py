from pathlib import Path
import shutil,difflib
r=Path(__file__).parent;p=r/'engine-source/src/mon.c';s=p.read_text();shutil.copy2(p,r/'worm53-before-mon.c')
a='m_at(x, ny) && m_at(nx, y) && worm_cross(x, y, nx, ny)';b='m_at(x, ny) && m_at(nx, y) == m_at(x, ny)\n                        && worm_cross(x, y, nx, ny)';assert s.count(a)==1;t=s.replace(a,b);p.write_text(t);(r/'worm53.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='a/src/mon.c',tofile='b/src/mon.c')))
