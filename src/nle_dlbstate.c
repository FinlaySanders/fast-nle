/* fast-nle: per-env storage for dlb.c's open data-library handles.
 * dlb.c is also compiled into the standalone `dlb` utility (which keeps
 * plain statics via NLE_OBJECTS_GLOBAL) and cannot include hack.h, so
 * these tiny accessors bridge it to struct nh_ctx. Slot 54. */

#include "hack.h"
#include "dlb.h"

library *
nle_dlb_libs(void)
{
    if (!nh_cur->nh_lazy[54])
        nh_cur->nh_lazy[54] = calloc(4 /* MAX_LIBS */, sizeof(library));
    return (library *) nh_cur->nh_lazy[54];
}

boolean *
nle_dlb_initialized(void)
{
    return &nh_cur->g_dlb_c_initialized;
}
