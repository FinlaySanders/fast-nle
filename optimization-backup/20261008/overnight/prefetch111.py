from pathlib import Path
import subprocess,difflib
r=Path(__file__).parent;p=r/'engine-source/src/monmove.c';before=p.read_text();assert before==(r/'pgo61-source/src/monmove.c').read_text()
a='''            cursor->index = i + 1;
            return nh_fobj_ptr[i];'''
b='''            cursor->index = i + 1;
            if (cursor->mask)
                __builtin_prefetch(nh_fobj_ptr[cursor->base + __builtin_ctz(cursor->mask) / 2], 0, 1);
            return nh_fobj_ptr[i];'''
assert before.count(a)==1
after=before.replace(a,b)
a='''                cursor->index = i + 1;
                return nh_fobj_ptr[i];'''
b='''                cursor->index = i + 1;
                if (cursor->mask)
                    __builtin_prefetch(nh_fobj_ptr[cursor->base + __builtin_ctz(cursor->mask) / 2], 0, 1);
                return nh_fobj_ptr[i];'''
assert after.count(a)==1;after=after.replace(a,b)
(r/'prefetch111-before-monmove.c').write_text(before)
(r/'prefetch111.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/monmove.c',tofile='b/src/monmove.c')))
p.write_text(after)
try:subprocess.run(['python',str(r/'engine_screen_alloc62.py'),'prefetch111'],check=True)
finally:p.write_text(before)
