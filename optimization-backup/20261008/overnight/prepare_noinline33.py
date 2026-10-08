from pathlib import Path
import shutil
r=Path(__file__).parent;p=r/'engine-source/src/monmove.c';shutil.copy2(p,r/'noinline33-before-monmove.c');s=p.read_text();needle='boolean\nonscary(x, y, mtmp)';assert s.count(needle)==1;s=s.replace(needle,'#if defined(__GNUC__)\n__attribute__((noinline))\n#endif\n'+needle);p.write_text(s)
