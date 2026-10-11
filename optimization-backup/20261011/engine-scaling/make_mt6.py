# mt6 = <base> + S2b: hero perception snapshot (Blind, See_invisible, Infravision, telepathy, Detect_monsters, Warn_of_mon, Invis,
# Displaced) computed lazily per game turn and invalidated at the central mutators (setworn/setnotworn, set_uasmon, set_itimeout/
# incr_itimeout, make_blinded) and at the start of the monster phase; the monster turn reads bits instead of the property macro chains.
# Verify twin (-DNLE_HP_VERIFY) compares each bit read with the live macro and logs HP_MISMATCH.
import shutil,subprocess,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'mt5'
dst=CS/'mt6/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('tools/globals.def',"global | hot | unsigned long | nh_invgen | | 0\n","global | hot | unsigned long | nh_invgen | | 0\nglobal | hot | unsigned char | nh_hp_valid | | 0\nglobal | hot | unsigned char | nh_hp_bits | | 0\n")
rep('include/hack.h',"#define nh_deepest_dirty() ((void) (nh_deepest_valid = 0))","""#define nh_deepest_dirty() ((void) (nh_deepest_valid = 0))
/* hero perception snapshot for the monster turn (see nh_hp_refresh) */
#define NH_HP_BLIND 1u
#define NH_HP_SEEINV 2u
#define NH_HP_INFRA 4u
#define NH_HP_BTELEPAT 8u
#define NH_HP_UTELEPAT 16u
#define NH_HP_DETECT 32u
#define NH_HP_WARNOFMON 64u
#define NH_HP_INVIS 128u
extern void NDECL(nh_hp_refresh);
extern unsigned char nh_hp_displaced_bit;
#define nh_hp_dirty() ((void) (nh_hp_valid = 0))""")
# the inline reader needs the ctx macros: place it after the ctx include (next to the floor-index cursor)
rep('include/hack.h',"struct nh_fobj_cursor {","""static inline unsigned nh_hp(void) { if (!nh_hp_valid) nh_hp_refresh(); return nh_hp_bits; }
#ifdef NLE_HP_VERIFY
#define NH_HPQ(bit, orig) ({ int hp_a_ = (nh_hp() & (bit)) != 0, hp_b_ = (orig) != 0; \\
    if (hp_a_ != hp_b_) fprintf(stderr, "HP_MISMATCH %s turn=%ld\\n", #orig, moves); hp_b_; })
#define NH_HP_DISPLACED_Q ({ int hp_a_ = (nh_hp(), nh_hp_displaced_bit) != 0, hp_b_ = (Displaced) != 0; \\
    if (hp_a_ != hp_b_) fprintf(stderr, "HP_MISMATCH Displaced turn=%ld\\n", moves); hp_b_; })
#else
#define NH_HPQ(bit, orig) ((nh_hp() & (bit)) != 0)
#define NH_HP_DISPLACED_Q ((nh_hp(), nh_hp_displaced_bit) != 0)
#endif
struct nh_fobj_cursor {""")
# refresh + canspotmon in mon.c (near movemon), invalidate at the start of the monster phase
rep('src/mon.c',"    for (mtmp = fmon; mtmp; mtmp = nmtmp) {\n        /* end monster movement early","    nh_hp_dirty(); /* hero actions since the last monster phase may have changed perception */\n    for (mtmp = fmon; mtmp; mtmp = nmtmp) {\n        /* end monster movement early")
md=dst/'src/mon.c'; s=md.read_text()
s=s.rstrip()+"""

/* Hero perception snapshot: recomputed lazily after any invalidation. Displaced is kept
   in its own byte because the bit word is full. */
unsigned char nh_hp_displaced_bit;
void
nh_hp_refresh()
{
    unsigned b = 0;
    if (Blind) b |= NH_HP_BLIND;
    if (See_invisible) b |= NH_HP_SEEINV;
    if (Infravision) b |= NH_HP_INFRA;
    if (Blind_telepat) b |= NH_HP_BTELEPAT;
    if (Unblind_telepat) b |= NH_HP_UTELEPAT;
    if (Detect_monsters) b |= NH_HP_DETECT;
    if (Warn_of_mon) b |= NH_HP_WARNOFMON;
    if (Invis) b |= NH_HP_INVIS;
    nh_hp_displaced_bit = Displaced ? 1 : 0;
    nh_hp_bits = (unsigned char) b;
    nh_hp_valid = 1;
}
"""
md.write_text(s)
# BUG GUARD: nh_hp_displaced_bit is a plain static (not per-game ctx) -> must be per game. Put it in the ctx instead.
s=md.read_text().replace("unsigned char nh_hp_displaced_bit;\n","")
s=s.replace("    nh_hp_displaced_bit = Displaced ? 1 : 0;","    nh_hp_disp = Displaced ? 1 : 0;")
md.write_text(s)
h=dst/'include/hack.h'; t=h.read_text().replace("extern unsigned char nh_hp_displaced_bit;\n","").replace("nh_hp_displaced_bit","nh_hp_disp"); h.write_text(t)
rep('tools/globals.def',"global | hot | unsigned char | nh_hp_bits | | 0\n","global | hot | unsigned char | nh_hp_bits | | 0\nglobal | hot | unsigned char | nh_hp_disp | | 0\n")
# mutators
rep('src/worn.c',"setworn(obj, mask)\nregister struct obj *obj;\nlong mask;\n{\n","setworn(obj, mask)\nregister struct obj *obj;\nlong mask;\n{\n    nh_hp_dirty();\n")
rep('src/worn.c',"setnotworn(obj)\nregister struct obj *obj;\n{\n","setnotworn(obj)\nregister struct obj *obj;\n{\n    nh_hp_dirty();\n")
rep('src/polyself.c',"set_uasmon()\n{\n","set_uasmon()\n{\n    nh_hp_dirty();\n")
rep('src/potion.c',"set_itimeout(which, val)\npropbits_t *which;\nlong val;\n{\n","set_itimeout(which, val)\npropbits_t *which;\nlong val;\n{\n    nh_hp_dirty();\n")
rep('src/potion.c',"incr_itimeout(which, incr)\npropbits_t *which;\nint incr;\n{\n","incr_itimeout(which, incr)\npropbits_t *which;\nint incr;\n{\n    nh_hp_dirty();\n")
rep('src/potion.c',"make_blinded(xtime, talk)\nlong xtime;\nboolean talk;\n{\n","make_blinded(xtime, talk)\nlong xtime;\nboolean talk;\n{\n    nh_hp_dirty();\n")
# uses in the monster turn (never inside mfndpos_reference)
rep('src/monmove.c',"    boolean already_saw_mon = !occupation ? 0 : canspotmon(mtmp);","    boolean already_saw_mon = !occupation ? 0 : nh_hp_canspotmon(mtmp);")
rep('src/monmove.c',"    if (!mtmp->mcansee || (Invis && !SPWQ(mtmp->data, SPW_PERCEIVES, perceives(mtmp->data)))) {","    if (!mtmp->mcansee || (NH_HPQ(NH_HP_INVIS, Invis) && !SPWQ(mtmp->data, SPW_PERCEIVES, perceives(mtmp->data)))) {")
rep('src/monmove.c',"            || (should_see && Invis && !SPWQ(ptr, SPW_PERCEIVES, perceives(ptr)) && rn2(11))","            || (should_see && NH_HPQ(NH_HP_INVIS, Invis) && !SPWQ(ptr, SPW_PERCEIVES, perceives(ptr)) && rn2(11))")
rep('src/monmove.c',"    notseen = (!mtmp->mcansee || (Invis && !SPWQ(mtmp->data, SPW_PERCEIVES, perceives(mtmp->data))));","    notseen = (!mtmp->mcansee || (NH_HPQ(NH_HP_INVIS, Invis) && !SPWQ(mtmp->data, SPW_PERCEIVES, perceives(mtmp->data))));")
rep('src/monmove.c',"    } else if (Displaced) {","    } else if (NH_HP_DISPLACED_Q) {")
rep('src/monmove.c',"    gotu = notseen ? !rn2(3) : Displaced ? !rn2(4) : FALSE;","    gotu = notseen ? !rn2(3) : NH_HP_DISPLACED_Q ? !rn2(4) : FALSE;")
rep('src/monmove.c',"             || (Displaced && mtmp->mux == x && mtmp->muy == y))","             || (NH_HP_DISPLACED_Q && mtmp->mux == x && mtmp->muy == y))")
rep('src/mon.c',"             || (Displaced && mon->mux == x && mon->muy == y))","             || (NH_HP_DISPLACED_Q && mon->mux == x && mon->muy == y))")
rep('src/mon.c',"    mover.monseeu = mon->mcansee && (!Invis || SPWQ(mdat, SPW_PERCEIVES, perceives(mdat)));","    mover.monseeu = mon->mcansee && (!NH_HPQ(NH_HP_INVIS, Invis) || SPWQ(mdat, SPW_PERCEIVES, perceives(mdat)));")
mc=dst/'src/mon.c'; s=mc.read_text()
old="                if (Displaced && monseeu && mon->mux == nx"
assert s.count(old)==2  # reference + masked; patch only the masked (second) occurrence
i=s.rindex(old); s=s[:i]+"                if (NH_HP_DISPLACED_Q && monseeu && mon->mux == nx"+s[i+len(old):]
mc.write_text(s)
# snapshot-based canspotmon for dochugw
rep('src/monmove.c',"int\ndochugw(mtmp)\nregister struct monst *mtmp;\n{","""/* canspotmon() with the hero perception snapshot (same expression, property macros replaced by bits) */
static inline boolean
nh_hp_canspotmon(struct monst *mon)
{
    unsigned hp = nh_hp();
    boolean blind = (hp & NH_HP_BLIND) != 0, seeinv = (hp & NH_HP_SEEINV) != 0, infra = (hp & NH_HP_INFRA) != 0;
    boolean r = ((mon->wormno ? worm_known(mon)
                 : (cansee(mon->mx, mon->my)
                    || (!blind && infra && SPWQ(mon->data, SPW_INFRAVISIBLE, infravisible(mon->data))
                        && couldsee(mon->mx, mon->my))))
                 && ((!mon->minvis || seeinv) && !mon->mundetected))
                || (!SPWQ(mon->data, SPW_MINDLESS, mindless(mon->data))
                    && ((blind && (hp & NH_HP_BTELEPAT))
                        || ((hp & NH_HP_UTELEPAT) && (distu(mon->mx, mon->my) <= (BOLT_LIM * BOLT_LIM)))))
                || (hp & NH_HP_DETECT) || ((hp & NH_HP_WARNOFMON) && MATCH_WARN_OF_MON(mon));
#ifdef NLE_HP_VERIFY
    if (r != (canspotmon(mon) != 0)) fprintf(stderr, "HP_MISMATCH canspotmon turn=%ld\\n", moves);
#endif
    return r;
}

int
dochugw(mtmp)
register struct monst *mtmp;
{""")
out=subprocess.run(['python3','tools/gen_ctx.py'],cwd=dst,capture_output=True,text=True); assert out.returncode==0, out.stderr[:300]
print('mt6 source ready (base', BASE+')')
