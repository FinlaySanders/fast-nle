// Reconstruction of the fork-only NetHack observation channels from stock NLE's public
// interface. Shared by the stock C backend (nh_stock_backend.c) and the gym backend
// (nh_gym_backend.c), so both rungs derive exactly the same values.
// Everything here reads only: glyphs, blstats, message, misc, tty text, farlook text,
// inventory text, plus zero-time probe keys (':' look here, '+' spells, '\' discoveries).
#ifndef NH_DERIVE_H
#define NH_DERIVE_H
#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "nh_tables.h"

#define DR_ROWS 21
#define DR_COLS 79
#define DR_CELLS (DR_ROWS * DR_COLS)
#define DR_TTY_LI 24
#define DR_TTY_CO 80
#define DR_SDESC 80
#define DR_INV 55
#define DR_INVSTR 80
#define DR_LEVELS 40
#define DR_PATH 512
// keys without game time before the episode is truncated: the challenge's own step cap, so the derive never pre-empts
// NLE's 10,000-step no-progress rule (the env's zero-time mask is what keeps the policy out of free-refusal loops)
static int dr_stall_cap(void) { return 1000000; } // clock-less keys before the episode is truncated: NetHackChallenge-v0 max_episode_steps
#define DR_STALL_CAP dr_stall_cap()

#define CMAP_OFF NHT_GLYPH_CMAP_OFF
#define OBJ_OFF NHT_GLYPH_OBJ_OFF
#define BODY_OFF NHT_GLYPH_BODY_OFF
#define STATUE_OFF NHT_GLYPH_STATUE_OFF
#define SWALLOW_OFF NHT_GLYPH_SWALLOW_OFF
#define SWALLOW_HI (SWALLOW_OFF + NHT_NUMMONS * 8)
#define TERR_HI (CMAP_OFF + NHT_MAXPCHARS - NHT_MAXEXPCHARS)
#define NUMMONS NHT_NUMMONS
#define NUM_OBJECTS NHT_NUM_OBJECTS
#define NO_GLYPH NHT_NO_GLYPH

// the public observation the derivations read (pointers into whichever buffers the engine fills)
typedef struct {
    short* glyphs;              // DR_CELLS
    long* blstats;              // 27
    unsigned char* message;     // 256
    int* misc;                  // 3
    unsigned char* tty_chars;   // 24*80
    signed char* tty_colors;    // 24*80
    unsigned char* tty_cursor;  // 2
    unsigned char* sdesc;       // DR_CELLS * 80
    unsigned char* redrawn;     // DR_CELLS: cells reprinted by the engine since the last export (stock backend hook), else NULL
    short* inv_glyphs;          // 55
    unsigned char* inv_strs;    // 55*80
    unsigned char* inv_letters; // 55
    unsigned char* inv_oclasses;// 55
    int* internal;              // fork's 11 (written: [6])
    signed char* inv_state;     // 55*8 (written)
    short* inv_true;            // 55 (written)
    unsigned char* rawout; int* rawlen; // stock backend: raw terminal stream since the last reset (NULL on the fork harness)
} DObs;

typedef struct { int dnum, dlevel; short terr[DR_CELLS]; short objm[DR_CELLS]; unsigned char engr[DR_CELLS]; unsigned char engr_blind[DR_CELLS]; unsigned char litmark[DR_CELLS]; unsigned char guess[DR_CELLS]; unsigned char corr_seen[DR_CELLS]; unsigned char shop[DR_CELLS]; int shop_set; int shop_r, shop_c; } DLevel;

typedef struct {
    // identity
    int role, race, gender, align;
    // per-level memory
    DLevel lv[DR_LEVELS]; int nlv; int cur;
    // engraving tracking
    int keybuf[16]; int nkey;
    char seq_msgs[12][128]; int nseq;
    // peaceful override cells: "gets angry" while the farlook text still says peaceful
    struct { int r, c; char txt[DR_SDESC]; } angry[16]; int nangry;
    unsigned char peace[DR_CELLS]; short peace_g[DR_CELLS]; long peace_t[DR_CELLS]; int peace_dirty; // farlook-classified monsters (cell, glyph, turn)
    int form, form_dirty; long form_t; // hero's polymorphed form (monster index, -1 = own form), from a farlook on the hero's cell; form_t = turn of that farlook (re-probed every 40 turns while polymorphed: the return-to-form line is often lost in a prayer's pages)
    int ident_seen; // harness: identity parsed from the start text at a boundary
    int shop_pending; // a shopkeeper greeting seen on some key since the last boundary (greetings inside multi-key steps were lost)
    int msg_pending; // any non-empty message on a key since the last boundary (discoveries re-probe trigger)
    int wlegs; long wlegs_t; // wounded legs (sides): weight_cap subtracts 100 per side unless flying; from kick/xan/bear-trap/land-mine messages, cleared by the heal message or when the wound's maximum duration has passed (the heal line is often lost in a multi-key step)
    // path
    int last_lx, last_ly, last_dn, last_dl, have_last;
    short path[2 * DR_PATH]; int path_n;
    // derived scalar hook values (valid for the next decision)
    int terrain, top, food, cont, engr_bits, inshop; long price;
    int lnc, wt, cap, castblk, intr, intr_gained, intr_lost; long fast_until; long form_hd; // intr_lost: bits removed by a loss message until re-gained; form_hd: last HD: value seen
    int nsp; short sp_ids[8]; signed char sp_levs[8], sp_fails[8]; int sp_knows[8];
    int spells_dirty; long probe_turn, disc_turn;
    // discoveries / appearance bijection
    unsigned char discovered[NUM_OBJECTS];
    // Stock (like every NLE) exports an object as OBJ_OFF + oc_descr_idx(type): the slot of the description the type wears this
    // game. The fork (NLE_TRUE_GLYPHS) exports OBJ_OFF + type once the type's name is known. type_of_descr[slot] = type is
    // learned from any text that shows a real name next to its raw glyph (inventory, discoveries list, look-here, farlook).
    short type_of_descr[NUM_OBJECTS];
    unsigned char descr_src[NUM_OBJECTS]; // 0 none, 1 inventory/look text, 2 discoveries list (authoritative)
    short type_prev[NUM_OBJECTS]; // identities as of the previous export: a cell printed during this step was printed before this step's identifications (monster item use prints first, learns after)
    int disc_time_probed; long terrain_probes; int prev_terr;
    int count_pending; long probes_deferred; // the env's last game key was a count digit: any probe key would cancel the count
    int cell_dirty; long last_look_turn; int last_skip; int meal_flag, took_flag; // eating / pickup seen on any key since the last boundary
    int drop_top; long drop_turn; int prev_dex; int was_blind; int was_engulfed; int key_blind; int disc_rows; int engr_known_cell; // the square whose engraving the policy last wrote, read or felt (the fork remembers one) // rows the discoveries list showed last time (>= 20: full-screen window) // blind state after the previous key (per key, not per boundary: sight can return inside a multi-key step) // the previous boundary was blind: things may have landed under the hero unseen, re-look when sight returns
    int land_top; long land_turn; // a projectile that just landed under the hero, from its message
    int arr_win_open, arr_win_col; // the game's own pile window (arrival) can page across keys: later pages carry no header // "You drop X": X is the new chain head (the fork's underfoot tile); the look lists big piles unreliably
    short pile[8]; short pile_qty[8]; int npile; // the hero-cell pile (top first) from the last sighted look, for blind bookkeeping
    short map_raw[DR_CELLS], map_out[DR_CELLS]; int map_valid; // the exported map: raw glyphs with identities applied at every fill
    short prev_inv_g[DR_INV]; signed char prev_inv_oc[DR_INV]; char prev_inv_t[DR_INV][DR_INVSTR]; int prev_inv_n; // inventory at the previous boundary: a dropped gem/candle/harp carries its slot // hero-cell events seen since the last look (messages arrive on earlier keys than the step boundary)
    long bless_est; int prayed; long pray_turn; // prayer-cooldown model for internal[5] (exact until the first prayer)
    // hero-tile: where and what we last decided
    int d_lv_dn, d_lv_dl, d_r, d_c, d_valid;
    // stall detection
    long last_t; int same; int trunc_pending;
    // probe bookkeeping
    long probes, probe_keys, probe_skip_blind, probe_skip_engulf, probe_skip_prompt;
    unsigned rng;
    long keys;
} DState;

// engine access the module needs: send one key (zero-time probe) and return done
typedef int (*dr_send_fn)(void* ctx, int key);

// ---------------------------------------------------------------- tables built once
static int g_dr_init;
static int g_name_order[NUM_OBJECTS]; static int g_name_n;
static char g_full[NUM_OBJECTS][64]; // class-prefixed lowercase real names ("potion of healing")
static int g_food_glyph[CMAP_OFF]; static int g_cont_glyph[CMAP_OFF];
static inline int dr_is_food(int g) { return g >= 0 && g < CMAP_OFF && g_food_glyph[g]; }
static inline int dr_is_cont(int g) { return g >= 0 && g < CMAP_OFF && g_cont_glyph[g]; }
static int g_class_first[128];
static int g_corpse_idx, g_water_idx, g_shk_idx;
// gems and glass share descriptions and are not shuffled: the public form of an unidentified gem is its description's
// canonical twin (the worthless glass if any, else the lowest index), the fork's shuffled_glyph rule
static int dr_gem_canon(int t) { // every class: the lowest index sharing the description within the class (worthless glass for gems), the fork's rule
    static short canon[NUM_OBJECTS]; static int init;
    if (!init) { init = 1; for (int i = 0; i < NUM_OBJECTS; i++) { canon[i] = (short)i; if (!NHT_OBJ_DESCR[i][0]) continue; int best = -1;
        for (int j = 0; j < NUM_OBJECTS; j++) { if (NHT_OBJ_CLASS[j] != NHT_OBJ_CLASS[i] || !NHT_OBJ_DESCR[j][0] || strcmp(NHT_OBJ_DESCR[i], NHT_OBJ_DESCR[j])) continue; if (best < 0) best = j; if (NHT_OBJ_CLASS[j] == 13 && !strncmp(NHT_OBJ_NAME[j], "worthless", 9)) best = j; }
        if (best >= 0) canon[i] = (short)best; } }
    return t >= 0 && t < NUM_OBJECTS ? canon[t] : t;
}
static int g_shuffled[NUM_OBJECTS]; static int g_app_slot[NUM_OBJECTS]; static int g_in_range[NUM_OBJECTS];
static int g_shuffle_lo[10], g_shuffle_hi[10], g_nshuffle;
static char g_japanese[14][2][24] = {{"wakizashi","short sword"},{"ninja-to","broadsword"},{"nunchaku","flail"},{"naginata","glaive"},{"osaku","lock pick"},{"koto","wooden harp"},{"shito","knife"},{"tanko","plate mail"},{"kabuto","helmet"},{"yugake","leather gloves"},{"gunyoki","food ration"},{"sake","potion of booze"},{"yumi","bow"},{"ya","arrow"}};
static int g_jap_idx[14];

static const char* dr_class_prefix(int c) {
    switch (c) { case 4: return "ring of "; case 5: return "amulet of "; case 8: return "potion of "; case 9: return "scroll of "; case 10: return "spellbook of "; case 11: return "wand of "; default: return ""; }
}
static void dr_lower(char* d, const char* s, size_t n) { size_t i = 0; for (; s[i] && i + 1 < n; i++) d[i] = (char)tolower((unsigned char)s[i]); d[i] = 0; }
static int dr_cls_range(int c, const char** stops, int nstop, int* lo, int* hi) {
    int first = -1, last = -1;
    for (int i = 0; i < NUM_OBJECTS; i++) if (NHT_OBJ_CLASS[i] == c && NHT_OBJ_NAME[i][0]) { if (first < 0) first = i; last = i; }
    if (first < 0) return 0;
    *lo = first; *hi = last;
    for (int i = first; i <= last; i++) { if (NHT_OBJ_CLASS[i] != c || !NHT_OBJ_NAME[i][0]) continue; for (int k = 0; k < nstop; k++) if (strcmp(NHT_OBJ_NAME[i], stops[k]) == 0) { *hi = i - 1; return 1; } }
    return 1;
}
static void dr_init_tables_impl(void) {
    for (int i = 0; i < NUM_OBJECTS; i++) {
        // Some names in the table already carry their class word ("amulet of ESP", "amulet versus poison") while their
        // classmates are bare ("see invisible"). Prefixing unconditionally built "amulet of amulet of esp", which can never
        // word-match displayed text, so TEN amulet types were unidentifiable by name from any source. Skip the prefix when
        // the name already starts with the class word.
        const char* pfx = dr_class_prefix(NHT_OBJ_CLASS[i]);
        { size_t w = 0; while (pfx[w] && pfx[w] != ' ') w++;
          if (w && !strncasecmp(NHT_OBJ_NAME[i], pfx, w) && NHT_OBJ_NAME[i][w] == ' ') pfx = ""; }
        char tmp[64]; snprintf(tmp, sizeof tmp, "%s%s", pfx, NHT_OBJ_NAME[i]);
        dr_lower(g_full[i], tmp, sizeof g_full[i]);
        if (NHT_OBJ_CLASS[i] == NHT_FOOD_CLASS) g_food_glyph[OBJ_OFF + i] = 1;
        const char* n = NHT_OBJ_NAME[i];
        if (!strcmp(n, "large box") || !strcmp(n, "chest") || !strcmp(n, "ice box") || !strcmp(n, "sack") || !strcmp(n, "oilskin sack") || !strcmp(n, "bag of holding")) g_cont_glyph[OBJ_OFF + i] = 1;
        if (!strcmp(n, "corpse")) g_corpse_idx = i;
        if (!strcmp(n, "water") && NHT_OBJ_CLASS[i] == 8) g_water_idx = i;
    }
    for (int g = BODY_OFF; g < BODY_OFF + NUMMONS; g++) g_food_glyph[g] = 1;
    for (int c = 0; c < 128; c++) g_class_first[c] = -1;
    for (int i = 0; i < NUM_OBJECTS; i++) if (g_class_first[NHT_OBJ_CLASS[i]] < 0) g_class_first[NHT_OBJ_CLASS[i]] = i;
    for (int i = 0; i < NUMMONS; i++) if (!strcmp(NHT_MON_NAME[i], "shopkeeper")) g_shk_idx = i;
    // real-name match order: longest first, so "potion of gain level" beats "potion of gain"
    g_name_n = 0;
    for (int i = 0; i < NUM_OBJECTS; i++) if (NHT_OBJ_NAME[i][0]) g_name_order[g_name_n++] = i;
    for (int a = 0; a < g_name_n; a++) for (int b = a + 1; b < g_name_n; b++)
        if (strlen(g_full[g_name_order[b]]) > strlen(g_full[g_name_order[a]])) { int t = g_name_order[a]; g_name_order[a] = g_name_order[b]; g_name_order[b] = t; }
    for (int j = 0; j < 14; j++) { g_jap_idx[j] = -1; for (int i = 0; i < NUM_OBJECTS; i++) if (!strcmp(g_full[i], g_japanese[j][1])) { g_jap_idx[j] = i; break; } }
    // shuffled appearance ranges (o_init.c), as the python bridge listed them
    const char* s8[] = {"water"}; const char* s5[] = {"cheap plastic imitation of the Amulet of Yendor"}; const char* s9[] = {"mail", "blank paper"}; const char* s10[] = {"blank paper"};
    g_nshuffle = 0; int lo, hi;
    if (dr_cls_range(8, s8, 1, &lo, &hi)) { g_shuffle_lo[g_nshuffle] = lo; g_shuffle_hi[g_nshuffle++] = hi; }
    if (dr_cls_range(5, s5, 1, &lo, &hi)) { g_shuffle_lo[g_nshuffle] = lo; g_shuffle_hi[g_nshuffle++] = hi; }
    if (dr_cls_range(9, s9, 2, &lo, &hi)) { g_shuffle_lo[g_nshuffle] = lo; g_shuffle_hi[g_nshuffle++] = hi; }
    if (dr_cls_range(10, s10, 1, &lo, &hi)) { g_shuffle_lo[g_nshuffle] = lo; g_shuffle_hi[g_nshuffle++] = hi; }
    if (dr_cls_range(4, NULL, 0, &lo, &hi)) { g_shuffle_lo[g_nshuffle] = lo; g_shuffle_hi[g_nshuffle++] = hi; }
    if (dr_cls_range(11, NULL, 0, &lo, &hi)) { g_shuffle_lo[g_nshuffle] = lo; g_shuffle_hi[g_nshuffle++] = hi; }
    int extra[4][2] = {{78, 81}, {136, 139}, {125, 128}, {143, 149}};
    for (int k = 0; k < 4; k++) { g_shuffle_lo[g_nshuffle] = extra[k][0]; g_shuffle_hi[g_nshuffle++] = extra[k][1]; }
    for (int k = 0; k < g_nshuffle; k++) for (int i = g_shuffle_lo[k]; i <= g_shuffle_hi[k]; i++) { g_in_range[i] = 1; if (NHT_OBJ_NAME[i][0]) g_shuffled[i] = 1; if ((NHT_OBJ_DESCR[i] && NHT_OBJ_DESCR[i][0]) || NHT_OBJ_NAME[i][0]) g_app_slot[i] = 1; }
    g_dr_init = 1;
}
#include <pthread.h>
static pthread_once_t g_dr_once = PTHREAD_ONCE_INIT;
static void dr_init_tables(void) { pthread_once(&g_dr_once, dr_init_tables_impl); } // env threads reset concurrently: a plain flag let a thread use half-built tables (intermittent start-hash diffs)

