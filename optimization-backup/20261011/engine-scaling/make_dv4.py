# dv4 = <base> + per-movemon sense bitmask + nh_newsym_moved(): a monster move's two newsym() calls skip when newsym() would provably change
# nothing. Hero-global sensing properties are hoisted into nh_display_sense (recomputed at movemon(), set to ALL by make_blinded/Blindf_on/
# Blindf_off/set_uasmon); per call: cansee, hero square, swallowed/underwater, then newsym()'s own per-monster predicates only if a monster is
# on the square, then the lit-memory fixup test and the screen-buffer compare.
import shutil,subprocess,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'mt7'
dst=CS/'dv4/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('tools/globals.def',"global | hot | int | nh_invwt_valid | | 0\n","global | hot | int | nh_invwt_valid | | 0\nglobal | hot | int | nh_display_sense | | 0\n")
rep('include/extern.h',"E void FDECL(newsym, (int, int));\n","E void FDECL(newsym, (int, int));\nE void FDECL(nh_newsym_moved, (int, int));\nE void NDECL(nh_display_sense_recalc);\n")
rep('include/display.h',"#define tp_sensemon(mon) \\\n","""/* nh_display_sense: hero-global sensing properties, hoisted for nh_newsym_moved() (display.c) */
#define NH_SENSE_TPBLIND 1
#define NH_SENSE_TP 2
#define NH_SENSE_WARNMON 4
#define NH_SENSE_DETECT 8
#define NH_SENSE_INFRA 16
#define NH_SENSE_WARNING 32
#define NH_SENSE_SPECIAL 64
#define NH_SENSE_ALL 127
#define NH_SENSE_VALID 128 /* 0 = stale: behave as ALL until movemon() recomputes */

#define tp_sensemon(mon) \\
""")
rep('src/display.c',"""#define gbuf_stop  (nh_cur->g_display_c_gbuf_stop)
""","""#define gbuf_stop  (nh_cur->g_display_c_gbuf_stop)

/* Hero-global half of newsym()'s out-of-sight branch as a bitmask; recomputed at movemon(), set to ALL whenever sight or form changes. */
void
nh_display_sense_recalc()
{
    int s = 0;

    if (Blind && Blind_telepat) s |= NH_SENSE_TPBLIND;
    if (Unblind_telepat) s |= NH_SENSE_TP;
    if (Warn_of_mon) s |= NH_SENSE_WARNMON;
    if (Detect_monsters) s |= NH_SENSE_DETECT;
    if (!Blind && Infravision) s |= NH_SENSE_INFRA;
    if (Warning) s |= NH_SENSE_WARNING;
    if (in_mklev || iflags.use_background_glyph || Is_rogue_level(&u.uz)
#ifdef HANGUPHANDLING
        || program_state.done_hup
#endif
        ) s |= NH_SENSE_SPECIAL;
    nh_display_sense = s | NH_SENSE_VALID;
}

/* newsym() for the square a monster just left or entered; skips when newsym() would provably change nothing. */
void
nh_newsym_moved(x, y)
int x, y;
{
    register struct rm *lev;
    struct monst *mon;
    int s = nh_display_sense;
#ifdef NLE_DISPLAY_VERIFY
    static long nh_ns_skip, nh_ns_call;
#endif

    if (!(s & NH_SENSE_VALID) || (s & NH_SENSE_SPECIAL) || u.uswallow || Underwater || (x == u.ux && y == u.uy) || cansee(x, y))
        goto full;
    if (s && (mon = m_at(x, y)) != 0) {
        if ((s & NH_SENSE_DETECT)
            || ((s & NH_SENSE_TPBLIND) && !mindless(mon->data))
            || ((s & NH_SENSE_TP) && !mindless(mon->data) && distu(mon->mx, mon->my) <= (BOLT_LIM * BOLT_LIM))
            || ((s & NH_SENSE_WARNMON) && MATCH_WARN_OF_MON(mon))
            || ((s & NH_SENSE_INFRA) && infravisible(mon->data) && couldsee(mon->mx, mon->my))
            || ((s & NH_SENSE_WARNING) && mon_warning(mon)))
            goto full;
    }
    lev = &(NH_TILE(x, y));
    if ((!lev->waslit || (flags.dark_room && iflags.use_color))
        && ((lev->glyph == cmap_to_glyph(S_litcorr) && lev->typ == CORR)
            || (lev->glyph == cmap_to_glyph(S_room) && lev->typ == ROOM)))
        goto full;
    if (gbuf_glyph[y][x] != lev->glyph)
        goto full;
#ifdef NLE_DISPLAY_VERIFY
    {
        int g0 = gbuf_glyph[y][x], c0 = gbuf_changed[y][x], s0 = gbuf_start[y], e0 = gbuf_stop[y];
        int lg0 = lev->glyph, wl0 = lev->waslit, sv0 = lev->seenv;
        newsym(x, y);
        if (g0 != gbuf_glyph[y][x] || c0 != gbuf_changed[y][x] || s0 != gbuf_start[y] || e0 != gbuf_stop[y]
            || lg0 != lev->glyph || wl0 != lev->waslit || sv0 != lev->seenv)
            fprintf(stderr, "NEWSYM_MISMATCH at %d,%d sense %d glyph %d->%d changed %d->%d bbox %d,%d->%d,%d lev %d->%d waslit %d->%d\\n",
                    x, y, s, g0, gbuf_glyph[y][x], c0, gbuf_changed[y][x], s0, e0, gbuf_start[y], gbuf_stop[y], lg0, lev->glyph, wl0, lev->waslit);
        long n = __atomic_add_fetch(&nh_ns_skip, 1, __ATOMIC_RELAXED);
        if ((n & ((1L << 22) - 1)) == 0) fprintf(stderr, "NEWSYM_STATS skip=%ld call=%ld\\n", n, __atomic_load_n(&nh_ns_call, __ATOMIC_RELAXED));
    }
#endif
    return;
 full:
#ifdef NLE_DISPLAY_VERIFY
    __atomic_add_fetch(&nh_ns_call, 1, __ATOMIC_RELAXED);
#endif
    newsym(x, y);
}
""")
rep('src/mon.c',"""movemon()
{
    register struct monst *mtmp, *nmtmp;
    register boolean somebody_can_move = FALSE;
""","""movemon()
{
    register struct monst *mtmp, *nmtmp;
    register boolean somebody_can_move = FALSE;

    nh_display_sense_recalc();
""")
rep('src/potion.c',"""    long old = Blinded;
    boolean u_could_see, can_see_now;
    const char *eyes;
""","""    long old = Blinded;
    boolean u_could_see, can_see_now;
    const char *eyes;

    nh_display_sense = 0; /* stale: sight changes; movemon() recomputes */
""")
rep('src/do_wear.c',"""Blindf_on(otmp)
struct obj *otmp;
{
    boolean already_blind = Blind, changed = FALSE;
""","""Blindf_on(otmp)
struct obj *otmp;
{
    boolean already_blind = Blind, changed = FALSE;

    nh_display_sense = 0; /* stale: sight changes; movemon() recomputes */
""")
rep('src/do_wear.c',"""Blindf_off(otmp)
struct obj *otmp;
{
    boolean was_blind = Blind, changed = FALSE;
""","""Blindf_off(otmp)
struct obj *otmp;
{
    boolean was_blind = Blind, changed = FALSE;

    nh_display_sense = 0; /* stale: sight changes; movemon() recomputes */
""")
rep('src/polyself.c',"""set_uasmon()
{
    struct permonst *mdat = &mons[u.umonnum];
""","""set_uasmon()
{
    struct permonst *mdat = &mons[u.umonnum];

    nh_display_sense = 0; /* stale: form changes eyes/infravision; movemon() recomputes */
""")
rep('src/monmove.c',"            newsym(omx, omy); /* update the old position */\n","            nh_newsym_moved(omx, omy); /* update the old position */\n")
rep('src/monmove.c',"""            } else
                newsym(mtmp->mx, mtmp->my);
        }
        if (nh_move_obj_at(mtmp->mx, mtmp->my) && mtmp->mcanmove) {""","""            } else
                nh_newsym_moved(mtmp->mx, mtmp->my);
        }
        if (nh_move_obj_at(mtmp->mx, mtmp->my) && mtmp->mcanmove) {""")
out=subprocess.run(['python3','tools/gen_ctx.py'],cwd=dst,capture_output=True,text=True); assert out.returncode==0, out.stderr[:400]
print('dv4 source written from',BASE)
