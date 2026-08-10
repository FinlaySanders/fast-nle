
#include <assert.h>
#include <string.h>
#include <sys/time.h>
#include <unistd.h>

#include <tmt.h>

#define NEED_VARARGS
#ifdef MONITOR_HEAP
#undef MONITOR_HEAP
#endif
#include "hack.h"

#include "dlb.h"

#include "nle.h"
#include "nlernd.h"

#ifdef NLE_BZ2_TTYRECS
#include <bzlib.h>
#endif

#ifndef __has_feature
#define __has_feature(x) 0 /* Compatibility with non-clang compilers. */
#endif

#if __has_feature(address_sanitizer) || defined(__SANITIZE_ADDRESS__)
#include <sanitizer/asan_interface.h>
#endif

#if __has_feature(address_sanitizer) || defined(__SANITIZE_ADDRESS__)
/* ASan redzones inflate frames ~4-8x; give the game coroutine room. */
#define STACK_SIZE (1 << 20) /* 1MiB under ASan */
#else
#define STACK_SIZE (1 << 18) /* 256KiB: 64KiB overflowed on deep call chains
                              * (throw/explode cascades in rich late states);
                              * multi-KB frames can leap the guard page and
                              * zero live frames -> ret-to-0 segv. Lazily
                              * committed, so cost is virtual only. */
#endif

static size_t
effective_stack_size(void)
{
    /* create_fcontext_stack() uses the first page as a guard page.
     *
     * On systems with 64KiB pages (e.g. some aarch64 kernels),
     * STACK_SIZE=64KiB results in a single page mapping, leaving no usable
     * stack space after the guard page. Ensure at least 2 pages (guard +
     * usable).
     */
    size_t stack_size = STACK_SIZE;
    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size > 0 && stack_size < 2u * (size_t) page_size) {
        stack_size = 2u * (size_t) page_size;
    }
    return stack_size;
}

extern int unixmain(int, char **);

signed char
vt_char_color_extract(TMTCHAR *c)
{
    /* We pick out the colors in the enum tmt_color_t. These match the order
     * found standard in IBM color graphics, and are the same order as those
     * found in src/color.h.  */

    /* TODO: We no longer need *signed* chars. Let's change the dtype of
     * tty_chars when we change the API next. */

    signed char color;

    if (c->a.fg == TMT_COLOR_DEFAULT) {
        /* Need to make a choice for default color. To stay compatible with
           NetHack, choose black for the "null glyph", gray otherwise. */
        color = (c->c == ' ') ? CLR_BLACK : CLR_GRAY; /* 0 or 7 */
    } else if (c->a.fg < TMT_COLOR_MAX) {
        color = c->a.fg - TMT_COLOR_BLACK + CLR_BLACK; /* TMT color offset. */
        if (c->a.bold) {
            color |= BRIGHT;
        }
    } else {
        fprintf(stderr, "Illegal color %d\n", (int) c->a.fg);
        color = CLR_GRAY;
    }

    /* The above is 0..15. For "reverse" colors (bg/fg swap), let's
     * use 16..31. */
    if (c->a.reverse) {
        color += CLR_MAX;
    }
    return color;
}

void
nle_vt_callback(tmt_msg_t m, TMT *vt, const void *a, void *p)
{
    const TMTSCREEN *s = tmt_screen(vt);
    const TMTPOINT *cur = tmt_cursor(vt);

    nle_ctx_t *nle = (nle_ctx_t *) p;
    if (!nle || !nle->observation) {
        return;
    }

    switch (m) {
    case TMT_MSG_BELL:
        break;

    case TMT_MSG_UPDATE:
        for (size_t r = 0; r < s->nline; r++) {
            if (s->lines[r]->dirty) {
                for (size_t c = 0; c < s->ncol; c++) {
                    size_t offset = (r * NLE_TERM_CO) + c;
                    TMTCHAR *tmt_c = &(s->lines[r]->chars[c]);

                    if (nle->observation->tty_chars) {
                        nle->observation->tty_chars[offset] = tmt_c->c;
                    }

                    if (nle->observation->tty_colors) {
                        nle->observation->tty_colors[offset] =
                            vt_char_color_extract(tmt_c);
                    }
                }
            }
        }
        tmt_clean(vt);
        break;

    case TMT_MSG_ANSWER:
        break;

    case TMT_MSG_MOVED:
        if (nle->observation->tty_cursor) {
            /* cast from size_t is safe from overflow, since r,c < 256 */
            nle->observation->tty_cursor[0] = (unsigned char) cur->r;
            nle->observation->tty_cursor[1] = (unsigned char) cur->c;
        }
        break;

    case TMT_MSG_CURSOR:
        break;
    }
}