// ---------------------------------------------------------------- text helpers
static void dr_msg(const DObs* o, char* out, size_t n) { size_t i = 0; for (; i + 1 < n && i < 256 && o->message[i]; i++) out[i] = (char)o->message[i]; out[i] = 0; }
static void dr_row(const DObs* o, int r, char* out) { if (!o->tty_chars) { out[0] = 0; return; } // 80 chars + NUL, right-trimmed
    int n = 0; for (int c = 0; c < DR_TTY_CO; c++) { unsigned char ch = o->tty_chars[r * DR_TTY_CO + c]; out[n++] = ch ? (char)ch : ' '; }
    while (n > 0 && out[n - 1] == ' ') n--; out[n] = 0;
}
static void dr_sdesc(const DObs* o, int r, int c, char* out) { const unsigned char* p = o->sdesc + (r * DR_COLS + c) * DR_SDESC; int i = 0; for (; i < DR_SDESC - 1 && p[i]; i++) out[i] = (char)p[i]; out[i] = 0; }
static void dr_invstr(const DObs* o, int i, char* out) { const unsigned char* p = o->inv_strs + i * DR_INVSTR; int k = 0; for (; k < DR_INVSTR - 1 && p[k]; k++) out[k] = (char)p[k]; out[k] = 0; }
static int dr_isword(char ch) { return isalnum((unsigned char)ch) || ch == '-' || ch == '\''; }
// whole-word occurrence of `name` in lowercase text `t`, plural s/es tolerated; returns 1 if found
static int dr_word_match_1(const char* t, const char* name);
static int dr_word_match(const char* t, const char* name) {
    if (dr_word_match_1(t, name)) return 1;
    const char* of = strstr(name, " of "); if (!of) return 0;
    char pl[96]; size_t h = (size_t)(of - name); if (h + 6 >= sizeof pl) return 0;
    memcpy(pl, name, h); pl[h] = 's'; strcpy(pl + h + 1, of); if (dr_word_match_1(t, pl)) return 1;
    memcpy(pl, name, h); pl[h] = 'e'; pl[h + 1] = 's'; strcpy(pl + h + 2, of); return dr_word_match_1(t, pl);
}
static int dr_word_match_1(const char* t, const char* name) {
    size_t n = strlen(name); if (!n) return 0;
    for (const char* p = t; (p = strstr(p, name)) != NULL; p++) {
        if (p > t && dr_isword(p[-1])) continue;
        const char* e = p + n;
        if (!dr_isword(*e)) return 1;
        if (e[0] == 's' && !dr_isword(e[1])) return 1;
        if (e[0] == 'e' && e[1] == 's' && !dr_isword(e[2])) return 1;
    }
    return 0;
}
static void dr_strip_parens(char* t) { // remove (...) groups
    char* w = t; int depth = 0;
    for (char* r = t; *r; r++) { if (*r == '(') depth++; else if (*r == ')') { if (depth) depth--; } else if (!depth) *w++ = *r; }
    *w = 0;
}
static int dr_is_appearance(const char* tl) { // unidentified appearance printed?
    if (strstr(tl, "labeled")) return 1;
    for (int i = 0; i < NUM_OBJECTS; i++) {
        const char* d = NHT_OBJ_DESCR[i]; if (!d || !d[0]) continue;
        char f[80]; char dl[64]; dr_lower(dl, d, sizeof dl);
        int c = NHT_OBJ_CLASS[i];
        const char* suf[3] = {NULL, NULL, NULL}; int ns = 0;
        switch (c) { case 8: suf[ns++] = " potion"; break; case 13: suf[ns++] = " gem"; suf[ns++] = " stone"; break; case 4: suf[ns++] = " ring"; break; case 11: suf[ns++] = " wand"; break; case 5: suf[ns++] = " amulet"; break; case 10: suf[ns++] = " spellbook"; break; case 9: break; default: suf[ns++] = ""; }
        for (int k = 0; k < ns; k++) { snprintf(f, sizeof f, "%s%s", dl, suf[k]); if (dr_word_match(tl, f)) return 1; }
    }
    return 0;
}
// index of the object type whose (original) description appears as a whole word in the text; longest match wins
#ifndef PET_OFF
#define PET_OFF NUMMONS
#endif
#ifndef INVIS_OFF
#define INVIS_OFF (2 * NUMMONS)
#endif
static int dr_parse_self(const char* d);
static void dr_learn_type(DState* S, int slot, int type);
static void dr_learn_type_src(DState* S, int slot, int type, int src);
static int dr_appearance_descr_c(const char* tl, int oc) { // oc < 0: any class
    int best = -1; size_t bl = 0;
    for (int j = 0; j < NUM_OBJECTS; j++) { if (!NHT_OBJ_DESCR[j][0] || (oc >= 0 && NHT_OBJ_CLASS[j] != oc)) continue; char dl[64]; dr_lower(dl, NHT_OBJ_DESCR[j], sizeof dl); size_t L = strlen(dl); if (L <= bl) continue; if (dr_word_match(tl, dl)) { best = j; bl = L; } }
    return best;
}
static int dr_appearance_descr(const char* tl) { return dr_appearance_descr_c(tl, -1); }
static int dr_name_index_lower_c(const char* tl0, int oc) {
    char tl[256]; snprintf(tl, sizeof tl, "%s", tl0); dr_strip_parens(tl);
    { char* kv = strstr(tl, "knives"); if (kv) { memcpy(kv, "knife ", 6); memmove(kv + 5, kv + 6, strlen(kv + 6) + 1); } } // irregular plural ("3 knives"), the only -ves object name
    size_t L = strlen(tl);
    if (strstr(tl, " corpse") || (L >= 7 && !strcmp(tl + L - 7, "corpses"))) return g_corpse_idx;
    if (strstr(tl, "holy water")) return g_water_idx;
    // an appearance ("crude dagger", "emerald potion", "opal ring") beats any real-name fragment it contains ("dagger",
    // "emerald", "opal"); the one exception is a real name that itself contains the appearance word ("oil lamp" / "lamp",
    // "wooden flute" / "flute", "tooled horn" / "horn"): the item is then displayed by name, so the type is known
    // the item's class (public) decides which tables apply: a food "orange" is not the potion/gem appearance "orange",
    // a food "tin" is not the wand appearance "tin"; within the class an appearance beats any name fragment it contains
    { int j = dr_appearance_descr_c(tl, oc);
      if (j >= 0) { char dl[64]; dr_lower(dl, NHT_OBJ_DESCR[j], sizeof dl);
          for (int k = 0; k < g_name_n; k++) { int i = g_name_order[k]; if ((oc < 0 || NHT_OBJ_CLASS[i] == oc) && strlen(g_full[i]) > strlen(dl) && dr_word_match(tl, g_full[i]) && dr_word_match(g_full[i], dl)) return i; }
          return -1; } }
    for (int k = 0; k < g_name_n; k++) { int i = g_name_order[k]; if ((oc < 0 || NHT_OBJ_CLASS[i] == oc) && dr_word_match(tl, g_full[i])) return i; }
    for (int j = 0; j < 14; j++) if (g_jap_idx[j] >= 0 && dr_word_match(tl, g_japanese[j][0])) return g_jap_idx[j];
    return -1;
}
static int dr_name_index_lower(const char* tl0) { return dr_name_index_lower_c(tl0, -1); }
static int dr_name_index(const char* t) { char tl[256]; dr_lower(tl, t, sizeof tl); return dr_name_index_lower(tl); }
static int dr_mon_index(const char* name) { if (!strncasecmp(name, "were", 4)) { for (int i = NUMMONS - 1; i >= 0; i--) if (!strcasecmp(NHT_MON_NAME[i], name)) return i; } for (int i = 0; i < NUMMONS; i++) if (!strcasecmp(NHT_MON_NAME[i], name)) return i; return -1; } // lowercased text vs capitalised names (Mordor orc, Uruk-hai)
static int dr_mon_index_suffix(char* cand) { // try the name, then drop leading words
    for (;;) { int mi = dr_mon_index(cand); if (mi >= 0) return mi; char* sp = strchr(cand, ' '); if (!sp) return -1; memmove(cand, sp + 1, strlen(sp + 1) + 1); }
}
static void dr_replace_all(char* s, const char* a, const char* b) { size_t la = strlen(a), lb = strlen(b); char* p; while ((p = strstr(s, a)) != NULL) { memmove(p + lb, p + la, strlen(p + la) + 1); memcpy(p, b, lb); s = p + lb; } }

// ---------------------------------------------------------------- level memory
static DLevel* dr_level(DState* S, const DObs* o) {
    int dn = (int)o->blstats[23], dl = (int)o->blstats[24];
    if (S->cur >= 0 && S->cur < S->nlv && S->lv[S->cur].dnum == dn && S->lv[S->cur].dlevel == dl) return &S->lv[S->cur];
    for (int i = 0; i < S->nlv; i++) if (S->lv[i].dnum == dn && S->lv[i].dlevel == dl) { S->cur = i; return &S->lv[i]; }
    int i = S->nlv < DR_LEVELS ? S->nlv++ : DR_LEVELS - 1;
    DLevel* L = &S->lv[i]; L->dnum = dn; L->dlevel = dl;
    for (int k = 0; k < DR_CELLS; k++) { L->terr[k] = -1; L->objm[k] = -1; L->engr[k] = 0; L->engr_blind[k] = 0; L->litmark[k] = 0; L->guess[k] = 0; L->corr_seen[k] = 0; L->shop[k] = 0; }
    L->shop_set = 0; S->cur = i;
    return L;
}
static const struct { const char* key; int off; } DR_STAIRS[4] = {{"staircase down here", 24}, {"staircase up here", 23}, {"ladder down here", 26}, {"ladder up here", 25}};
static int dr_lead_qty(const char* s) { while (*s == ' ') s++; if (*s >= '1' && *s <= '9') { int q = atoi(s); return q > 0 ? q : 1; } return 1; }
static int dr_qty_after_here(const char* t) { const char* h = strstr(t, "here "); return h ? dr_lead_qty(h + 5) : 1; } // "You see here 2 jackal corpses." loses its count in dr_see_here
static int dr_see_here(const char* msg, char* item, size_t n) { // "You see here [an|a|N|the|your] X." -> X
    const char* p = strstr(msg, "You see here "); if (p) p += 13; else { p = strstr(msg, "You feel here "); if (!p) return 0; p += 14; } // blind arrival: "You feel here X."
    if (!strncmp(p, "an ", 3)) p += 3; else if (!strncmp(p, "a ", 2)) p += 2; else if (!strncmp(p, "the ", 4)) p += 4; else if (!strncmp(p, "your ", 5)) p += 5;
    else if (isdigit((unsigned char)*p)) { while (isdigit((unsigned char)*p)) p++; if (*p == ' ') p++; }
    size_t k = 0; while (p[k] && k + 1 < n) { if (p[k] == '.' && (p[k + 1] == ' ' || p[k + 1] == 0)) break; item[k] = p[k]; k++; }
    item[k] = 0; return k > 0;
}
static int dr_gone_msg(const char* m) {
    if (((m[0] >= 'a' && m[0] <= 'z') || (m[0] >= 'A' && m[0] <= 'Z') || m[0] == '$' || m[0] == '#') && m[1] == ' ' && m[2] == '-' && m[3] == ' ') return 1;
    return strstr(m, "nothing here to pick up") || strstr(m, "You finish eating") || strstr(m, "You pick up") || strstr(m, "You steal") || strstr(m, "You snatch") || strstr(m, "There are several objects here") || strstr(m, "There are many objects here");
}
// floor item text -> glyph, food, container (resolve_item)
// an appearance shared by several types ("black gem": jet / black opal / worthless black glass, "candle", "harp"): the fork shows the
// true type's slot. If the hero held an item of that appearance at the previous boundary, the object here is most likely that item
// (just dropped or thrown), whose raw inventory glyph carried the slot.
static int dr_slot_from_prev_inventory(const DState* S, int j) {
    const char* d = NHT_OBJ_DESCR[j]; if (!d[0]) return -1; char dl[64]; dr_lower(dl, d, sizeof dl);
    for (int i = 0; i < S->prev_inv_n; i++) { int g = S->prev_inv_g[i]; if (g < OBJ_OFF || g >= CMAP_OFF) continue; int slot = g - OBJ_OFF;
        if (NHT_OBJ_CLASS[slot] != NHT_OBJ_CLASS[j] || strcmp(NHT_OBJ_DESCR[slot], d)) continue;
        char tl[DR_INVSTR]; dr_lower(tl, S->prev_inv_t[i], sizeof tl); if (dr_word_match(tl, dl)) return g; }
    return -1;
}
static int dr_resolve_item_inner(DState* S, const char* t0, int memglyph, int* food, int* cont);
static int dr_resolve_item(DState* S, const char* t0, int memglyph, int* food, int* cont) { int r = dr_resolve_item_inner(S, t0, memglyph, food, cont); return r; }
static int dr_resolve_item_inner(DState* S, const char* t0, int memglyph, int* food, int* cont) {
    char t[256]; snprintf(t, sizeof t, "%s", t0); dr_strip_parens(t);
    char tl[256]; dr_lower(tl, t, sizeof tl);
    // trim
    char* s = tl; while (*s == ' ') s++; size_t L = strlen(s); while (L && s[L - 1] == ' ') s[--L] = 0;
    *food = 0; *cont = 0;
    { char* fg = strstr(s, "figurine"); if (fg) { char* of = strstr(fg, " of "); if (of) *of = 0; } } // "figurine of a violet fungus" is the figurine object
    const char* st = strstr(s, "statue of ");
    if (!st) st = strstr(s, "statues of ");
    if (st) {
        const char* p = strchr(st, ' '); p = strchr(p + 1, ' ') + 1; // after "statue(s) of "
        if (!strncmp(p, "an ", 3)) p += 3; else if (!strncmp(p, "a ", 2)) p += 2; else if (!strncmp(p, "the ", 4)) p += 4;
        char cand[128]; snprintf(cand, sizeof cand, "%s", p); char* nm = strstr(cand, " named "); if (nm) *nm = 0;
        int mi = dr_mon_index_suffix(cand);
        return STATUE_OFF + (mi >= 0 ? mi : 0);
    }
    if (strstr(s, " corpse") || (L >= 7 && !strcmp(s + L - 7, "corpses"))) {
        char cand[128] = ""; const char* cp = strstr(s, " corpse");
        if (cp) { size_t k = (size_t)(cp - s); if (k >= sizeof cand) k = sizeof cand - 1; memcpy(cand, s, k); cand[k] = 0; }
        const char* strip[] = {"partly eaten ", "uncursed ", "cursed ", "blessed ", "very rotten ", "rotten ", "stale "};
        for (int k = 0; k < 7; k++) dr_replace_all(cand, strip[k], "");
        char* c2 = cand; while (*c2 == ' ') c2++;
        int mi = dr_mon_index_suffix(c2);
        *food = 1; return BODY_OFF + (mi >= 0 ? mi : 0);
    }
    static const struct { const char* w; int c; } CW[] = {{"potion", 8}, {"scroll", 9}, {"spellbook", 10}, {"wand", 11}, {"ring", 4}, {"amulet", 5}, {"gem", 13}, {"stone", 13}, {"glass", 13}, {"rock", 13}, {"gold piece", 12},
        {"boots", 3}, {"shoes", 3}, {"gloves", 3}, {"gauntlets", 3}, {"cloak", 3}, {"helmet", 3}, {"hat", 3}, {"cap", 3}, {"robe", 3}, {"mail", 3}, {"armor", 3}, {"shield", 3}};
    int cls = -1; for (size_t k = 0; k < sizeof CW / sizeof CW[0]; k++) if (strstr(s, CW[k].w)) { cls = CW[k].c; break; }
    int memobj = memglyph >= OBJ_OFF && memglyph < CMAP_OFF;
    // the result is in stock's raw form (OBJ_OFF + description slot); the export maps known slots to their type like the fork.
    // A real name means the type is name-known: pair it with the remembered raw glyph of the same class (learning the slot);
    // an appearance ("crude dagger", "thick spellbook") is its own slot.
    { int lc = cls; int mc = memobj ? NHT_OBJ_CLASS[memglyph - OBJ_OFF] : -1;
      int called = strstr(s, " called ") != NULL;
      int t = called ? -1 : dr_name_index_lower_c(s, lc);
      if (t < 0 && !called && lc >= 0) t = dr_name_index_lower_c(s, -1); // a class word inside a name ("ring mail"): real names win over the class guess
      if (t < 0 && !called && lc < 0 && mc >= 0) t = dr_name_index_lower_c(s, mc); // class words absent: the remembered class only as a hint
      // no slot learning here: the remembered glyph may be a stale or lower pile member (the look text is authoritative)
      if (t >= 0) { int g = OBJ_OFF + t; *food = g_food_glyph[g]; *cont = g_cont_glyph[g] && !strstr(s, "empty") && !strstr(s, "locked");
          for (int d = 0; d < NUM_OBJECTS; d++) if (S->type_of_descr[d] == t) return OBJ_OFF + d;
          if (memobj && memglyph - OBJ_OFF != t && S->type_of_descr[memglyph - OBJ_OFF] < 0 && NHT_OBJ_CLASS[memglyph - OBJ_OFF] == NHT_OBJ_CLASS[t] && g_shuffled[t]) return memglyph; // name of a shuffled type whose slot is still unknown: trust the remembered slot
          return g; }
      // a bare food name is food, not the potion/wand/gem appearance of the same word ("an orange", "a tin", "an apple")
      if (lc < 0) { static const char* FOODS[] = {"orange", "tin", "apple", "pear", "melon", "banana", "carrot", "egg", "lembas wafer", "cram ration", "food ration"};
          for (size_t q = 0; q < sizeof FOODS / sizeof FOODS[0]; q++) { const char* w = s; if (!strncmp(w, "an ", 3)) w += 3; else if (!strncmp(w, "a ", 2)) w += 2; else if (isdigit((unsigned char)*w)) { while (isdigit((unsigned char)*w)) w++; while (*w == ' ') w++; }
              size_t L = strlen(FOODS[q]); if (!strncmp(w, FOODS[q], L) && (w[L] == 0 || w[L] == 's' || w[L] == ' ')) { for (int i2 = 0; i2 < NUM_OBJECTS; i2++) if (NHT_OBJ_CLASS[i2] == 7 && !strcmp(NHT_OBJ_NAME[i2], FOODS[q])) { *food = 1; return OBJ_OFF + i2; } } } }
      int j = dr_appearance_descr_c(s, lc);
      if (j < 0 && lc < 0 && mc >= 0) j = dr_appearance_descr_c(s, mc);
      if (j < 0 && lc >= 0) j = dr_appearance_descr_c(s, -1);
      if (j >= 0) { // several types wear this description: the fork shows the true type's slot; take the most common one
          const char* d = NHT_OBJ_DESCR[j]; int best = j;
          for (int q = 0; q < NUM_OBJECTS; q++) if (q != j && NHT_OBJ_CLASS[q] == NHT_OBJ_CLASS[j] && !strcmp(NHT_OBJ_DESCR[q], d)) {
              if (NHT_OBJ_CLASS[j] == 13 && !strncmp(NHT_OBJ_NAME[q], "worthless", 9)) best = q; // glass outnumbers real gems
              if (NHT_OBJ_CLASS[j] == 6 && !strcmp(NHT_OBJ_NAME[q], "sack")) best = q; } // sack is the common "bag"
          j = best; }
      if (j >= 0) { int g = OBJ_OFF + j; *food = g_food_glyph[g]; *cont = g_cont_glyph[g] && !strstr(s, "empty") && !strstr(s, "locked");
          // several types can wear one description (amethyst / worthless violet glass): the remembered raw glyph carries the engine's slot
          if (memobj && NHT_OBJ_CLASS[memglyph - OBJ_OFF] == NHT_OBJ_CLASS[j] && !strcmp(NHT_OBJ_DESCR[memglyph - OBJ_OFF], NHT_OBJ_DESCR[j])) { *food = g_food_glyph[memglyph]; return memglyph; }
          { int shared = 0; for (int q = 0; q < NUM_OBJECTS; q++) if (q != j && NHT_OBJ_CLASS[q] == NHT_OBJ_CLASS[j] && !strcmp(NHT_OBJ_DESCR[q], NHT_OBJ_DESCR[j])) shared = 1;
            if (shared) { int pg = dr_slot_from_prev_inventory(S, j); if (pg >= 0) { *food = g_food_glyph[pg]; return pg; } } }
          return g; } }
    for (int j = 0; j < 14; j++) if (g_jap_idx[j] >= 0 && dr_word_match(s, g_japanese[j][0])) { int g = OBJ_OFF + g_jap_idx[j]; *food = g_food_glyph[g]; return g; }
    if (memglyph >= 0 && (cls < 0 || (memglyph >= OBJ_OFF && memglyph < CMAP_OFF && NHT_OBJ_CLASS[memglyph - OBJ_OFF] == cls))) { *food = dr_is_food(memglyph); *cont = dr_is_cont(memglyph); return memglyph; }
    if (cls >= 0) { *food = cls == 7; return OBJ_OFF + g_class_first[cls]; }
    return memglyph >= 0 ? memglyph : OBJ_OFF + g_class_first[6];
}
static int dr_shop_welcome(const char* msg);
static void dr_update_memory(DState* S, const DObs* o, const char* msg) {
    DLevel* L = dr_level(S, o);
    const short* g = o->glyphs;
    for (int k = 0; k < DR_CELLS; k++) {
        int v = g[k];
        if (v > CMAP_OFF && v < TERR_HI) { L->terr[k] = (short)v; L->objm[k] = -1; L->guess[k] = 0; if (v == CMAP_OFF + 22) L->litmark[k] = 1; } // a corridor once shown lit is lit (lev->lit is permanent): the screen shows it unlit again when it leaves sight, but stepping on it makes waslit = lit, so the fork's hero tile says lit (cell watch ec0182ea: 2381 at T11094, 2380 at T11337, hero tile 2381 at T11341)
        else if ((v >= OBJ_OFF && v < CMAP_OFF) || (v >= BODY_OFF && v < BODY_OFF + NUMMONS)) L->objm[k] = (short)v;
    }
    int col = (int)o->blstats[0], row = (int)o->blstats[1];
    if (row < 0 || row >= DR_ROWS || col < 0 || col >= DR_COLS) return;
    int k = row * DR_COLS + col;
    for (int i = 0; i < 4; i++) if (strstr(msg, DR_STAIRS[i].key)) L->terr[k] = (short)(CMAP_OFF + DR_STAIRS[i].off);
    char item[200];
    if (dr_see_here(msg, item, sizeof item)) { int f, c; L->objm[k] = (short)dr_resolve_item(S, item, L->objm[k], &f, &c); S->npile = 1; S->pile[0] = L->objm[k]; S->pile_qty[0] = (short)dr_qty_after_here(msg); }
    else if (o->tty_chars && (S->arr_win_open || strstr(msg, "You try to feel") || strstr(msg, "Things that you feel here") || strstr(msg, "Things that are here") || strstr(msg, "There are several objects here") || strstr(msg, "There are many objects here"))) {
        // the game's own pile window (arrival, possibly blind), paged by the env across keys: page 1 carries the header
        // (item rows below it at the header's column), later pages carry item rows from the top; "--More--"/"(end)" end a page
        int hdr_row = -1; for (int r = 0; r < DR_TTY_LI; r++) { char row[DR_TTY_CO + 1]; dr_row(o, r, row); const char* h = strstr(row, "that you feel here"); if (!h) h = strstr(row, "that are here"); if (h) { hdr_row = r; const char* hs = row; while (*hs == ' ') hs++; S->arr_win_col = (int)(hs - row); break; } }
        int fresh = hdr_row >= 0;
        if (fresh) { S->npile = 0; S->arr_win_open = 1; }
        if (S->arr_win_open) {
            for (int r = (fresh ? hdr_row + 1 : 0); r < DR_TTY_LI; r++) { char row[DR_TTY_CO + 1]; dr_row(o, r, row);
                const char* rr = row + (S->arr_win_col < (int)strlen(row) ? S->arr_win_col : (int)strlen(row)); while (*rr == ' ') rr++;
                if (!*rr) { if (fresh) break; else continue; }
                if (!strncmp(rr, "--More--", 8) || !strcmp(rr, "(end)")) break;
                if (r >= 22 && (strstr(rr, "St:") || strstr(rr, "Dlvl:"))) continue;
                char t[120]; snprintf(t, sizeof t, "%s", rr); dr_replace_all(t, "--More--", ""); { char* e = t + strlen(t); while (e > t && e[-1] == ' ') *--e = 0; }
                if (!*t) continue; int f, c; int gl = dr_resolve_item(S, t, -1, &f, &c); if (S->npile < 8) { S->pile_qty[S->npile] = (short)dr_lead_qty(t); S->pile[S->npile++] = (short)gl; } }
            if (S->npile) L->objm[k] = S->pile[0];
            if (!o->misc[2]) S->arr_win_open = 0; // the window closed with this key
        } }
    else if (dr_gone_msg(msg)) L->objm[k] = -1;
}

