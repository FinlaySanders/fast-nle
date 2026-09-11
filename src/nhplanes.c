/* fast-nle: per-cell lookup planes + compact floor-object index.
 *
 * The monster-AI hot loops (mfndpos, m_move's item search, onscary,
 * dog_goal, wipe_engr_at) each walked a level-wide list per candidate cell
 * or per monster per turn: the trap list (t_at), the engraving list
 * (engr_at), the object pile at a cell (sobj_at, cursed_object_at) and the
 * whole floor-object chain (fobj). Under a trained policy those walks were
 * over half of an env step and grew with the number of monsters, drops and
 * engravings. Each plane mirrors one list exactly and is maintained
 * write-through at every mutation site (see the nh_*_fix / nh_pile_*
 * calls), rebuilt at level entry next to nh_typ_sync(), and hard-compared
 * against the lists at every obs fill under NLE_PLANE_VERIFY. No RNG, no
 * behavior change: every consumer gets the answer the walk gave.
 * The engraving plane lives in engrave.c (head_engr is private there). */
#include "hack.h"

static unsigned char
nh_pile_bits_of(struct obj *o)
{
    unsigned char b = 0;

    if (o->otyp == BOULDER)
        b |= NH_PB_BOULDER;
    else if (o->otyp == SCR_SCARE_MONSTER)
        b |= NH_PB_SCARE;
    else if (o->otyp == CLOVE_OF_GARLIC)
        b |= NH_PB_GARLIC;
    if (o->cursed)
        b |= NH_PB_CURSED;
    return b;
}

void
nh_pile_recompute(int x, int y)
{
    struct obj *o;
    unsigned char b = 0;

    if (x < 0 || x >= COLNO || y < 0 || y >= ROWNO)
        return;
    for (o = level.objs[x][y]; o; o = o->nexthere)
        b |= nh_pile_bits_of(o);
    nh_pile_plane[x][y] = b;
}

void
nh_pile_touch_obj(struct obj *o)
{
    if (o && o->where == OBJ_FLOOR)
        nh_pile_recompute(o->ox, o->oy);
}

/* first trap in ftrap order at (x,y), exactly what t_at() walked to */
void
nh_trap_plane_fix(int x, int y)
{
    struct trap *t;

    if (x < 0 || x >= COLNO || y < 0 || y >= ROWNO)
        return;
    for (t = ftrap; t; t = t->ntrap)
        if (t->tx == x && t->ty == y)
            break;
    nh_trap_plane[x][y] = t;
}

void
nh_fobj_rebuild(void)
{
    struct obj *o;
    int n = 0;

    for (o = fobj; o; o = o->nobj) {
        if (n >= NH_FOBJ_CAP) {
            nh_fobj_n = -2; /* too many: consumers walk fobj directly */
            return;
        }
        nh_fobj_xy[n] = (unsigned short) (((o->ox & 0xff) << 8) | (o->oy & 0xff));
        nh_fobj_ptr[n] = o;
        n++;
    }
    nh_fobj_n = n;
}

/* the level's lists are being freed or replaced: drop every plane entry so
   no consumer can dereference a freed trap/engraving before the next sync
   (level generation calls t_at() long before vision_reset) */
void
nh_planes_clear(void)
{
    (void) memset((genericptr_t) nh_trap_plane, 0, sizeof nh_trap_plane);
    (void) memset((genericptr_t) nh_engr_plane, 0, sizeof nh_engr_plane);
    (void) memset((genericptr_t) nh_pile_plane, 0, sizeof nh_pile_plane);
    nh_fobj_n = -1;
}

/* full rebuild; called wherever nh_typ_sync() is (level creation, entry,
   restore) -- after monsters, objects, traps and engravings are in place */
void
nh_planes_sync(void)
{
    int x, y;
    struct trap *t;


    (void) memset((genericptr_t) nh_trap_plane, 0, sizeof nh_trap_plane);
    for (t = ftrap; t; t = t->ntrap)
        if (t->tx >= 0 && t->tx < COLNO && t->ty >= 0 && t->ty < ROWNO
            && !nh_trap_plane[t->tx][t->ty])
            nh_trap_plane[t->tx][t->ty] = t;
    nh_engr_plane_sync();
    for (x = 0; x < COLNO; x++)
        for (y = 0; y < ROWNO; y++)
            nh_pile_recompute(x, y);
    nh_fobj_n = -1;
}

void
nh_planes_verify(const char *where)
{
    int x, y, n;
    struct trap *t;
    struct obj *o;
    struct trap *et[COLNO][ROWNO]; /* stack: verify must not touch the allocator */

    (void) memset((genericptr_t) et, 0, sizeof et);
    for (t = ftrap; t; t = t->ntrap)
        if (t->tx >= 0 && t->tx < COLNO && t->ty >= 0 && t->ty < ROWNO
            && !et[t->tx][t->ty])
            et[t->tx][t->ty] = t;
    for (x = 0; x < COLNO; x++)
        for (y = 0; y < ROWNO; y++) {
            unsigned char b = 0;

            if (nh_trap_plane[x][y] != et[x][y])
                { fprintf(stderr, "PLANE: trap desync (%d,%d) [%s]\n", x, y, where); panic("trap plane desync (%d,%d) [%s]", x, y, where); }
            for (o = level.objs[x][y]; o; o = o->nexthere)
                b |= nh_pile_bits_of(o);
            if (nh_pile_plane[x][y] != b)
                { fprintf(stderr, "PLANE: pile desync (%d,%d) plane=%d real=%d [%s]\n", x, y, nh_pile_plane[x][y], b, where); panic("pile plane desync [%s]", where); }
        }
    nh_engr_plane_verify(where);
    if (nh_fobj_n >= 0) {
        for (n = 0, o = fobj; o; o = o->nobj, n++) {
            if (n >= nh_fobj_n || nh_fobj_ptr[n] != o
                || nh_fobj_xy[n]
                       != (unsigned short) (((o->ox & 0xff) << 8) | (o->oy & 0xff)))
                { fprintf(stderr, "PLANE: fobj index desync at %d of %d [%s]\n", n, nh_fobj_n, where); panic("fobj index desync [%s]", where); }
        }
        if (n != nh_fobj_n)
            { fprintf(stderr, "PLANE: fobj count desync %d vs %d [%s]\n", n, nh_fobj_n, where); panic("fobj count desync [%s]", where); }
    }
}