nle_ctx_t *
init_nle(FILE *ttyrec, nle_obs *obs)
{
    /* calloc, not malloc: the struct carries per-env game-visible state
     * (rl_in_yn_function, rl_instance, ...) that stock kept in zero-init
     * statics; garbage here becomes garbage in the misc[] observation and
     * in winrl branches. */
    nle_ctx_t *nle = calloc(1, sizeof(nle_ctx_t));

    /* fast-nle: allocate this env's migrated game state and anchor the
     * context pointer before any game code can run. */
    nle->nh = nh_ctx_new();
    assert(nle->nh);
    nh_cur = nle->nh;

    /* Seed the per-env save/restore codec tables (they hold function
     * pointers, so they can't be zero-init or memcpy templates; the
     * helpers live in save.c / restore.c to reach the static codecs). */
    {
        extern void NDECL(nle_restoreprocs_init);
        extern void NDECL(nle_saveprocs_init);
        nle_restoreprocs_init();
        nle_saveprocs_init();
    }

    /* Set CO and LI to control ttyrec output size (used by tmt_open below).
     * They live in the migrated tc_gbl_data, so this cannot happen before
     * the ctx exists — it used to be done at the top of nle_start. */
    CO = NLE_TERM_CO;
    LI = NLE_TERM_LI;

    nle->ttyrec = ttyrec;

#ifdef NLE_BZ2_TTYRECS
    if (nle->ttyrec) {
        int bzerror;
        nle->ttyrec_bz2 = BZ2_bzWriteOpen(&bzerror, ttyrec, 9, 0, 0);
        assert(bzerror == BZ_OK);
    }
#endif

    nle->observation = obs;
    nle->tty_emit =
        (ttyrec != NULL)
        || (obs && (obs->tty_chars || obs->tty_colors || obs->tty_cursor));

    /* The vterminal only consumes bytes when a tty_* obs is bound or a
     * ttyrec is recorded (see nle_write's gate); its 24x80 attributed
     * screen was ~22% of all LL write misses per episode at 341 envs.
     * Create it lazily on first use instead. */
    nle->vterminal = NULL;
    if (nle->tty_emit) {
        TMT *vterminal = tmt_open(LI, CO, nle_vt_callback, nle, NULL, true);
        assert(vterminal);
        nle->vterminal = vterminal;
    }

    nle->outbuf_write_ptr = nle->outbuf;
    nle->outbuf_write_end = nle->outbuf + sizeof(nle->outbuf);

    return nle;
}

/* settings: per-env field on nle_ctx_t (accessor in nle.h) */

/* The NLE-layer per-env pointer, thread-local like nh_cur so a thread
 * pool can step any env from any thread. macOS caveat: __thread in a
 * dylib blocks dlclose() unloading (per-env leak under the Python
 * dlopen-copy model on dev boxes; the Linux target is unaffected). */
NH_THREAD_LOCAL nle_ctx_t *current_nle_ctx;

