# mbits = misc1 + per-monster 64-bit carried-otyp filter (superset invariant) so m_carrying() skips the minvent walk.
import shutil,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'misc1'
dst=CS/'mbits/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('include/monst.h',"    uint32_t mtrapseen, mspare1;\n};","    uint32_t mtrapseen, mspare1;\n    uint64_t mcarry_bits; /* superset of NH_OTYP_BIT(otyp) over minvent; m_carrying filter */\n};")
rep('src/mon.c',"struct nh_mon_slot {\n    struct monst value;\n    unsigned char padding[8];\n};","struct nh_mon_slot {\n    struct monst value;\n};")
rep('include/mon_save.h','_Static_assert(sizeof(struct monst)==120,"hot monster size");','_Static_assert(sizeof(struct monst)==128,"hot monster size");')
rep('src/save.c','_Static_assert(sizeof(struct monst) ==  120, "save.c: sizeof(struct monst) drifted");','_Static_assert(sizeof(struct monst) ==  128, "save.c: sizeof(struct monst) drifted");')
rep('src/restore.c','_Static_assert(sizeof(struct monst) ==  120, "restore.c: sizeof(struct monst) drifted");','_Static_assert(sizeof(struct monst) ==  128, "restore.c: sizeof(struct monst) drifted");')
ms=dst/'include/mon_save.h'; s=ms.read_text(); head,tail=s.split('static inline void mon_from_legacy',1)
assert tail.count("    out->mspare1=in->mspare1;\n")==1
ms.write_text(head+'static inline void mon_from_legacy'+tail.replace("    out->mspare1=in->mspare1;\n","    out->mspare1=in->mspare1;\n    out->mcarry_bits=0;\n"))
rep('include/hack.h',"#define nh_deepest_dirty() ((void) (nh_deepest_valid = 0))",
    "#define nh_deepest_dirty() ((void) (nh_deepest_valid = 0))\n#define NH_OTYP_BIT(t) (1ull << ((t) & 63))\n#define nh_mcarry_add(m, t) ((void) ((m) ? ((m)->mcarry_bits |= NH_OTYP_BIT(t)) : 0ull))")
# insertion / type-change hooks
rep('src/mkobj.c',"    obj->where = OBJ_MINVENT;\n    obj->ocarry = mon;\n    obj->nobj = mon->minvent;\n    mon->minvent = obj;\n",
    "    obj->where = OBJ_MINVENT;\n    obj->ocarry = mon;\n    obj->nobj = mon->minvent;\n    mon->minvent = obj;\n    nh_mcarry_add(mon, obj->otyp);\n")
rep('src/mkobj.c',"    case OBJ_MINVENT:\n        otmp->nobj = obj->nobj;\n        otmp->ocarry = obj->ocarry;","    case OBJ_MINVENT:\n        otmp->nobj = obj->nobj;\n        otmp->ocarry = obj->ocarry;\n        nh_mcarry_add(otmp->ocarry, otmp->otyp);")
rep('include/movement_facts.h',"       if ((obj)->where == OBJ_FLOOR) nh_pile_update((obj)->ox, (obj)->oy); \\",
    "       if ((obj)->where == OBJ_FLOOR) nh_pile_update((obj)->ox, (obj)->oy); \\\n       else if ((obj)->where == OBJ_MINVENT) nh_mcarry_add((obj)->ocarry, (obj)->otyp); \\")
rep('src/restore.c',"            for (obj = mtmp->minvent; obj; obj = obj->nobj)\n                obj->ocarry = mtmp;","            for (obj = mtmp->minvent; obj; obj = obj->nobj)\n                obj->ocarry = mtmp, nh_mcarry_add(mtmp, obj->otyp);")
# chains moved between monsters: union the bits
rep('src/mon.c',"    mtmp->minvent = 0;\n","    mtmp2->mcarry_bits |= mtmp->mcarry_bits;\n    mtmp->minvent = 0;\n")
rep('src/zap.c',"        mtmp2->minvent = mtmp->minvent; /*redundant*/","        mtmp2->minvent = mtmp->minvent; /*redundant*/\n        mtmp2->mcarry_bits |= mtmp->mcarry_bits;")
# filter
rep('src/mthrowu.c',"""    register struct obj *otmp;

    for (otmp = mtmp->minvent; otmp; otmp = otmp->nobj)
        if (otmp->otyp == type)
            return otmp;
    return (struct obj *) 0;""","""    register struct obj *otmp;

    if (!(mtmp->mcarry_bits & NH_OTYP_BIT(type))) {
#ifdef NLE_MBITS_VERIFY
        for (otmp = mtmp->minvent; otmp; otmp = otmp->nobj)
            if (otmp->otyp == type) {
                fprintf(stderr, "MBITS_MISMATCH turn=%ld mon=%d otyp=%d\\n", moves, (int) mtmp->mnum, type);
                mtmp->mcarry_bits |= NH_OTYP_BIT(type);
                return otmp;
            }
#endif
        return (struct obj *) 0;
    }
    for (otmp = mtmp->minvent; otmp; otmp = otmp->nobj)
        if (otmp->otyp == type)
            return otmp;
    return (struct obj *) 0;""")
print('mbits source ready (base', BASE+')')