// ---------------------------------------------------------------- engraving / anger / intrinsics per key
static const char* DR_ENGR_REFUSE[] = {"can't even hold", "can't reach the floor", "unable to", "can't write", "not going to get anywhere", "no free hand", "too hard", "can't engrave", "can't even"};
static const char* DR_MELEE[] = {"You hit", "You miss", "You kill", "You destroy", "You smite", "You strike", "You punch", "You bite", "You butt", "You kick"};
// intrinsic losses: attrcurse() (gremlin at night) and u_slow_down(); the bit stays off until a gain message re-sets it
static const struct { const char* pat; int bit; } DR_LOSE[] = {{"slowing down", 128}, {"slow down", 128}, {"You feel slower", 128}, {"feel warmer", 2}, {"feel cooler", 4}, {"a little sick", 1}, {"You feel tired", 8}, {"senses fail", 32}, {"thought you saw something", 64}};
static const struct { const char* pat; int bit; } DR_GAIN[] = {{"healthy.", 1}, {"momentary chill", 2}, {"full of hot air", 4}, {"wide awake", 8}, {"feels amplified", 16}, {"strange mental acuity", 32}, {"in touch with the cosmos", 32}, {"seem faster", 128}, {"You speed up", 128}, {"quickness feels more natural", 128}};
static int dr_read_engr(const char* msg, int* bits) { // 'You read: "X"' -> 2 elbereth / 1 other
    const char* p = strstr(msg, "You read: \""); if (!p) return 0; p += 11;
    char w[64]; int k = 0; while (p[k] && p[k] != '"' && k < 63) { w[k] = (char)tolower((unsigned char)p[k]); k++; } w[k] = 0;
    char* s = w; while (*s == ' ') s++; size_t L = strlen(s); while (L && s[L - 1] == ' ') s[--L] = 0;
    *bits = !strcmp(s, "elbereth") ? 2 : 1; return 1;
}
static void dr_track_engraving(DState* S, const DObs* o, int key, const char* msg) {
    DLevel* L = dr_level(S, o);
    int col = (int)o->blstats[0], row = (int)o->blstats[1];
    int cell = (row >= 0 && row < DR_ROWS && col >= 0 && col < DR_COLS) ? row * DR_COLS + col : -1;
    if (S->nkey < 16) S->keybuf[S->nkey++] = key; else { memmove(S->keybuf, S->keybuf + 1, 15 * sizeof(int)); S->keybuf[15] = key; }
    if (key == 'E') S->nseq = 0;
    if (S->nseq < 12) snprintf(S->seq_msgs[S->nseq++], 128, "%s", msg); else { memmove(S->seq_msgs[0], S->seq_msgs[1], 11 * 128); snprintf(S->seq_msgs[11], 128, "%s", msg); }
    if (cell >= 0 && S->nkey >= 9 && (key == 13 || key == 10)) {
        const char tail[] = "Elbereth"; int ok = 1;
        for (int i = 0; i < 8; i++) if (S->keybuf[S->nkey - 9 + i] != tail[i]) ok = 0;
        if (ok) { int refused = 0; for (int m = 0; m < S->nseq; m++) for (size_t r = 0; r < sizeof DR_ENGR_REFUSE / sizeof DR_ENGR_REFUSE[0]; r++) if (strstr(S->seq_msgs[m], DR_ENGR_REFUSE[r])) refused = 1;
            if (!refused) { L->engr[cell] = 1; L->engr_blind[cell] = 1; S->engr_known_cell = cell; } } // 1, not 2, on writing: the engine only counts an Elbereth as ACTIVE once engr_time <= moves (sengr_at), so it is not
        // effective the instant the typing finishes, and walking over dust wipes rnd(5) characters per step (hack.c wipe_engr_at),
        // which no reconstruction can predict. A look that actually reads "Elbereth" upgrades it to 2. Claiming 2 at write time
        // made us report exactly one level too high in 63 of 66 engraving divergences across 1,600 games. // unread since written: while blind the export is capped at 1 (fork public-obs rule); sighted, the probe look reads the truth // blind at the moment of writing = the state before this key (sight can return in the same turn: "You can see again") // written blind: the fork exports 1 until the hero reads or feels the text (public-obs rule) // blind: doengrave garbles each dust letter with 1/11 on top of 1/25, so a blind Elbereth is intact only ~1 in 3; no look can check it
    }
    int bits; if (cell >= 0 && dr_read_engr(msg, &bits)) L->engr[cell] = (unsigned char)bits;
    if (cell >= 0 && (strstr(msg, "You read: \"") || strstr(msg, "You feel the words: \""))) { L->engr_blind[cell] = 0; S->engr_known_cell = cell; } // the policy's own read (arrival or look): the text is known again
    if (cell >= 0 && strstr(msg, "You feel like a hypocrite")) L->engr[cell] = 0; // attacking from an Elbereth square erases it (uhitm: del_engr_at)
    if (cell >= 0 && L->engr[cell] >= 1) for (size_t r = 0; r < sizeof DR_MELEE / sizeof DR_MELEE[0]; r++) if (strstr(msg, DR_MELEE[r])) { S->cell_dirty = 1; if ((o->blstats[25] & 0x20) && L->engr[cell] > 1) L->engr[cell] = 1; break; } // blind: the hero knows it may have smudged its Elbereth (the fork caps the belief at 1) // a hero wipe may have happened: re-read the text at the next boundary (look-here is free) instead of guessing
    { const char* dm = strstr(msg, "You dream that "); const char* mm = dm ? dm + 15 : msg; // asleep: the engine wraps the message, the effect is real
      for (size_t r = 0; r < sizeof DR_GAIN / sizeof DR_GAIN[0]; r++) if (strstr(mm, DR_GAIN[r].pat)) { S->intr_gained |= DR_GAIN[r].bit; S->intr_lost &= ~DR_GAIN[r].bit; }
      if (strstr(mm, "slowing down a bit") || strstr(mm, "slow down a bit")) S->fast_until = 0; // Very_fast ended, intrinsic Fast remains (timeout.c)
      else for (size_t r = 0; r < sizeof DR_LOSE / sizeof DR_LOSE[0]; r++) if (strstr(mm, DR_LOSE[r].pat)) { S->intr_lost |= DR_LOSE[r].bit; S->intr_gained &= ~DR_LOSE[r].bit; if (DR_LOSE[r].bit == 128) S->fast_until = 0; } }
    if (strstr(msg, "suddenly moving") && strstr(msg, "faster")) S->fast_until = o->blstats[20] + 120;
    if (strstr(msg, " gets angry") || strstr(msg, "You hear the shrieks") || strstr(msg, "turns to flee")) S->peace_dirty = 1; // re-classify visible monsters
    if (strstr(msg, "You hit ") || strstr(msg, "You miss ") || strstr(msg, "You kill ") || strstr(msg, " hits the ") || strstr(msg, "You smite") || strstr(msg, "You strike")) { // the hero attacked: hmon_hitmon and missum wakeup(TRUE) unconditionally; a thrown MISS angers only 1 in 3 (tmiss) and then prints "gets angry", handled above
        int melee = strstr(msg, "You hit ") || strstr(msg, "You miss ") || strstr(msg, "You smite") || strstr(msg, "You strike"); int hr = (int)o->blstats[1], hc = (int)o->blstats[0];
        int cand = 0, ck = -1; for (int k = 0; k < DR_CELLS; k++) { int g = o->glyphs[k]; if (g >= 0 && g < NUMMONS && strstr(msg, NHT_MON_NAME[g])) { cand++; ck = k; } }
        for (int k = 0; k < DR_CELLS; k++) { int g = o->glyphs[k]; if (!S->peace[k] || g < 0 || g >= NUMMONS || !strstr(msg, NHT_MON_NAME[g])) continue;
            int adj = abs(k / DR_COLS - hr) <= 1 && abs(k % DR_COLS - hc) <= 1;
            if (cand == 1 || (melee && adj)) { S->peace[k] = 0; S->peace_g[k] = (short)g; S->peace_t[k] = o->blstats[20]; } } (void)ck; }
    if (strstr(msg, " misses the ")) { // a thrown miss angers 1 in 3 (tmiss) and the "gets angry" line can fall behind a --More--: re-look at the named monster next boundary
        for (int k = 0; k < DR_CELLS; k++) { int g = o->glyphs[k]; if (S->peace[k] && g >= 0 && g < NUMMONS && strstr(msg, NHT_MON_NAME[g])) S->peace_t[k] = -1000; } }
    if (dr_shop_welcome(msg) || strstr(msg, "for sale") || strstr(msg, "zorkmid") || strstr(msg, "You sold") || strstr(msg, "Usage fee") || strstr(msg, "for shopping")) S->shop_pending = 1; // greetings and transactions (shops entered without a greeting: dead/absent shopkeeper, level revisit)
    if (msg[0]) S->msg_pending = 1;
    { long T = o->blstats[20]; int dexdrop = S->prev_dex > 0 && (int)o->blstats[4] == S->prev_dex - 1; // set_wounded_legs: ATEMP(A_DEX)-- when the legs were sound
      // set_wounded_legs(side, t): EWounded_legs = side (REPLACES the mask, weight_cap -100 per side), HWounded_legs = t (replaced while timed); heal_legs prints "somewhat better"
      if (strstr(msg, "You strain a muscle")) { S->wlegs = 1; S->wlegs_t = T + 10; } // RIGHT_SIDE, 5 + rnd(5)
      if (strstr(msg, "Ouch!  That hurts!") && dexdrop) { S->wlegs = 1; S->wlegs_t = T + 10; } // kicking something solid: 1 in 3, told apart by the Dex drop
      if (strstr(msg, "bear trap closes on your")) { S->wlegs = 1; S->wlegs_t = T + 19; } // one side, rn1(10, 10)
      if (strstr(msg, "pricks your")) { S->wlegs = 1; S->wlegs_t = T + 60; } // xan: one side, rnd(60 - Dex)
      if (strstr(msg, "in no shape for")) { S->wlegs = strstr(msg, "legs are") ? 2 : 1; if (S->wlegs_t < T + 10) S->wlegs_t = T + 10; } // the kick refusal names the wounded side(s)
      if (strstr(msg, "KAABLAMM") && strstr(msg, "land mine")) { S->wlegs = 2; S->wlegs_t = T + 75; } } // "You triggered a land mine!": both sides, rn1(35, 41); seeing/disarming one does not
    // "Ouch!  That hurts!" (kicking a wall) wounds only 1 in 3 and is not used; 6.7% of capacity queries were wrong before the strain rule (2026-09-12)
    if (strstr(msg, "somewhat better") || (strstr(msg, "Your ") && strstr(msg, "feel") && strstr(msg, " better")) || strstr(msg, "You turn into") || strstr(msg, "new man") || strstr(msg, "new woman")) S->wlegs = 0; // heal_legs in 3.6.6: "Your leg feels better." / "Your legs feel better." ("somewhat better" is the 3.4 text and never fired)
    if (strstr(msg, "You turn into") || strstr(msg, "You return to") || strstr(msg, "new man") || strstr(msg, "new woman") || strstr(msg, "feel like a new") || strstr(msg, "You feel a change coming over") || strstr(msg, "You feel purified") || strstr(msg, "You finish your prayer") || strstr(msg, "You begin praying")) S->form_dirty = 1; // prayer can cure lycanthropy and rehumanize inside its pages
}

// ---------------------------------------------------------------- peaceful map

