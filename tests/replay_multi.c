/* Multi-env replay: prove per-env isolation in ONE loaded libnethack.
 *
 * Modes (docs/DESIGN.md oracle (b), multi-env forms):
 *   --interleaved g1 g2 ...   envs run in PAIRS, stepped alternately
 *                             (A,B,A,B,...). Each env must still match its
 *                             golden hashes exactly — catches cross-env
 *                             state leakage even when both games "work".
 *   --shuffled g1 g2 ...      same pairing, but every nle_* call executes
 *                             on a rotating pool thread — catches any state
 *                             stashed in thread-locals other than the two
 *                             sanctioned ctx pointers.
 *
 * Build:
 *   cc -O2 -Iinclude tests/replay_multi.c -o build/replay_multi -lpthread
 * Run:
 *   build/replay_multi --interleaved build/libnethack.so build/dat \
 *       tests/goldens/*.golden
 */

#include <dlfcn.h>
#include <errno.h>
#include <limits.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "nletypes.h"

#define ROWNO 21
#define COLNO 80
#define MAPLEN (ROWNO * (COLNO - 1))
#define MAX_STEPS 131072

typedef void *(*nle_start_fn)(nle_obs *, FILE *, nle_settings *);
typedef void *(*nle_step_fn)(void *, nle_obs *);
typedef void (*nle_end_fn)(void *);
static nle_start_fn lib_start;
static nle_step_fn lib_step;
static nle_end_fn lib_end;

/* ------------------------------------------------------------------ */
/* golden file, fully parsed                                           */

struct golden {
    const char *path;
    unsigned long core, disp, lgen;
    int have_lgen;
    char options[32768];
    int fix_moon_phase;
    uint64_t init_hash;
    int n_steps;
    int *actions;      /* heap: MAX_STEPS entries (AutoAscend runs are long) */
    uint64_t *hashes;
};

static int
parse_golden(const char *path, struct golden *g)
{
    FILE *f = fopen(path, "r");
    char line[65536];

    if (!f) {
        fprintf(stderr, "cannot open %s: %s\n", path, strerror(errno));
        return 1;
    }
    memset(g, 0, sizeof(*g));
    g->path = path;
    g->actions = (int *) malloc(MAX_STEPS * sizeof(int));
    g->hashes = (uint64_t *) malloc(MAX_STEPS * sizeof(uint64_t));
    while (fgets(line, sizeof(line), f)) {
        if (line[0] == '#' || line[0] == '\n')
            continue;
        if (strncmp(line, "meta core=", 10) == 0) {
            sscanf(line, "meta core=%lu disp=%lu", &g->core, &g->disp);
        } else if (strncmp(line, "meta lgen=", 10) == 0) {
            g->have_lgen = (sscanf(line, "meta lgen=%lu", &g->lgen) == 1);
        } else if (strncmp(line, "meta options=", 13) == 0) {
            char *opts = line + 13;
            opts[strcspn(opts, "\n")] = 0;
            snprintf(g->options, sizeof(g->options), "%s", opts);
        } else if (strncmp(line, "meta fix_moon_phase=1", 21) == 0) {
            g->fix_moon_phase = 1;
        } else if (strncmp(line, "init ", 5) == 0) {
            g->init_hash = strtoull(line + 5, NULL, 16);
        } else if (strncmp(line, "step ", 5) == 0) {
            int action;
            char hash_hex[32];
            if (sscanf(line, "step %d %31s", &action, hash_hex) == 2
                && g->n_steps < MAX_STEPS) {
                g->actions[g->n_steps] = action;
                g->hashes[g->n_steps] = strtoull(hash_hex, NULL, 16);
                g->n_steps++;
            }
        }
    }
    fclose(f);
    return 0;
}

/* ------------------------------------------------------------------ */
/* one live env                                                        */

struct env {
    const struct golden *g;
    void *nle;
    nle_obs obs;
    short glyphs[MAPLEN];
    unsigned char chars[MAPLEN], colors[MAPLEN], specials[MAPLEN];
    long blstats[NLE_BLSTATS_SIZE];
    unsigned char message[NLE_MESSAGE_SIZE];
    int misc[NLE_MISC_SIZE];
    nle_settings settings;
    char vardir[PATH_MAX];
    int step_idx;
    int done;
    int failed;
};

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
env_hash(const struct env *e)
{
    uint64_t h = 14695981039346656037ULL;
    h = fnv1a64(e->glyphs, sizeof(e->glyphs), h);
    h = fnv1a64(e->chars, sizeof(e->chars), h);
    h = fnv1a64(e->colors, sizeof(e->colors), h);
    h = fnv1a64(e->specials, sizeof(e->specials), h);
    h = fnv1a64(e->blstats, sizeof(e->blstats), h);
    h = fnv1a64(e->message, sizeof(e->message), h);
    return h;
}

static void
touch(const char *dir, const char *name)
{
    char path[PATH_MAX];
    FILE *f;
    snprintf(path, sizeof(path), "%s/%s", dir, name);
    if ((f = fopen(path, "a")) != NULL)
        fclose(f);
}

