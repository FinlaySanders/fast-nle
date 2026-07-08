/* Pin time(2) to $NLE_FAKE_TIME (unix epoch seconds) for the whole
 * process. Used when recording golden trajectories from STOCK NLE, whose
 * ubirthday = time(0) leaks wall-clock into gameplay (shopkeeper names,
 * used-item price parity, scroll labels — see nle_birthday_maybe_fixed()
 * in src/hacklib.c, which is the fast-nle engine's seeded equivalent).
 *
 * The recorder (tools/record_autoascend.py) sets NLE_FAKE_TIME to the
 * same epoch the fast-nle engine derives from time_seed, so a stock
 * recording and a fast-nle replay agree bit-for-bit.
 *
 * Build:
 *   macOS: clang -O2 -dynamiclib faketime_shim.c -o faketime_shim.dylib
 *   Linux: clang -O2 -shared -fPIC faketime_shim.c -o faketime_shim.so
 * Load via DYLD_INSERT_LIBRARIES / LD_PRELOAD.
 *
 * NLE_FAKE_TIME is re-read on every call (not cached) so one process can
 * record several seeds with different pinned epochs.
 */
#include <stdlib.h>
#include <time.h>

static time_t
resolve(time_t *tloc)
{
    const char *spec = getenv("NLE_FAKE_TIME");
    time_t v;

    if (spec) {
        v = (time_t) strtoll(spec, NULL, 10);
    } else {
        struct timespec ts;
        clock_gettime(CLOCK_REALTIME, &ts);
        v = ts.tv_sec;
    }
    if (tloc)
        *tloc = v;
    return v;
}

#ifdef __APPLE__
typedef struct interpose_s {
    const void *replacement;
    const void *original;
} interpose_t;

static time_t
fake_time(time_t *tloc)
{
    return resolve(tloc);
}

__attribute__((used, section("__DATA,__interpose")))
static const interpose_t interposers[] = {
    { (const void *) fake_time, (const void *) time },
};
#else
time_t
time(time_t *tloc)
{
    return resolve(tloc);
}
#endif
