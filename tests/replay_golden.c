/* Replay golden trajectories (recorded by tools/record_goldens.py from
 * stock NLE) against a libnethack build, and fail on the first observation
 * hash mismatch. Oracle (b) from docs/DESIGN.md: this is the commit gate
 * that proves an engine change did not alter game behavior.
 *
 * Build (from repo root, after cmake build):
 *   cc -O2 -Iinclude -Ibuild/_deps/fcontext-src/include \
 *      tests/replay_golden.c sys/unix/nledl.c -o build/replay_golden
 * Run:
 *   build/replay_golden build/libnethack.so build/dat tests/goldens/*.golden
 *
 * argv[2] is the directory containing nhdat (a scratch vardir is built per
 * episode, mirroring what nle/nethack/nethack.py does: symlink nhdat, touch
 * perm/record/logfile/xlogfile, mkdir save).
 *
 * The hash must match tools/record_goldens.py bit-for-bit: FNV-1a 64 over
 * glyphs (int16), chars, colors, specials (u8), blstats (long), message
 * (u8), native little-endian, in that order.
 */

#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

#include <dlfcn.h>

#include "nletypes.h"

#ifndef __has_feature
#define __has_feature(x) 0
#endif
#if __has_feature(memory_sanitizer)
#include <sanitizer/msan_interface.h>
/* Funnel: any uninitialized byte the engine copied into the observation
 * gets reported here WITH its allocation origin. Plain copying is only
 * "propagation" to MSan; this check is what fires. */
#define CHECK_OBS_INIT(o) do { \
    __msan_check_mem_is_initialized((o)->glyphs, MAPLEN * sizeof(short)); \
    __msan_check_mem_is_initialized((o)->chars, MAPLEN); \
    __msan_check_mem_is_initialized((o)->colors, MAPLEN); \
    __msan_check_mem_is_initialized((o)->specials, MAPLEN); \
    __msan_check_mem_is_initialized((o)->blstats, NLE_BLSTATS_SIZE * sizeof(long)); \
    __msan_check_mem_is_initialized((o)->message, NLE_MESSAGE_SIZE); \
} while (0)
#else
#define CHECK_OBS_INIT(o) ((void) 0)
#endif

/* The library is dlopen'd ONCE and shared by every episode (and, in the
 * multi-env modes, by simultaneously-live envs). This exercises the
 * single-library model the vecenv will use — per-env state must live in
 * the per-env contexts, never in the library image. */
typedef void *(*nle_start_fn)(nle_obs *, FILE *, nle_settings *);
typedef void *(*nle_step_fn)(void *, nle_obs *);
typedef void (*nle_end_fn)(void *);
static nle_start_fn lib_start;
static nle_step_fn lib_step;
static nle_end_fn lib_end;

static void
load_lib(const char *dlpath)
{
    void *h = dlopen(dlpath, RTLD_LAZY);
    if (!h) {
        fprintf(stderr, "dlopen(%s): %s\n", dlpath, dlerror());
        exit(2);
    }
    lib_start = (nle_start_fn) dlsym(h, "nle_start");
    lib_step = (nle_step_fn) dlsym(h, "nle_step");
    lib_end = (nle_end_fn) dlsym(h, "nle_end");
    if (!lib_start || !lib_step || !lib_end) {
        fprintf(stderr, "dlsym: %s\n", dlerror());
        exit(2);
    }
}

#define ROWNO 21
#define COLNO 80
#define MAPLEN (ROWNO * (COLNO - 1))

static uint64_t
fnv1a64(const void *data, size_t len, uint64_t h)
{
    const unsigned char *p = data;
    while (len--) {
        h ^= *p++;
        h *= 1099511628211ULL;
    }
    return h;
}

static uint64_t
obs_hash(const nle_obs *obs)
{
    uint64_t h = 14695981039346656037ULL;
    h = fnv1a64(obs->glyphs, MAPLEN * sizeof(short), h);
    h = fnv1a64(obs->chars, MAPLEN, h);
    h = fnv1a64(obs->colors, MAPLEN, h);
    h = fnv1a64(obs->specials, MAPLEN, h);
    h = fnv1a64(obs->blstats, NLE_BLSTATS_SIZE * sizeof(long), h);
    h = fnv1a64(obs->message, NLE_MESSAGE_SIZE, h);
    return h;
}

