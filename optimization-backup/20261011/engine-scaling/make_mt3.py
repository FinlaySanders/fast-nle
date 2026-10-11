# mt3 = <base> + forced inlining of the per-move helpers that LTO left as calls (distfleeck x3, set_apparxy, should_displace,
# m_digweapon_check, monhaskey, dochugw): removes ~15K/step of prologue/epilogue. No semantic change.
import shutil,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'mt2'
dst=CS/'mt3/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('src/monmove.c',"STATIC_DCL void FDECL(distfleeck, (struct monst *, int *, int *, int *));",
"""STATIC_DCL void FDECL(distfleeck, (struct monst *, int *, int *, int *)) __attribute__((always_inline));
/* per-move helpers: inline into the monster-turn pass (their out-of-line copies stay for other callers) */
extern void FDECL(set_apparxy, (struct monst *)) __attribute__((always_inline));
extern boolean FDECL(should_displace, (struct monst *, coord *, long *, int, XCHAR_P, XCHAR_P)) __attribute__((always_inline));
extern boolean FDECL(m_digweapon_check, (struct monst *, XCHAR_P, XCHAR_P)) __attribute__((always_inline));
extern boolean FDECL(monhaskey, (struct monst *, BOOLEAN_P)) __attribute__((always_inline));
extern int FDECL(dochugw, (struct monst *)) __attribute__((always_inline));""")
rep('src/mon.c','#include "hack.h"\n','#include "hack.h"\nextern int FDECL(dochugw, (struct monst *)) __attribute__((always_inline));\n')
print('mt3 source ready (base', BASE+')')
