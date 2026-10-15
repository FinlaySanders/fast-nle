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
    memset(nh_track_near, 0, sizeof(nh_track_near));
}

static void
nh_track_adjust(coord *position, int delta)
{
    int x, y;
    /* v1.8: padded array, so the 3x3 window needs no clamps (track positions are hero positions: 0..COLNO-1, 0..ROWNO-1) */
    for (x = position->x; x <= position->x + 2; x++)
        for (y = position->y; y <= position->y + 2; y++)
            nh_track_near[x][y] += delta;
}

/* add to track */
void
settrack()
{
    int full = (utcnt == UTSZ);
    if (utcnt < UTSZ)
        utcnt++;
    if (utpnt == UTSZ)
        utpnt = 0;
    if (full)
        nh_track_adjust(&utrack[utpnt], -1);
    utrack[utpnt].x = u.ux;
    utrack[utpnt].y = u.uy;
    nh_track_adjust(&utrack[utpnt], 1);
    utpnt++;
}

coord *
gettrack(x, y)
register int x, y;
{
    register int cnt, ndist;
    register coord *tc;
    if (x >= 0 && x < COLNO && y >= 0 && y < ROWNO && !nh_track_near[x + 1][y + 1])
        return (coord *) 0;
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