/* TODO: Consider copying the relevant parts of main() in unixmain.c. */
void
mainloop(fcontext_transfer_t ctx_transfer)
{
    current_nle_ctx->returncontext = ctx_transfer.ctx;
#if __has_feature(address_sanitizer) || defined(__SANITIZE_ADDRESS__)
    /* ASan isn't happy with fcontext's assembly.
     * See: https://bugs.llvm.org/show_bug.cgi?id=27627 and
     * https://github.com/boostorg/coroutine/issues/30#issuecomment-325578344
     * TODO: I don't understand why __sanitizer_(start/finish)_switch_fiber
     * doesn't work here.
     */
    fcontext_stack_t *stack = &current_nle_ctx->stack;
    ASAN_UNPOISON_MEMORY_REGION((char *) stack->sptr - stack->ssize,
                                stack->ssize);
#endif

    int len = strnlen(settings.hackdir, sizeof(settings.hackdir));

    if (len >= sizeof(settings.hackdir) - 1) {
        error("HACKDIR too long");
        return;
    }
    if (settings.hackdir[len - 1] != '/') {
        settings.hackdir[len] = '/';
        settings.hackdir[len + 1] = '\0';
    } else {
        settings.hackdir[len] = '\0';
    }

    char *scoreprefix = (settings.scoreprefix[0] != '\0')
                            ? settings.scoreprefix
                            : settings.hackdir;
    fqn_prefix[SYSCONFPREFIX] = settings.hackdir;
    fqn_prefix[CONFIGPREFIX] = settings.hackdir;
    fqn_prefix[HACKPREFIX] = settings.hackdir;
    fqn_prefix[SAVEPREFIX] = settings.hackdir;
    fqn_prefix[LEVELPREFIX] = settings.hackdir;
    fqn_prefix[BONESPREFIX] = settings.hackdir;
    fqn_prefix[SCOREPREFIX] = scoreprefix;
    fqn_prefix[LOCKPREFIX] = settings.hackdir;
    fqn_prefix[TROUBLEPREFIX] = settings.hackdir;
    fqn_prefix[DATAPREFIX] = settings.hackdir;

    char *argv[1] = { "nethack" };

    unixmain(1, argv);
}

boolean
write_ttyrec_data(void *buf, int length)
{
    nle_ctx_t *nle = current_nle_ctx;
#ifdef NLE_BZ2_TTYRECS
    int bzerror;
    BZ2_bzWrite(&bzerror, nle->ttyrec_bz2, buf, length);
    assert(bzerror == BZ_OK);
#else
    assert(fwrite(buf, 1, length, nle->ttyrec) == length);
#endif
    return TRUE;
}

boolean
write_ttyrec_header(int length, unsigned char channel)
{
    struct timeval tv;
    gettimeofday(&tv, NULL);

    int buffer[3];
    buffer[0] = tv.tv_sec;
    buffer[1] = tv.tv_usec;
    buffer[2] = length;

    /* Assumes little endianness */
    write_ttyrec_data(buffer, 3 * sizeof(int));
    write_ttyrec_data(&channel, 1);

    return TRUE;
}

/* win/tty only calls fflush(stdout). */
int
nle_fflush(FILE *stream)
{
    /* Only act on fflush(stdout). */
    if (stream != stdout) {
        fprintf(stderr,
                "Warning: nle_flush called with unexpected FILE pointer %p ",
                stream);
        return fflush(stream);
    }
    nle_ctx_t *nle = current_nle_ctx;

    ssize_t length = nle->outbuf_write_ptr - nle->outbuf;
    if (length == 0)
        return 0;

    if (nle->ttyrec) {
        write_ttyrec_header(length, 0);
        write_ttyrec_data(nle->outbuf, length);
    }

    nle_obs *obs = nle->observation;
    if (obs->tty_chars || obs->tty_colors || obs->tty_cursor) {
        if (!nle->vterminal) { /* tty obs bound mid-game: create on demand */
            nle->vterminal =
                tmt_open(LI, CO, nle_vt_callback, nle, NULL, true);
            assert(nle->vterminal);
        }
        tmt_write(nle->vterminal, nle->outbuf, length);
    }
    nle->outbuf_write_ptr = nle->outbuf;

#ifdef NLE_BZ2_TTYRECS
    return 0;
#else
    return nle->ttyrec ? fflush(nle->ttyrec) : 0;
#endif
}

/*
 * NetHack prints most of its output via putchar. We do our
 * own buffering.
 */
