// Gym backend: the PufferLib NetHack env driven by the REAL NetHackChallenge-v0
// environment. Same shape as nh_stock_backend.c, but the engine transport is a
// callback into Python instead of a privately dlopened libnethack.so, so every
// keystroke -- policy action and reconstruction probe alike -- is an ordinary
// env.step() that the challenge counts. The fork-only introspection hooks are
// reconstructed from the challenge observation by nh_derive.h.
#define _GNU_SOURCE
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "nletypes.h"
#include "nh_derive.h"

#define ROWS 21
#define COLS 79
#define TTY_LI 24
#define TTY_CO 80
#define INV 55

// Python side: send one key, then call nhg_fill() with the resulting observation.
// Returns non-zero when the episode has ended.
typedef int (*nhg_send_cb)(void* ud, int key);
// Python side: reset the challenge env (seeding it) and call nhg_fill() with the first observation.
typedef int (*nhg_reset_cb)(void* ud);
static nhg_send_cb g_send; static nhg_reset_cb g_resetcb; static void* g_ud;

typedef struct {
    nle_obs* fobs;
    DObs d;
    DState S;
    // raw challenge channels for anything the env does not bind itself
    short glyphs[ROWS * COLS];
    unsigned char chars[ROWS * COLS], colors[ROWS * COLS], specials[ROWS * COLS];
    long blstats[NLE_BLSTATS_SIZE];
    unsigned char message[NLE_MESSAGE_SIZE];
    int internal[NLE_INTERNAL_SIZE];
    int prog[6];
    short inv_glyphs[INV];
    unsigned char inv_strs[INV * NLE_INVENTORY_STR_LENGTH], inv_letters[INV], inv_oclasses[INV];
    unsigned char tty_chars[TTY_LI * TTY_CO];
    signed char tty_colors[TTY_LI * TTY_CO];
    unsigned char tty_cursor[2];
    int misc[3];
    int done, how_done, in_normal_game, mapped;
    // probes overwrite the top line; the fork never sees that, so the message the
    // env reads is saved across a probe group and put back (the stock backend does
    // the same thing to the engine's own toplines, which is not reachable here)
    unsigned char msg_save[NLE_MESSAGE_SIZE]; int msg_saved; long probe_mark;
    int vmore; char vmore_text[300];
    long ch_steps, ch_probe, ch_noprog, ch_maxnoprog, ch_turn;
    long fin_steps, fin_probe, fin_maxnoprog, fin_turn; // the episode that just ended, kept across the reset
    unsigned long ep;
} GInst;
static GInst G;
// NH_GYM keylog: 'K <key> <done>' per env-driven key (probes excluded, as in the fork
// harness log) and 'R <hash>' per env step boundary, for replay/determinism checks
static long g_nbound, g_nafter, g_nrefresh;

void nhg_set_callback(nhg_send_cb cb, nhg_reset_cb rc, void* ud) { g_send = cb; g_resetcb = rc; g_ud = ud; }

// the env may re-bind its observation buffers between calls: always derive where it reads
static void wire_obs(GInst* g, nle_obs* o) {
    g->fobs = o;
    DObs* d = &g->d;
#define NHB(f, mine) (o->f ? o->f : g->mine)
    d->glyphs = NHB(glyphs, glyphs);
    d->blstats = NHB(blstats, blstats);
    d->message = NHB(message, message);
    d->misc = NHB(misc, misc);
    d->tty_chars = NHB(tty_chars, tty_chars);
    d->tty_colors = NHB(tty_colors, tty_colors);
    d->tty_cursor = NHB(tty_cursor, tty_cursor);
    d->inv_glyphs = NHB(inv_glyphs, inv_glyphs);
    d->inv_strs = NHB(inv_strs, inv_strs);
    d->inv_letters = NHB(inv_letters, inv_letters);
    d->inv_oclasses = NHB(inv_oclasses, inv_oclasses);
    d->internal = NHB(internal, internal);
#undef NHB
    d->sdesc = NULL;      // the challenge does not export screen descriptions
    d->rawout = NULL; d->rawlen = NULL;
    d->redrawn = NULL;    // no print_glyph hook: the engine lives in the NLE process
    if (o->inv_state) d->inv_state = o->inv_state;
    if (o->inv_true_glyphs) d->inv_true = o->inv_true_glyphs;
}