// ---------------------------------------------------------------- walked path
static int dr_run_key(int k) { return strchr("HJKLYUBN_", k) != NULL || k == 5 || k == 10 || k == 11 || k == 12 || k == 25 || k == 21 || k == 2 || k == 14; }
static int dr_blocked(const short* g, int c, int r) { int v = g[r * DR_COLS + c]; return v == CMAP_OFF || (v >= CMAP_OFF + 1 && v <= CMAP_OFF + 11) || v == CMAP_OFF + 15 || v == CMAP_OFF + 16 || v == CMAP_OFF + 17; }
static int dr_door(const short* g, int c, int r) { int v = g[r * DR_COLS + c]; return v >= CMAP_OFF + 12 && v <= CMAP_OFF + 14; }
static void dr_path_push(DState* S, int x1, int y) { if (S->path_n < DR_PATH) { S->path[2 * S->path_n] = (short)x1; S->path[2 * S->path_n + 1] = (short)y; S->path_n++; } }
static void dr_bfs_fill(DState* S, const short* g, int ax, int ay, int bx, int by) {
    static const int NONE = -1;
    short prev[DR_CELLS]; for (int k = 0; k < DR_CELLS; k++) prev[k] = (short)NONE;
    short q[DR_CELLS]; int qh = 0, qt = 0; int a = ay * DR_COLS + ax, b = by * DR_COLS + bx;
    prev[a] = (short)a; q[qt++] = (short)a; int n = 0;
    while (qh < qt && n < 4000) {
        int cur = q[qh++]; n++; if (cur == b) break;
        int cx = cur % DR_COLS, cy = cur / DR_COLS;
        for (int dc = -1; dc <= 1; dc++) for (int dr = -1; dr <= 1; dr++) {
            int nx = cx + dc, ny = cy + dr; if ((!dc && !dr) || nx < 0 || nx >= DR_COLS || ny < 0 || ny >= DR_ROWS) continue;
            int nk = ny * DR_COLS + nx; if (prev[nk] != NONE || dr_blocked(g, nx, ny)) continue;
            if (dc && dr && (dr_door(g, cx, cy) || dr_door(g, nx, ny))) continue;
            prev[nk] = (short)cur; q[qt++] = (short)nk;
        }
    }
    if (prev[b] == NONE) return;
    short out[DR_CELLS]; int m = 0; int cur = prev[b];
    while (cur != a && m < DR_CELLS) { out[m++] = (short)cur; cur = prev[cur]; }
    for (int i = m - 1; i >= 0; i--) dr_path_push(S, out[i] % DR_COLS + 1, out[i] / DR_COLS);
}
static void dr_track_path(DState* S, const DObs* o, int key) {
    int x = (int)o->blstats[0], y = (int)o->blstats[1], dn = (int)o->blstats[23], dl = (int)o->blstats[24];
    if (S->have_last && S->last_dn == dn && S->last_dl == dl && (x != S->last_lx || y != S->last_ly)) {
        int jump = abs(x - S->last_lx) > abs(y - S->last_ly) ? abs(x - S->last_lx) : abs(y - S->last_ly);
        if (jump <= 1) dr_path_push(S, x + 1, y);
        else if (key >= 0 && dr_run_key(key)) { dr_bfs_fill(S, o->glyphs, S->last_lx, S->last_ly, x, y); dr_path_push(S, x + 1, y); }
    }
    S->have_last = 1; S->last_lx = x; S->last_ly = y; S->last_dn = dn; S->last_dl = dl;
}

// ---------------------------------------------------------------- probes
static int dr_prompt_open(const DObs* o) {
    if (o->misc[0] || o->misc[1] || o->misc[2]) return 1;
    char top[DR_TTY_CO + 1]; dr_row(o, 0, top);
    if (top[0] == '#' && (top[1] == ' ' || top[1] == 0)) return 1; // extended-command line: keys typed here go into the command buffer
    { char m[256]; dr_msg(o, m, sizeof m); if (m[0] == '#' && (m[1] == ' ' || m[1] == 0)) return 1; }
    if (strstr(top, "(For instructions type a") || strstr(top, "Where do you want") || strstr(top, "Pick an object") || strstr(top, "Select ")) return 1; // getpos (browse_map after detection, spell targeting, farlook): NLE raises no misc flag for it
    { char m[256]; dr_msg(o, m, sizeof m); if (strstr(m, "(For instructions type a") || strstr(m, "Where do you want")) return 1; }
    return strstr(top, "What do you want") || strstr(top, "In what direction") || strstr(top, "[yn") || strstr(top, "[ynq") || strstr(top, "Continue?") || strstr(top, "--More--") || strstr(top, "? [");
}
typedef struct { unsigned char message[256]; int misc[3]; unsigned char tty[DR_TTY_LI * DR_TTY_CO]; signed char ttyc[DR_TTY_LI * DR_TTY_CO]; unsigned char cur[2]; } DSave;
static void dr_save(const DObs* o, DSave* s) { memcpy(s->message, o->message, 256); memcpy(s->misc, o->misc, 3 * sizeof(int)); memcpy(s->tty, o->tty_chars, sizeof s->tty); if (o->tty_colors) memcpy(s->ttyc, o->tty_colors, sizeof s->ttyc); if (o->tty_cursor) memcpy(s->cur, o->tty_cursor, 2); }
static void dr_restore(DObs* o, const DSave* s) { memcpy(o->message, s->message, 256); memcpy(o->misc, s->misc, 3 * sizeof(int)); memcpy(o->tty_chars, s->tty, sizeof s->tty); if (o->tty_colors) memcpy(o->tty_colors, s->ttyc, sizeof s->ttyc); if (o->tty_cursor) memcpy(o->tty_cursor, s->cur, 2); }

static const struct { const char* name; int off; } DR_FEATURES[] = {{"staircase up", 23}, {"staircase down", 24}, {"ladder up", 25}, {"ladder down", 26}, {"fountain", 31}, {"sink", 30}, {"grave", 28}, {"throne", 29}, {"tree", 18},
    {"doorway", 12}, {"broken door", 12}, {"open door", 13}, {"pool of water", 32}, {"water", 41}, {"molten lava", 34}, {"ice", 33}, {"air", 39}, {"cloud", 40}, {"cloudy area", 40}, {"fog/vapor cloud", 40}, {"set of iron bars", 17}, {"open drawbridge portcullis", 35}};
typedef struct { int terrain; int nobj; char objs[16][120]; short qty[16]; int engr; long price; char raw[3][DR_TTY_CO + 1]; int nraw; int partial; } DLook;
static int dr_wall_at(const short* g, int r, int c) { if (r < 0 || r >= DR_ROWS || c < 0 || c >= DR_COLS) return 0; int v = g[r * DR_COLS + c]; return v >= CMAP_OFF + 1 && v <= CMAP_OFF + 11; }
static __thread int g_door_prev_r, g_door_prev_c, g_door_prev_valid; // hero position at the previous boundary (door orientation fallback)
static void dr_parse_look_line(const DObs* o, const char* l, DLook* res) {
    // One line can carry SEVERAL "There is ..." clauses ("There is a pit here.  There is a doorway here."), and only the
    // last of them is the terrain: a pit is a trap overlay, the doorway is the floor. Parsing just the first one lost the
    // feature whenever a trap shared the square (33fb701b: a monster stood on a destroyed door, so the screen never showed
    // the change and this text was the only public evidence).
    for (const char* p = strstr(l, "There is "); p; p = strstr(p, "There is ")) {
        p += 9; if (!strncmp(p, "an ", 3)) p += 3; else if (!strncmp(p, "a ", 2)) p += 2; else if (!strncmp(p, "the ", 4)) p += 4;
        const char* e = strstr(p, " here."); if (e) {
            char name[96]; size_t n = (size_t)(e - p); if (n >= sizeof name) n = sizeof name - 1; memcpy(name, p, n); name[n] = 0;
            if (!strncmp(name, "altar", 5)) res->terrain = 27;
            else for (size_t k = 0; k < sizeof DR_FEATURES / sizeof DR_FEATURES[0]; k++) if (!strcmp(name, DR_FEATURES[k].name)) {
                res->terrain = DR_FEATURES[k].off;
                if (DR_FEATURES[k].off == 13) { int r = (int)o->blstats[1], c = (int)o->blstats[0];
                    int lr = dr_wall_at(o->glyphs, r, c - 1) || dr_wall_at(o->glyphs, r, c + 1), ud = dr_wall_at(o->glyphs, r - 1, c) || dr_wall_at(o->glyphs, r + 1, c);
                    if (lr && !ud) res->terrain = 14; else if (ud && !lr) res->terrain = 13;
                    else { int dcol = c - g_door_prev_c, drow = r - g_door_prev_r; res->terrain = (g_door_prev_valid && drow != 0 && dcol == 0) ? 14 : 13; } } // entered vertically: door in a horizontal wall
            }
        }
    }
    int bits; if (dr_read_engr(l, &bits)) res->engr = bits;
    else if (!res->engr && (strstr(l, "written here") || strstr(l, "engraved here") || strstr(l, "burned into") || strstr(l, "scrawled in blood") || strstr(l, "graffiti"))) res->engr = 1;
    const char* q = l;
    while ((q = strchr(q, '(')) != NULL) { q++; const char* z = NULL; if (!strncmp(q, "for sale, ", 10)) z = q + 10; else if (!strncmp(q, "unpaid, ", 8)) z = q + 8;
        if (z && isdigit((unsigned char)*z)) { long v = atol(z); const char* zz = z; while (isdigit((unsigned char)*zz)) zz++; if (!strncmp(zz, " zorkmid", 8)) res->price = (res->price < 0 ? 0 : res->price) + v; } }
}
// Is a window actually open? AutoAscend answers this from the SCREEN, not from the interface flags, scanning for one of
// three markers (agent.py _find_marker): "--More--", "(end)", or a page counter "(N of M)". The flags are not a reliable
// answer -- guarding the probes' trailing ESC on them alone collapsed both corpora to 0 exact on 2026-09-11.
static int dr_window_open(const DObs* o) {
    if (o->misc && (o->misc[0] || o->misc[1] || o->misc[2])) return 1;
    if (!o->tty_chars) return 0;
    for (int r = 0; r < DR_TTY_LI; r++) {
        char row[DR_TTY_CO + 1]; dr_row(o, r, row);
        if (strstr(row, "--More--") || strstr(row, "(end)")) return 1;
        for (const char* q = strchr(row, '('); q; q = strchr(q + 1, '(')) { // "(3 of 7)"
            const char* d = q + 1; if (!isdigit((unsigned char)*d)) continue;
            while (isdigit((unsigned char)*d)) d++;
            if (strncmp(d, " of ", 4)) continue; d += 4;
            if (!isdigit((unsigned char)*d)) continue;
            while (isdigit((unsigned char)*d)) d++;
            if (*d == ')') return 1; }
    }
    return 0;
}

static const char* DR_CELL_EVENTS[] = {"You can see again", "crashes on", "shards", "is missed", "It misses", "It hits", "evaporates", "You drop", "You throw", "You fire", "hits the", "misses the", "is killed", "You kill", "misses you", "hits you", "You are hit", "hit by", "almost hit", "throws", "shoots", "fires", "hurls", "whizz", "lands", "falls", "drops", "out of your", "break out of", "falls off", "slides off", "slips", "to the floor", "seams burst", "You spill", "You see here", "Things that are here", "There are", "There is", "You finish", "You kill", "You destroy", "shatter", "You dig", "You read", "corpse", "engrav", "write", "picks up", "You put", "You take", " - ", "You empty", "You loot", "You open", "welcome", "Welcome", "disappear", "vanish", "crumble", "rot", "You eat", "You start eating"};
static int dr_cell_event(const char* msg) { if (!msg || !*msg) return 0; for (size_t k = 0; k < sizeof DR_CELL_EVENTS / sizeof DR_CELL_EVENTS[0]; k++) if (strstr(msg, DR_CELL_EVENTS[k])) return 1; return 0; }
static int dr_look_here(DState* S, DObs* o, void* ctx, dr_send_fn send, DLook* res) {
    S->last_skip = 0;
    if (S->count_pending) { S->probes_deferred++; S->last_skip = 1; return 0; }
    long cond = o->blstats[25];
    // hallucination: xname draws RNG for the fake names -> never look; blind: the look is RNG-free and dknown-free
    // (xname skips dknown when Blind) and the cockatrice feel already happened on the fork's arrival look, so it is allowed
    // (allowing the blind look was tried: the game then RNG-diverges in half the episodes)
    if ((cond & 0x200) || (cond & 0x20)) { S->probe_skip_blind++; S->last_skip = 3; return 0; }
    for (int k = 0; k < DR_CELLS; k++) if (o->glyphs[k] >= SWALLOW_OFF && o->glyphs[k] < SWALLOW_HI) { S->probe_skip_engulf++; S->last_skip = 4; return 0; }
    if (dr_prompt_open(o)) { S->probe_skip_prompt++; S->last_skip = 5; return 0; }
    DSave sv; dr_save(o, &sv);
    memset(res, 0, sizeof *res); res->terrain = -1; res->price = -1;
    char lines[24][DR_TTY_CO + 1]; int nl = 0; char win[64][120]; int nw = 0; int win_started = 0, win_col = 0; int paged_no_hdr = 0, hdr_empty = 0;
    // (a ^P/^R "park the cursor" prep was tried here and refuted: it wedges the headless port, and both keys
    //  are outside the NetHack Challenge action set. Removed 2026-09-10 so no debug switch can leave that set.)
    if (o->rawout && o->rawlen) *o->rawlen = 0;
    send(ctx, ':'); S->probes++; S->probe_keys++;
    for (int it = 0; it < 10; it++) {
        char m[256]; dr_msg(o, m, sizeof m); char* ms = m; while (*ms == ' ') ms++; size_t L = strlen(ms); while (L && ms[L - 1] == ' ') ms[--L] = 0;
        if (*ms && nl < 24) snprintf(lines[nl++], DR_TTY_CO + 1, "%.80s", ms);
        if (o->misc[2]) {
            // the pile window: an overlay (header row, then item rows at the header's column until "(end)"/"--More--")
            // or, when it does not fit, a paged window whose later pages carry item rows from the top until the mark
            int any = 0, hdr_row = -1;
            for (int r = 0; r < DR_TTY_LI; r++) { char row[DR_TTY_CO + 1]; dr_row(o, r, row); const char* h = strstr(row, "Things that are here"); if (!h) h = strstr(row, "that you feel here"); if (h) { any = 1; hdr_row = r; win_col = (int)(h - row); win_started = 1; break; } }
            if (!any && !win_started) paged_no_hdr = 1; // a later page of a pile window whose first page the tty already dropped (> ~16 objects): the list we read is incomplete // the overlay window sits at the header's column; the map may fill the columns to its left
            if (any || win_started) { int nw0 = nw;
                for (int r = (any ? hdr_row + 1 : 0); r < DR_TTY_LI; r++) { char row[DR_TTY_CO + 1]; dr_row(o, r, row);
                    const char* rr = row + (win_col < (int)strlen(row) ? win_col : (int)strlen(row)); while (*rr == ' ') rr++;
                    if (!*rr) { if (any) break; else continue; }
                    if (!strncmp(rr, "--More--", 8) || !strcmp(rr, "(end)")) break;
                    char t[120]; snprintf(t, sizeof t, "%s", rr); dr_replace_all(t, "--More--", ""); { char* e = t + strlen(t); while (e > t && e[-1] == ' ') *--e = 0; }
                    if (*t && nw < 64) snprintf(win[nw++], 120, "%s", t); }
                if (any && nw == nw0) hdr_empty = 1; // header page without a single item row: the tty anchored a too-tall window at the bottom and the item pages are shown one line at a time (only the last survives in the observation)
            } else {
                for (int r = 0; r < 2; r++) { char row[DR_TTY_CO + 1]; dr_row(o, r, row); dr_replace_all(row, "--More--", ""); char* s = row; while (*s == ' ') s++; if (*s && nl < 24) snprintf(lines[nl++], DR_TTY_CO + 1, "%s", s); }
            }
            send(ctx, ' '); /* space pages text and menu windows; Enter would close them after the first page */ S->probe_keys++; continue;
        }
        if (o->misc[0] || o->misc[1]) { send(ctx, 27); S->probe_keys++; continue; }
        break;
    }
    if (dr_window_open(o)) { send(ctx, 27); S->probe_keys++; } // marker-based, not flag-based (see dr_window_open)
    res->partial = hdr_empty; (void)paged_no_hdr; // only the observed signature: a header page with no item rows; a header-less paged text (engraving + "no objects") is not a pile window
    dr_restore(o, &sv);
    if (o->rawout && o->rawlen && *o->rawlen > 0) { // the raw terminal stream (see tmt_write in the backend): the tty drops the first full-screen page of a long pile window from the screen, the stream has every line
        char seg[200]; int sl = 0, inwin = 0, rn = 0, pending_more = 0, saw_clear = 0; static __thread char rw[64][120]; const unsigned char* p = o->rawout; int n = *o->rawlen;
#define DR_FLUSH_SEG() do { while (sl && seg[sl - 1] == ' ') sl--; seg[sl] = 0; int b = 0; while (seg[b] == ' ') b++; if (sl > b) { const char* t = seg + b; \
            if (strstr(t, "Dlvl:") || strstr(t, " St:")) inwin = -1; else if (strstr(t, "Things that are here") || strstr(t, "that you feel here")) inwin = 1; \
            else if (inwin == 1 && (!strncmp(t, "--More--", 8) || !strcmp(t, "(end)"))) { pending_more = 1; saw_clear = 0; } /* a page break: the next page starts with a cleared screen, anything else is the map repaint after the window closed */ \
            else if (inwin == 1 && pending_more && !saw_clear) inwin = -1; \
            else if (inwin == 1 && rn < 64) { pending_more = 0; char tt[120]; snprintf(tt, sizeof tt, "%s", t); dr_replace_all(tt, "--More--", ""); { char* e = tt + strlen(tt); while (e > tt && e[-1] == ' ') *--e = 0; } if (*tt) snprintf(rw[rn++], 120, "%s", tt); } } sl = 0; } while (0)
        for (int i = 0; i < n && inwin >= 0; i++) { unsigned char c = p[i];
            if (c == 27) { DR_FLUSH_SEG(); i++; if (i < n && p[i] == '[') { i++; int ps = i; while (i < n && ((p[i] >= '0' && p[i] <= '9') || p[i] == ';' || p[i] == '?')) i++; if (i < n && p[i] == 'J' && i - ps == 1 && p[ps] == '2') saw_clear = 1; } else if (i < n && (p[i] == '(' || p[i] == ')')) i++; continue; }
            if (c == '\r' || c == '\n' || c == 7 || c == 8) { DR_FLUSH_SEG(); continue; }
            if (c >= 32 && c < 127 && sl < (int)sizeof seg - 1) seg[sl++] = (char)c; }
        DR_FLUSH_SEG();
#undef DR_FLUSH_SEG
        if (rn > 0) { nw = 0; for (int i = 0; i < rn; i++) snprintf(win[nw++], 120, "%s", rw[i]); }
    }
    res->nraw = 0; for (int i = 0; i < nl && res->nraw < 3; i++) snprintf(res->raw[res->nraw++], DR_TTY_CO + 1, "%s", lines[i]);
    for (int i = 0; i < nl; i++) dr_parse_look_line(o, lines[i], res);
    for (int i = 0; i < nw; i++) { dr_parse_look_line(o, win[i], res); }
    for (int i = 0; i < nw && res->nobj < 16; i++) { res->qty[res->nobj] = (short)dr_lead_qty(win[i]); snprintf(res->objs[res->nobj++], 120, "%s", win[i]); }
    if (!res->nobj) { char item[120]; for (int i = 0; i < nl; i++) if (dr_see_here(lines[i], item, sizeof item)) { res->qty[res->nobj] = (short)dr_qty_after_here(lines[i]); snprintf(res->objs[res->nobj++], 120, "%s", item); break; } }
    if (res->price < 0 && res->nobj) for (int i = 0; i < nl; i++) if (strstr(lines[i], "no charge)")) res->price = 0;
    return 1;
}