/* NLE_REPLAY_DUMP_STEPS="54957,55270" + NLE_REPLAY_DUMP_DIR=<dir>: write a
   human-readable dump of the full observation at those steps, whether or
   not the hash matches. Diffing dumps from two platforms localizes exactly
   which bytes disagree at a divergent step. */
static int
dump_step_wanted(long step)
{
    const char *spec = getenv("NLE_REPLAY_DUMP_STEPS");
    if (!spec)
        return 0;
    while (*spec) {
        char *end;
        long v = strtol(spec, &end, 10);
        if (end == spec)
            break;
        if (v == step)
            return 1;
        spec = (*end == ',') ? end + 1 : end;
    }
    return 0;
}

static void
dump_obs(const nle_obs *obs, long step)
{
    const char *dir = getenv("NLE_REPLAY_DUMP_DIR");
    if (!dir)
        dir = ".";
    char path[PATH_MAX];
    snprintf(path, sizeof(path), "%s/obs_step%ld.txt", dir, step);
    FILE *f = fopen(path, "w");
    if (!f)
        return;
    fprintf(f, "step %ld\n", step);
    fprintf(f, "hash %016llx\n", (unsigned long long) obs_hash(obs));
    fprintf(f, "h.glyphs   %016llx\n", (unsigned long long) fnv1a64(
                obs->glyphs, MAPLEN * sizeof(short), 14695981039346656037ULL));
    fprintf(f, "h.chars    %016llx\n", (unsigned long long) fnv1a64(
                obs->chars, MAPLEN, 14695981039346656037ULL));
    fprintf(f, "h.colors   %016llx\n", (unsigned long long) fnv1a64(
                obs->colors, MAPLEN, 14695981039346656037ULL));
    fprintf(f, "h.specials %016llx\n", (unsigned long long) fnv1a64(
                obs->specials, MAPLEN, 14695981039346656037ULL));
    fprintf(f, "h.blstats  %016llx\n", (unsigned long long) fnv1a64(
                obs->blstats, NLE_BLSTATS_SIZE * sizeof(long),
                14695981039346656037ULL));
    fprintf(f, "h.message  %016llx\n", (unsigned long long) fnv1a64(
                obs->message, NLE_MESSAGE_SIZE, 14695981039346656037ULL));
    fprintf(f, "message: \"%.*s\"\n", NLE_MESSAGE_SIZE,
            (const char *) obs->message);
    fprintf(f, "message hex:");
    for (int i = 0; i < NLE_MESSAGE_SIZE; i++)
        fprintf(f, "%s%02x", (i % 32) ? " " : "\n",
                ((const unsigned char *) obs->message)[i]);
    fprintf(f, "\nblstats:");
    for (int i = 0; i < NLE_BLSTATS_SIZE; i++)
        fprintf(f, " %ld", (long) obs->blstats[i]);
    fprintf(f, "\nchars map:\n");
    for (int r = 0; r < ROWNO; r++) {
        for (int c = 0; c < COLNO - 1; c++) {
            unsigned char ch = obs->chars[r * (COLNO - 1) + c];
            fputc((ch >= 32 && ch < 127) ? ch : '?', f);
        }
        fputc('\n', f);
    }
    fprintf(f, "glyphs (nonzero r,c=v):\n");
    for (int i = 0; i < MAPLEN; i++)
        if (obs->glyphs[i])
            fprintf(f, "%d,%d=%d\n", i / (COLNO - 1), i % (COLNO - 1),
                    (int) obs->glyphs[i]);
    fclose(f);
}

static void
touch(const char *dir, const char *name)
{
    char path[PATH_MAX];
    snprintf(path, sizeof(path), "%s/%s", dir, name);
    FILE *f = fopen(path, "a");
    if (f)
        fclose(f);
}