// destinations for the current observation, in the order the Python side passes them
void nhg_fill(const short* glyphs, const unsigned char* chars, const unsigned char* colors,
              const unsigned char* specials, const long* blstats, const unsigned char* message,
              const short* inv_glyphs, const unsigned char* inv_strs, const unsigned char* inv_letters,
              const unsigned char* inv_oclasses, const unsigned char* tty_chars, const signed char* tty_colors,
              const unsigned char* tty_cursor, const int* misc, int done, int how_done) {
    GInst* g = &G; DObs* d = &g->d;
    if (glyphs && d->glyphs) memcpy(d->glyphs, glyphs, ROWS * COLS * sizeof(short));
    if (chars) memcpy(g->chars, chars, ROWS * COLS);
    if (colors) memcpy(g->colors, colors, ROWS * COLS);
    if (specials) memcpy(g->specials, specials, ROWS * COLS);
    if (blstats && d->blstats) memcpy(d->blstats, blstats, NLE_BLSTATS_SIZE * sizeof(long));
    if (message && d->message) memcpy(d->message, message, NLE_MESSAGE_SIZE);
    if (inv_glyphs && d->inv_glyphs) memcpy(d->inv_glyphs, inv_glyphs, INV * sizeof(short));
    if (inv_strs && d->inv_strs) memcpy(d->inv_strs, inv_strs, INV * NLE_INVENTORY_STR_LENGTH);
    if (inv_letters && d->inv_letters) memcpy(d->inv_letters, inv_letters, INV);
    if (inv_oclasses && d->inv_oclasses) memcpy(d->inv_oclasses, inv_oclasses, INV);
    if (tty_chars && d->tty_chars) memcpy(d->tty_chars, tty_chars, TTY_LI * TTY_CO);
    if (tty_colors && d->tty_colors) memcpy(d->tty_colors, tty_colors, TTY_LI * TTY_CO);
    if (tty_cursor && d->tty_cursor) memcpy(d->tty_cursor, tty_cursor, 2);
    if (misc && d->misc) memcpy(d->misc, misc, 3 * sizeof(int));
    if (d->internal) memset(d->internal, 0, NLE_INTERNAL_SIZE * sizeof(int)); // the challenge exports no internal channel
    g->done = done; g->how_done = how_done;
    g->in_normal_game = !done;
}

static int gym_key(GInst* g, int key, int is_probe) {
    if (g->done) return 1;
    g->ch_steps++; if (is_probe) g->ch_probe++;
    int done = g_send(g_ud, key);
    g->done = done;
    return done;
}

static int gym_send(void* ctx, int key) { // probe keystroke: an ordinary, counted env step
    GInst* g = (GInst*)ctx;
    return gym_key(g, key, 1);
}

// the top line across a probe group
static void topl_save(GInst* g) {
    if (!g->d.message) { g->msg_saved = 0; return; }
    memcpy(g->msg_save, g->d.message, NLE_MESSAGE_SIZE); g->msg_saved = 1; g->probe_mark = g->S.probe_keys;
}
static void topl_restore(GInst* g) {
    if (!g->msg_saved) return; g->msg_saved = 0;
    if (g->S.probe_keys == g->probe_mark) return; // no probe ran: the engine's own message stands
    if (g->d.message) memcpy(g->d.message, g->msg_save, NLE_MESSAGE_SIZE);
}
static void topl_restore_always(GInst* g) {
    if (!g->msg_saved) return; g->msg_saved = 0;
    if (g->d.message) memcpy(g->d.message, g->msg_save, NLE_MESSAGE_SIZE);
}