int
nle_putchar(int c)
{
    nle_ctx_t *nle = current_nle_ctx;
    /* No tty obs bound and no ttyrec: the bytes would be dropped at
     * nle_fflush anyway — skip the buffer write path entirely. Most
     * emitters are gated upstream at xputc/xputs via ttyDisplay->nle_emit;
     * this is the backstop for direct putchar overrides. */
    if (!nle->tty_emit)
        return c;
    if (nle->outbuf_write_ptr >= nle->outbuf_write_end) {
        nle_fflush(stdout);
    }
    *nle->outbuf_write_ptr++ = c;
    return c;
}

/*
 * Used in place of xputs from termcap.c. Not using
 * the tputs padding logic from tclib.c.
 */
void
nle_xputs(const char *str)
{
    int c;
    const char *p = str;

    if (!p || !*p)
        return;

    nle_ctx_t *nle = current_nle_ctx;
    if (nle && !nle->tty_emit)
        return;

    while ((c = *p++) != '\0') {
        nle_putchar(c);
    }
}

/* For win/tty to cache on ttyDisplay: whether escape bytes are consumed. */
int
nle_wants_tty_output(void)
{
    nle_ctx_t *nle = current_nle_ctx;
    return nle ? nle->tty_emit : 1;
}

/*
 * puts seems to be called only by tty_raw_print and tty_raw_print_bold.
 * We could probably override this in winrl instead.
 */
int
nle_puts(const char *str)
{
    if (!*str) /* At exit, an empty string gets printed in tty_raw_print. */
        return 0;

    int val = fputs(str, stdout);
    putc('\n', stdout); /* puts includes a newline, fputs doesn't */
    return val;
}

/* Necessary for initial observation struct. */
nle_obs *
nle_get_obs()
{
    return current_nle_ctx->observation;
}

void *
nle_yield(void *notdone)
{
    nle_fflush(stdout);
    /* Capture the ctx VALUE before suspending: the env resumed after the
     * jump is by definition this same env, but the thread may differ —
     * re-reading current_nle_ctx after the jump through a TLS address the
     * compiler cached pre-jump would hit the OLD thread's slot (whatever
     * env it moved on to). The value is stable; the slot is not. */
    nle_ctx_t *nle = current_nle_ctx;
    fcontext_transfer_t t = jump_fcontext(nle->returncontext, notdone);
#if __has_feature(address_sanitizer) || defined(__SANITIZE_ADDRESS__)
    fcontext_stack_t *stack = &nle->stack;
    ASAN_UNPOISON_MEMORY_REGION((char *) stack->sptr - stack->ssize,
                                stack->ssize);
#endif

    if (notdone)
        nle->returncontext = t.ctx;

    return t.data;
}

void
nethack_exit(int status)
{
    if (status) {
        fprintf(stderr, "NetHack exit with status %i\n", status);
    }
    nle_yield(NULL);
}

/* Called in really_done() in end.c to get "how". */
void
nle_done(int how)
{
    nle_ctx_t *nle = current_nle_ctx;
    if (how == DIED && !strncmp(killer.name, "the wrath of ", 13))
        how = NLE_HOW_WRATH;
    if (nle->observation->internal) {
        /* killer identity for death logging; slots 9,10 are never touched
           by fill_obs. name_to_mon on the killer string: monster deaths
           store their article-free name (KILLED_BY_AN), everything else
           parses to NON_PM. */
        int mnum = (how == DIED) ? name_to_mon(killer.name) : NON_PM;
        nle->observation->internal[9] = mnum + 1; /* 0 = not a monster */
        nle->observation->internal[10] = mnum >= 0 ? mons[mnum].mlevel : 0;
    }
    nle->observation->how_done = how;
}

char *
nle_ttyrecname()
{
    return settings.ttyrecname;
}

int
nle_spawn_monsters()
{
    return settings.spawn_monsters;
}

int
nle_underfoot_glyphs()
{
    return settings.underfoot_glyphs;
}

char *
nle_getenv(const char *name)
{
    if (strcmp(name, "TERM") == 0) {
        return "ansi";
    }
    if (strcmp(name, "NETHACKOPTIONS") == 0) {
        return settings.options;
    }
    /* Don't return anything for "SHOPTYPE" or "SPLEVTYPE". */
    return (char *) 0;
}