// farlook probes (';' + getpos). Monsters are reached with the 'm' jump (nearest first), so the cursor never rests on an
// object cell: with autodescribe on, describing a cell next to the hero marks its objects dknown, which is exactly the
// side effect that made stock's screen descriptions unusable. The hero's own cell is selected directly.
static void dr_getpos_more(DState* S, DObs* o, void* ctx, dr_send_fn send) { for (int it = 0; it < 4 && o->misc[2]; it++) { send(ctx, ' '); S->probe_keys++; } }
// getpos selection ('.'): read the description BEFORE dismissing --More-- pages (with a message still on the top line the
// description arrives behind a --More--; dr_getpos_more used to space it away unread -> empty text -> "hostile"/no form). Keeps
// the page that looks like a farlook line ("x  a thing (peaceful name) [seen: ...]"), else the concatenation.
static void dr_probe_text(DState* S, DObs* o, void* ctx, dr_send_fn send, char* out, size_t n) {
    char best[256] = ""; char acc[512] = ""; char m[256]; dr_msg(o, m, sizeof m); dr_replace_all(m, "--More--", " ");
    if (m[0]) { snprintf(acc, sizeof acc, "%s", m); if (strchr(m, '(') && strchr(m, ')')) snprintf(best, sizeof best, "%s", m); }
    for (int it = 0; it < 4 && o->misc[2]; it++) { send(ctx, ' '); S->probe_keys++; dr_msg(o, m, sizeof m); dr_replace_all(m, "--More--", " ");
        if (m[0] && !strstr(acc, m)) { size_t L = strlen(acc); snprintf(acc + L, sizeof acc - L, " %s", m); if (strchr(m, '(') && strchr(m, ')')) snprintf(best, sizeof best, "%s", m); } }
    snprintf(out, n, "%s", best[0] ? best : acc);
}
static void dr_probe_self(DState* S, DObs* o, void* ctx, dr_send_fn send) {
    if (S->count_pending || dr_prompt_open(o)) return;
    if (o->blstats[25] & 0x200) return; // hallucinating: farlook names draw from the display RNG
    DSave sv; dr_save(o, &sv);
    send(ctx, ';'); S->probes++; S->probe_keys++; dr_getpos_more(S, o, ctx, send);
    send(ctx, '.'); S->probe_keys++; char m[256]; dr_probe_text(S, o, ctx, send, m, sizeof m); S->form = dr_parse_self(m); S->form_dirty = 0; S->form_t = o->blstats[20];
    if (o->misc[0] || o->misc[1] || o->misc[2]) { send(ctx, 27); S->probe_keys++; }
    dr_restore(o, &sv);
}
static void dr_probe_peaceful(DState* S, DObs* o, void* ctx, dr_send_fn send) {
    if (o->blstats[25] & 0x200) return; // hallucinating: farlook names draw from the display RNG
    long T = o->blstats[20]; int need = 0; int hr = (int)o->blstats[1], hc = (int)o->blstats[0]; int hk = hr * DR_COLS + hc;
    for (int k = 0; k < DR_CELLS; k++) { int g = o->glyphs[k];
        if (g >= 0 && g < PET_OFF) { if (k == hk) { S->peace[k] = 0; continue; } if (S->peace_dirty || S->peace_g[k] != g || T - S->peace_t[k] > 30) need++; }
        else if (g >= PET_OFF && g < INVIS_OFF) { S->peace[k] = 1; S->peace_g[k] = (short)g; S->peace_t[k] = T; }
        else { S->peace[k] = 0; S->peace_g[k] = -1; } }
    if (!need) { S->peace_dirty = 0; return; }
    if (S->count_pending || dr_prompt_open(o) || (o->blstats[25] & 0x220) || !o->tty_cursor) { S->probes_deferred++; return; }
    DSave sv; dr_save(o, &sv);
    int seen[32]; int nseen = 0;
    for (int i = 0; i < 12; i++) { // monster i: ';' then i+1 jumps, then select
        send(ctx, ';'); S->probes++; S->probe_keys++; dr_getpos_more(S, o, ctx, send);
        int k = -1;
        for (int j = 0; j <= i; j++) { send(ctx, 'm'); S->probe_keys++; dr_getpos_more(S, o, ctx, send); }
        { int r = (int)o->tty_cursor[0] - 1, c = (int)o->tty_cursor[1]; if (r >= 0 && r < DR_ROWS && c >= 0 && c < DR_COLS) k = r * DR_COLS + c; }
        int dup = 0; for (int j = 0; j < nseen; j++) if (seen[j] == k) dup = 1;
        if (k < 0 || dup || k == hk) { send(ctx, 27); S->probe_keys++; break; } // no further monster: the cursor stayed
        if (nseen < 32) seen[nseen++] = k;
        if (o->glyphs[k] < 0 || o->glyphs[k] >= PET_OFF) { send(ctx, 27); S->probe_keys++; continue; } // a pet or a remembered marker: skip, keep walking
        send(ctx, '.'); S->probe_keys++; char m[256]; dr_probe_text(S, o, ctx, send, m, sizeof m);
        S->peace[k] = (unsigned char)(strstr(m, "peaceful ") != NULL || strstr(m, "tame ") != NULL); // farlook text: "d        a dog or other canine (peaceful jackal) [seen: ...]"
        S->peace_g[k] = (short)o->glyphs[k]; S->peace_t[k] = T;
        if (o->misc[0] || o->misc[1] || o->misc[2]) { send(ctx, 27); S->probe_keys++; }
    }
    dr_restore(o, &sv); S->peace_dirty = 0;
}

// '+' spell menu
static int dr_spellbook_index(const char* name) { for (int i = 0; i < NUM_OBJECTS; i++) if (NHT_OBJ_CLASS[i] == NHT_SPBOOK_CLASS && !strcmp(NHT_OBJ_NAME[i], name)) return i; return -1; }
static void dr_probe_spells(DState* S, DObs* o, void* ctx, dr_send_fn send) {
    if (o->blstats[25] & 0x200) return; // hallucinating: no probe key at all (every redraw draws hallucinated glyphs from the display RNG, whose state the fork's screen depends on)

    if (S->count_pending) { S->probes_deferred++; return; }
    if (dr_prompt_open(o)) return;
    DSave sv; dr_save(o, &sv);
    send(ctx, '+'); S->probe_keys += 2;
    S->nsp = 0;
    for (int r = 0; r < DR_TTY_LI && S->nsp < 8; r++) {
        char row[DR_TTY_CO + 1]; dr_row(o, r, row);
        // "<a> - <name>   <lev> <school> <fail>% <retention>"
        for (const char* p = row; *p; p++) {
            if (!((p == row || p[-1] == ' ') && islower((unsigned char)p[0]) && p[1] == ' ' && p[2] == '-' && p[3] == ' ')) continue;
            const char* nm = p + 4; const char* e = strstr(nm, "  "); if (!e) break;
            char name[64]; size_t n = (size_t)(e - nm); if (n >= sizeof name) n = sizeof name - 1; memcpy(name, nm, n); name[n] = 0;
            char* t = name + strlen(name); while (t > name && t[-1] == ' ') *--t = 0;
            int idx = dr_spellbook_index(name); if (idx < 0) break;
            const char* q = e; while (*q == ' ') q++; int lev = atoi(q); while (isdigit((unsigned char)*q)) q++; while (*q == ' ') q++;
            while (*q && *q != ' ') q++; while (*q == ' ') q++; int fail = atoi(q); while (isdigit((unsigned char)*q)) q++; if (*q == '%') q++; while (*q == ' ') q++;
            int ret = 0; if (!strncmp(q, "(gone", 5)) ret = 0; else { const char* d = strrchr(q, '-'); ret = atoi(d ? d + 1 : q); }
            S->sp_ids[S->nsp] = (short)idx; S->sp_levs[S->nsp] = (signed char)lev; S->sp_fails[S->nsp] = (signed char)fail; S->sp_knows[S->nsp] = ret * 200; S->nsp++;
            break;
        }
    }
    send(ctx, 27);
    dr_restore(o, &sv);
}
// '\' discoveries
static void dr_note_discovered(DState* S, int idx) { if (idx >= 0 && idx < NUM_OBJECTS && (g_shuffled[idx] || NHT_OBJ_DESCR[idx][0])) { S->discovered[idx] = 1; } }
static void dr_probe_discoveries(DState* S, DObs* o, void* ctx, dr_send_fn send) {
    if (S->count_pending) { S->probes_deferred++; return; }
    if (o->blstats[25] & 0x20) { S->probe_skip_blind++; return; } // blind: the list window's docrt() would refresh the hero's square memory from the object chain (the fork never redraws there)
    if (dr_prompt_open(o)) return;
    if (o->blstats[25] & 0x200) return; // hallucinating: the list shows random names drawn from the display RNG, whose state the fork's hallucinated screen depends on (c7e37f2a k9200: 18 monster cells + inventory glyphs)
    // (blind deferral removed 16:30: identities learned late cost more map cells than the rare full-screen repaint)
    DSave sv; dr_save(o, &sv); int rows_seen = 0;
    // The window does not always open: a '\\' arriving while the engine still has a prompt pending is eaten, and the probe then
    // scrapes the map and comes back with almost nothing (measured: 523 of 4327 probes on one game). Learning is additive, so a
    // short read cannot unlearn anything -- it silently DELAYS an identity, which is exactly the late-identity divergence family
    // (8bef51f5: the engine identified a potion on the very key whose probe read one row). Retry when the read is short of the
    // most rows this game has ever shown; the list only ever grows, so that high-water mark is a sound floor.
    for (int attempt = 0; attempt < 2; attempt++) {
    rows_seen = 0;
    send(ctx, '\\'); S->probe_keys += 2;
    // Page cap: with no clear-to-end-of-screen the window SCROLLS, so a long list arrives one entry per page rather than a
    // screenful at a time (8bef51f5 T34497: page 1 = title only, page 2 = a single row, then --More-- again). Six pages
    // truncated every list past a handful of items. The loop still exits as soon as no --More-- is on screen, so the higher
    // cap costs nothing on short lists; discovery lists cannot exceed a few dozen entries.
    for (int it = 0; it < 96; it++) {
        for (int r = 0; r < DR_TTY_LI; r++) {
            char row[DR_TTY_CO + 1]; dr_row(o, r, row); char* s = row;
            // the menu overlays the map: keep only the text after the last run of two spaces (a map row with "(" in it used to
            // be stripped as a parenthetical and the entry was never learned, e.g. "#|(.....#   wand of striking (zinc)")
            { char* last = NULL; for (char* q = s; q[0] && q[1]; q++) if (q[0] == ' ' && q[1] == ' ') last = q; if (last) { s = last; while (*s == ' ') s++; } }
            while (*s == ' ') s++; if (*s == '*') s++; while (*s == ' ') s++;
            char* par = strstr(s, " ("); size_t L = strlen(s);
            if (!par) continue; if (s[L - 1] != ')') continue;
            rows_seen++;
            char descr[64]; snprintf(descr, sizeof descr, "%.60s", par + 2); { char* e = strrchr(descr, ')'); if (e) *e = 0; }
            *par = 0; if (strstr(s, " called ")) continue; int idx = dr_name_index(s); dr_note_discovered(S, idx);
            if (idx >= 0) { char dl[64]; dr_lower(dl, descr, sizeof dl); int slot = dr_appearance_descr_c(dl, NHT_OBJ_CLASS[idx]); if (slot >= 0) dr_learn_type_src(S, slot, idx, 2); }
        }
        // The tty build has no clear-to-end-of-screen, so a window taller than the space below the cursor SCROLLS: the entries
        // walk off the top and the screen keeps only the title and a "--More--" (turn 34497 of 8bef51f5: rows 0-21 blank,
        // row 22 "Discoveries", row 23 " --More--"). misc[2] does not always flag that, so page on the screen text too --
        // tty_chars is a challenge-visible channel, unlike the raw terminal stream the pile parser uses.
        { int more = 0; for (int r = DR_TTY_LI - 3; r < DR_TTY_LI && !more; r++) { if (r < 0) continue; char mr[DR_TTY_CO + 1]; dr_row(o, r, mr); if (strstr(mr, "--More--")) more = 1; }
          if (o->misc[2] || more) { send(ctx, ' '); /* space pages text and menu windows; Enter would close them after the first page */ S->probe_keys++; continue; } }
        break;
    }
    send(ctx, 27);
    if (rows_seen >= S->disc_rows) break;
    }
    dr_restore(o, &sv);
    if (rows_seen > S->disc_rows) S->disc_rows = rows_seen; // high-water mark: the discoveries list never shrinks
}