// a position prompt is open: answer it with a keystroke, as any agent must
static void nh_answer_getpos(GInst* g) {
    for (int it = 0; it < 3; it++) {
        if (g->d.misc && (g->d.misc[0] || g->d.misc[1] || g->d.misc[2])) return;
        char m[256]; dr_msg(&g->d, m, sizeof m);
        char* mk = strstr(m, "(For instructions type a"); if (!mk) return;
        int force = strstr(m, "Where do you want") != NULL || strstr(m, "the desired") != NULL;
        topl_save(g); gym_send(g, force ? '.' : 27);
        char post[256]; post[0] = 0;
        if (g->d.message) snprintf(post, sizeof post, "%.255s", (const char*)g->d.message);
        int post_wait = g->d.misc && (g->d.misc[0] || g->d.misc[1] || g->d.misc[2]);
        topl_restore_always(g);
        *mk = 0; { char* e = m + strlen(m); while (e > m && e[-1] == ' ') *--e = 0; }
        if (!force && m[0] && !post_wait && !g->done) {
            g->vmore = 1; snprintf(g->vmore_text, sizeof g->vmore_text, "%s", post);
            if (g->d.misc) g->d.misc[2] = 1;
        }
        if (g->d.message) { memset(g->d.message, 0, NLE_MESSAGE_SIZE); snprintf((char*)g->d.message, NLE_MESSAGE_SIZE, "%s", m); }
    }
}


// The challenge runs with NLE's default options, which include nolegacy: the
// "You are a neutral female human Valkyrie" line the derive normally reads at
// start-up is never printed, so identity has to be asked for. ^X (attributes)
// prints it, costs no game time, and is in the published action set.
static int dr_identity_probe(GInst* g) {
    static const char* ROLES[13] = {"Archeologist", "Barbarian", "Caveman", "Healer", "Knight", "Monk",
                                    "Priest", "Rogue", "Ranger", "Samurai", "Tourist", "Valkyrie", "Wizard"};
    static const char* RACES[5] = {"human", "elven", "dwarven", "gnomish", "orcish"};
    static const char* RACES2[5] = {"human", "elf", "dwarf", "gnome", "orc"};
    static const char* ALIGNS[3] = {"chaotic", "neutral", "lawful"};
    if (g->done) return 0;
    gym_send(g, 24); // ^X
    if (g->done) return 0;
    int got = 0;
    char page[DR_TTY_LI][DR_TTY_CO + 1];
    for (int r = 0; r < DR_TTY_LI; r++) dr_row(&g->d, r, page[r]);
    for (int r = 0; r < DR_TTY_LI && !got; r++) {
        const char* p = strstr(page[r], "a level ");
        if (!p) continue;
        p += 8;
        while (*p && *p != ' ') p++;              // the level number
        char w[4][32]; int k = 0;
        while (k < 4 && *p) {
            while (*p == ' ') p++;
            int j = 0; while (*p && *p != ' ' && *p != '.' && *p != ',' && j < 31) w[k][j++] = *p++;
            w[k][j] = 0; if (j) k++;
            if (*p == '.' || *p == ',') break;
        }
        if (k < 2) continue;
        const char* ro = w[k - 1];
        const char* ra = w[k - 2];
        const char* ge = (k >= 3) ? w[k - 3] : NULL;
        int role = -1, race = -1;
        for (int i = 0; i < 13; i++) if (!strcmp(ro, ROLES[i])) role = i;
        if (role < 0 && !strcmp(ro, "Cavewoman")) { role = 2; }
        if (role < 0 && !strcmp(ro, "Priestess")) { role = 6; }
        for (int i = 0; i < 5; i++) if (!strcmp(ra, RACES[i]) || !strcmp(ra, RACES2[i])) race = i;
        if (role < 0 || race < 0) continue;
        g->S.role = role; g->S.race = race;
        g->S.gender = (ge && !strcmp(ge, "female")) || !strcmp(ro, "Cavewoman") || !strcmp(ro, "Priestess")
                      || !strcmp(ro, "Valkyrie") ? 1 : 0;
        got = 1;
    }
    for (int r = 0; r < DR_TTY_LI; r++) { // "You are chaotic, on a mission for ..."
        const char* p = strstr(page[r], "You are ");
        if (!p) continue;
        p += 8;
        for (int i = 0; i < 3; i++) if (!strncmp(p, ALIGNS[i], strlen(ALIGNS[i]))) { g->S.align = i; break; }
    }
    for (int i = 0; i < 6 && !g->done; i++) { // close the paged window
        if (!dr_window_open(&g->d) && !(g->d.misc && (g->d.misc[0] || g->d.misc[1] || g->d.misc[2]))) break;
        gym_send(g, 27);
    }
    return got;
}

