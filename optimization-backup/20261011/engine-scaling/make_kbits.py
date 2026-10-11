# kbits = <base> + per-game bitset of objects[].oc_name_known for the hot export reads (inv_state, inv_true_glyphs, maybe_true_glyph).
import shutil,subprocess,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'mbits'
dst=CS/'kbits/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('tools/globals.def',"global | hot | unsigned long | nh_invgen | | 0\n","global | hot | unsigned long | nh_invgen | | 0\nglobal | hot | unsigned long long | nh_oc_known | [8] | 0\nglobal | hot | unsigned char | nh_oc_known_valid | | 0\n")
rep('include/hack.h',"struct nh_fobj_cursor {","""#define NH_KBIT(t) (1ull << ((t) & 63))
/* objects[].oc_name_known mirrored in 8 words; rebuilt lazily, kept by discover_object/forget_single_object */
extern void NDECL(nh_oc_known_rebuild);
#define nh_oc_known_set(t) ((void) (nh_oc_known_valid ? (nh_oc_known[(t) >> 6] |= NH_KBIT(t)) : 0ull))
#define nh_oc_known_clear(t) ((void) (nh_oc_known_valid ? (nh_oc_known[(t) >> 6] &= ~NH_KBIT(t)) : 0ull))
static inline int
nh_oc_known_q(int t)
{
    int b;
    if (!nh_oc_known_valid)
        nh_oc_known_rebuild();
    b = (int) ((nh_oc_known[t >> 6] >> (t & 63)) & 1ull);
#ifdef NLE_KBITS_VERIFY
    if (b != (int) objects[t].oc_name_known) {
        fprintf(stderr, "KBITS_MISMATCH turn=%ld otyp=%d bit=%d field=%d\\n", moves, t, b, (int) objects[t].oc_name_known);
        nh_oc_known_valid = 0;
        nh_oc_known_rebuild();
        b = (int) objects[t].oc_name_known;
    }
#endif
    return b;
}
struct nh_fobj_cursor {""")
rep('src/o_init.c',"            objects[oindx].oc_name_known = 1;\n            nle_discoveries_changed();","            objects[oindx].oc_name_known = 1;\n            nh_oc_known_set(oindx);\n            nle_discoveries_changed();")
rep('src/read.c',"    objects[obj_id].oc_name_known = 0;\n    nle_discoveries_changed();","    objects[obj_id].oc_name_known = 0;\n    nh_oc_known_clear(obj_id);\n    nle_discoveries_changed();")
rep('src/o_init.c',"    mread(fd, (genericptr_t) objects, sizeof(struct objclass) * NUM_OBJECTS);\n","    mread(fd, (genericptr_t) objects, sizeof(struct objclass) * NUM_OBJECTS);\n    nh_oc_known_valid = 0;\n")
# rebuild function at the end of o_init.c
p=dst/'src/o_init.c'; s=p.read_text(); s=s.rstrip()+"""

_Static_assert(NUM_OBJECTS <= 512, "nh_oc_known holds 512 object types");
void
nh_oc_known_rebuild()
{
    int i;
    for (i = 0; i < 8; i++)
        nh_oc_known[i] = 0ull;
    for (i = 0; i < NUM_OBJECTS; i++)
        if (objects[i].oc_name_known)
            nh_oc_known[i >> 6] |= NH_KBIT(i);
    nh_oc_known_valid = 1;
}
"""; p.write_text(s)
# hot reads
rep('win/rl/winrl.cc',"        if (!objects[obj].oc_name_known) return GLYPH_OBJ_OFF + gem_canon(objects[obj].oc_descr_idx);","        if (!nh_oc_known_q(obj)) return GLYPH_OBJ_OFF + gem_canon(objects[obj].oc_descr_idx);")
rep('win/rl/winrl.cc',"        && objects[glyph_to_obj(glyph)].oc_name_known)\n        return glyph;","        && nh_oc_known_q(glyph_to_obj(glyph)))\n        return glyph;")
rep('win/rl/winrl.cc',"(otmp->dknown && objects[otmp->otyp].oc_name_known)","(otmp->dknown && nh_oc_known_q(otmp->otyp))",3)
rep('src/nle.c',"                int typ = (otmp->dknown && objects[otmp->otyp].oc_name_known)","                int typ = (otmp->dknown && nh_oc_known_q(otmp->otyp))")
rep('src/nle.c',"        if (!objects[o->otyp].oc_name_known && !o->dknown) nunid++;","        if (!nh_oc_known_q(o->otyp) && !o->dknown) nunid++;")
out=subprocess.run(['python3','tools/gen_ctx.py'],cwd=dst,capture_output=True,text=True); assert out.returncode==0, out.stderr[:400]
print('kbits source ready (base', BASE+')')