// ---------------------------------------------------------------- appearance learning
static void dr_learn_type_src(DState* S, int slot, int type, int src) {
    if (slot < 0 || type < 0 || slot >= NUM_OBJECTS || type >= NUM_OBJECTS || slot == type) return;
    if (NHT_OBJ_CLASS[slot] != NHT_OBJ_CLASS[type]) return;
    if (!g_shuffled[type]) return; // unshuffled classes: the raw glyph already is the type; a discovered twin (runesword) must not remap its description twins (elven broadsword)
    // The discoveries list pairs a name with its appearance on one line, so it cannot mis-pair. Inventory text is paired with
    // inv_glyphs by index, and those two arrays are not always captured at the same instant (a probe can refill one), which
    // produced contradictory learns: one game taught THREE different appearance slots for "a scroll of teleportation", only
    // one of them right. So a list-taught mapping is never overwritten by weaker evidence, and a type may own only one slot.
    if (S->descr_src[slot] == 2 && src < 2 && S->type_of_descr[slot] != type) return;
    if (src < 2) { for (int q = 0; q < NUM_OBJECTS; q++) if (q != slot && S->descr_src[q] == 2 && S->type_of_descr[q] == type) return; }
    // and retract weaker claims on this type: a type has exactly one appearance, so when the list finally names it, any slot
    // that a text pairing had already guessed for it was wrong and must go back to unknown (the bad learn usually lands first).
    if (src == 2) { for (int q = 0; q < NUM_OBJECTS; q++) if (q != slot && S->descr_src[q] < 2 && S->type_of_descr[q] == type) { S->type_of_descr[q] = -1; S->descr_src[q] = 0; } }
    S->type_of_descr[slot] = (short)type; S->descr_src[slot] = (unsigned char)src;
}
static void dr_learn_type(DState* S, int slot, int type) { dr_learn_type_src(S, slot, type, 1); }
// text shows a real name (the type is name-known) next to raw glyph g: learn the slot -> type pair
static int dr_learn_named(DState* S, int g, const char* text, int oc) {
    if (g < OBJ_OFF || g >= CMAP_OFF || !text || !*text) return -1;
    char tl[DR_INVSTR]; dr_lower(tl, text, sizeof tl);
    if (strstr(tl, " called ")) return -1; // user-named, not identified
    int t = dr_name_index_lower_c(tl, oc >= 0 ? oc : NHT_OBJ_CLASS[g - OBJ_OFF]);
    if (t >= 0) dr_learn_type(S, g - OBJ_OFF, t);
    return t;
}
// ---------------------------------------------------------------- inventory
typedef struct { char t[DR_INVSTR]; int oc, g, idx; } DItem;
static int dr_inv_items(const DObs* o, DItem* out) {
    int n = 0;
    for (int i = 0; i < DR_INV; i++) { if (!o->inv_letters[i]) break; dr_invstr(o, i, out[n].t); out[n].oc = o->inv_oclasses[i]; out[n].g = o->inv_glyphs[i]; out[n].idx = (out[n].g >= OBJ_OFF && out[n].g < CMAP_OFF) ? out[n].g - OBJ_OFF : -1; n++; }
    return n;
}
static int dr_quantity(const char* t) { if (isdigit((unsigned char)t[0])) { const char* p = t; while (isdigit((unsigned char)*p)) p++; if (*p == ' ') return atoi(t); } return 1; }
static int dr_erosion(const char* t, const char* w) { char b[64]; snprintf(b, sizeof b, "thoroughly %s", w); if (strstr(t, b)) return 3; snprintf(b, sizeof b, "very %s", w); if (strstr(t, b)) return 2; return strstr(t, w) ? 1 : 0; }
static void dr_item_state(DState* S, const DItem* it, signed char st[8], short* true_glyph) {
    char t[DR_INVSTR]; dr_lower(t, it->t, sizeof t); memset(st, 0, 8);
    if (it->oc == 12) { int q = dr_quantity(t); st[1] = -128; st[2] = (signed char)(q > 127 ? 127 : q); *true_glyph = NO_GLYPH; return; }
    char sp[DR_INVSTR + 2]; snprintf(sp, sizeof sp, " %s", t);
    st[0] = strstr(sp, " cursed ") ? 1 : (strstr(t, "blessed") ? 3 : (strstr(t, "uncursed") ? 2 : 0));
    if (strstr(t, "unholy water")) st[0] = 1; else if (strstr(t, "holy water")) st[0] = 3;
    int have_spe = 0, spe = -128;
    { const char* p = strchr(t, '('); while (p) { const char* q = p + 1; if ((*q == '-' || *q == '+' || isdigit((unsigned char)*q))) { const char* c = strchr(q, ':'); if (c && c < strchr(q, ')') ) { spe = atoi(c + 1); have_spe = 1; break; } } p = strchr(p + 1, '('); } }
    if (!have_spe) { // "^(an?|N)? (words)? ([+-]N) "
        const char* p = t; if (!strncmp(p, "an ", 3)) p += 3; else if (!strncmp(p, "a ", 2)) p += 2; else if (isdigit((unsigned char)*p)) { while (isdigit((unsigned char)*p)) p++; while (*p == ' ') p++; }
        for (const char* q = p; *q && q < t + 40; q++) if ((q == p || q[-1] == ' ') && (*q == '+' || *q == '-') && isdigit((unsigned char)q[1])) { const char* e = q + 1; while (isdigit((unsigned char)*e)) e++; if (*e == ' ') { spe = atoi(q); have_spe = 1; } break; }
    }
    // rings: the fork exports spe when obj->known (rings without charges are born known -> 0); a chargeable ring shows
    // "+N" once known, so no "+N" on a chargeable type means -128. Unidentified rings: assume the common non-chargeable case.
    if (!have_spe && it->oc == 4) { static const char* chg[] = {"adornment", "gain strength", "gain constitution", "increase accuracy", "increase damage", "protection"};
        int chargeable = 0; for (int c = 0; c < 6; c++) { const char* q = strstr(t, chg[c]); if (q && !(c == 5 && !strncmp(q, "protection from", 15))) chargeable = 1; } if (!chargeable) { have_spe = 1; spe = 0; } }
    st[1] = (signed char)(have_spe ? (spe > 127 ? 127 : (spe < -128 ? -128 : spe)) : -128);
    if (st[0] == 0 && (S->role == 6 || (have_spe && it->oc != 3 && it->oc != 4))) st[0] = 2;
    int q = dr_quantity(t); st[2] = (signed char)(q > 127 ? 127 : q);
    int e1 = dr_erosion(t, "rusty"); int e1b = dr_erosion(t, "burnt"); st[3] = (signed char)(e1 > e1b ? e1 : e1b);
    int e2 = dr_erosion(t, "corroded"); int e2b = dr_erosion(t, "rotted"); st[4] = (signed char)(e2 > e2b ? e2 : e2b);
    int f = 0;
    if (strstr(t, "(being worn") || strstr(t, "(on right hand") || strstr(t, "(on left hand") || strstr(t, "(embedded in your skin")) f |= 1;
    if (strstr(t, "(weapon in hand") || strstr(t, "(wielded") || strstr(t, "(weapon in hands")) f |= 2;
    if (strstr(t, "(alternate weapon")) f |= 4;
    if (strstr(t, "(in quiver") || strstr(t, "(at the ready")) f |= 8;
    if (strstr(t, "poisoned")) f |= 16;
    if (strstr(t, "greased")) f |= 32;
    if (strstr(t, "rustproof") || strstr(t, "fireproof") || strstr(t, "corrodeproof") || strstr(t, "fixed")) f |= 64;
    st[5] = (signed char)f;
    int idx = dr_name_index_lower_c(t, it->oc);
    int known = idx >= 0 && !strstr(t, "called");
    if (known && it->oc == 13) { const char* tl0 = t; char tl[DR_INVSTR]; dr_lower(tl, tl0, sizeof tl);
        if (strstr(tl, " gem") || strstr(tl, "gray stone")) known = 0; } // "a blue gem" / "a gray stone" are appearances, not identified names: the resolver picks the description's first type, which must not count as discovered (the fork keeps canonicalizing until oc_name_known)
    if (known) dr_note_discovered(S, idx);
    st[6] = (signed char)(known ? 1 : 0);
    if (it->g >= BODY_OFF && it->g < BODY_OFF + NUMMONS) idx = g_corpse_idx;
    *true_glyph = (short)(known ? OBJ_OFF + idx : NO_GLYPH);
}
static int dr_parse_self(const char* d) { // farlook text of the hero's own cell: "<form> called <name>" when polymorphed
    const char* ca = strstr(d, " called "); if (!ca) return -1;
    const char* st = d; for (const char* p = d; p < ca; p++) if (*p == '(') st = p + 1; // "d        a dog or other canine (werejackal called Agent)": the form is the parenthesised name (parsed from the line start before 2026-09-12: never matched)
    char name[256]; size_t n = (size_t)(ca - st); if (n >= sizeof name) n = sizeof name - 1; memcpy(name, st, n); name[n] = 0;
    char* nm = name; while (*nm == ' ') nm++; if (!strncmp(nm, "a ", 2)) nm += 2; else if (!strncmp(nm, "an ", 3)) nm += 3; else if (!strncmp(nm, "the ", 4)) nm += 4;
    static const char* races[] = {"human", "elf", "dwarf", "gnome", "orc", "elven", "dwarvish", "gnomish", "orcish"};
    for (int k = 0; k < 9; k++) { size_t L = strlen(races[k]); if (!strncmp(nm, races[k], L) && (nm[L] == ' ' || !nm[L])) return -1; }
    int mi = dr_mon_index_suffix(nm); if (mi < 0 || (mi >= 327 && mi <= 341)) return -1;
    if (!strncasecmp(NHT_MON_NAME[mi], "were", 4)) { // the name is shared by the animal (low index, 'd'/'r'/'w') and the @ form: the line's class letter picks
        const char* q = d; while (*q == ' ') q++; int lo = -1, hi = -1; for (int i = 0; i < NUMMONS; i++) if (!strcasecmp(NHT_MON_NAME[i], NHT_MON_NAME[mi])) { if (lo < 0) lo = i; hi = i; }
        mi = (*q == '@') ? hi : lo; }
    return mi;
}
static const char* DR_BOWS[] = {"bow", "elven bow", "orcish bow", "yumi"}; static const char* DR_ARROWS[] = {"arrow", "elven arrow", "orcish arrow", "silver arrow", "ya"};
static const char* DR_TWOH[] = {"two-handed sword", "tsurugi", "battle-axe", "quarterstaff", "dwarvish mattock", "lance", "bow", "elven bow", "orcish bow", "yumi", "crossbow", "glaive", "halberd", "bardiche", "voulge", "dwarvish spear", "spetum", "lucern hammer", "guisarme", "ranseur", "bill-guisarme", "partisan", "fauchard", "bec de corbin"};
static int dr_in(const char* s, const char** arr, int n) { for (int i = 0; i < n; i++) if (!strcmp(s, arr[i])) return 1; return 0; }
static int dr_corpse_mon_from_text(const char* t) { // "a partly eaten uncursed newt corpse" -> newt (suffix match; articles/quantities irrelevant)
    char s[256]; dr_lower(s, t, sizeof s); const char* cp = strstr(s, " corpse"); if (!cp) return -1;
    char cand[128] = ""; size_t k = (size_t)(cp - s); if (k >= sizeof cand) k = sizeof cand - 1; memcpy(cand, s, k); cand[k] = 0;
    const char* strip[] = {"partly eaten ", "uncursed ", "cursed ", "blessed ", "very rotten ", "rotten ", "stale "}; for (int q = 0; q < 7; q++) dr_replace_all(cand, strip[q], "");
    char* c2 = cand; while (*c2 == ' ') c2++; return dr_mon_index_suffix(c2);
}
static void dr_derive_inventory(DState* S, const DObs* o, const DItem* items, int n) {
    long cond = o->blstats[25];
    int lnc = 0;
    for (int i = 0; i < n; i++) {
        const char* nm = items[i].idx >= 0 ? NHT_OBJ_NAME[items[i].idx] : "";
        int isb = dr_in(nm, DR_BOWS, 4), iscb = !strcmp(nm, "crossbow"), issl = !strcmp(nm, "sling");
        if (!isb && !iscb && !issl) continue;
        int ammo = 0;
        for (int j = 0; j < n; j++) { const char* nj = items[j].idx >= 0 ? NHT_OBJ_NAME[items[j].idx] : ""; if ((isb && dr_in(nj, DR_ARROWS, 5)) || (iscb && !strcmp(nj, "crossbow bolt")) || (issl && items[j].oc == 13)) ammo = 1; }
        if (ammo) lnc |= 1;
        if (strstr(items[i].t, "(weapon in hand")) { lnc |= 2; if (ammo) lnc |= 4; }
    }
    int wt = 0;
    // The inventory TEXT is never hallucinated (objnam.c has no Hallucination branch); the glyphs are (random_obj_to_glyph). So price
    // from the text first -- real name -> true type, corpse -> its monster -- then the glyph (= appearance slot on both engines, the
    // fork's f7d8749ab pricing) when it can be trusted, and the appearance named by the text while hallucinating.
    int hallu = (cond & 0x200) != 0;
    for (int i = 0; i < n; i++) {
        const char* t = items[i].t; int q = dr_quantity(t); int half = strstr(t, "partly eaten") ? 2 : 1;
        if (items[i].oc == 12) { wt += (q + 50) / 100; continue; }
        int mi = dr_corpse_mon_from_text(t);
        if (mi < 0 && !hallu && items[i].g >= BODY_OFF && items[i].g < BODY_OFF + NUMMONS) mi = items[i].g - BODY_OFF;
        if (mi >= 0) { wt += (NHT_MON_CWT[mi] * q) / half; continue; }
        int idx; { char tl[256]; dr_lower(tl, t, sizeof tl); idx = dr_name_index_lower_c(tl, items[i].oc); } // class-aware: food "tin"/"orange" are not the wand/potion appearances
        if (idx < 0 && !hallu) idx = items[i].idx;
        if (idx < 0) { char tl[256]; dr_lower(tl, t, sizeof tl); dr_strip_parens(tl); int j = dr_appearance_descr_c(tl, items[i].oc); if (j >= 0) idx = dr_gem_canon(j); }
        if (idx >= 0) wt += (NHT_OBJ_WT[idx] * q) / half;
    }
    int cap = 25 * ((int)o->blstats[2] + (int)o->blstats[5]) + 50;
    int form = S->form;
    if (form >= 0) { // polymorphed: no msize/mflags in the tables here; nymphs and heavy forms approximated by corpse weight
        const char* mn = NHT_MON_NAME[form]; size_t L = strlen(mn); // weight_cap(): S_NYMPH -> MAX; cwt 0 -> * msize / MZ_HUMAN; else scale by cwt unless a strong monster no heavier than a human
        if (L >= 5 && !strcmp(mn + L - 5, "nymph")) cap = 1000;
        else if (NHT_MON_CWT[form] == 0) cap = cap * NHT_MON_SIZE[form] / 2;
        else if (!(NHT_MON_M2[form] & 0x04000000u) || NHT_MON_CWT[form] > 1450) cap = cap * NHT_MON_CWT[form] / 1450;
    }
    if (S->wlegs && S->wlegs_t && o->blstats[20] > S->wlegs_t) S->wlegs = 0; // maximum duration passed: the heal message was lost
    if (cond & 0x400) cap = 1000; else { if (cap > 1000) cap = 1000; if (!(cond & 0x800)) cap -= 100 * S->wlegs; }
    if (cap < 1) cap = 1; if (cap > 1000) cap = 1000;
    int blocked = (cond & 0x84) != 0 || (int)o->blstats[3] < 4;
    for (int i = 0; i < n; i++) if (strstr(items[i].t, "(weapon in hand") && strstr(items[i].t, "cursed") && (strstr(items[i].t, "hands)") || (items[i].idx >= 0 && dr_in(NHT_OBJ_NAME[items[i].idx], DR_TWOH, 24)))) blocked = 1;
    S->lnc = lnc; S->wt = wt; S->cap = cap; S->castblk = blocked;
}
static const struct { int lvl, bit; } DR_ROLE_INNATE[13][8] = {{{1, 128}}, {{1, 1}, {7, 128}}, {{7, 128}}, {{1, 1}}, {{7, 128}}, {{1, 128}, {1, 8}, {1, 64}, {3, 1}, {11, 2}, {13, 4}, {15, 16}}, {{20, 2}}, {{0, 0}}, {{15, 64}}, {{1, 128}}, {{20, 1}}, {{1, 4}, {7, 128}}, {{0, 0}}};
static const struct { int lvl, bit; } DR_RACE_INNATE[5] = {{0, 0}, {4, 8}, {0, 0}, {0, 0}, {1, 1}};
static int dr_intrinsics(const DState* S, const DObs* o) {
    int lvl = (int)o->blstats[18]; int b = S->intr_gained;
    for (int k = 0; k < 8; k++) { int l = DR_ROLE_INNATE[S->role][k].lvl, bit = DR_ROLE_INNATE[S->role][k].bit; if (bit && lvl >= l) b |= bit; }
    if (DR_RACE_INNATE[S->race].bit && lvl >= DR_RACE_INNATE[S->race].lvl) b |= DR_RACE_INNATE[S->race].bit;
    if (o->blstats[20] < S->fast_until) b |= 128;
    if (S->form >= 0 && S->form < NUMMONS) { // polymorphed: set_uasmon PROPSETs the form's resistances into the H* intrinsics the fork exports
        unsigned mr = NHT_MON_MR[S->form]; if (mr & 32) b |= 1; if (mr & 1) b |= 2; if (mr & 2) b |= 4; if (mr & 4) b |= 8; if (mr & 16) b |= 16;
        if (NHT_MON_M1[S->form] & 0x01000000u) b |= 64;
        const char* mn = NHT_MON_NAME[S->form]; if (!strcmp(mn, "floating eye") || !strcmp(mn, "mind flayer") || !strcmp(mn, "master mind flayer")) b |= 32; }
    return b & ~S->intr_lost;
}

// ---------------------------------------------------------------- shops
static int dr_shop_welcome(const char* msg) {
    const char* p = strstr(msg, "Welcome"); if (!p) return 0; p += 7; if (!strncmp(p, " again", 6)) p += 6; if (strncmp(p, " to ", 4)) return 0; p += 4;
    const char* ex = strchr(p, '!'); if (!ex) return 0; const char* ap = strstr(p, "'s "); if (!ap || ap > ex) return 0; return 1;
}
static void dr_shop_fill(DState* S, DLevel* L, const DObs* o) {
    const short* g = o->glyphs; int sr = (int)o->blstats[1], sc = (int)o->blstats[0];
    memset(L->shop, 0, DR_CELLS); short q[DR_CELLS]; int qh = 0, qt = 0, seen = 0;
    L->shop[sr * DR_COLS + sc] = 1; q[qt++] = (short)(sr * DR_COLS + sc); seen = 1;
    while (qh < qt && seen < 600) {
        int cur = q[qh++]; int r = cur / DR_COLS, c = cur % DR_COLS;
        for (int dr = -1; dr <= 1; dr++) for (int dc = -1; dc <= 1; dc++) {
            int nr = r + dr, nc = c + dc; if ((!dr && !dc) || nr < 0 || nr >= DR_ROWS || nc < 0 || nc >= DR_COLS) continue;
            int k = nr * DR_COLS + nc; if (L->shop[k]) continue;
            int v = L->terr[k] >= 0 ? L->terr[k] : g[k];
            if ((v >= CMAP_OFF && v < CMAP_OFF + 17) || v == CMAP_OFF + 21 || v == CMAP_OFF + 22) continue;
            L->shop[k] = 1; q[qt++] = (short)k; seen++;
        }
    }
    L->shop_set = 1; L->shop_r = sr; L->shop_c = sc;
    (void)S;
}

