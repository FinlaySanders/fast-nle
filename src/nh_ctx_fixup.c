/* fast-nle: handwritten fixups for ctx fields whose stock initializer took
 * the address of another global — those can't be expressed as memcpy
 * templates because the target now lives inside the ctx itself.
 * Called from nh_ctx_new() (generated), after templates are applied. */

#include "hack.h"

void
nh_ctx_fixup(struct nh_ctx *nh)
{
    /* decl.c: NEARDATA struct mkroom *subrooms = &rooms[MAXNROFROOMS + 1]; */
    nh->g_subrooms = &nh->g_rooms[MAXNROFROOMS + 1];
}
