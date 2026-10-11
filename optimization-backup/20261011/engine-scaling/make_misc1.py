# misc1 = fobj2 + three per-step walks removed: hidden_gold() and check_leash() cached behind a hero-inventory
# generation counter (nh_invgen), deepest_lev_reached() cached until dunlev_ureached changes.
import shutil,subprocess
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
dst=CS/'misc1/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/'fobj2/source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('tools/globals.def',"global | cold | int | nh_fobj_lo | | 0\n","""global | cold | int | nh_fobj_lo | | 0
global | hot | unsigned long | nh_invgen | | 0
global | hot | unsigned long | nh_hgold_gen | | 0
global | hot | long | nh_hgold_val | | 0
global | hot | unsigned long | nh_leash_gen | | 0
global | hot | unsigned char | nh_hgold_valid | | 0
global | hot | unsigned char | nh_leash_valid | | 0
global | hot | unsigned char | nh_leash_cnt | | 0
global | hot | unsigned char | nh_deepest_valid | | 0
global | hot | schar | nh_deepest_val | [2] | 0
""")
rep('include/hack.h',"#define nh_mload_dirty(m)" if False else "#define nh_invwt_dirty() ((void) (nh_invwt_valid = 0))",
    "#define nh_invwt_dirty() ((void) (nh_invwt_valid = 0))\n#define nh_deepest_dirty() ((void) (nh_deepest_valid = 0))")
# hero-inventory generation: every insertion site already clears nh_no_hero_gold
for f,n in [('src/invent.c',6),('src/mkobj.c',1),('src/restore.c',1)]:
    rep(f,"nh_no_hero_gold = 0;","nh_no_hero_gold = 0; nh_invgen++;",n)
rep('src/mkobj.c',"    if (head_ptr == &invent)\n        nh_invwt_dirty();\n","    if (head_ptr == &invent) {\n        nh_invwt_dirty();\n        nh_invgen++;\n    }\n")
# contents of a hero-carried container
rep('src/mkobj.c',"    obj->nobj = container->cobj;\n    container->cobj = obj;\n    return obj;","    obj->nobj = container->cobj;\n    container->cobj = obj;\n    nh_cont_dirty(container);\n    return obj;")
rep('src/mkobj.c',"        extract_nobj(obj, &obj->ocontainer->cobj);","        nh_cont_dirty(obj->ocontainer);\n        extract_nobj(obj, &obj->ocontainer->cobj);",2)
rep('src/mkobj.c','#include "hack.h"\n','#include "hack.h"\n\n/* contents of a container the hero carries count toward hidden gold */\nstatic void\nnh_cont_dirty(struct obj *c)\n{\n    while (c && c->where == OBJ_CONTAINED)\n        c = c->ocontainer;\n    if (c && c->where == OBJ_INVENT)\n        nh_invgen++;\n}\n')
# hidden_gold cache
rep('src/vault.c',"""long
hidden_gold()
{
    long value = 0L;
    struct obj *obj;

    for (obj = invent; obj; obj = obj->nobj)
        if (Has_contents(obj))
            value += contained_gold(obj);
    /* unknown gold stuck inside statues may cause some consternation... */

    return value;
}""","""long
hidden_gold()
{
    long value = 0L;
    struct obj *obj;

    /* cached until the set of objects reachable from invent changes */
    if (nh_hgold_valid && nh_hgold_gen == nh_invgen) {
#ifdef NLE_MISC_VERIFY
        for (obj = invent; obj; obj = obj->nobj)
            if (Has_contents(obj))
                value += contained_gold(obj);
        if (value != nh_hgold_val) {
            fprintf(stderr, "HGOLD_MISMATCH turn=%ld cached=%ld walked=%ld\\n", moves, nh_hgold_val, value);
            nh_hgold_val = value;
        }
        return value;
#else
        return nh_hgold_val;
#endif
    }
    for (obj = invent; obj; obj = obj->nobj)
        if (Has_contents(obj))
            value += contained_gold(obj);
    /* unknown gold stuck inside statues may cause some consternation... */
    nh_hgold_val = value; nh_hgold_gen = nh_invgen; nh_hgold_valid = 1;
    return value;
}""")
# leash gate
rep('src/apply.c',"""    register struct obj *otmp;
    register struct monst *mtmp;

    for (otmp = invent; otmp; otmp = otmp->nobj) {
        if (otmp->otyp != LEASH || otmp->leashmon == 0)
            continue;""","""    register struct obj *otmp;
    register struct monst *mtmp;

    /* no leash carried: nothing to check (count cached per inventory generation) */
    if (nh_leash_valid && nh_leash_gen == nh_invgen && nh_leash_cnt == 0) {
#ifdef NLE_MISC_VERIFY
        for (otmp = invent; otmp; otmp = otmp->nobj)
            if (otmp->otyp == LEASH) {
                fprintf(stderr, "LEASH_MISMATCH turn=%ld\\n", moves);
                break;
            }
#endif
        return;
    }
    {
        int n = 0;
        for (otmp = invent; otmp; otmp = otmp->nobj)
            if (otmp->otyp == LEASH)
                n++;
        nh_leash_cnt = n > 255 ? 255 : n; nh_leash_gen = nh_invgen; nh_leash_valid = 1;
        if (!n)
            return;
    }
    for (otmp = invent; otmp; otmp = otmp->nobj) {
        if (otmp->otyp != LEASH || otmp->leashmon == 0)
            continue;""")