// ---------------------------------------------------------------- per-key and per-boundary entry points
static void dr_reset(DState* S, const DObs* o, unsigned seed) {
    dr_init_tables();
    memset(S, 0, sizeof *S);
    S->cur = -1; S->price = -1; S->cap = 1000; S->last_t = -1; S->probe_turn = -1; S->disc_turn = -1; S->spells_dirty = 1;
    S->rng = seed ? seed : 1;
    for (int i = 0; i < NUM_OBJECTS; i++) { S->type_of_descr[i] = -1; S->type_prev[i] = -1; } S->engr_known_cell = -1;
    for (int k = 0; k < DR_CELLS; k++) S->peace_g[k] = -1;
    S->form = -1;
    S->bless_est = 300;
    (void)o;
}
static void dr_identity_from_text(DState* S, const DObs* o) {
    char buf[256 + 3 * (DR_TTY_CO + 2)]; dr_msg(o, buf, 256); size_t n = strlen(buf); buf[n++] = ' ';
    // the welcome line wraps past 80 columns for the longest identity ("You are a neutral female gnomish Archeologist.") and a
    // moon/Friday-13th line can replace it in the message buffer: read the top three screen rows, not just row 0 (2026-09-12: 1 % of games)
    for (int r = 0; r < 3 && n < sizeof buf - DR_TTY_CO - 2; r++) { char row[DR_TTY_CO + 1]; dr_row(o, r, row); n += (size_t)snprintf(buf + n, sizeof buf - n, "%s ", row); }
    dr_replace_all(buf, "--More--", " ");
    for (char* c = buf; *c; c++) if (*c == '\n' || *c == '\r') *c = ' '; // tty update_topl splits a message of >= 80 columns at a space it overwrites with '\n'
    const char* p = strstr(buf, "You are a"); if (!p) return; p += 9; if (*p == 'n') p++;
    char w[4][32]; int k = 0;
    while (k < 4 && *p) { while (*p == ' ') p++; int j = 0; while (*p && *p != ' ' && *p != '.' && j < 31) w[k][j++] = *p++; w[k][j] = 0; if (j) k++; if (*p == '.') break; }
    if (k < 3) return;
    static const char* ROLES[13] = {"Archeologist", "Barbarian", "Caveman", "Healer", "Knight", "Monk", "Priest", "Rogue", "Ranger", "Samurai", "Tourist", "Valkyrie", "Wizard"};
    static const char* RACES[5] = {"human", "elven", "dwarven", "gnomish", "orcish"}; static const char* RACES2[5] = {"human", "elf", "dwarf", "gnome", "orc"}; static const char* ALIGNS[3] = {"lawful", "neutral", "chaotic"};
    const char* al = w[0]; const char* ge = NULL; const char* ra; const char* ro;
    int cut = 0; if (k == 3) for (int i = 0; i < 5; i++) if (!strcmp(w[2], RACES[i])) cut = 1;
    // the welcome line is 80 columns for exactly two identities ("You are a neutral female gnomish Archeologist.", "... lawful
    // female dwarvish Archeologist."): the tty splits it with a '\n' (handled above) and shows the tail behind a --More--; if only
    // the first row survives, three words ending in a race adjective is that cut (2026-09-12: 1 % of games were male human Archeologists)
    if (cut) { ge = w[1]; ra = w[2]; ro = "Archeologist"; }
    else if (k == 4) { ge = w[1]; ra = w[2]; ro = w[3]; } else { ra = w[1]; ro = w[2]; }
    S->gender = (ge && !strcmp(ge, "female")) ? 1 : 0;
    if (!strcmp(ro, "Cavewoman")) { ro = "Caveman"; S->gender = 1; } if (!strcmp(ro, "Priestess")) { ro = "Priest"; S->gender = 1; } if (!strcmp(ro, "Valkyrie")) S->gender = 1;
    S->role = 0; S->race = 0; S->align = 1;
    for (int i = 0; i < 13; i++) if (!strcmp(ro, ROLES[i])) S->role = i;
    for (int i = 0; i < 5; i++) if (!strcmp(ra, RACES[i]) || !strcmp(ra, RACES2[i])) S->race = i;
    for (int i = 0; i < 3; i++) if (!strcmp(al, ALIGNS[i])) S->align = i;
}
// after every engine key (the env's own keys, not probes). Returns 1 if the stall cap tripped (episode should end).
static void dr_mark_lit(DState* S, const DObs* o);
static int dr_after_key(DState* S, DObs* o, void* ctx, dr_send_fn send, int key, int done) {
    S->keys++;
    char msg[256]; dr_msg(o, msg, sizeof msg);
    if (!done) {
        long turn = o->blstats[20] / 500;
        if (strstr(msg, "repertoire") || strstr(msg, "quite well already") || strstr(msg, "keener") || strstr(msg, "restored") || strstr(msg, "You learn ") || turn != S->probe_turn) S->spells_dirty = 1;
        if (S->spells_dirty && !dr_prompt_open(o)) { S->probe_turn = turn; S->spells_dirty = 0; dr_probe_spells(S, o, ctx, send); }
        long dturn = o->blstats[20] / 50; char dm[256]; dr_msg(o, dm, sizeof dm);
        // the fork shows a type's true glyph the moment its name becomes known: re-read the list after any message (identification
        // events all print one) and every 50 turns as a backstop
        if ((dturn != S->disc_turn || dm[0] || S->msg_pending) && !dr_prompt_open(o)) { S->disc_turn = dturn; dr_probe_discoveries(S, o, ctx, send); }
        S->msg_pending = 0;
        if (msg[0] && dr_cell_event(msg)) S->cell_dirty = 1; // a cell event inside a multi-key step (a missile landing during a prayer's pages): the boundary sees only the last key's message
        { int eng = 0; for (int k = 0; k < DR_CELLS; k++) if (o->glyphs[k] >= SWALLOW_OFF && o->glyphs[k] < SWALLOW_HI) { eng = 1; break; } if (S->was_engulfed && !eng) S->cell_dirty = 1; S->was_engulfed = eng; } // no look inside an engulfer; re-look once expelled
        if (S->engr_bits && msg[0]) S->cell_dirty = 1; // melee on an engraving wipes letters (u_wipe_engr): re-read it after any event
        if (strstr(msg, "You finish eating") || strstr(msg, "You finish your meal") || strstr(msg, "You feel that eating") || strstr(msg, "Rotten food") || strstr(msg, "You're having a hard time getting all of it down") || (strstr(msg, "This ") && (strstr(msg, " is delicious") || strstr(msg, " tastes"))) || strstr(msg, "You eat ")) S->meal_flag = 1;
        if (dr_gone_msg(msg)) S->took_flag = 1;
        { // "You are hit by a yellow gem." / "A crude dagger misses you." / "You are almost hit by an orcish dagger.": it lands on the hero's square
            const char* hp = strstr(msg, "You are hit by "); const char* ap = strstr(msg, "You are almost hit by "); const char* mp = strstr(msg, " misses you"); const char* item = NULL; char buf[200]; buf[0] = 0;
            if (hp) item = hp + 15; else if (ap) item = ap + 22;
            if (item) { size_t q = 0; while (item[q] && q + 1 < sizeof buf) { if (item[q] == '.' || item[q] == '!') break; buf[q] = item[q]; q++; } buf[q] = 0; }
            else if (mp) { const char* st = mp; while (st > msg && st[-1] != '.' && st[-1] != '!') st--; while (*st == ' ') st++; if (!strncmp(st, "The ", 4) || !strncmp(st, "the ", 4)) st += 4; else if (!strncmp(st, "An ", 3) || !strncmp(st, "an ", 3)) st += 3; else if (!strncmp(st, "A ", 2) || !strncmp(st, "a ", 2)) st += 2; size_t q = (size_t)(mp - st); if (q >= sizeof buf) q = sizeof buf - 1; memcpy(buf, st, q); buf[q] = 0; }
            if (buf[0]) { int f, c; DLevel* L = dr_level(S, o); int hk = (int)o->blstats[1] * DR_COLS + (int)o->blstats[0]; S->land_top = dr_resolve_item(S, buf, L->objm[hk], &f, &c); S->land_turn = o->blstats[20]; } }
        { const char* dp = strstr(msg, "You drop "); if (dp) { char item[200]; size_t q = 0; dp += 9; while (dp[q] && q + 1 < sizeof item) { if (dp[q] == '.' && (dp[q + 1] == ' ' || dp[q + 1] == 0)) break; item[q] = dp[q]; q++; } item[q] = 0;
            if (q) { int f, c; DLevel* L = dr_level(S, o); int hk = (int)o->blstats[1] * DR_COLS + (int)o->blstats[0]; S->drop_top = dr_resolve_item(S, item, L->objm[hk], &f, &c); S->drop_turn = o->blstats[20]; } } }
        if (strstr(msg, "Really attack")) { // the confirm prompt itself says the target is peaceful (the fork's mask never lets the move through)
            static const char* DK = "hjklyubn"; static const int DX[] = {-1, 0, 0, 1, -1, 1, -1, 1}, DY[] = {0, 1, -1, 0, -1, -1, 1, 1};
            const char* q = key > 0 && key < 128 ? strchr(DK, key) : NULL; if (!q && key > 0 && key < 128) q = strchr(DK, tolower(key));
            if (q) { int d = (int)(q - DK); int r = (int)o->blstats[1] + DY[d], c = (int)o->blstats[0] + DX[d];
                if (r >= 0 && r < DR_ROWS && c >= 0 && c < DR_COLS) { int k = r * DR_COLS + c; S->peace[k] = 1; S->peace_g[k] = (short)o->glyphs[k]; S->peace_t[k] = o->blstats[20]; } }
        }
        if (dr_cell_event(msg) || strstr(msg, "What do you want to write") || strstr(msg, "What do you want to drop") || strstr(msg, "What do you want to throw")) S->cell_dirty = 1;
        dr_update_memory(S, o, msg); dr_track_engraving(S, o, key, msg); dr_track_path(S, o, key); S->key_blind = (o->blstats[25] & 0x20) != 0;
        if (strstr(msg, "lit field surrounds you")) dr_mark_lit(S, o);
    }
    long t = o->blstats[20]; S->same = (t == S->last_t) ? S->same + 1 : 0; S->last_t = t;
    if (!done && (S->same >= DR_STALL_CAP || S->trunc_pending)) { S->trunc_pending = 1; return 1; }
    return 0;
}
// terrain guess for the hero's cell when nothing displayed it: NetHack only draws a corridor square once you stand
// next to it, so on arrival the cell itself is unknown. Rule: coming from a corridor or a doorway, and no orthogonal
// neighbour remembered as room floor -> corridor; any neighbour remembered as room floor/wall/door -> room floor; else corridor.
static int dr_wallv(const DLevel* L, int r, int c) { if (r < 0 || r >= DR_ROWS || c < 0 || c >= DR_COLS) return -1; int v = L->terr[r * DR_COLS + c]; return v < 0 ? -1 : v - CMAP_OFF; }
// The hero just stepped off a door (previous position) onto a never-displayed square. Doors sit in walls; the wall's corner
// pieces (3/4 top, 5/6 bottom; 3/5 left, 4/6 right) say on which side the room is: that side is floor, the other a corridor.
static int dr_door_side(const DState* S, const DLevel* L, int row, int col) {
    if (!S->d_valid) return -1;
    int pr = S->d_r, pc = S->d_c; int pv = dr_wallv(L, pr, pc); if (pv < 12 || pv > 16) return -1;
    int dr = row - pr, dc = col - pc; if (abs(dr) + abs(dc) != 1) return -1;
    int lw = dr_wallv(L, pr, pc - 1), rw = dr_wallv(L, pr, pc + 1), uw = dr_wallv(L, pr - 1, pc), dw = dr_wallv(L, pr + 1, pc);
    int horiz = (lw >= 1 && lw <= 11) || (rw >= 1 && rw <= 11), vert = (uw >= 1 && uw <= 11) || (dw >= 1 && dw <= 11);
    if (horiz && dr != 0) { for (int k = 1; k <= 12; k++) { int a = dr_wallv(L, pr, pc - k), b = dr_wallv(L, pr, pc + k);
            if (a == 3 || a == 4 || b == 3 || b == 4) return dr > 0 ? 19 : 21; /* top wall: room below */
            if (a == 5 || a == 6 || b == 5 || b == 6) return dr < 0 ? 19 : 21; /* bottom wall: room above */
            if ((a >= 0 && !(a >= 1 && a <= 16)) && (b >= 0 && !(b >= 1 && b <= 16))) break; } }
    if (vert && dc != 0) { for (int k = 1; k <= 12; k++) { int a = dr_wallv(L, pr - k, pc), b = dr_wallv(L, pr + k, pc);
            if (a == 3 || a == 5 || b == 3 || b == 5) return dc > 0 ? 19 : 21; /* left wall: room to the right */
            if (a == 4 || a == 6 || b == 4 || b == 6) return dc < 0 ? 19 : 21; /* right wall: room to the left */
            if ((a >= 0 && !(a >= 1 && a <= 16)) && (b >= 0 && !(b >= 1 && b <= 16))) break; } }
    return -1;
}
static int dr_guess_terrain(const DState* S, const DLevel* L, int row, int col) {
    int prev = S->prev_terr; int room_nb = 0, any_nb = 0, corr_nb = 0;
    { int side = dr_door_side(S, L, row, col); if (side >= 0) return side; }
    static const int dr[4] = {-1, 1, 0, 0}, dc[4] = {0, 0, -1, 1};
    for (int i = 0; i < 4; i++) { int r = row + dr[i], c = col + dc[i]; if (r < 0 || r >= DR_ROWS || c < 0 || c >= DR_COLS) continue; int v = L->terr[r * DR_COLS + c]; if (v < 0) continue; int vv = v - CMAP_OFF; any_nb++; if (vv == 19 || vv == 20) room_nb++; if (vv == 21 || vv == 22) corr_nb++; }
    // a wall corner diagonal to the cell whose inside points at the cell puts the cell inside the room (tlcorn NW, trcorn NE,
    // blcorn SW, brcorn SE); needed when objects/monsters cover the orthogonal floor (2x2 room, doorway with monsters around)
    { static const int dd[4][2] = {{-1, -1}, {-1, 1}, {1, -1}, {1, 1}}; static const int want[4] = {3, 4, 5, 6};
      if (!corr_nb) for (int i = 0; i < 4; i++) { int r = row + dd[i][0], c = col + dd[i][1]; if (r < 0 || r >= DR_ROWS || c < 0 || c >= DR_COLS) continue; if (L->terr[r * DR_COLS + c] == CMAP_OFF + want[i]) return 19; } }
    if (corr_nb && !room_nb) { for (int i = 0; i < 4; i++) { int r = row + dr[i], c = col + dc[i]; if (r < 0 || r >= DR_ROWS || c < 0 || c >= DR_COLS) continue; if (L->terr[r * DR_COLS + c] == CMAP_OFF + 22) return 22; }
        { int lit = 0, unlit = 0; for (int r = row - 2; r <= row + 2; r++) for (int c = col - 2; c <= col + 2; c++) { if (r < 0 || r >= DR_ROWS || c < 0 || c >= DR_COLS || (r == row && c == col)) continue; int v = L->terr[r * DR_COLS + c]; if (v == CMAP_OFF + 22) lit++; else if (v == CMAP_OFF + 21) unlit++; } if (lit > unlit) return 22; }
        return 21; } // S_litcorr marks a permanently lit square (waslit = lev->lit, e.g. a light-scroll pool): pools are contiguous
    if ((prev == 21 || prev == 22 || (prev >= 12 && prev <= 16)) && !room_nb) return 21; // refuted: 'undisplayed + came from a door = corridor' broke 89 episodes before turn 200 (dark rooms); keep the room-neighbour veto
    if (room_nb) return 19;
    { int diag_corr = 0; for (int r = row - 1; r <= row + 1; r++) for (int c = col - 1; c <= col + 1; c++) { if (r < 0 || r >= DR_ROWS || c < 0 || c >= DR_COLS) continue; int v = L->terr[r * DR_COLS + c]; if (v == CMAP_OFF + 21 || v == CMAP_OFF + 22) diag_corr++; }
      if (diag_corr) return 21; } // a corridor square diagonal to the cell and no room floor around it: corridors hug room walls, so a wall corner nearby does not make it a room (25204cd0 T33187, probe refused while confused)
    for (int r = row - 1; r <= row + 1; r++) for (int c = col - 1; c <= col + 1; c++) { if (r < 0 || r >= DR_ROWS || c < 0 || c >= DR_COLS) continue; int v = L->terr[r * DR_COLS + c]; if (v < 0) continue; int vv = v - CMAP_OFF; if (vv == 19 || vv == 20 || (vv >= 1 && vv <= 11)) return 19; }
    return any_nb ? 21 : 21;
}
// Terrain under the hero when neither the look nor the level memory knows it (arrival on a never-displayed cell,
// e.g. walking a dark corridor): #terrain is zero-time and redraws the known terrain map, so the hero's cell then
// carries its terrain glyph (the fork exports the true terrain there). One ESC restores the normal display.
static int dr_probe_terrain(DState* S, DObs* o, void* ctx, dr_send_fn send, int k) {
    if (S->count_pending) { S->probes_deferred++; return -1; }
    if (dr_prompt_open(o)) return -1;
    if (o->blstats[25] & 0x3a0) return -1; // blind or hallucinating: the view is meaningless; stunned or confused: "You are too disoriented for this." (25204cd0 T33187)
    for (int c = 0; c < DR_CELLS; c++) if (o->glyphs[c] >= SWALLOW_OFF && o->glyphs[c] < SWALLOW_HI) return -1; // engulfed: the terrain view's redraw leaves the engine believing the hero can see its engulfer (681d11e0 k3730: "You hit the fog cloud." became "!")
    DSave sv; dr_save(o, &sv);
    const char* cmd = "#terrain\n"; for (const char* p = cmd; *p; p++) { send(ctx, (int)(unsigned char)*p); S->probe_keys++; }
    if (o->misc[2] || o->misc[0]) { send(ctx, 13); S->probe_keys++; } // the "View which?" menu, item a preselected (13 = Enter; '\n' is not in the challenge action set)
    int v = o->glyphs[k]; int t = (v > CMAP_OFF && v < TERR_HI) ? v - CMAP_OFF : -1;
    // The view renders the WHOLE known terrain map, not just the square we asked about, and it is the engine's own answer
    // rather than something scraped off a remembered screen. Harvest all of it: it fills squares the screen never showed
    // (walls and doorways behind objects, dark floor vs lit floor) that we would otherwise have to guess at.
    { DLevel* HL = dr_level(S, o);
        for (int c = 0; c < DR_CELLS; c++) { int gv = o->glyphs[c];
            if (gv > CMAP_OFF && gv < TERR_HI) { HL->terr[c] = (short)gv; HL->guess[c] = 0; if (gv == CMAP_OFF + 22) HL->litmark[c] = 1; } } }
    send(ctx, 27); S->probe_keys++; if (o->misc[2] || o->misc[0]) { send(ctx, 27); S->probe_keys++; }
    S->probes++; S->terrain_probes++;
    dr_restore(o, &sv);
    return t;
}

