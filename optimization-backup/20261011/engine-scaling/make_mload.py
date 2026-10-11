# Monster-load cache candidate: engines/mload = invwt + cached curr_mon_load per monster (bit31 = valid).
import re,shutil,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
dst=CS/'mload/source'
if dst.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/'invwt/source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:60]); p.write_text(s.replace(old,new))
# field
rep('include/monst.h',"    uint32_t mtrapseen, mspare1;\n};","    uint32_t mtrapseen, mspare1;\n    uint32_t mload_cache; /* bit31 valid | carried weight (non-rock-thrower form); see curr_mon_load */\n};")
# pool slot: monst is now 128 B
rep('src/mon.c',"struct nh_mon_slot {\n    struct monst value;\n    unsigned char padding[8];\n};","struct nh_mon_slot {\n    struct monst value;\n};")
# cache in curr_mon_load (+ optional verify)
rep('src/mon.c',"""int curr_mon_load(mtmp) struct monst *mtmp;
{
    int curload = 0;
    struct obj *obj;

    for (obj = mtmp->minvent; obj; obj = obj->nobj) {
        if (obj->otyp != BOULDER || !throws_rocks(mtmp->data))
            curload += obj->owt;
    }

    return curload;
}""","""int curr_mon_load(mtmp) struct monst *mtmp;
{
    int curload = 0;
    struct obj *obj;
    boolean rocks = throws_rocks(mtmp->data);

    /* Cached per monster unless it throws rocks (then boulders are exempt
       and the sum depends on its form). Invalidated (bit31 cleared) by
       nh_mload_dirty() at every change of its inventory chain or weights. */
    if (!rocks && (mtmp->mload_cache & 0x80000000u)) {
        curload = (int) (mtmp->mload_cache & 0x7fffffffu);
#ifdef NLE_MLOAD_VERIFY
        {
            int ref = 0;
            for (obj = mtmp->minvent; obj; obj = obj->nobj)
                ref += obj->owt;
            if (ref != curload) {
                fprintf(stderr, "MLOAD_MISMATCH turn=%ld mon=%d cached=%d walked=%d\\n", moves, (int) mtmp->mnum, curload, ref);
                curload = ref;
                mtmp->mload_cache = 0;
            }
        }
#endif
        return curload;
    }
    for (obj = mtmp->minvent; obj; obj = obj->nobj) {
        if (obj->otyp != BOULDER || !rocks)
            curload += obj->owt;
    }
    if (!rocks && curload >= 0)
        mtmp->mload_cache = 0x80000000u | (uint32_t) curload;
    return curload;
}""")
# dirty macro + nh_set_owt extension
rep('include/hack.h',"#define nh_set_owt(o) ((o)->owt = weight(o), ((o)->where == OBJ_INVENT ? nh_invwt_dirty() : (void) 0))",
"""#define nh_mload_dirty(m) ((void) ((m) ? ((m)->mload_cache = 0) : 0))
#define nh_set_owt(o) ((o)->owt = weight(o), ((o)->where == OBJ_INVENT ? nh_invwt_dirty() \\
                       : (o)->where == OBJ_MINVENT ? nh_mload_dirty((o)->ocarry) : (void) 0))""")
# hooks
rep('src/mkobj.c',"    obj->where = OBJ_MINVENT;\n    obj->ocarry = mon;\n    obj->nobj = mon->minvent;\n    mon->minvent = obj;\n    return 0; /* obj on mon's inventory chain */",
    "    obj->where = OBJ_MINVENT;\n    obj->ocarry = mon;\n    obj->nobj = mon->minvent;\n    mon->minvent = obj;\n    nh_mload_dirty(mon);\n    return 0; /* obj on mon's inventory chain */")
rep('src/mkobj.c',"    case OBJ_MINVENT:\n        extract_nobj(obj, &obj->ocarry->minvent);\n        obj->ocarry = (struct monst *) 0; /* clear stale back-link */",
    "    case OBJ_MINVENT:\n        nh_mload_dirty(obj->ocarry);\n        extract_nobj(obj, &obj->ocarry->minvent);\n        obj->ocarry = (struct monst *) 0; /* clear stale back-link */")