static void
make_vardir(char *vardir, size_t sz, const char *nhdat_dir)
{
    char template[] = "/tmp/nle-multi-XXXXXX";
    char nhdat_abs[PATH_MAX], nhdat_src[PATH_MAX], nhdat_dst[PATH_MAX];
    char save[PATH_MAX];

    if (!mkdtemp(template)) {
        perror("mkdtemp");
        exit(2);
    }
    snprintf(vardir, sz, "%s", template);
    if (!realpath(nhdat_dir, nhdat_abs)) {
        fprintf(stderr, "realpath(%s): %s\n", nhdat_dir, strerror(errno));
        exit(2);
    }
    snprintf(nhdat_src, sizeof(nhdat_src), "%s/nhdat", nhdat_abs);
    snprintf(nhdat_dst, sizeof(nhdat_dst), "%s/nhdat", vardir);
    if (symlink(nhdat_src, nhdat_dst) != 0) {
        perror("symlink nhdat");
        exit(2);
    }
    touch(vardir, "perm");
    touch(vardir, "record");
    touch(vardir, "logfile");
    touch(vardir, "xlogfile");
    snprintf(save, sizeof(save), "%s/save", vardir);
    mkdir(save, 0755);
}

/* Work items executed (possibly) on pool threads. */
enum env_op { OP_START, OP_STEP, OP_END };

static void
env_exec(struct env *e, enum env_op op)
{
    uint64_t h, want;

    switch (op) {
    case OP_START:
        e->obs.glyphs = e->glyphs;
        e->obs.chars = e->chars;
        e->obs.colors = e->colors;
        e->obs.specials = e->specials;
        e->obs.blstats = e->blstats;
        e->obs.message = e->message;
        e->obs.misc = e->misc;
        memset(&e->settings, 0, sizeof(e->settings));
        e->settings.spawn_monsters = 1;
        snprintf(e->settings.options, sizeof(e->settings.options), "%s",
                 e->g->options);
        snprintf(e->settings.hackdir, sizeof(e->settings.hackdir), "%s",
                 e->vardir);
        e->settings.initial_seeds.seeds[0] = e->g->core;
        e->settings.initial_seeds.seeds[1] = e->g->disp;
        e->settings.initial_seeds.reseed = 0;
        e->settings.initial_seeds.use_init_seeds = true;
        e->settings.initial_seeds.lgen_seed = e->g->lgen;
        e->settings.initial_seeds.use_lgen_seed = e->g->have_lgen ? true : false;
        if (e->g->fix_moon_phase) {
            e->settings.fix_moon_phase = true;
            e->settings.time_seed = e->g->core + 1;
            e->settings.time_seed_is_set = true;
        }
        e->nle = lib_start(&e->obs, NULL, &e->settings);
        h = env_hash(e);
        if (h != e->g->init_hash) {
            fprintf(stderr, "%s: INIT HASH MISMATCH got %016llx want %016llx\n",
                    e->g->path, (unsigned long long) h,
                    (unsigned long long) e->g->init_hash);
            e->failed = 1;
            e->done = 1;
        }
        break;
    case OP_STEP:
        e->obs.action = e->g->actions[e->step_idx];
        lib_step(e->nle, &e->obs);
        h = env_hash(e);
        want = e->g->hashes[e->step_idx];
        e->step_idx++;
        /* No mismatch tolerance: the flickers once tolerated here were
         * wall-clock leaking through ubirthday; goldens are now recorded
         * with time(2) pinned, so replays must be exact. */
        if (h != want) {
            fprintf(stderr,
                    "%s: HASH MISMATCH at step %d: got %016llx want %016llx\n",
                    e->g->path, e->step_idx, (unsigned long long) h,
                    (unsigned long long) want);
            e->failed = 1;
            e->done = 1;
        }
        if (!e->failed && (e->obs.done || e->step_idx >= e->g->n_steps))
            e->done = 1;
        break;
    case OP_END:
        if (e->nle)
            lib_end(e->nle);
        e->nle = NULL;
        break;
    }
}

/* ------------------------------------------------------------------ */
/* thread pool: each submitted op runs on a rotating worker thread     */

#define N_WORKERS 4

struct pool {
    pthread_t threads[N_WORKERS];
    pthread_mutex_t mu;
    pthread_cond_t cv_work, cv_done;
    struct env *env;
    enum env_op op;
    int target; /* which worker must take the job; -1 = none pending */
    int done_flag;
    int shutdown;
};

static struct pool pool;

static void *
worker(void *arg)
{
    int me = (int) (intptr_t) arg;

    pthread_mutex_lock(&pool.mu);
    for (;;) {
        while (!pool.shutdown && pool.target != me)
            pthread_cond_wait(&pool.cv_work, &pool.mu);
        if (pool.shutdown)
            break;
        env_exec(pool.env, pool.op);
        pool.target = -1;
        pool.done_flag = 1;
        pthread_cond_broadcast(&pool.cv_done);
    }
    pthread_mutex_unlock(&pool.mu);
    return NULL;
}