// line of sight over what the hero can know: a square is see-through when it shows floor, corridor, a doorway or open door,
// stairs and other features, or a monster or object (visible things stand on see-through squares); walls, closed doors,
// trees, bars and never-displayed rock block. Bresenham between the endpoints (endpoints themselves excluded).
static int dr_transparent(const DLevel* L, const DObs* o, int k) {
    int g = o->glyphs[k];
    if (g >= 0 && g < CMAP_OFF) return 1; // a monster, object or body is showing
    int v = g > CMAP_OFF && g < TERR_HI ? g : (L->terr[k] > CMAP_OFF ? L->terr[k] : -1); if (v < 0) return 0;
    int i = v - CMAP_OFF;
    if (i <= 11 || i == 15 || i == 16 || i == 17 || i == 18) return 0;
    return 1;
}
static int dr_clear_path(const DLevel* L, const DObs* o, int r0, int c0, int r1, int c1) {
    int dr = abs(r1 - r0), dc = abs(c1 - c0), sr = r0 < r1 ? 1 : -1, sc = c0 < c1 ? 1 : -1, err = dc - dr, r = r0, c = c0;
    for (int n = 0; n < 32; n++) {
        if (r == r1 && c == c1) return 1;
        if (!(r == r0 && c == c0) && !dr_transparent(L, o, r * DR_COLS + c)) return 0;
        int e2 = 2 * err; if (e2 > -dr) { err -= dr; c += sc; } if (e2 < dc) { err += dc; r += sr; }
    }
    return 0;
}
// "A lit field surrounds you!" (scroll, spell or wand of light): do_clear_area lights every square within the radius-5 circle that
// has a clear line of sight. The screen shows the newly visible ones lit at once, but squares already in sight (adjacent, or
// under a monster or object) keep a stale glyph, and the message can sit on an inner key of a multi-key step (606aac6f
// T52376: the boundary message was the next event), so the marking runs per key from the hero's position at that key.
static void dr_mark_lit(DState* S, const DObs* o) {
    DLevel* L = dr_level(S, o); int col = (int)o->blstats[0], row = (int)o->blstats[1];
    if (row < 0 || row >= DR_ROWS || col < 0 || col >= DR_COLS) return;
    for (int r = row - 5; r <= row + 5; r++) for (int c = col - 5; c <= col + 5; c++) {
        if (r < 0 || r >= DR_ROWS || c < 0 || c >= DR_COLS) continue; int dr = r - row, dc = c - col; if (dr * dr + dc * dc > 25) continue;
        if (dr_clear_path(L, o, row, col, r, c)) L->litmark[r * DR_COLS + c] = 1; }
}
// step boundary: probe the tile and settle every hook value for the next decision
static int dr_hero_moved(DState* S, DObs* o) { // the hero's cell changed since the last boundary derive (a move inside a multi-key env step)
    if (!o->blstats) return 0; DLevel* L = dr_level(S, o); int col = (int)o->blstats[0], row = (int)o->blstats[1];
    return !S->d_valid || S->d_r != row || S->d_c != col || S->d_lv_dn != L->dnum || S->d_lv_dl != L->dlevel;
}
// polymorph state from the status line: "HD:" replaces "Xp:" while Upolyd (botl.c); exact and immediate, unlike the messages
// ("You turn into"/"You return to" fall behind --More-- or a getlin prompt). -1 = neither shown (fall back to blstats[17] > 0).
static int dr_poly_status(const DState* S, const DObs* o) {
    if (o->tty_chars) { char r[DR_TTY_CO + 1]; for (int row = 23; row >= 22; row--) { dr_row(o, row, r); if (strstr(r, "HD:")) return 1; if (strstr(r, "Xp:")) return 0; } }
    { long hd = o->blstats[17]; if (hd > 0) return 1; if (S->form >= 0 && S->form_hd > 0) return 0; return -1; } // no status text (fork recordings): HD alone, ambiguous for level-0 forms
}
static void dr_apply_drop(DState* S, DLevel* L, int k, long T) { // "You drop X": dropz -> place_object heads the chain, then stackobj merges X into an existing stack of its type (which keeps its place lower down)
    if (S->drop_turn != T || S->drop_top < 0) return;
    int merged = -1; for (int pi = 0; pi < S->npile; pi++) if (S->pile[pi] == S->drop_top) merged = pi;
    if (merged < 0) { S->top = S->drop_top; L->objm[k] = (short)S->top; if (S->npile < 8) { memmove(S->pile + 1, S->pile, (size_t)S->npile * sizeof S->pile[0]); memmove(S->pile_qty + 1, S->pile_qty, (size_t)S->npile * sizeof S->pile_qty[0]); S->npile++; } S->pile[0] = (short)S->top; S->pile_qty[0] = 1; }
    else S->pile_qty[merged]++;
    S->drop_top = -1;
}
static void dr_boundary(DState* S, DObs* o, void* ctx, dr_send_fn send) {
    DLevel* L = dr_level(S, o);
    int col = (int)o->blstats[0], row = (int)o->blstats[1]; int inb = row >= 0 && row < DR_ROWS && col >= 0 && col < DR_COLS; int k = inb ? row * DR_COLS + col : 0;
    int moved = !S->d_valid || S->d_r != row || S->d_c != col || S->d_lv_dn != L->dnum || S->d_lv_dl != L->dlevel;
    char m0[256]; dr_msg(o, m0, sizeof m0);
    int on_corpse = S->d_valid && S->top >= BODY_OFF && S->top < BODY_OFF + NUMMONS;
    int blind_now = (o->blstats[25] & 0x20) != 0; int sight_back = S->was_blind && !blind_now; S->was_blind = blind_now;
    int hero_redrawn = o->redrawn && inb && o->redrawn[k] && S->d_valid && !(!S->d_valid || S->d_r != row || S->d_c != col); // the engine reprinted the hero's square during the key (an object landed, a corpse appeared) without a message
    int acted = moved || S->cell_dirty || sight_back || hero_redrawn || dr_cell_event(m0) || o->blstats[20] <= 1 || (o->blstats[20] - S->last_look_turn >= 10) || on_corpse; // periodic revalidation: objects under the hero can vanish silently (corpses rot)
    g_door_prev_valid = S->d_valid; g_door_prev_r = S->d_r; g_door_prev_c = S->d_c;
    DLook res; int have = (inb && acted) ? dr_look_here(S, o, ctx, send, &res) : 0;
    if (have) { S->cell_dirty = 0; S->last_look_turn = o->blstats[20]; }
    else if (inb && acted && S->last_skip != 3 && S->last_skip != 4) S->cell_dirty = 1; // a look skipped for a prompt/count retries at the next boundary (an arrival under a --More-- used to lose its look for good)
    int terrain, top, food = 0, cont = 0, engr, price = -1;
    if (have) {
        int t = res.terrain;
        // the look names an open door without its orientation; the door glyph seen before stepping on it carries it
        if ((t == 13 || t == 14) && L->terr[k] >= CMAP_OFF + 13 && L->terr[k] <= CMAP_OFF + 14) t = L->terr[k] - CMAP_OFF;
        if (t < 0) {
            // the look text named no feature (a pile window without its feature line, or plain floor): a remembered
            // permanent feature at this cell (door/bars/tree/corridor/stairs/altar..water, seen before stepping on it)
            // beats probing and guessing
            int mt = L->terr[k] >= 0 ? L->terr[k] - CMAP_OFF : -1;
            if (mt == 21 && L->litmark[k]) mt = 22; // lit by a light spell while already in sight: the screen never redrew it
            int guessed = L->guess[k] && (o->blstats[25] & 0x3a0) == 0; // a guessed memory (the cell was always covered) yields to the probe when the probe may run
            // A corridor's lit state cannot be read back off a remembered screen: once out of sight NetHack redraws a lit
            // corridor with the plain corridor symbol (colour is the only difference, and memory does not keep it), while the
            // fork's hero tile calls back_to_glyph and reports the truth. The #terrain view DOES report it (measured: 15 cells
            // in one game where memory said plain and the view said lit). Probe each corridor square once per level and cache.
            if (mt == 21 && !L->corr_seen[k] && (o->blstats[25] & 0x3a0) == 0) {
                int pv = dr_probe_terrain(S, o, ctx, send, k);
                L->corr_seen[k] = 1;
                if (pv == 22) { L->litmark[k] = 1; L->terr[k] = (short)(CMAP_OFF + 22); mt = 22; }
            }
            if (mt == 21 && L->litmark[k]) mt = 22;
            if ((mt == 21 || mt == 22) && !guessed) t = mt;
            else if (!guessed && mt >= 12 && mt <= 41 && mt != 19 && mt != 20) t = mt;
            else if ((t = dr_probe_terrain(S, o, ctx, send, k)) >= 0) { L->terr[k] = (short)(CMAP_OFF + t); L->guess[k] = 0; }
            else if (guessed && (mt == 21 || mt == 22 || (mt >= 12 && mt <= 41 && mt != 19 && mt != 20))) t = mt;
            else if ((t = dr_guess_terrain(S, L, row, col)) >= 0) { }
            else { int nb = 0, corr = 1; for (int r = row - 1; r <= row + 1; r++) for (int c = col - 1; c <= col + 1; c++) { if (r < 0 || r >= DR_ROWS || c < 0 || c >= DR_COLS || (r == row && c == col)) continue; int v = L->terr[r * DR_COLS + c]; if (v < 0) continue; nb++; int vv = v - CMAP_OFF; if (vv != 21 && vv != 22) corr = 0; } t = (nb && corr) ? 21 : 19; }
        }
        if (t == 21 && inb && L->litmark[k]) t = 22; // lit corridor under the hero (see dr_mark_lit)
        if (res.partial && !moved && S->d_valid && S->npile > 0 && res.nobj < S->npile) { dr_apply_drop(S, L, k, o->blstats[20]); top = S->top; food = 0; cont = 0; for (int pi = 0; pi < S->npile; pi++) { food |= dr_is_food(S->pile[pi]); cont |= dr_is_cont(S->pile[pi]); } }
        else { top = -1; S->npile = 0;
        for (int i = 0; i < res.nobj; i++) { int f, c; int gl = dr_resolve_item(S, res.objs[i], L->objm[k], &f, &c); if (i == 0) top = gl; food |= f; cont |= c; if (S->npile < 8) { S->pile_qty[S->npile] = res.qty[i]; S->pile[S->npile++] = (short)gl; } }
        }
        L->objm[k] = (short)top;
        terrain = CMAP_OFF + t; engr = res.engr; price = (int)res.price; L->engr[k] = (unsigned char)res.engr;
    } else if (!moved && S->d_valid && inb) {
        dr_apply_drop(S, L, k, o->blstats[20]);
        if (S->land_turn == o->blstats[20] && S->land_top >= 0) { S->top = S->land_top; L->objm[k] = (short)S->top; if (S->npile < 8) { memmove(S->pile + 1, S->pile, (size_t)S->npile * sizeof S->pile[0]); memmove(S->pile_qty + 1, S->pile_qty, (size_t)S->npile * sizeof S->pile_qty[0]); S->npile++; } S->pile[0] = (short)S->top; S->pile_qty[0] = 1; }
        int ate = S->meal_flag || strstr(m0, "You finish eating") || strstr(m0, "You feel that eating") || strstr(m0, "Rotten food");
        int took = S->took_flag || (strstr(m0, " - ") != NULL && !strstr(m0, "What do you want")); // pickup letter assignment
        if ((ate && S->top >= 0 && ((S->top >= BODY_OFF && S->top < BODY_OFF + NUMMONS) || (S->top >= OBJ_OFF && S->top < CMAP_OFF && dr_is_food(S->top)))) || took) {
            // no look possible (blind/hallucinating): the top object left; promote the next remembered pile member
            if (ate && !took && S->npile > 0 && S->pile_qty[0] > 1) { S->pile_qty[0]--; /* one of a stack eaten: the rest stays on top */ }
            else if (S->npile > 1) { memmove(S->pile, S->pile + 1, (size_t)(S->npile - 1) * sizeof S->pile[0]); memmove(S->pile_qty, S->pile_qty + 1, (size_t)(S->npile - 1) * sizeof S->pile_qty[0]); S->npile--; S->top = S->pile[0]; } else { S->npile = 0; S->top = -1; }
            L->objm[k] = (short)S->top; food = dr_is_food(S->top); cont = dr_is_cont(S->top); top = S->top; }
        // still on the same cell, nothing happened to it: the last decision stands (the fork's hooks would return the same values)
        terrain = S->terrain; top = L->objm[k] != S->top && L->objm[k] >= 0 ? L->objm[k] : S->top; food = dr_is_food(top); cont = dr_is_cont(top); for (int pi = 0; pi < S->npile; pi++) { food |= dr_is_food(S->pile[pi]); cont |= dr_is_cont(S->pile[pi]); } engr = L->engr[k]; price = (int)S->price; // the fork scans the whole floor chain for food/containers, not the top object (2.4% food mismatch before 2026-09-12) // L->engr carries the typed/wiped model when no look is possible
    } else {
        int t = L->terr[k], ob = L->objm[k];
        if (t >= CMAP_OFF + 42) t = -1; // traps (42+) and beams/explosions are overlays, not the floor the fork's back_to_glyph reports
        if (t == CMAP_OFF + 20) t = CMAP_OFF + 19; // dark room floor is exported as room floor (the fork's back_to_glyph convention)
        if (t < 0 && o->blstats[20] <= 1 && inb) t = CMAP_OFF + 23; // game start: the hero stands on the up staircase
        if (t < 0 && inb) { int pt = dr_probe_terrain(S, o, ctx, send, k); if (pt >= 0) { t = CMAP_OFF + pt; L->terr[k] = (short)t; L->guess[k] = 0; } else { t = CMAP_OFF + dr_guess_terrain(S, L, row, col); L->guess[k] = 1; } }
        if (ob >= 0 && (S->meal_flag || strstr(m0, "You finish eating") || strstr(m0, "You feel that eating") || strstr(m0, "You eat ") || strstr(m0, "Rotten food")) && ((ob >= BODY_OFF && ob < BODY_OFF + NUMMONS) || (ob >= OBJ_OFF && ob < CMAP_OFF && dr_is_food(ob)))) { ob = -1; L->objm[k] = -1; } // arrived and ate without a look (blind)
        terrain = t; /* unknown stays -1 (was 0 = glyph 0, a monster) */ top = ob; food = dr_is_food(ob); cont = dr_is_cont(ob); engr = L->engr[k]; S->npile = ob >= 0 ? 1 : 0; S->pile[0] = (short)ob; S->pile_qty[0] = 1;
    }
    char msg[256]; dr_msg(o, msg, sizeof msg);
    if ((dr_shop_welcome(msg) || S->shop_pending) && !L->shop_set) { dr_shop_fill(S, L, o); if (terrain >= CMAP_OFF + 12 && terrain <= CMAP_OFF + 16) L->shop[k] = 0; }
    S->shop_pending = 0;
    int inshop = L->shop_set && L->shop[k];
    if (!inshop) price = -1; else if (price < 0 && top >= 0 && !have) price = 1;
    // refuted 18:40: 'lit corridor under the hero = hero carries a lit light source' — newsym sets waslit from the square's permanent lit
    // flag (lev->lit), not from the hero's light; a hero with a lit candle on a dark corridor showed S_corr in the fork.
    S->prev_terr = terrain >= CMAP_OFF ? terrain - CMAP_OFF : -1;
    if (blind_now || (o->blstats[25] & 0x200)) { engr = (inb && k == S->engr_known_cell) ? L->engr[k] : 0; if (inb && engr > 1) engr = 1; } // cap at 1 whenever we cannot see, not only when we wrote it blind: the fork also caps on nle_engr_wiped, i.e. scuffed
        // since last read, and wiping (u_wipe_engr on melee and movement) is silent and random so we can never observe it.
        // Claiming an intact Elbereth we have not re-read is the 63-of-66 overcount; under-claiming is the rarer error (3). // blind: the fork exports what the hero last knew on the one square it remembers, nothing elsewhere
    else if (inb) { S->engr_known_cell = k; L->engr_blind[k] = 0; } // sighted: the truth is public and becomes the remembered belief for this square
    S->terrain = terrain; S->top = top; S->food = food; S->cont = cont; S->engr_bits = engr; S->inshop = inshop; S->price = price;
    S->meal_flag = 0; S->took_flag = 0;
    S->d_lv_dn = L->dnum; S->d_lv_dl = L->dlevel; S->d_r = row; S->d_c = col; S->d_valid = inb;
    { int ps = dr_poly_status(S, o); long hd = o->blstats[17];
      if (ps == 0 && S->form >= 0) { S->form = -1; S->form_dirty = 0; }              // reverted to the natural form: no probe needed
      else if (ps == 1 && (S->form < 0 || hd != S->form_hd)) S->form_dirty = 1;      // entered a form, or the form changed (different HD)
      S->form_hd = hd;
      if (S->form_dirty && ps != 0) dr_probe_self(S, o, ctx, send); }                 // before inventory/capacity/intrinsics use the form
    DItem items[DR_INV]; int n = dr_inv_items(o, items);
    for (int i = 0; i < n; i++) dr_learn_named(S, items[i].g, items[i].t, items[i].oc);
    if (o->sdesc) for (int k = 0; k < DR_CELLS; k++) { int g = o->glyphs[k]; if (g >= OBJ_OFF && g < CMAP_OFF) dr_learn_named(S, g, (const char*)o->sdesc + (size_t)k * 80, -1); }
    { long T = o->blstats[20]; char pm[256]; dr_msg(o, pm, sizeof pm);
      if (!S->prayed && strstr(pm, "You begin praying")) { S->prayed = 1; S->pray_turn = T; }
      long v = S->prayed ? 350 - (T - S->pray_turn) : 300 - (T - 1); S->bless_est = v > 0 ? v : 0; }
    dr_derive_inventory(S, o, items, n); S->intr = dr_intrinsics(S, o);
    S->prev_inv_n = n < DR_INV ? n : DR_INV; for (int i = 0; i < S->prev_inv_n; i++) { S->prev_inv_g[i] = (short)items[i].g; S->prev_inv_oc[i] = (signed char)items[i].oc; snprintf(S->prev_inv_t[i], DR_INVSTR, "%s", items[i].t); }
    if (o->inv_state || o->inv_true) for (int i = 0; i < DR_INV; i++) {
        signed char st[8] = {0}; short tg = NO_GLYPH;
        if (i < n) dr_item_state(S, &items[i], st, &tg);
        if (o->inv_state) memcpy(o->inv_state + i * 8, st, 8);
        if (o->inv_true) o->inv_true[i] = tg;
    }
    S->prev_dex = (int)o->blstats[4];
    dr_probe_peaceful(S, o, ctx, send);
    if (S->form >= 0 && !S->form_dirty && o->blstats[20] - S->form_t >= 40) S->form_dirty = 1; // periodic re-check while polymorphed
    if (S->form_dirty) dr_probe_self(S, o, ctx, send);
}
// glyph export for the stock backend: appearance bijection on undiscovered shuffled types, hero tile = top object else terrain
static inline short dr_map_glyph(const DState* S, short g) {
    if (g >= OBJ_OFF && g < CMAP_OFF) { int i = g - OBJ_OFF; if (!S->discovered[i] && dr_gem_canon(i) != i) { return (short)(OBJ_OFF + dr_gem_canon(i)); } int t = S->type_of_descr[i]; if (t >= 0) return (short)(OBJ_OFF + t); }
    return g;
}
static void dr_export_glyphs(DState* S, DObs* o, int with_hero_tile) {
    for (int k = 0; k < DR_CELLS; k++) { S->map_raw[k] = o->glyphs[k]; S->map_out[k] = o->glyphs[k] = dr_map_glyph(S, o->glyphs[k]); } S->map_valid = 1; // identities apply at every fill, as the fork does
    // inventory glyphs stay in slot form on both engines (the fork's inventory fill uses shuffled_glyph only); the map uses maybe_true_glyph
    if (with_hero_tile && S->d_valid) {
        int under = S->top >= 0 ? S->top : S->terrain;
        if (under < 0) under = CMAP_OFF + 19;
        // public-obs fork export: while blind OR hallucinating the hero's own cell shows the hero glyph (the screen buffer), not the pile;
        // stock's raw glyph there already is the hero, so leave it (NH_STOCK_BLINDPILE=1 restores the remembered-pile export)
        int engulfed = 0; for (int q = 0; q < DR_CELLS; q++) if (o->glyphs[q] >= SWALLOW_OFF && o->glyphs[q] < SWALLOW_HI) { engulfed = 1; break; }
        if (engulfed) o->glyphs[S->d_r * DR_COLS + S->d_c] = S->map_raw[S->d_r * DR_COLS + S->d_c]; // engulfed: the fork shows the screen (nothing under the hero can be inspected)
        else if (!(o->blstats[25] & 0x220)) o->glyphs[S->d_r * DR_COLS + S->d_c] = dr_map_glyph(S, (short)under); // 0x220 = blind|hallucinating: the fork now conceals the hero's own cell for both (a hallucinating hero can no more identify what is underfoot than a blind one), so leave stock's raw hero glyph
        else o->glyphs[S->d_r * DR_COLS + S->d_c] = S->map_raw[S->d_r * DR_COLS + S->d_c];
    }
    // public form of an unidentified gem in the inventory: done here, after every probe, because each probe key refills
    // inv_glyphs from the engine (the peaceful/self farlooks run after the inventory pass in dr_boundary; 710dbc5d k104)
    if (o->inv_glyphs) for (int i = 0; i < DR_INV; i++) { int g = o->inv_glyphs[i]; if (g >= OBJ_OFF && g < CMAP_OFF && !S->discovered[g - OBJ_OFF]) o->inv_glyphs[i] = (short)(OBJ_OFF + dr_gem_canon(g - OBJ_OFF)); }
    int eb = S->engr_bits;
    for (int k = 0; k < DR_CELLS; k++) if (o->glyphs[k] >= SWALLOW_OFF && o->glyphs[k] < SWALLOW_HI) { eb |= 4; break; }
    if (o->internal) { o->internal[6] = eb; o->internal[5] = 0; } // slot 5 carried a prayer-cooldown estimate; the fork no longer exports one
    memcpy(S->type_prev, S->type_of_descr, sizeof S->type_prev);
}

#endif