FILE *
nle_fopen_wizkit_file()
{
    size_t len = strnlen(settings.wizkit, sizeof(settings.wizkit));
    if (!len) {
        return (FILE *) 0;
    }
    return fmemopen(settings.wizkit, len, "r");
}

nle_ctx_t *
nle_start(nle_obs *obs, FILE *ttyrec, nle_settings *settings_p)
{
    /* CO/LI setup moved into init_nle: they live in the migrated
     * tc_gbl_data and need the ctx allocated first. */
    nle_ctx_t *nle = init_nle(ttyrec, obs);

    /* Anchor the ctx BEFORE the settings copy: `settings` is a per-env
     * field reached through current_nle_ctx now. */
    current_nle_ctx = nle;
    settings = *settings_p;

    /* Initialise the level generation RNG */
    nle_init_lgen_rng();

    nle->stack = create_fcontext_stack(effective_stack_size());
    nle->generatorcontext =
        make_fcontext(nle->stack.sptr, nle->stack.ssize, mainloop);

    current_nle_ctx = nle;
    fcontext_transfer_t t = jump_fcontext(nle->generatorcontext, NULL);
    nle->generatorcontext = t.ctx;
    nle->done = (t.data == NULL);
    obs->done = nle->done;

    if (nle->ttyrec) {
        if (obs->blstats) {
            /* See comment in `nle_step`. We record the score in line with
             * the state to ensure s,r -> a -> s', r'. These lines ensure
             * we don't skip the first reward. */
            write_ttyrec_header(4, 2);
            write_ttyrec_data(&obs->blstats[9], 4);
        }
    }

    return nle;
}

/* 1 if the hero is inside a shop room (any tile, merchandise or not).
 * Public information: the shopkeeper greets the player on entry. */
int
nle_inside_shop(nle_ctx_t *nle)
{
    struct nh_ctx *saved = nh_cur;
    int r;

    nh_cur = (struct nh_ctx *) nle->nh;
    r = inside_shop(u.ux, u.uy) ? 1 : 0;
    nh_cur = saved;
    return r;
}

/* Terrain glyph under the hero, ignoring any objects piled on it. The map
 * observation shows only the TOP item of a tile (underfoot_glyphs), so a
 * scroll dropped on a staircase hides the staircase; callers that gate on
 * terrain need this. Shuffling is irrelevant for cmap glyphs. Reads only. */
int
nle_terrain_underfoot(nle_ctx_t *nle)
{
    struct nh_ctx *saved = nh_cur;
    int g;

    nh_cur = (struct nh_ctx *) nle->nh;
    g = back_to_glyph(u.ux, u.uy);
    nh_cur = saved;
    return g;
}

/* Shop state under the hero: -1 not standing on shop goods, otherwise the
 * asking price of the unpaid item there (0 if it carries no charge). The
 * shopkeeper quotes this to the player on arrival, so it is public
 * information, not a peek at hidden state. Reads only; no RNG. */
long
nle_shop_price(nle_ctx_t *nle)
{
    struct nh_ctx *saved = nh_cur;
    struct obj *otmp;
    long price = -1L;

    nh_cur = (struct nh_ctx *) nle->nh;
    if (shop_object(u.ux, u.uy) != 0) {
        /* PICKUP takes the WHOLE pile (select-all), so the caller needs the
         * total bill, not the price of whichever item happens to be on top. */
        price = 0L;
        for (otmp = level.objs[u.ux][u.uy]; otmp; otmp = otmp->nexthere) {
            int nochrg = -1;
            long cost;
            if (otmp->oclass == COIN_CLASS)
                continue;
            cost = get_cost_of_shop_item(otmp, &nochrg);
            if (nochrg == 0)
                price += cost;
        }
    }
    nh_cur = saved;
    return price;
}

/* Tippable containers (chest/box/bag) on the hero's tile. Presence is
 * public (the container renders as its object glyph); known-empty and
 * known-locked are gated on cknown/lknown, which track what the HERO has
 * learned, so this leaks no hidden state. A tip of a locked box costs a
 * real turn for "It's locked." and sets lknown; kicking the lock open
 * clears olocked and the container counts again. Reads only; no RNG. */
