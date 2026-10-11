# mt1 = <base> + terrain lookup table in the neighbour query (mfndpos_masked): per-cell terrain predicates become one table load + bit tests.
import shutil,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'misc1'
dst=CS/'mt1/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
p=dst/'src/mon.c'; s=p.read_text()
def rep(old,new,count=1):
    global s; assert s.count(old)==count,(s.count(old),old[:80]); s=s.replace(old,new)
# table + init (pthread_once: lazy statics race the multithreaded env)
rep("/* Query-local capability state; no cached monster state survives the query. */","""/* Terrain facts as a pure function of (typ, rmflags): one table load per cell.
 * Level-dependent cases (arboreal STONE counts as TREE, Juiblex drawbridge-over-moat
 * is not a pool) are handled by two per-query booleans. */
#define MV_POOL_DB (1U << 23) /* DRAWBRIDGE_UP over moat: a pool except on the Juiblex level */
#include <pthread.h>
static unsigned int nh_terrain_lut[64][32];
static pthread_once_t nh_terrain_lut_once = PTHREAD_ONCE_INIT;
static void
nh_terrain_lut_init(void)
{
    int typ, fl;
    for (typ = 0; typ < 64; typ++)
        for (fl = 0; fl < 32; fl++) {
            unsigned int f = 0;
            int stwall = typ <= DBWALL;
            if (typ < POOL) f |= MV_ROCK;
            if (typ == TREE) f |= MV_TREE;
            if (!(stwall && (fl & W_NONPASSWALL))) f |= MV_PASSWALL;
            if (!((stwall || typ == TREE) && (fl & W_NONDIGGABLE))) f |= MV_DIG;
            if (typ == IRONBARS) f |= MV_BARS;
            if (fl & W_NONDIGGABLE) f |= MV_NONDIG;
            if (typ == DOOR) {
                f |= MV_DOOR;
                if (fl & D_CLOSED) f |= MV_CLOSED;
                if (fl & D_LOCKED) f |= MV_LOCKED;
                if (fl & ~D_BROKEN) f |= MV_DOOR_DIAG;
            }
            if (typ == POOL || typ == MOAT || typ == WATER) f |= MV_POOL;
            if (typ == DRAWBRIDGE_UP && (fl & DB_UNDER) == DB_MOAT) f |= MV_POOL_DB;
            if (typ == LAVAPOOL || (typ == DRAWBRIDGE_UP && (fl & DB_UNDER) == DB_LAVA)) f |= MV_LAVA;
            if (typ == ALTAR) f |= MV_ALTAR;
            nh_terrain_lut[typ][fl] = f;
        }
}
#define NH_TLUT(cell) (nh_terrain_lut[(unsigned char) (cell)->typ & 63][(cell)->rmflags])
/* IS_TREE()/nh_cell_dig() with the arboreal-level STONE rule */
static inline boolean nh_lut_tree(unsigned int tb, const struct rm *c, boolean arboreal)
{ return (tb & MV_TREE) != 0 || (arboreal && c->typ == STONE); }
static inline boolean nh_lut_dig(unsigned int tb, const struct rm *c, boolean arboreal)
{ return (arboreal && c->typ == STONE) ? !(c->rmflags & W_NONDIGGABLE) : (tb & MV_DIG) != 0; }

/* Query-local capability state; no cached monster state survives the query. */""")
rep("""    boolean rogue, sokoban, monseeu;
};""","""    boolean rogue, sokoban, monseeu, arboreal;
};""")
rep("""static inline boolean nh_mover_bad_rock(struct nh_mover *m, int x, int y)
{
    const struct rm *f = nh_move_cell(x, y);
    return (m->sokoban && (NH_SUMMARY(x, y).move_pile & 1U))
           || (IS_ROCK(TYP_AT(x, y))
               && !(tunnels(m->data) && !needspick(m->data) && nh_cell_dig(f))
               && !(passes_walls(m->data) && nh_cell_passwall(f, x, y)));
}""","""static inline boolean nh_mover_bad_rock(struct nh_mover *m, int x, int y)
{
    const struct rm *f = nh_move_cell(x, y);
    unsigned int tb = NH_TLUT(f);
    return (m->sokoban && (NH_SUMMARY(x, y).move_pile & 1U))
           || ((tb & MV_ROCK)
               && !(tunnels(m->data) && !needspick(m->data) && nh_lut_dig(tb, f, m->arboreal))
               && !(passes_walls(m->data) && (tb & MV_PASSWALL)));
}""")
rep("""    boolean poisongas_ok, in_poisongas;


    x = mon->mx;
    y = mon->my;
    origin = nh_move_cell(x, y);
    origin_typ = TYP_AT(x, y);
    mover.mon = mon; mover.data = mdat;
    mover.fog = mover.squeeze = mover.scary_immune = -1;
    mover.rogue = Is_rogue_level(&u.uz);
    mover.sokoban = Sokoban;""","""    boolean poisongas_ok, in_poisongas;
    boolean juiblex, origin_door, origin_door_diag;
    unsigned int tb;

    pthread_once(&nh_terrain_lut_once, nh_terrain_lut_init);
    x = mon->mx;
    y = mon->my;
    origin = nh_move_cell(x, y);
    origin_typ = TYP_AT(x, y);
    mover.mon = mon; mover.data = mdat;
    mover.fog = mover.squeeze = mover.scary_immune = -1;
    mover.rogue = Is_rogue_level(&u.uz);
    mover.sokoban = Sokoban;
    mover.arboreal = level.lflags.arboreal != 0;
    juiblex = Is_juiblex_level(&u.uz);
    origin_door = IS_DOOR(origin_typ);
    origin_door_diag = origin_door && (origin->rmflags & ~D_BROKEN);""")
