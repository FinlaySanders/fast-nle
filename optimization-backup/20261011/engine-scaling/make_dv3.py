# dv3 = dv2 + flag invalidation in Blindf_on/Blindf_off/set_uasmon. dv2 = <base> + per-movemon display-quiet flag + nh_newsym_moved(): the two newsym() calls of a monster move skip newsym() when it would
# provably be a no-op; the hero-global half of newsym()'s out-of-sight checks is hoisted into nh_display_quiet (recomputed at movemon(),
# dropped by make_blinded()), leaving cansee / hero square / lit-memory fixup / screen-buffer compare per call.
import shutil,subprocess,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'mt7'
dst=CS/'dv3/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('tools/globals.def',"global | hot | int | nh_invwt_valid | | 0\n","global | hot | int | nh_invwt_valid | | 0\nglobal | hot | int | nh_display_quiet | | 0\n")
rep('include/extern.h',"E void FDECL(newsym, (int, int));\n","E void FDECL(newsym, (int, int));\nE void FDECL(nh_newsym_moved, (int, int));\nE void NDECL(nh_display_quiet_recalc);\n")
rep('src/display.c',"""#define gbuf_stop  (nh_cur->g_display_c_gbuf_stop)
""","""#define gbuf_stop  (nh_cur->g_display_c_gbuf_stop)

/* Hero-global half of newsym()'s out-of-sight branch: nothing on an out-of-sight square can be sensed and no level-wide
 * special case applies. Recomputed at movemon(), dropped by make_blinded(); everything else is checked per square. */
void
nh_display_quiet_recalc()
{
    nh_display_quiet = (!in_mklev && !iflags.use_background_glyph && !Is_rogue_level(&u.uz)
                        && !(Blind && Blind_telepat) && !Unblind_telepat && !Warn_of_mon && !Detect_monsters
                        && !(!Blind && Infravision) && !Warning
#ifdef HANGUPHANDLING
                        && !program_state.done_hup
#endif
                        ) ? 1 : 0;
}

/* newsym() for the square a monster just left or entered; skips when newsym() would provably change nothing. */
void
nh_newsym_moved(x, y)
int x, y;
{
    register struct rm *lev;
#ifdef NLE_DISPLAY_VERIFY
    static long nh_ns_skip, nh_ns_call;
#endif

    if (!nh_display_quiet || u.uswallow || Underwater || (x == u.ux && y == u.uy) || cansee(x, y)) {
#ifdef NLE_DISPLAY_VERIFY
        __atomic_add_fetch(&nh_ns_call, 1, __ATOMIC_RELAXED);
#endif
        newsym(x, y);
        return;
    }
    lev = &(NH_TILE(x, y));
    if ((!lev->waslit || (flags.dark_room && iflags.use_color))
        && ((lev->glyph == cmap_to_glyph(S_litcorr) && lev->typ == CORR)
            || (lev->glyph == cmap_to_glyph(S_room) && lev->typ == ROOM))) {
        newsym(x, y);
        return;
    }
    if (gbuf_glyph[y][x] != lev->glyph) {
        newsym(x, y);
        return;
    }
#ifdef NLE_DISPLAY_VERIFY
    {
        int g0 = gbuf_glyph[y][x], c0 = gbuf_changed[y][x], s0 = gbuf_start[y], e0 = gbuf_stop[y];
        int lg0 = lev->glyph, wl0 = lev->waslit, sv0 = lev->seenv;
        newsym(x, y);
        if (g0 != gbuf_glyph[y][x] || c0 != gbuf_changed[y][x] || s0 != gbuf_start[y] || e0 != gbuf_stop[y]
            || lg0 != lev->glyph || wl0 != lev->waslit || sv0 != lev->seenv)
            fprintf(stderr, "NEWSYM_MISMATCH at %d,%d glyph %d->%d changed %d->%d bbox %d,%d->%d,%d lev %d->%d waslit %d->%d\\n",
                    x, y, g0, gbuf_glyph[y][x], c0, gbuf_changed[y][x], s0, e0, gbuf_start[y], gbuf_stop[y], lg0, lev->glyph, wl0, lev->waslit);
        long n = __atomic_add_fetch(&nh_ns_skip, 1, __ATOMIC_RELAXED);
        if ((n & ((1L << 22) - 1)) == 0) fprintf(stderr, "NEWSYM_STATS skip=%ld call=%ld\\n", n, __atomic_load_n(&nh_ns_call, __ATOMIC_RELAXED));
    }
#endif
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

    nh_display_quiet_recalc();
""")
rep('src/potion.c',"""    long old = Blinded;
    boolean u_could_see, can_see_now;
    const char *eyes;
""","""    long old = Blinded;
    boolean u_could_see, can_see_now;
    const char *eyes;

    nh_display_quiet = 0; /* sensing may change with sight; movemon() recomputes */
""")
rep('src/monmove.c',"            newsym(omx, omy); /* update the old position */\n","            nh_newsym_moved(omx, omy); /* update the old position */\n")
rep('src/monmove.c',"""            } else
                newsym(mtmp->mx, mtmp->my);
        }
        if (nh_move_obj_at(mtmp->mx, mtmp->my) && mtmp->mcanmove) {""","""            } else
                nh_newsym_moved(mtmp->mx, mtmp->my);
        }
        if (nh_move_obj_at(mtmp->mx, mtmp->my) && mtmp->mcanmove) {""")
rep('src/do_wear.c',"""Blindf_on(otmp)
struct obj *otmp;
{
    boolean already_blind = Blind, changed = FALSE;
""","""Blindf_on(otmp)
struct obj *otmp;
{
    boolean already_blind = Blind, changed = FALSE;

    nh_display_quiet = 0; /* sight changes; movemon() recomputes */
""")
rep('src/do_wear.c',"""Blindf_off(otmp)
struct obj *otmp;
{
    boolean was_blind = Blind, changed = FALSE;
""","""Blindf_off(otmp)
struct obj *otmp;
{
    boolean was_blind = Blind, changed = FALSE;

    nh_display_quiet = 0; /* sight changes; movemon() recomputes */
""")
rep('src/polyself.c',"""set_uasmon()
{
    struct permonst *mdat = &mons[u.umonnum];
""","""set_uasmon()
{
    struct permonst *mdat = &mons[u.umonnum];

    nh_display_quiet = 0; /* form changes eyes/infravision; movemon() recomputes */
""")
out=subprocess.run(['python3','tools/gen_ctx.py'],cwd=dst,capture_output=True,text=True); assert out.returncode==0, out.stderr[:400]
print('dv3 source written from',BASE)