/* Any FOOD_CLASS object in the pile on the hero's tile (corpses included).
 * Presence is public (pile renders as object glyphs). Reads only; no RNG. */
int
nle_food_underfoot(nle_ctx_t *nle)
{
    struct nh_ctx *saved = nh_cur;
    struct obj *otmp;
    int n = 0;

    nh_cur = (struct nh_ctx *) nle->nh;
    for (otmp = level.objs[u.ux][u.uy]; otmp; otmp = otmp->nexthere)
        if (otmp->oclass == FOOD_CLASS) { n = 1; break; }
    nh_cur = saved;
    return n;
}

/* AC granted by the protection spell (u.uspellprot); decays on its own
 * clock. Reads only; no RNG. */
int
nle_spellprot(nle_ctx_t *nle)
{
    struct nh_ctx *saved = nh_cur;
    int n;

    nh_cur = (struct nh_ctx *) nle->nh;
    n = (int) u.uspellprot;
    nh_cur = saved;
    return n;
}

/* Carried weight and capacity (inv_weight is relative to capacity in the
 * engine: it returns wc-adjusted; export both raw). Reads only; no RNG. */
void
nle_weight(nle_ctx_t *nle, int *wt, int *cap)
{
    struct nh_ctx *saved = nh_cur;

    nh_cur = (struct nh_ctx *) nle->nh;
    *cap = weight_cap();
    *wt = inv_weight() + *cap;   /* inv_weight() returns carried - cap */
    nh_cur = saved;
}

int
nle_container_at(nle_ctx_t *nle)
{
    struct nh_ctx *saved = nh_cur;
    struct obj *otmp;
    int n = 0;

    nh_cur = (struct nh_ctx *) nle->nh;
    for (otmp = level.objs[u.ux][u.uy]; otmp; otmp = otmp->nexthere) {
        if (!Is_container(otmp))
            continue;
        if (otmp->cknown && !otmp->cobj)
            continue;   /* seen inside; it was/is empty */
        if (otmp->lknown && otmp->olocked)
            continue;   /* known locked: tip would waste the turn */
        n++;
    }
    nh_cur = saved;
    return n;
}

/* Known-spell summary for the obs: sp_id, level, fail%% (the '+' menu's
 * column) per slot. Interface-public; reads only; no RNG. */
int
nle_spells(nle, ids, levs, fails, max)
nle_ctx_t *nle;
short *ids;
signed char *levs, *fails;
int max;
{
    struct nh_ctx *saved = nh_cur;
    int n;
    extern int nle_spell_summary();

    nh_cur = (struct nh_ctx *) nle->nh;
    n = nle_spell_summary(ids, levs, fails, max);
    nh_cur = saved;
    return n;
}

/* Slot-faithful spell summary with retention (sp_know turns, 0 = forgotten).
 * Slot index == cast menu letter. Interface-public; reads only; no RNG. */
int
nle_spells2(nle, ids, levs, fails, knows, max)
nle_ctx_t *nle;
short *ids;
signed char *levs, *fails;
int *knows;
int max;
{
    struct nh_ctx *saved = nh_cur;
    int n;
    extern int nle_spell_summary2();

    nh_cur = (struct nh_ctx *) nle->nh;
    n = nle_spell_summary2(ids, levs, fails, knows, max);
    nh_cur = saved;
    return n;
}

/* 1 if the engine would refuse a cast for free before spell selection
 * (stun, chant, freehand, too-weak).  RL-mask gate; pure predicate. */
int
nle_cast_blocked2(nle)
nle_ctx_t *nle;
{
    struct nh_ctx *saved = nh_cur;
    int r;
    extern int nle_cast_blocked();

    nh_cur = (struct nh_ctx *) nle->nh;
    r = nle_cast_blocked();
    nh_cur = saved;
    return r;
}

/* 1 if a peaceful or tame monster occupies (x,y). Farlook names attitude
 * for any monster the hero can see, so this is interface-public; callers
 * only query positions where a visible monster glyph exists. Reads only;
 * no RNG. */