static void
pool_run(struct env *e, enum env_op op, int worker_idx)
{
    pthread_mutex_lock(&pool.mu);
    pool.env = e;
    pool.op = op;
    pool.done_flag = 0;
    pool.target = worker_idx;
    pthread_cond_broadcast(&pool.cv_work);
    while (!pool.done_flag)
        pthread_cond_wait(&pool.cv_done, &pool.mu);
    pthread_mutex_unlock(&pool.mu);
}

static void
pool_init(void)
{
    int i;
    pthread_mutex_init(&pool.mu, NULL);
    pthread_cond_init(&pool.cv_work, NULL);
    pthread_cond_init(&pool.cv_done, NULL);
    pool.target = -1;
    for (i = 0; i < N_WORKERS; i++)
        pthread_create(&pool.threads[i], NULL, worker, (void *) (intptr_t) i);
}

static void
pool_shutdown(void)
{
    int i;
    pthread_mutex_lock(&pool.mu);
    pool.shutdown = 1;
    pthread_cond_broadcast(&pool.cv_work);
    pthread_mutex_unlock(&pool.mu);
    for (i = 0; i < N_WORKERS; i++)
        pthread_join(pool.threads[i], NULL);
}

/* ------------------------------------------------------------------ */

/* Run a pair of envs to completion, alternating steps. In shuffled mode
 * every operation lands on a rotating worker thread, so consecutive steps
 * of the SAME env execute on DIFFERENT threads. */
static int
run_pair(const struct golden *ga, const struct golden *gb,
         const char *nhdat_dir, int shuffled)
{
    static struct env ea, eb; /* zeroed below; big, keep off the stack */
    struct env *envs[2] = { &ea, &eb };
    int i, rr = 0, live;

    memset(&ea, 0, sizeof(ea));
    memset(&eb, 0, sizeof(eb));
    ea.g = ga;
    eb.g = gb;
    make_vardir(ea.vardir, sizeof(ea.vardir), nhdat_dir);
    if (gb)
        make_vardir(eb.vardir, sizeof(eb.vardir), nhdat_dir);

#define RUN(e, op) \
    (shuffled ? pool_run((e), (op), rr++ % N_WORKERS) : env_exec((e), (op)))

    RUN(&ea, OP_START);
    if (gb)
        RUN(&eb, OP_START);

    do {
        live = 0;
        for (i = 0; i < 2; i++) {
            struct env *e = envs[i];
            if (!e->g || e->done)
                continue;
            RUN(e, OP_STEP);
            if (!e->done)
                live++;
        }
    } while (live);

    RUN(&ea, OP_END);
    if (gb)
        RUN(&eb, OP_END);
#undef RUN

    for (i = 0; i < 2; i++) {
        struct env *e = envs[i];
        if (!e->g)
            continue;
        if (e->failed)
            return 1;
        printf("OK %s (%d steps, %s%s)\n", e->g->path, e->step_idx,
               gb ? "interleaved" : "solo", shuffled ? "+shuffled" : "");
    }
    return 0;
}

int
main(int argc, char **argv)
{
    int shuffled = 0, argi = 1, fails = 0, i;
    static struct golden gs[64];
    int n = 0;

    if (argc > 1 && strcmp(argv[1], "--interleaved") == 0) {
        argi = 2;
    } else if (argc > 1 && strcmp(argv[1], "--shuffled") == 0) {
        shuffled = 1;
        argi = 2;
    } else {
        fprintf(stderr,
                "usage: %s --interleaved|--shuffled <lib> <nhdat-dir> "
                "<golden>...\n",
                argv[0]);
        return 2;
    }
    if (argc < argi + 3)
        return 2;

    void *h = dlopen(argv[argi], RTLD_LAZY);
    if (!h) {
        fprintf(stderr, "dlopen: %s\n", dlerror());
        return 2;
    }
    lib_start = (nle_start_fn) dlsym(h, "nle_start");
    lib_step = (nle_step_fn) dlsym(h, "nle_step");
    lib_end = (nle_end_fn) dlsym(h, "nle_end");
    if (!lib_start || !lib_step || !lib_end) {
        fprintf(stderr, "dlsym: %s\n", dlerror());
        return 2;
    }

    for (i = argi + 2; i < argc && n < 64; i++)
        if (parse_golden(argv[i], &gs[n]) == 0)
            n++;

    if (shuffled)
        pool_init();

    for (i = 0; i < n; i += 2)
        fails += run_pair(&gs[i], (i + 1 < n) ? &gs[i + 1] : NULL,
                          argv[argi + 1], shuffled);

    if (shuffled)
        pool_shutdown();

    if (fails) {
        fprintf(stderr, "FAIL: %d pair(s) diverged\n", fails);
        return 1;
    }
    printf("OK: %d golden(s) replay identically under %s multi-env\n", n,
           shuffled ? "thread-shuffled" : "interleaved");
    return 0;
}