static void sync_status(GInst* g, nle_obs* o) {
    o->done = g->done; o->how_done = g->how_done; o->in_normal_game = (char)g->in_normal_game;
    if (o->internal) { o->internal[9] = 0; o->internal[10] = 0; }
}

// ---------------------------------------------------------------- engine entry points (fork signatures)
static int g_started;
nle_ctx_t* nle_start(nle_obs* obs, FILE* f, nle_settings* set) {
    (void)f; (void)set;
    GInst* g = &G;
    // nh_stock_backend.c calloc's a fresh Inst for every episode, so nothing at all
    // survives a reset there. Resetting only the fields that looked per-episode left
    // the rest carrying over and made every episode after the first play differently
    // from the same game started fresh. Clear the whole struct and match it.
    long fs = g->ch_steps, fp = g->ch_probe, fm = g->ch_maxnoprog;
    long ft = g->d.blstats ? g->d.blstats[20] : -1;
    unsigned long ep = g->ep;
    memset(g, 0, sizeof *g);
    g->fin_steps = fs; g->fin_probe = fp; g->fin_maxnoprog = fm; g->fin_turn = ft;
    g->ep = ep;
    g->in_normal_game = 1; g->ch_turn = -1;
    wire_obs(g, obs);
    g->done = g_resetcb(g_ud); // resets and seeds the challenge env, then calls nhg_fill()
    dr_reset(&g->S, &g->d, (unsigned)(g->ep * 7919 + 13));
    dr_identity_from_text(&g->S, &g->d);
    { // NLE's gym reset presses SPACE past the welcome line, so identity has to be
      // asked for. When the line IS present (driving Nethack directly) the probe
      // would be an extra keystroke, so skip it.
      char b[256 + DR_TTY_CO + 2]; dr_msg(&g->d, b, 256); size_t n = strlen(b); b[n++] = ' ';
      char top[DR_TTY_CO + 1]; dr_row(&g->d, 0, top); snprintf(b + n, sizeof b - n, "%s", top);
      if (!strstr(b, "You are a")) dr_identity_probe(g); }
    g->ep++;
    sync_status(g, obs);   // the immediate nle_obs_refresh runs the first boundary probes
    g_started = 1;
    return (nle_ctx_t*)g;
}

nle_ctx_t* nle_step(nle_ctx_t* c, nle_obs* obs) {
    GInst* g = (GInst*)c;
    if (g->done) { obs->done = 1; return c; }
    wire_obs(g, obs);
    int key = obs->action;
    if (g->vmore) { // the fork is showing --More-- here: only space/Enter/ESC get through
        int dis = key == ' ' || key == 13 || key == 10 || key == 27;
        if (dis) {
            g->vmore = 0; const char* t = key == 27 ? "" : g->vmore_text;
            if (g->d.message) { memset(g->d.message, 0, NLE_MESSAGE_SIZE); snprintf((char*)g->d.message, NLE_MESSAGE_SIZE, "%s", t); }
            if (g->d.misc) g->d.misc[2] = 0;
        }
        goto vmore_skip;
    }
    g->S.count_pending = (key >= '0' && key <= '9'); // no probe between a count prefix and its command
    gym_key(g, key, 0);
    { long t = g->d.blstats ? g->d.blstats[20] : 0;
      if (t == g->ch_turn) { if (++g->ch_noprog > g->ch_maxnoprog) g->ch_maxnoprog = g->ch_noprog; }
      else { g->ch_turn = t; g->ch_noprog = 0; } }
vmore_skip:
    g->mapped = 0;
    sync_status(g, obs);
    if (!g->done && !g->vmore) nh_answer_getpos(g);
    topl_save(g);
    g_nafter++;
    int stalled = dr_after_key(&g->S, &g->d, g, gym_send, key, g->done);
    if (!g->done && !stalled) {
        if (dr_hero_moved(&g->S, &g->d) && !dr_prompt_open(&g->d) && !g->S.count_pending
            && g->d.blstats && !(g->d.blstats[25] & 0x220))
            dr_boundary(&g->S, &g->d, g, gym_send);
    }
    topl_restore(g);
    if (stalled) { obs->done = 1; obs->how_done = -1; g->done = 1; }
    sync_status(g, obs);
    return c;
}