int
nle_peaceful_at(nle_ctx_t *nle, int x, int y)
{
    struct nh_ctx *saved = nh_cur;
    struct monst *mtmp;
    int r = 0;

    nh_cur = (struct nh_ctx *) nle->nh;
    if (x >= 1 && x < COLNO && y >= 0 && y < ROWNO) {
        mtmp = m_at(x, y);
        if (mtmp && (mtmp->mpeaceful || mtmp->mtame))
            r = 1;
    }
    nh_cur = saved;
    return r;
}

/* Number of object types the hero has discovered (the discoveries list,
 * including born-known types — callers difference per episode). Reads only;
 * no RNG. */
int
nle_discoveries(nle_ctx_t *nle)
{
    struct nh_ctx *saved = nh_cur;
    int i, n = 0;

    nh_cur = (struct nh_ctx *) nle->nh;
    for (i = 1; i < NUM_OBJECTS; i++)
        if (objects[i].oc_name_known)
            n++;
    nh_cur = saved;
    return n;
}

/* Hero tiles walked during the last nle_step, oldest first, as x,y pairs.
 * Multi-move commands (rush, occupations) resolve many moves inside one step
 * and lookaround() turns corners, so the caller cannot reconstruct the path
 * from the endpoints. Returns the number of tiles written (<= max). */
int
nle_path_drain(nle_ctx_t *nle, short *out, int max)
{
    struct nh_ctx *nh = (struct nh_ctx *) nle->nh;
    int n = nh->g_nle_hero_path_n;
    if (n > max) n = max;
    for (int i = 0; i < 2 * n; i++) out[i] = nh->g_nle_hero_path[i];
    /* drain semantics: the caller's logical step may span several nle_step
     * calls (prompt drains, macro keys), so clearing per nle_step would wipe
     * the walked path before the caller reads it. Clear on read instead. */
    nh->g_nle_hero_path_n = 0;
    return n;
}

/* Out-of-band full observation export: runs the standard fill against the
 * current game state without stepping. Pairs with nle_obs.partial — a
 * wrapper that sends several keys per logical step keeps partial set (cheap
 * misc/message fills on intermediate keys) and pulls one full observation
 * here at the step boundary. */
nle_ctx_t *
nle_obs_refresh(nle_ctx_t *nle, nle_obs *obs)
{
    extern void nle_rl_fill_obs(nle_obs *);
    char p = obs->partial;
    current_nle_ctx = nle;
    nh_cur = (struct nh_ctx *) nle->nh;
    obs->partial = 0;
    nle_rl_fill_obs(obs);
    obs->partial = p;
    return nle;
}

nle_ctx_t *
nle_step(nle_ctx_t *nle, nle_obs *obs)
{
    current_nle_ctx = nle;
    nh_cur = (struct nh_ctx *) nle->nh;
    nle->observation = obs;
    /* tty gating tracks the CURRENT step's bindings, not nle_start's:
     * the C API lets each step pass a different obs, so tty_* fields can
     * appear/vanish mid-game. Keep ttyDisplay's cached copy in sync. */
    {
        char emit = (char) ((nle->ttyrec != NULL)
                            || (obs
                                && (obs->tty_chars || obs->tty_colors
                                    || obs->tty_cursor)));
        if (emit != nle->tty_emit) {
            extern void nle_refresh_tty_emit(void);
            nle->tty_emit = emit;
            nle_refresh_tty_emit();
        }
    }
    if (nle->ttyrec) {
        write_ttyrec_header(1, 1);
        write_ttyrec_data(&obs->action, 1);
    }
    fcontext_transfer_t t = jump_fcontext(nle->generatorcontext, obs);
    nle->generatorcontext = t.ctx;
    nle->done = (t.data == NULL);
    obs->done = nle->done;

    if (nle->ttyrec) {
        /* NLE ttyrec version 3 stores the action and in-game score in
         * different channels of the ttyrec. These channels are:
         *  - 0: the terminal instructions (classic ttyrec)
         *  - 1: the keypress/action (1 byte)
         *  - 2: the in-game score (4 bytes)
         *
         * We could either the note the in-game score every time we flush the
         * terminal instructions to screen, (eg writing [ 0 2 0 2 <step> 1 0 2
         * <step> 1 ]) or we can note it _just_ before resuming the game,
         * assuming no chicanery has happened to the score after it is written
         * to the array `blstats`, (eg writing [ 0 2 <step> 1 0 2 <step> 1 0 2
         * <step> ]). We chose the latter for compression & simplicity
         * reasons.
         *
         * Note: blstats[9] == botl_score which is used for score/reward fns.
         * see winrl.cc
         */
        if (obs->blstats) {
            write_ttyrec_header(4, 2);
            write_ttyrec_data(&obs->blstats[9], 4);
        }
    }

    return nle;
}