rep('src/mkobj.c',"    case OBJ_MINVENT:\n        otmp->nobj = obj->nobj;\n        otmp->ocarry = obj->ocarry;","    case OBJ_MINVENT:\n        nh_mload_dirty(obj->ocarry);\n        otmp->nobj = obj->nobj;\n        otmp->ocarry = obj->ocarry;")
# merged(): glob absorb path also for monster inventories
rep('src/invent.c',"            otmp->owt += obj->owt;\n            if (otmp->where == OBJ_INVENT) nh_invwt_dirty();",
    "            otmp->owt += obj->owt;\n            if (otmp->where == OBJ_INVENT) nh_invwt_dirty();\n            else if (otmp->where == OBJ_MINVENT) nh_mload_dirty(otmp->ocarry);")
# direct minvent assignments
for path,old in [('src/mon.c',"    mtmp->minvent = 0;"),('src/zap.c',"        mtmp2->minvent = mtmp->minvent; /*redundant*/"),('src/mkobj.c',"        mtmp2->minvent = (struct obj *) 0;")]:
    p=dst/path; s=p.read_text(); assert s.count(old)==1,(path,s.count(old)); 
    who='mtmp2' if 'mtmp2' in old else 'mtmp'
    p.write_text(s.replace(old, old+f"\n        nh_mload_dirty({who});" if old.startswith('        ') else old+f"\n    nh_mload_dirty({who});"))
rep('src/shk.c',"            otmp->owt = 0; /* superfluous */","            otmp->owt = 0; /* superfluous */\n            nh_mload_dirty(otmp->ocarry);")
# restore conversion: cache invalid after level restore
ms=dst/'include/mon_save.h'; s=ms.read_text(); head,tail=s.split('static inline void mon_from_legacy',1)
assert tail.count("    out->mspare1=in->mspare1;\n")==1
ms.write_text(head+'static inline void mon_from_legacy'+tail.replace("    out->mspare1=in->mspare1;\n","    out->mspare1=in->mspare1;\n    out->mload_cache=0;\n"))
# extra chain/weight sites found in the audit
rep('src/makemon.c',"    m2->minvent = (struct obj *) 0; /* objects don't clone */","    m2->minvent = (struct obj *) 0; /* objects don't clone */\n    nh_mload_dirty(m2);")
rep('src/makemon.c',"        mtmp->minvent = (struct obj *) 0; /* caller expects this */","        mtmp->minvent = (struct obj *) 0; /* caller expects this */\n        nh_mload_dirty(mtmp);")
rep('src/restore.c',"            mtmp->minvent = restobjchn(fd, ghostly, FALSE);","            mtmp->minvent = restobjchn(fd, ghostly, FALSE);\n            nh_mload_dirty(mtmp);")
rep('src/mkobj.c',"            otmp1->owt += o2wt;\n","            otmp1->owt += o2wt;\n            if (otmp1->where == OBJ_INVENT) nh_invwt_dirty();\n            else if (otmp1->where == OBJ_MINVENT) nh_mload_dirty(otmp1->ocarry);\n")
rep('src/read.c',"        uball->owt += IRON_BALL_W_INCR * (1 + sobj->cursed);","        uball->owt += IRON_BALL_W_INCR * (1 + sobj->cursed);\n        if (uball->where == OBJ_INVENT) nh_invwt_dirty();")
# brace the merged() hook (invwt left the dirty outside the else-if; harmless but wrong-looking)
rep('src/invent.c',"        else if (!Is_pudding(otmp))\n            otmp->owt += obj->owt;\n            if (otmp->where == OBJ_INVENT) nh_invwt_dirty();\n            else if (otmp->where == OBJ_MINVENT) nh_mload_dirty(otmp->ocarry);",
    "        else if (!Is_pudding(otmp))\n            otmp->owt += obj->owt;\n        if (otmp->where == OBJ_INVENT) nh_invwt_dirty();\n        else if (otmp->where == OBJ_MINVENT) nh_mload_dirty(otmp->ocarry);")
# struct monst 120 -> 128 B (fills the pool slot padding)
rep('include/mon_save.h','_Static_assert(sizeof(struct monst)==120,"hot monster size");','_Static_assert(sizeof(struct monst)==128,"hot monster size");')
rep('src/save.c','_Static_assert(sizeof(struct monst) ==  120, "save.c: sizeof(struct monst) drifted");','_Static_assert(sizeof(struct monst) ==  128, "save.c: sizeof(struct monst) drifted");')
rep('src/restore.c','_Static_assert(sizeof(struct monst) ==  120, "restore.c: sizeof(struct monst) drifted");','_Static_assert(sizeof(struct monst) ==  128, "restore.c: sizeof(struct monst) drifted");')
print('mload source ready')