# deepest level cache
rep('src/dungeon.c',"""    register int i;
    d_level tmp;
    register schar ret = 0;

    for (i = 0; i < n_dgns; i++) {
        if (noquest && i == quest_dnum)
            continue;
        tmp.dlevel = dungeons[i].dunlev_ureached;
        if (tmp.dlevel == 0)
            continue;
        tmp.dnum = i;
        if (depth(&tmp) > ret)
            ret = depth(&tmp);
    }
    return (xchar) ret;""","""    register int i;
    d_level tmp;
    register schar ret = 0;
    int slot = noquest ? 1 : 0;

    if (nh_deepest_valid & (1 << slot)) {
#ifdef NLE_MISC_VERIFY
        for (i = 0; i < n_dgns; i++) {
            if (noquest && i == quest_dnum)
                continue;
            tmp.dlevel = dungeons[i].dunlev_ureached;
            if (tmp.dlevel == 0)
                continue;
            tmp.dnum = i;
            if (depth(&tmp) > ret)
                ret = depth(&tmp);
        }
        if (ret != nh_deepest_val[slot])
            fprintf(stderr, "DEEPEST_MISMATCH turn=%ld cached=%d walked=%d\\n", moves, nh_deepest_val[slot], ret);
        nh_deepest_val[slot] = ret;
#endif
        return (xchar) nh_deepest_val[slot];
    }
    for (i = 0; i < n_dgns; i++) {
        if (noquest && i == quest_dnum)
            continue;
        tmp.dlevel = dungeons[i].dunlev_ureached;
        if (tmp.dlevel == 0)
            continue;
        tmp.dnum = i;
        if (depth(&tmp) > ret)
            ret = depth(&tmp);
    }
    nh_deepest_val[slot] = ret; nh_deepest_valid |= 1 << slot;
    return (xchar) ret;""")
rep('src/do.c',"dunlev_reached(&u.uz) = dunlev(&u.uz);","dunlev_reached(&u.uz) = dunlev(&u.uz), nh_deepest_dirty();",2)
rep('src/dungeon.c',"            dungeons[i].dunlev_ureached = 0;\n        }","            dungeons[i].dunlev_ureached = 0;\n        }\n        nh_deepest_dirty();")
rep('src/dungeon.c',"    mread(fd, (genericptr_t) dungeons, sizeof(dungeon) * (unsigned) n_dgns);","    mread(fd, (genericptr_t) dungeons, sizeof(dungeon) * (unsigned) n_dgns);\n    nh_deepest_dirty();")
out=subprocess.run(['python3','tools/gen_ctx.py'],cwd=dst,capture_output=True,text=True); assert out.returncode==0, out.stderr[:400]
d=subprocess.run(['diff','-u',str(CS/'fobj2/source/include/nh_ctx_gen.h'),str(dst/'include/nh_ctx_gen.h')],capture_output=True,text=True).stdout
print('ctx header diff:', [l for l in d.splitlines() if l.startswith(('+','-')) and not l.startswith(('+++','---')) and 'nh_' in l][:12])
print('misc1 source ready')