void
nle_end(nle_ctx_t *nle)
{
    /* Anchor this env before teardown: freedynamicdata, dlb_cleanup and
     * nle_fflush all reach state through the thread-locals, and nle_end
     * may run on a thread whose last nle_* call was for a DIFFERENT env
     * (vec close from a main thread, or a truncation reset right after
     * stepping a neighbor). Without this, teardown frees the wrong env's
     * live game state. */
    current_nle_ctx = nle;
    nh_cur = (struct nh_ctx *) nle->nh;

    if (!nle->done) {
        /* Reset without closing nethack. Need free memory, etc.
         * this is what nh_terminate in end.c does. I hope it's enough. */
        if (!program_state.panicking) {
            freedynamicdata();
            dlb_cleanup();
        }
    }
    nle_fflush(stdout);

#ifdef NLE_BZ2_TTYRECS
    if (nle->ttyrec) {
        int bzerror;
        BZ2_bzWriteClose(&bzerror, nle->ttyrec_bz2, 0, NULL, NULL);
        assert(bzerror == BZ_OK);
    }
#endif

    if (nle->vterminal)
        tmt_close(nle->vterminal);

    destroy_fcontext_stack(&nle->stack);
    nh_cur = (struct nh_ctx *) 0;
    current_nle_ctx = (nle_ctx_t *) 0;
    nh_ctx_free((struct nh_ctx *) nle->nh);
    free(nle);
}

/* From unixtty.c */
/* fatal error */
/*VARARGS1*/
void error
VA_DECL(const char *, s)
{
    VA_START(s);
    VA_INIT(s, const char *);

    if (iflags.window_inited)
        exit_nhwindows((char *) 0); /* for tty, will call settty() */

    fprintf(stderr, s, VA_ARGS);
    fprintf(stderr, "\n");
    VA_END();
    nethack_exit(EXIT_FAILURE);
}

/* From unixtty.c */
char erase_char, intr_char, kill_char;

void
gettty()
{
    /* Should set erase_char, intr_char, kill_char */
}

void
settty(const char *s)
{
    end_screen();
    if (s)
        raw_print(s);
}

void
setftty()
{
    start_screen();

    iflags.cbreak = ON;
    iflags.echo = OFF;
}

void
intron()
{
}

void
introff()
{
}

#ifdef __linux__ /* via Jesse Thilo and Ben Gertzfield */
#include <sys/ioctl.h>
#include <sys/vt.h>

int linux_flag_console = 0;

void NDECL(linux_mapon);
void NDECL(linux_mapoff);
void NDECL(check_linux_console);
void NDECL(init_linux_cons);

void
linux_mapon()
{
#ifdef TTY_GRAPHICS
    if (WINDOWPORT("tty") && linux_flag_console) {
        write(1, "\033(B", 3);
    }
#endif
}

void
linux_mapoff()
{
#ifdef TTY_GRAPHICS
    if (WINDOWPORT("tty") && linux_flag_console) {
        write(1, "\033(U", 3);
    }
#endif
}

void
check_linux_console()
{
    struct vt_mode vtm;

    if (isatty(0) && ioctl(0, VT_GETMODE, &vtm) >= 0) {
        linux_flag_console = 1;
    }
}

void
init_linux_cons()
{
#ifdef TTY_GRAPHICS
    if (WINDOWPORT("tty") && linux_flag_console) {
        atexit(linux_mapon);
        linux_mapoff();
#ifdef TEXTCOLOR
        /*if (has_colors())*/ /* Assume true in NLE. */
        iflags.use_color = TRUE;
#endif
    }
#endif
}
#endif /* __linux__ */
