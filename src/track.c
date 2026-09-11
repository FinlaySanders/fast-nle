/* NetHack 3.6	track.c	$NHDT-Date: 1432512769 2015/05/25 00:12:49 $  $NHDT-Branch: master $:$NHDT-Revision: 1.9 $ */
/* Copyright (c) Stichting Mathematisch Centrum, Amsterdam, 1985. */
/*-Copyright (c) Kenneth Lorber, Kensington, Maryland, 2015. */
/* NetHack may be freely redistributed.  See license for details. */
/* track.c - version 1.0.2 */

#include "hack.h"
#include "nh_ctx_files/track_c.h" /* utcnt, utpnt, utrack -> nh_cur */

#define UTSZ 50

void
initrack()
{
    utcnt = utpnt = 0;
    (void) memset((genericptr_t) nh_track_cnt, 0, sizeof nh_track_cnt);
    (void) memset((genericptr_t) nh_track_bits, 0, sizeof nh_track_bits);
}

/* add to track */
void
settrack()
{
    /* NLE: nh_track_cnt[x][y] = number of live ring entries at that cell,
       so gettrack() can reject cells with no entry in their 3x3 block. */
    if (utcnt == UTSZ) { /* ring full: the slot being reused is live */
        coord *old = &utrack[utpnt == UTSZ ? 0 : utpnt];
        if (nh_track_cnt[old->x][old->y] && !--nh_track_cnt[old->x][old->y])
            nh_track_bits[old->x] &= ~(1u << old->y);
    }
    if (utcnt < UTSZ)
        utcnt++;
    if (utpnt == UTSZ)
        utpnt = 0;
    utrack[utpnt].x = u.ux;
    utrack[utpnt].y = u.uy;
    nh_track_cnt[u.ux][u.uy]++;
    nh_track_bits[u.ux] |= 1u << u.uy; /* column mask: bit y = some entry at (x,y) */
    utpnt++;
}

coord *
gettrack(x, y)
register int x, y;
{
    register int cnt, ndist;
    register coord *tc;

    /* NLE: the loop below returns non-null only for an entry with
       distmin <= 1, i.e. inside the 3x3 block around (x,y); if no live
       entry lies there the answer is null without scanning (exact). */
    if (isok(x, y)) {
        unsigned cols = nh_track_bits[x];
        if (x > 0)
            cols |= nh_track_bits[x - 1];
        if (x < COLNO - 1)
            cols |= nh_track_bits[x + 1];
        /* rows y-1..y+1; y == 0 shifts to bits 0..1 (bit -1 does not exist) */
        if (!(cols & ((y > 0) ? (7u << (y - 1)) : 3u)))
            return (coord *) 0;
    }
    cnt = utcnt;
    for (tc = &utrack[utpnt]; cnt--;) {
        if (tc == utrack)
            tc = &utrack[UTSZ - 1];
        else
            tc--;
        ndist = distmin(x, y, tc->x, tc->y);

        /* if far away, skip track entries til we're closer */
        if (ndist > 2) {
            ndist -= 2; /* be careful due to extra decrement at top of loop */
            cnt -= ndist;
            if (cnt <= 0)
                return (coord *) 0; /* too far away, no matches possible */
            if (tc < &utrack[ndist])
                tc += (UTSZ - ndist);
            else
                tc -= ndist;
        } else if (ndist <= 1)
            return (ndist ? tc : 0);
    }
    return (coord *) 0;
}

/*track.c*/
