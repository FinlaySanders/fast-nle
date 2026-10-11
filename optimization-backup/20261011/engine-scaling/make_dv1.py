# dv1 = <base> + nh_newsym_moved(): the two newsym() calls a monster move issues skip the work when newsym() would provably be a no-op
# (square out of sight, nothing sensible there, no lit-memory fixup pending, screen buffer already shows the remembered glyph).
import shutil,subprocess,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'mt7'
dst=CS/'dv1/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('include/extern.h',"E void FDECL(newsym, (int, int));\n","E void FDECL(newsym, (int, int));\nE void FDECL(nh_newsym_moved, (int, int));\n")
rep('src/display.c',"""#define gbuf_stop  (nh_cur->g_display_c_gbuf_stop)
""","""#define gbuf_stop  (nh_cur->g_display_c_gbuf_stop)

/* newsym() for the square a monster just left or entered. Falls through to newsym() unless every branch newsym() could
 * take on an out-of-sight square is provably idle: nothing there can be sensed, no lit-memory fixup applies and the
 * screen buffer already shows the remembered glyph. */
void
nh_newsym_moved(x, y)
int x, y;
{
    register struct rm *lev;
    struct monst *mon;
#ifdef NLE_DISPLAY_VERIFY
    static long nh_ns_skip, nh_ns_call;
#endif

    if (in_mklev || u.uswallow || Underwater || (x == u.ux && y == u.uy) || cansee(x, y)
        || Is_rogue_level(&u.uz) || iflags.use_background_glyph
#ifdef HANGUPHANDLING
        || program_state.done_hup
#endif
        ) {
        newsym(x, y);
        return;
    }
    mon = m_at(x, y);
    if (mon && ((Blind && Blind_telepat) || Unblind_telepat || Warn_of_mon || Detect_monsters
                || (!Blind && Infravision) || Warning)) {
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
# the verify twin counts the fall-through calls too
rep('src/display.c',"""        ) {
        newsym(x, y);
        return;
    }
    mon = m_at(x, y);""","""        ) {
#ifdef NLE_DISPLAY_VERIFY
        __atomic_add_fetch(&nh_ns_call, 1, __ATOMIC_RELAXED);
#endif
        newsym(x, y);
        return;
    }
    mon = m_at(x, y);""")
rep('src/monmove.c',"            newsym(omx, omy); /* update the old position */\n","            nh_newsym_moved(omx, omy); /* update the old position */\n")
rep('src/monmove.c',"""            } else
                newsym(mtmp->mx, mtmp->my);
        }
        if (nh_move_obj_at(mtmp->mx, mtmp->my) && mtmp->mcanmove) {""","""            } else
                nh_newsym_moved(mtmp->mx, mtmp->my);
        }
        if (nh_move_obj_at(mtmp->mx, mtmp->my) && mtmp->mcanmove) {""")
print('dv1 source written from',BASE)