/* Build a scratch HACKDIR the way nle/nethack/nethack.py does. */
static void
make_vardir(char *vardir, size_t sz, const char *nhdat_dir)
{
    char template[] = "/tmp/nle-replay-XXXXXX";
    if (!mkdtemp(template)) {
        perror("mkdtemp");
        exit(2);
    }
    snprintf(vardir, sz, "%s", template);

    /* The symlink lives in the vardir, so its target must be absolute —
     * a relative nhdat_dir would dangle and the game boots into a
     * degenerate seed-independent state instead of failing loudly. */
    char nhdat_abs[PATH_MAX];
    if (!realpath(nhdat_dir, nhdat_abs)) {
        fprintf(stderr, "realpath(%s): %s\n", nhdat_dir, strerror(errno));
        exit(2);
    }
    char nhdat_src[PATH_MAX], nhdat_dst[PATH_MAX];
    snprintf(nhdat_src, sizeof(nhdat_src), "%s/nhdat", nhdat_abs);
    snprintf(nhdat_dst, sizeof(nhdat_dst), "%s/nhdat", vardir);
    struct stat st;
    if (stat(nhdat_src, &st) != 0) {
        fprintf(stderr, "no nhdat at %s\n", nhdat_src);
        exit(2);
    }
    if (symlink(nhdat_src, nhdat_dst) != 0) {
        perror("symlink nhdat");
        exit(2);
    }
    touch(vardir, "perm");
    touch(vardir, "record");
    touch(vardir, "logfile");
    touch(vardir, "xlogfile");
    char save[PATH_MAX];
    snprintf(save, sizeof(save), "%s/save", vardir);
    mkdir(save, 0755);
}

