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

    /* cmd.c: static const char *readchar_queue = ""; NULL would crash the
     * first *readchar_queue deref, so point it at the empty string. */
    nh->g_cmd_c_readchar_queue = "";

    /* cmd.c: static winid en_win = WIN_ERR; (stored as short in the ctx) */
    nh->g_cmd_c_en_win = (short) WIN_ERR;

    /* invent.c: static int lastinvnr = 51; static winid cached_pickinv_win
     * = WIN_ERR; */
    nh->g_invent_c_lastinvnr = 51;
    nh->g_invent_c_cached_pickinv_win = WIN_ERR;

    /* rnd.c: static unsigned seed = 1; (rn2_on_display_rng's non-ISAAC
     * fallback LCG must not start at 0) */
    nh->g_rnd_c_rn2disprng_seed = 1;

    /* options.c: static char fmtstr_doset[] = "%s%-15s [%s]   "; */
    strcpy(nh->g_options_c_fmtstr_doset, "%s%-15s [%s]   ");

    /* sp_lev.c: static aligntyp ralign[3] = {chaotic, neutral, lawful};
     * (values shuffled per special level) */
    nh->g_sp_lev_c_ralign[0] = AM_CHAOTIC;
    nh->g_sp_lev_c_ralign[1] = AM_NEUTRAL;
    nh->g_sp_lev_c_ralign[2] = AM_LAWFUL;
}
