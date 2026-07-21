#ifndef NLE_H
#define NLE_H

#define NLE_BZ2_TTYRECS

#include <stdio.h>

#include <fcontext/fcontext.h>

#include "nletypes.h"

/* TODO: Fix this. */
#undef SIG_RET_TYPE
#define SIG_RET_TYPE void (*)(int)

/*
 * Would like to annotate this with __thread, but that causes
 * the MacOS dynamic linker to not unload the library on dlclose().
 */
extern NH_THREAD_LOCAL nle_ctx_t *current_nle_ctx; /* defined in nle.c;
    NH_THREAD_LOCAL comes from nh_ctx_gen.h (via hack.h) */

/* fast-nle: per-env settings (field on nle_ctx_t). Consumers that used the
 * old process global just work; the ctx pointer is anchored at every API
 * entry before any settings access. */
#define settings (current_nle_ctx->settings)

nle_ctx_t *nle_start(nle_obs *, FILE *, nle_settings *);
nle_ctx_t *nle_step(nle_ctx_t *, nle_obs *);
nle_ctx_t *nle_obs_refresh(nle_ctx_t *, nle_obs *);
void nle_end(nle_ctx_t *);

#endif /* NLE_H */