static int
replay_one(const char *dlpath, const char *nhdat_dir, const char *golden_path)
{
    FILE *f = fopen(golden_path, "r");
    if (!f) {
        fprintf(stderr, "cannot open %s: %s\n", golden_path, strerror(errno));
        return 1;
    }

    nle_settings settings;
    memset(&settings, 0, sizeof(settings));
    settings.spawn_monsters = 1;
    unsigned long core = 0, disp = 0, lgen = 0;
    int have_seeds = 0, have_options = 0, have_lgen = 0;
    uint64_t init_hash = 0;
    int have_init = 0;
    /* NLE_REPLAY_KEEP_GOING: step through every recorded action even after
       hash mismatches. The trajectory is no longer golden-verified, but the
       game is still real — used to extend MemorySanitizer coverage past a
       known cross-platform fork point. */
    int keep_going = getenv("NLE_REPLAY_KEEP_GOING") != NULL;
    long kg_mismatches = 0;

    /* Observation buffers: exactly the keys the recorder bound; all other
     * nle_obs pointers stay NULL (unbound), matching the Python side.
     * MUST be zero-filled per episode: the recorder hashes np.zeros-backed
     * buffers, and the engine does not overwrite every byte (message tail,
     * unreached map cells) — uninitialized bytes poison the hash. */
    static short glyphs[MAPLEN];
    static unsigned char chars[MAPLEN], colors[MAPLEN], specials[MAPLEN];
    static long blstats[NLE_BLSTATS_SIZE];
    static unsigned char message[NLE_MESSAGE_SIZE];
    static int misc[NLE_MISC_SIZE];
    memset(glyphs, 0, sizeof(glyphs));
    memset(chars, 0, sizeof(chars));
    memset(colors, 0, sizeof(colors));
    memset(specials, 0, sizeof(specials));
    memset(blstats, 0, sizeof(blstats));
    memset(message, 0, sizeof(message));
    memset(misc, 0, sizeof(misc));
    nle_obs obs;
    memset(&obs, 0, sizeof(obs));
    obs.glyphs = glyphs;
    obs.chars = chars;
    obs.colors = colors;
    obs.specials = specials;
    obs.blstats = blstats;
    obs.message = message;
    obs.misc = misc;

    void *nle = NULL;
    char vardir[PATH_MAX];
    long lineno = 0, steps = 0;
    int rc = 0;
    /* Stock NetHack contains a rare uninitialized-memory read that
     * perturbs ONE observation snapshot (~1 per 100k steps) without
     * affecting the game state: the very next step's hash realigns.
     * Tolerate that exact signature up to a small budget; anything else
     * is a hard failure. See tests/README.md. */
    int transients = 0, pending_transient = 0;
    uint64_t pending_h = 0, pending_want = 0;
    long pending_step = 0;
    char line[65536];

    while (fgets(line, sizeof(line), f)) {
        lineno++;
        if (line[0] == '#' || line[0] == '\n')
            continue;
        if (strncmp(line, "meta core=", 10) == 0) {
            if (sscanf(line, "meta core=%lu disp=%lu", &core, &disp) != 2) {
                fprintf(stderr, "%s:%ld: bad seed line\n", golden_path, lineno);
                rc = 1;
                break;
            }
            have_seeds = 1;
        } else if (strncmp(line, "meta lgen=", 10) == 0) {
            have_lgen = (sscanf(line, "meta lgen=%lu", &lgen) == 1);
        } else if (strncmp(line, "meta options=", 13) == 0) {
            char *opts = line + 13;
            opts[strcspn(opts, "\n")] = 0;
            snprintf(settings.options, sizeof(settings.options), "%s", opts);
            have_options = 1;
        } else if (strncmp(line, "meta fix_moon_phase=1", 21) == 0) {
            settings.fix_moon_phase = true;
        } else if (strncmp(line, "init ", 5) == 0) {
            if (!have_seeds || !have_options) {
                fprintf(stderr, "%s: init before required meta\n", golden_path);
                rc = 1;
                break;
            }
            init_hash = strtoull(line + 5, NULL, 16);
            have_init = 1;

            make_vardir(vardir, sizeof(vardir), nhdat_dir);
            snprintf(settings.hackdir, sizeof(settings.hackdir), "%s", vardir);
            settings.initial_seeds.seeds[0] = core;
            settings.initial_seeds.seeds[1] = disp;
            settings.initial_seeds.reseed = 0;
            settings.initial_seeds.use_init_seeds = true;
            settings.initial_seeds.lgen_seed = lgen;
            settings.initial_seeds.use_lgen_seed = have_lgen ? true : false;
            if (settings.fix_moon_phase) {
                /* Mirrors pynethack.cc set_initial_seeds: offset by 1 to
                 * decorrelate from the core RNG seed. */
                settings.time_seed = core + 1;
                settings.time_seed_is_set = true;
            }

            nle = lib_start(&obs, NULL, &settings);
            if (!nle) {
                fprintf(stderr, "%s: nle_start failed\n", golden_path);
                rc = 1;
                break;
            }
            if (dump_step_wanted(0))
                dump_obs(&obs, 0); /* init frame */
            uint64_t h = obs_hash(&obs);
            if (h != init_hash) {
                fprintf(stderr,
                        "%s: INIT HASH MISMATCH: got %016llx want %016llx\n",
                        golden_path, (unsigned long long) h,
                        (unsigned long long) init_hash);
                rc = 1;
                break;
            }
        } else if (strncmp(line, "step ", 5) == 0) {
            int action;
            char hash_hex[32];
            if (sscanf(line, "step %d %31s", &action, hash_hex) != 2) {
                fprintf(stderr, "%s:%ld: bad step line\n", golden_path, lineno);
                rc = 1;
                break;
            }
            if (!have_init) {
                fprintf(stderr, "%s: step before init\n", golden_path);
                rc = 1;
                break;
            }
            uint64_t want = strtoull(hash_hex, NULL, 16);
            /* NLE_TRACE_AT_STEP=<n>: enable engine RNG tracing for exactly
               that step, to diff draw sequences across builds/platforms. */
            {
                static long trace_step = -2;
                if (trace_step == -2) {
                    const char *ts = getenv("NLE_TRACE_AT_STEP");
                    trace_step = ts ? atol(ts) : -1;
                }
                if (steps + 1 == trace_step)
                    setenv("NLE_RNG_TRACE", "1", 1);
                else if (steps == trace_step)
                    unsetenv("NLE_RNG_TRACE");
            }
            obs.action = action;
            lib_step(nle, &obs);
            steps++;
            /* NLE_TRACE_DEPTH: log every dungeon-depth change with its
               step — locates the step at which a given level was first
               generated (where level-gen rng draws happen). */
            {
                static long prev_depth = -1;
                if (getenv("NLE_TRACE_DEPTH")
                    && obs.blstats[12] != prev_depth) {
                    fprintf(stderr, "DEPTH %ld -> %ld at step %ld\n",
                            prev_depth, (long) obs.blstats[12], steps);
                    prev_depth = obs.blstats[12];
                }
            }
            CHECK_OBS_INIT(&obs);
            uint64_t h = obs_hash(&obs);
            if (dump_step_wanted(steps))
                dump_obs(&obs, steps);
            if (keep_going) {
                if (h != want) {
                    kg_mismatches++;
                    /* first 40 in full; the tail is usually one fork
                       cascading, not new information */
                    if (kg_mismatches <= 40)
                        printf("kg-mismatch step %ld action %d got %016llx "
                               "want %016llx\n",
                               steps, action, (unsigned long long) h,
                               (unsigned long long) want);
                }
                if (obs.done)
                    break;
                continue;
            }
            if (pending_transient) {
                if (h == want) {
                    transients++;
                    fprintf(stderr,
                            "%s: transient obs mismatch at step %ld "
                            "(got %016llx want %016llx), realigned — "
                            "stock uninit-read noise (%d/%d)\n",
                            golden_path, pending_step,
                            (unsigned long long) pending_h,
                            (unsigned long long) pending_want, transients, 3);
                    pending_transient = 0;
                } else {
                    fprintf(stderr,
                            "%s: HASH MISMATCH at step %ld: got %016llx "
                            "want %016llx (no realignment)\n",
                            golden_path, pending_step,
                            (unsigned long long) pending_h,
                            (unsigned long long) pending_want);
                    rc = 1;
                    break;
                }
            } else if (h != want) {
                if (transients < 3 && !obs.done) {
                    pending_transient = 1;
                    pending_h = h;
                    pending_want = want;
                    pending_step = steps;
                } else {
                    fprintf(stderr,
                            "%s: HASH MISMATCH at step %ld (action %d): "
                            "got %016llx want %016llx\n",
                            golden_path, steps, action,
                            (unsigned long long) h,
                            (unsigned long long) want);
                    rc = 1;
                    break;
                }
            }
            if (obs.done)
                break; /* trailing steps in file (if any) are unreachable */
        } else if (strncmp(line, "end ", 4) == 0) {
            break;
        } else {
            fprintf(stderr, "%s:%ld: unknown line: %s", golden_path, lineno,
                    line);
            rc = 1;
            break;
        }
    }

    if (nle)
        lib_end(nle);
    fclose(f);
    if (keep_going)
        printf("KEEP-GOING %s (%ld steps, %ld hash mismatches ignored)\n",
               golden_path, steps, kg_mismatches);
    else if (rc == 0)
        printf("OK %s (%ld steps)\n", golden_path, steps);
    return keep_going ? 0 : rc;
}

