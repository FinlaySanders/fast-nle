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
#include <unistd.h>

#include "nledl.h"

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
    unsigned long core = 0, disp = 0;
    int have_seeds = 0, have_options = 0;
    uint64_t init_hash = 0;
    int have_init = 0;

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

    nledl_ctx *nle = NULL;
    char vardir[PATH_MAX];
    long lineno = 0, steps = 0;
    int rc = 0;
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
            settings.initial_seeds.use_lgen_seed = false;
            if (settings.fix_moon_phase) {
                /* Mirrors pynethack.cc set_initial_seeds: offset by 1 to
                 * decorrelate from the core RNG seed. */
                settings.time_seed = core + 1;
                settings.time_seed_is_set = true;
            }

            nle = nle_start(dlpath, &obs, NULL, &settings);
            if (!nle) {
                fprintf(stderr, "%s: nle_start failed\n", golden_path);
                rc = 1;
                break;
            }
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
            obs.action = action;
            nle_step(nle, &obs);
            steps++;
            uint64_t h = obs_hash(&obs);
            if (h != want) {
                fprintf(stderr,
                        "%s: HASH MISMATCH at step %ld (action %d): "
                        "got %016llx want %016llx\n",
                        golden_path, steps, action, (unsigned long long) h,
                        (unsigned long long) want);
                rc = 1;
                break;
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
        nle_end(nle);
    fclose(f);
    if (rc == 0)
        printf("OK %s (%ld steps)\n", golden_path, steps);
    return rc;
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
    for (int i = 3; i < argc; i++)
        fails += replay_one(argv[1], argv[2], argv[i]);
    if (fails) {
        fprintf(stderr, "FAIL: %d golden(s) diverged\n", fails);
        return 1;
    }
    printf("OK: all %d golden(s) replay identically\n", argc - 3);
    return 0;
}
