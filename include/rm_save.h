#ifndef RM_SAVE_H
#define RM_SAVE_H
#include <limits.h>
_Static_assert(MAX_GLYPH <= SHRT_MAX, "glyph must fit signed short");
_Static_assert(sizeof(struct rm) == 6, "compact terrain cell");
_Static_assert(sizeof(struct rm_legacy) == 8, "saved terrain cell");
static inline void rm_to_legacy(struct rm_legacy *out,const struct rm *in) {
    memset(out,0,sizeof(*out));
    out->glyph = in->glyph;
    out->typ = in->typ;
    out->seenv = in->seenv;
    out->rmflags = in->rmflags;
    out->horizontal = in->horizontal;
    out->lit = in->lit;
    out->waslit = in->waslit;
    out->roomno = in->roomno;
    out->edge = in->edge;
    out->candig = in->candig;
 }
static inline void rm_from_legacy(struct rm *out,const struct rm_legacy *in) {
    out->glyph = in->glyph;
    out->typ = in->typ;
    out->seenv = in->seenv;
    out->rmflags = in->rmflags;
    out->horizontal = in->horizontal;
    out->lit = in->lit;
    out->waslit = in->waslit;
    out->roomno = in->roomno;
    out->edge = in->edge;
    out->candig = in->candig;
 }
#endif