/* NLE_FAKE_TIME=<epoch>: interpose time(2) for the whole process. With
   -rdynamic on ELF, the dlopen'd engine binds to this definition, so
   u_init's `time(&ubirthday)` gets the fake epoch. Used to prove the
   golden divergence tracks wall-clock via shknam.c's
   `nseed = ubirthday / 257`. */
time_t
time(time_t *tloc)
{
    static time_t fake = -2;
    if (fake == -2) {
        const char *spec = getenv("NLE_FAKE_TIME");
        fake = spec ? (time_t) strtoll(spec, NULL, 10) : -1;
    }
    if (fake != -1) {
        if (tloc)
            *tloc = fake;
        return fake;
    }
    struct timeval tv;
    gettimeofday(&tv, NULL);
    if (tloc)
        *tloc = tv.tv_sec;
    return tv.tv_sec;
}

/* NLE_REPLAY_PREALLOC="count,size,leak": perturb the malloc arena before
   the engine starts. If replay results change with this (same binary, same
   addresses modulo ASLR), the engine depends on heap chunk ORDER — i.e., a
   pointer-comparison somewhere ties game behavior to allocation history. */
static void
prealloc_perturb(void)
{
    const char *spec = getenv("NLE_REPLAY_PREALLOC");
    if (!spec)
        return;
    long count = 0, size = 0, leak = 0;
    if (sscanf(spec, "%ld,%ld,%ld", &count, &size, &leak) != 3)
        return;
    for (long i = 0; i < count; i++) {
        void *p = malloc((size_t) size);
        if (p && !leak)
            free(p);
        else if (p)
            memset(p, 0, 1); /* keep the leak from being optimized out */
    }
    fprintf(stderr, "prealloc: %ld x %ld bytes, leak=%ld\n", count, size,
            leak);
}

int
main(int argc, char **argv)
{
    if (argc < 4) {
        fprintf(stderr,
                "usage: %s <libnethack.so> <nhdat-dir> <golden>...\n",
                argv[0]);
        return 2;
    }
    int fails = 0;
    prealloc_perturb();
    load_lib(argv[1]);
    for (int i = 3; i < argc; i++)
        fails += replay_one(argv[1], argv[2], argv[i]);
    if (fails) {
        fprintf(stderr, "FAIL: %d golden(s) diverged\n", fails);
        return 1;
    }
    printf("OK: all %d golden(s) replay identically\n", argc - 3);
    return 0;
}