rep("""            cell = nh_move_cell(nx, ny);
            cell_typ = TYP_AT(nx, ny);
            if (IS_ROCK(cell_typ)
                && !((flag & ALLOW_WALL) && nh_cell_passwall(cell, nx, ny))
                && !((IS_TREE(cell_typ) ? treeok : rockok) && nh_cell_dig(cell)))
                continue;
            /* KMH -- Added iron bars */
            if ((cell_typ == IRONBARS)
                && (!(flag & ALLOW_BARS)
                    || ((cell->rmflags & W_NONDIGGABLE)
                        && (dmgtype(mdat, AD_RUST)
                            || dmgtype(mdat, AD_CORR)))))
                continue;
            if (IS_DOOR(cell_typ) && !(amorphous(mdat) || nh_mover_fog(&mover))
                && (((cell->rmflags & D_CLOSED) && !(flag & OPENDOOR))
                    || ((cell->rmflags & D_LOCKED)
                        && !(flag & UNLOCKDOOR)))
                && !thrudoor)
                continue;""","""            cell = nh_move_cell(nx, ny);
            cell_typ = cell->typ;
            tb = NH_TLUT(cell);
            if ((tb & MV_ROCK)
                && !((flag & ALLOW_WALL) && (tb & MV_PASSWALL))
                && !((nh_lut_tree(tb, cell, mover.arboreal) ? treeok : rockok)
                     && nh_lut_dig(tb, cell, mover.arboreal)))
                continue;
            /* KMH -- Added iron bars */
            if ((tb & MV_BARS)
                && (!(flag & ALLOW_BARS)
                    || ((tb & MV_NONDIG)
                        && (dmgtype(mdat, AD_RUST)
                            || dmgtype(mdat, AD_CORR)))))
                continue;
            if ((tb & MV_DOOR) && !(amorphous(mdat) || nh_mover_fog(&mover))
                && (((tb & MV_CLOSED) && !(flag & OPENDOOR))
                    || ((tb & MV_LOCKED)
                        && !(flag & UNLOCKDOOR)))
                && !thrudoor)
                continue;""")
rep("""            if (nx != x && ny != y
                && (nodiag
                    || (IS_DOOR(origin_typ) && (origin->rmflags & ~D_BROKEN))
                    || (IS_DOOR(cell_typ) && (cell->rmflags & ~D_BROKEN))
                    || ((IS_DOOR(origin_typ) || IS_DOOR(cell_typ))
                        && mover.rogue)""","""            if (nx != x && ny != y
                && (nodiag
                    || origin_door_diag
                    || ((tb & MV_DOOR) && (tb & MV_DOOR_DIAG))
                    || ((origin_door || (tb & MV_DOOR))
                        && mover.rogue)""")
rep("""            if (((nh_cell_pool(cell, nx, ny) != 0) == wantpool || poolok)
                && (lavaok || !nh_cell_lava(cell, nx, ny))) {""","""            if ((((tb & MV_POOL) || (!juiblex && (tb & MV_POOL_DB))) == wantpool || poolok)
                && (lavaok || !(tb & MV_LAVA))) {""")
# verify twin: report instead of aborting the game
rep('''        panic("movement count/state mismatch at %d,%d", x, y);''','''        fprintf(stderr, "MFNDPOS_MISMATCH count turn=%ld at %d,%d\\n", moves, x, y);''')
rep('''            panic("movement ordered candidate mismatch at %d,%d", x, y);''','''            fprintf(stderr, "MFNDPOS_MISMATCH candidate turn=%ld at %d,%d i=%d\\n", moves, x, y, i);''')
p.write_text(s); print('mt1 source ready (base', BASE+')')