// step boundary: probes, the derived hook values, then the glyph export
nle_ctx_t* nle_obs_refresh(nle_ctx_t* c, nle_obs* obs) {
    GInst* g = (GInst*)c;
    wire_obs(g, obs);
    sync_status(g, obs);
    if (obs->done) return c;
    g_nrefresh++;
    if (g->mapped) return c;
    topl_save(g);
    g_nbound++;
    dr_boundary(&g->S, &g->d, g, gym_send);
    topl_restore(g);
    dr_export_glyphs(&g->S, &g->d, 1);
    g->mapped = 1;
    return c;
}

void nle_end(nle_ctx_t* c) { (void)c; }
void nle_identity(nle_ctx_t* c, int* r, int* rc, int* gd, int* a) {
    GInst* g = (GInst*)c; *r = g->S.role; *rc = g->S.race; *gd = g->S.gender; *a = g->S.align;
}
int nle_path_drain(nle_ctx_t* c, short* p, int n) {
    GInst* g = (GInst*)c; int m = n < g->S.path_n ? n : g->S.path_n;
    memcpy(p, g->S.path, 2 * (size_t)m * sizeof(short)); g->S.path_n = 0; return m;
}

// ---------------------------------------------------------------- fork-only hooks, from the derived state
long nle_shop_price(nle_ctx_t* c) { return ((GInst*)c)->S.price; }
int nle_terrain_underfoot(nle_ctx_t* c) { return ((GInst*)c)->S.terrain; }
int nle_inside_shop(nle_ctx_t* c) { return ((GInst*)c)->S.inshop; }
int nle_container_at(nle_ctx_t* c) { return ((GInst*)c)->S.cont; }
int nle_food_underfoot(nle_ctx_t* c) { return ((GInst*)c)->S.food; }
int nle_discoveries(nle_ctx_t* c) { (void)c; return 0; }
int nle_peaceful_at(nle_ctx_t* c, int x, int y) { GInst* g = (GInst*)c; return (x >= 1 && x < 80 && y >= 0 && y < 21) ? g->S.peace[y * 79 + (x - 1)] : 0; }
int nle_lnc_bits(nle_ctx_t* c) { return ((GInst*)c)->S.lnc; }
void nle_weight(nle_ctx_t* c, int* wt, int* cap) { GInst* g = (GInst*)c; *wt = g->S.wt; *cap = g->S.cap; }
int nle_spells(nle_ctx_t* c, short* a, signed char* b, signed char* d, int* e, int n) {
    GInst* g = (GInst*)c; int m = n < g->S.nsp ? n : g->S.nsp;
    for (int i = 0; i < m; i++) { a[i] = g->S.sp_ids[i]; b[i] = g->S.sp_levs[i]; d[i] = g->S.sp_fails[i]; e[i] = g->S.sp_knows[i]; }
    return m;
}
int nle_cast_blocked(nle_ctx_t* c) { return ((GInst*)c)->S.castblk; }
int nle_intrinsics(nle_ctx_t* c) { return ((GInst*)c)->S.intr; }

// ---------------------------------------------------------------- accounting for the Python driver
void nhg_counters(long* out) { out[0] = G.fin_steps; out[1] = G.fin_probe; out[2] = G.fin_maxnoprog; out[3] = G.fin_turn;
    out[4] = G.S.probe_keys; out[5] = g_nbound; out[6] = g_nafter; out[7] = g_nrefresh; }
