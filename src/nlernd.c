#include "nlernd.h"
#include "hack.h"
#include "nle.h" /* per-env settings */
#include "isaac64.h"
#include <string.h>
#include <time.h>

/* See rnd.c: per-env RNG state accessors. */
extern isaac64_ctx *FDECL(nle_rng_state, (int));
extern int FDECL(whichrng, (int FDECL((*fn), (int) )));

/* See hacklib.c. */
extern int FDECL(set_random, (unsigned long, int FDECL((*fn), (int) )));

/* An appropriate version of this must always be provided in
   port-specific code somewhere. It returns a number suitable
   as seed for the random number generator */
extern unsigned long NDECL(sys_random_seed);


/*
 * Initializes the random number generator.
 * Originally in hacklib.c.
 */
void
init_random(int FDECL((*fn), (int) ))
{
    if (settings.initial_seeds.use_init_seeds) {
        set_random(settings.initial_seeds.seeds[whichrng(fn)], fn);
        has_strong_rngseed = settings.initial_seeds.reseed;
    } else {
        set_random(sys_random_seed(), fn);
    }
}

/* nle_seeds: per-env ctx field now (see globals.def) */

/* We define the number of dungeons explicitly here.
   NetHack works it out from the "dungeon.def" file,
   sadly after already sampling random numbers. This
   means you have to make sure that if the number of
   dungeons changes in the future then this needs to
   be kept in sync. */
#define NLE_NUM_DUNGEONS 8

/* Base LGEN RNG state, initialised via the seed &
   used in turn to sample seed values for the RNGs
   for each dungeon. */
#define nle_lgen_base (nh_cur->g_nlernd_c_lgen_base)

/* RNG States for level generation, one for each dungeon */
#define nle_lgen_state (nh_cur->g_nlernd_c_lgen_state)

/* State of the NetHack CORE RNG, used to remember what
   it was before we created the level and then restored
   after the level is ready. This allows for randomness
   during exploration / combat in-level. */
#define nle_core_state (nh_cur->g_nlernd_c_core_state)

/* Some flags to help manage the lgen seed */
#define lgen_initialised (nh_cur->g_nlernd_c_lgen_initialised)
#define lgen_active (nh_cur->g_nlernd_c_lgen_active)

/* Seeding function to initialise a fixed-level RNG state.
   Borrowed from init_isaac64 in NetHack's rnd.c */
void
nle_init_lgen_state(unsigned long seed, struct isaac64_ctx *state)
{
    unsigned char new_rng_state[sizeof seed];
    unsigned i;

    for (i = 0; i < sizeof seed; i++) {
        new_rng_state[i] = (unsigned char) (seed & 0xFF);
        seed >>= 8;
    }

    isaac64_init(state, new_rng_state, (int) sizeof seed);
}

void
nle_init_lgen_rng()
{
    if (settings.initial_seeds.use_lgen_seed) {
        /* initialise the base state which will be used
           for seeding the RNGs for the dungeons */
        nle_init_lgen_state(settings.initial_seeds.lgen_seed, &nle_lgen_base);

        /* generate a new RNG for each of the dungeons */
        for (int i = 0; i < NLE_NUM_DUNGEONS; i++)
            nle_init_lgen_state(isaac64_next_uint64(&nle_lgen_base),
                                &(nle_lgen_state[i]));

        lgen_initialised = true;
    } else {
        lgen_initialised = false;
    }
    /* Even if we didn't use it, stash the seed */
    nle_seeds[2] = settings.initial_seeds.lgen_seed;
}

void
nle_swap_to_lgen(int dungeon_num)
{
    if (lgen_initialised && !lgen_active) {
        int core_rng = whichrng(rn2);

        /* stash the current core state */
        nle_core_state = *nle_rng_state(core_rng);

        /* copy the current lgen state */
        *nle_rng_state(core_rng) = nle_lgen_state[dungeon_num];

        /* since we want nle_swap_to_lgen and swap_to_core to be
           called in the correct sequence we ignore subsequent
           calls to this function. */
        lgen_active = true;
    }
}

void
nle_swap_to_core(int dungeon_num)
{
    if (lgen_initialised && lgen_active) {
        int core_rng = whichrng(rn2);

        /* stash the current lgen state */
        nle_lgen_state[dungeon_num] = *nle_rng_state(core_rng);

        /* restore the core state */
        *nle_rng_state(core_rng) = nle_core_state;

        /* since we want nle_swap_to_lgen and swap_to_core to be
           called in the correct sequence we ignore subsequent
           calls to this function. */
        lgen_active = false;
    }
}

/*
 * Fill a struct tm with deterministic values derived from the
 * given seed using a private ISAAC64 RNG instance.
 */
void
nle_fill_fixed_tm(struct tm *tm, unsigned long seed)
{
    isaac64_ctx time_rng;
    unsigned char seed_bytes[sizeof(seed)];

    memcpy(seed_bytes, &seed, sizeof(seed_bytes));
    isaac64_init(&time_rng, seed_bytes, sizeof(seed_bytes));

    tm->tm_year = 100 + (int) isaac64_next_uint(&time_rng, 50);
    tm->tm_mon = (int) isaac64_next_uint(&time_rng, 12);
    tm->tm_mday = 1 + (int) isaac64_next_uint(&time_rng, 28);
    tm->tm_hour = (int) isaac64_next_uint(&time_rng, 24);
    tm->tm_wday = (int) isaac64_next_uint(&time_rng, 7);
    tm->tm_yday = tm->tm_mon * 30 + tm->tm_mday;
}

void
nle_set_seed(nle_ctx_t *nle, unsigned long core, unsigned long disp,
             boolean reseed, unsigned long lgen)
{
    /* Keep up to date with rnglist[] in rnd.c. */
    set_random(core, rn2);
    set_random(disp, rn2_on_display_rng);

    /* Determines logic in reseed_random() in hacklib.c. */
    has_strong_rngseed = reseed;

    nle_init_lgen_state(lgen, &nle_lgen_base);
    lgen_initialised = true;
    nle_seeds[2] = lgen;
};

void
nle_get_seed(nle_ctx_t *nle, unsigned long *core, unsigned long *disp,
             boolean *reseed, unsigned long *lgen, bool *lgen_in_use)
{
    *core = nle_seeds[0];
    *disp = nle_seeds[1];
    *reseed = has_strong_rngseed;
    *lgen = nle_seeds[2];
    *lgen_in_use = lgen_initialised;
}