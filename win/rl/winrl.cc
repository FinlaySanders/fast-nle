/* Copyright (c) Facebook, Inc. and its affiliates. */
#include <array>
#include <cassert>
#include <cstring>
#include <deque>
#include <iostream>
#include <map>
#include <memory>
#include <stdio.h>
#include <string>
#include <unistd.h>
#include <vector>

extern "C" {
#include "hack.h"
extern "C" {
#include "nle.h" /* current_nle_ctx for per-env window-port state */
}
}

extern "C" {
#include "wintty.h"
}

extern "C" {
#include "nletypes.h"
}

/* MSan boundary check: the C engine is instrumented but libstdc++ is not,
   so once a string enters std::string its shadow is untrustworthy. Check
   engine-produced strings here, at the C -> C++ crossing, where the shadow
   is still real. No-op outside MemorySanitizer builds. */
#if defined(__has_feature)
#if __has_feature(memory_sanitizer)
#include <sanitizer/msan_interface.h>
#define MSAN_CHECK_CSTR(s)                                       \
    do {                                                         \
        if (s)                                                   \
            __msan_check_mem_is_initialized((s), strlen(s) + 1); \
    } while (0)
#endif
#endif
#ifndef MSAN_CHECK_CSTR
#define MSAN_CHECK_CSTR(s) ((void) 0)
#endif

#define USE_DEBUG_API 0

#if USE_DEBUG_API
#define DEBUG_API(x)    \
    do {                \
        std::cerr << x; \
    } while (0)
#else
#define DEBUG_API(x)
#endif

/*
 * We had to change xwaitforspace() in getline.c to tell the agent in a
 * --More-- situation that enter/return (ironically not necessarily space)
 * is required to continue.
 */

/* some hack.h macros. Can be undefined here. */
#undef Invisible
#undef Warning
#undef index
#undef msleep
#undef rindex
#undef wizard
#undef yn

extern "C" {
extern void *nle_yield(boolean);
extern nle_obs *nle_get_obs();
extern int nle_underfoot_glyphs();
}

/* Initial value of glyph_ buffer. Cf. display.c. */
const int nul_glyph = cmap_to_glyph(S_stone);

namespace nethack_rl
{
/* The former win_proc_calls debug deque is gone: it was the last
 * process-global in the window port, its std::string churn perturbed the
 * heap on every window call (a suspect for layout-dependent behavior),
 * and it drowned MemorySanitizer in uninstrumented-libstdc++ shadow
 * noise. DEBUG_API logging remains for tracing. */
#define in_yn_function (current_nle_ctx->rl_in_yn_function)
#define in_getlin (current_nle_ctx->rl_in_getlin)

// Glyphs provide instructions for windows to render the game (see display.h).
// At the start of the game, descriptions and properties of the object classes
// are shuffled (see o_init.c) while the glyphs pointing to these classes are
// not. This means glyph observations would always identify a 'wand of
// wishing', regardless of whether it is 'metal', 'balsa', &c.
//
// In this function, we map a glyph to correspond to its shuffled equivalent,
// following the logic used by tiles that also need to generate images from
// glyphs (c.f. o_init.c).  In practice this means:
//   BEFORE: looking up objclass on a glyph gives CORRECT name INCORRECT descr
//   AFTER: looking up objclass on a glyph gives INCORRECT name CORRECT descr
int
shuffled_glyph(int glyph)
{
    if glyph_is_normal_object (glyph) {
        return GLYPH_OBJ_OFF + objects[glyph_to_obj(glyph)].oc_descr_idx;
    }
    return glyph;
}

class NetHackRL
{
  public:
    NetHackRL(int &argc, char **argv);

    static void rl_init_nhwindows(int *argc, char **argv);
    static void rl_player_selection();
    static void rl_askname();
    static void rl_get_nh_event();
    static void rl_exit_nhwindows(const char *);
    static void rl_suspend_nhwindows(const char *);
    static void rl_resume_nhwindows();
    static winid rl_create_nhwindow(int type);
    static void rl_clear_nhwindow(winid wid);
    static void rl_display_nhwindow(winid wid, BOOLEAN_P block);
    static void rl_destroy_nhwindow(winid wid);
    static void rl_curs(winid wid, int x, int y);
    static void rl_putstr(winid wid, int attr, const char *text);
    static void rl_display_file(const char *filename, BOOLEAN_P must_exist);
    static void rl_start_menu(winid wid);
    static void rl_add_menu(winid wid, int glyph, const ANY_P *identifier,
                            CHAR_P ch, CHAR_P gch, int attr, const char *str,
                            BOOLEAN_P presel);
    static void rl_end_menu(winid wid, const char *prompt);
    static int rl_select_menu(winid wid, int how, MENU_ITEM_P **menu_list);
    static void rl_update_inventory();
    static void rl_mark_synch();
    static void rl_wait_synch();

    static void rl_cliparound(int x, int y);
    static void rl_print_glyph(winid wid, XCHAR_P x, XCHAR_P y, int glyph,
                               int bkglyph);
    static void rl_raw_print(const char *str);
    static void rl_raw_print_bold(const char *str);
    static int rl_nhgetch();
    static int rl_nh_poskey(int *x, int *y, int *mod);
    static void rl_nhbell();
    static int rl_doprev_message();
    static char rl_yn_function(const char *question, const char *choices,
                               CHAR_P def);
    static void rl_getlin(const char *prompt, char *line);
    static int rl_get_ext_cmd();
    static void rl_number_pad(int);
    static void rl_delay_output();
    static void rl_start_screen();
    static void rl_end_screen();

    static char *rl_getmsghistory(BOOLEAN_P init);
    static void rl_putmsghistory(const char *msg, BOOLEAN_P is_restoring);

    static void rl_outrip(winid wid, int how, time_t when);
    static void rl_status_init();

    static void rl_status_update(int fldidx, genericptr_t ptr, int chg,
                                 int percent, int color,
                                 unsigned long *colormasks);

    /* !status_updates mode: blstats_ cache pumps from botl.c (see
       nle_rl_bot_direct / nle_rl_timebot_direct below). */
    static void rl_bot_direct();
    static void rl_timebot_direct();
    static void rl_fill_obs_direct(nle_obs *);

  private:
    struct rl_menu_item {
        int glyph;           /* character glyph */
        anything identifier; /* user identifier */
        long count;          /* user count */
        std::string str;     /* description string */
        int attr;            /* string attribute */
        boolean selected;    /* TRUE if selected by user */
        char selector;       /* keyboard accelerator */
        char gselector;      /* group accelerator */
    };

    struct rl_window {
        int type;
        std::vector<rl_menu_item> menu_items;
        std::vector<std::string> strings;
    };

    struct rl_inventory_item {
        int glyph;
        // TODO: Don't heap allocate this stuff.
        std::string str;
        char letter;
        char object_class;
        // TODO: Don't heap allocate this stuff.
        std::string object_class_name;
    };

    // TODO: Don't heap allocate this stuff.
    std::vector<std::unique_ptr<rl_window> > windows_;

    std::array<int16_t, (COLNO - 1) * ROWNO> glyphs_;

    /* Output of mapglyph */
    std::array<uint8_t, (COLNO - 1) * ROWNO> chars_;
    std::array<uint8_t, (COLNO - 1) * ROWNO> colors_;
    std::array<uint8_t, (COLNO - 1) * ROWNO> specials_;

    /* Rows of the four display arrays changed since the last fill_obs;
       fill_obs copies only these into the obs buffers (obs rows not
       re-copied are unchanged from the previous fill, so the obs buffers
       must be stable per env — any buffer-pointer change forces a full
       copy). All-dirty on construction, map clears, not-in-game fills. */
    uint32_t dirty_rows_ = ~0u;
    const int16_t *last_glyphs_buf_ = nullptr;
    bool inv_synced_ = false;
    const uint8_t *last_chars_buf_ = nullptr;
    const uint8_t *last_colors_buf_ = nullptr;
    const uint8_t *last_specials_buf_ = nullptr;

    std::array<char, (COLNO - 1) * ROWNO * NLE_SCREEN_DESCRIPTION_LENGTH>
        screen_descriptions_;

    void store_glyph(XCHAR_P x, XCHAR_P y, int glyph);
    void store_mapped_glyph(int ch, int color, int special, XCHAR_P x,
                            XCHAR_P y);
    void store_screen_description(XCHAR_P x, XCHAR_P y, int glyph);

    void fill_obs(nle_obs *);
    void update_blstats_direct();
    int getch_method();

    std::array<std::string, MAXBLSTATS> status_;
    long condition_bits_;

    void update_blstats();
    long blstats_[NLE_BLSTATS_SIZE];

    void player_selection_method();
    void status_update_method(int fldidx, genericptr_t ptr, int, int percent,
                              int color, unsigned long *colormasks);

    void putstr_method(winid wid, int attr, const char *str);

    std::vector<rl_inventory_item> inventory_;

    void start_menu_method(winid wid);
    void add_menu_method(winid wid, int glyph, const anything *identifier,
                         char ch, char gch, int attr, const char *str,
                         bool preselected);
    void update_inventory_method();

    winid create_nhwindow_method(int type);
    void clear_nhwindow_method(winid wid);
    void display_nhwindow_method(winid wid, BOOLEAN_P block);
    void destroy_nhwindow_method(winid wid);
};

/* Per-env window-port object, stored on nle_ctx_t (raw pointer: a C
 * struct can't hold a unique_ptr). Created in rl_init_nhwindows, deleted
 * in rl_exit_nhwindows / error paths below. */
#define instance (*(NetHackRL **) &current_nle_ctx->rl_instance)

NetHackRL::NetHackRL(int &argc, char **argv) : glyphs_(), blstats_{}
{
    // create base window
    // (done in tty_init_nhwindows before this NetHackRL object got created).
    assert(BASE_WINDOW == 0);
    windows_.emplace_back(new rl_window({ NHW_BASE }));
    glyphs_.fill(nul_glyph);
}

void
NetHackRL::player_selection_method()
{
    windows_[BASE_WINDOW]->strings.clear();
}

/* Direct blstats refresh for the !status_updates (RL perf) mode: called
 * from bot() (botl.c) in place of the status pipeline, which drags
 * recalc_mapseen plus the status sprintf machinery behind it (~25% of
 * engine instructions at 16 envs) for a status line nothing reads.
 * Runs at exactly the pipeline's trigger points so cache staleness at the
 * observation point is bit-identical to the status_updates path (gated:
 * full-corpus golden replay with ",!status_updates" appended must match
 * the stock-recorded hashes). Delegates to update_blstats() for the field
 * list and computes the condition mask that BL_CONDITION delivery would
 * otherwise carry. */
void
NetHackRL::update_blstats_direct()
{
    update_blstats();

    /* Condition mask, mirroring botl.c's BL_CONDITION assembly. */
    long cond = 0L;
    if (Stoned)
        cond |= BL_MASK_STONE;
    if (Slimed)
        cond |= BL_MASK_SLIME;
    if (Strangled)
        cond |= BL_MASK_STRNGL;
    if (Sick && (u.usick_type & SICK_VOMITABLE) != 0)
        cond |= BL_MASK_FOODPOIS;
    if (Sick && (u.usick_type & SICK_NONVOMITABLE) != 0)
        cond |= BL_MASK_TERMILL;
    if (Blind)
        cond |= BL_MASK_BLIND;
    if (Deaf)
        cond |= BL_MASK_DEAF;
    if (Stunned)
        cond |= BL_MASK_STUN;
    if (Confusion)
        cond |= BL_MASK_CONF;
    if (Hallucination)
        cond |= BL_MASK_HALLU;
    if (Levitation)
        cond |= BL_MASK_LEV;
    if (Flying)
        cond |= BL_MASK_FLY;
    if (u.usteed)
        cond |= BL_MASK_RIDE;
    condition_bits_ = cond;
    blstats_[NLE_BL_CONDITION] = cond;
}

void
NetHackRL::fill_obs(nle_obs *obs)
{
    {
        static int verify = -1;
        if (verify < 0) verify = getenv("NLE_TYP_VERIFY") ? 1 : 0;
        if (verify && program_state.in_moveloop && !program_state.gameover)
            nh_typ_verify("fill_obs");
    }
    if (obs->prog_state) {
        obs->prog_state[0] = program_state.gameover;
        obs->prog_state[1] = program_state.panicking;
        obs->prog_state[2] = program_state.exiting;
        obs->prog_state[3] = program_state.in_moveloop;
        obs->prog_state[4] = program_state.in_impossible;
        obs->prog_state[5] = program_state.something_worth_saving;
        // TODO: Consider adding something_worth_saving.
        // Also consider adding ttyDisplay->inmore ...
    }
    /* Opt-in cheap fill for the intermediate keystrokes of a multi-key
       wrapper step: only prog_state/misc/message are exported. Honored
       only for healthy in-game fills so boot and gameover fills (and any
       consumer that never sets obs->partial, e.g. golden replays) are
       byte-identical to stock. */
    const boolean nle_partial =
        obs->partial && program_state.in_moveloop && !program_state.gameover;
    if (obs->internal && !nle_partial) {
        // From do.c. sstairs is a potential "special" staircase.
        boolean stairs_down =
            ((u.ux == xdnstair && u.uy == ydnstair)
             || (u.ux == sstairs.sx && u.uy == sstairs.sy && !sstairs.up));

        obs->internal[0] = deepest_lev_reached(false);
        obs->internal[1] = in_yn_function;
        obs->internal[2] = in_getlin;
        obs->internal[3] = xwaitingforspace;
        obs->internal[4] = stairs_down;
        obs->internal[5] = u.ublesscnt; /* prayer cooldown (was core seed) */
        /* Underfoot engraving state (was disp seed, then 0): 0 none,
           1 engraving present, 2 active legible Elbereth (the exact
           strict fuzzymatch monsters respect in onscary, incl. the
           engr_time drying gate). Readable in-game via ':' — fair. */
        {
            struct engr *uep = engr_at(u.ux, u.uy);
            obs->internal[6] =
                uep ? (sengr_at("Elbereth", u.ux, u.uy, TRUE) ? 2 : 1) : 0;
        }
        obs->internal[7] = u.uhunger;
        obs->internal[8] =
            u.urexp; /* score (careful! check botl_score() and end.c) */
    }
    if (obs->misc) {
        obs->misc[0] = in_yn_function;
        obs->misc[1] = in_getlin;
        obs->misc[2] = xwaitingforspace;
    }

    if ((!program_state.something_worth_saving && !program_state.in_moveloop)
        || !iflags.window_inited) {
        // Game not yet started (!something_worth_saving && !in_moveloop -- we
        // need both as something_worth_saving also becomes false in
        // really_done(), but we still want to see the "Do you want..."
        // questions) or windows have already been destroyed. Return zero
        // observations.
        obs->in_normal_game = false;
        if (obs->glyphs)
            std::fill_n(obs->glyphs, glyphs_.size(), nul_glyph);
        if (obs->chars)
            std::memset(obs->chars, 0, chars_.size()); /* Or fill with ' '? */
        if (obs->colors)
            std::memset(obs->colors, 0, colors_.size());
        if (obs->specials)
            std::memset(obs->specials, 0, specials_.size());
        if (obs->message)
            std::memset(obs->message, 0, NLE_MESSAGE_SIZE);
        if (obs->blstats)
            std::memset(obs->blstats, 0, sizeof(long) * NLE_BLSTATS_SIZE);
        if (obs->screen_descriptions)
            std::memset(obs->screen_descriptions, 0,
                        screen_descriptions_.size());
        dirty_rows_ = ~0u; /* obs no longer mirrors the display arrays */
        return;
    }
    obs->in_normal_game = true;

    if (nle_partial)
        goto fill_message; /* dirty_rows_/last_*_buf_ keep accumulating */

    {
        bool same_bufs = obs->glyphs == last_glyphs_buf_
                         && obs->chars == last_chars_buf_
                         && obs->colors == last_colors_buf_
                         && obs->specials == last_specials_buf_;
        uint32_t dirty = same_bufs ? dirty_rows_ : ~0u;
        last_glyphs_buf_ = obs->glyphs;
        last_chars_buf_ = obs->chars;
        last_colors_buf_ = obs->colors;
        last_specials_buf_ = obs->specials;
        if (dirty) {
            constexpr size_t W = COLNO - 1;
            for (size_t j = 0; j < ROWNO; ++j) {
                if (!(dirty & (1u << j)))
                    continue;
                size_t off = j * W;
                if (obs->glyphs)
                    std::memcpy(obs->glyphs + off, glyphs_.data() + off,
                                sizeof(int16_t) * W);
                if (obs->chars)
                    std::memcpy(obs->chars + off, chars_.data() + off, W);
                if (obs->colors)
                    std::memcpy(obs->colors + off, colors_.data() + off, W);
                if (obs->specials)
                    std::memcpy(obs->specials + off, specials_.data() + off,
                                W);
            }
            dirty_rows_ = 0;
        }
    }
    if (obs->glyphs && nle_underfoot_glyphs() && u.ux >= 1 && u.ux < COLNO
        && u.uy >= 0 && u.uy < ROWNO) {
        // Hero tile shows what the hero stands on (top object, else terrain)
        // instead of the hero glyph. Patched into obs->glyphs only, after the
        // dirty-row copy so it always wins; recomputed every fill.
        struct obj *under = vobj_at(u.ux, u.uy);
        int g = under ? obj_to_glyph(under, rn2_on_display_rng)
                      : back_to_glyph(u.ux, u.uy);
        obs->glyphs[(size_t) u.uy * (COLNO - 1) + (u.ux - 1)] =
            shuffled_glyph(g);
    }
fill_message:
    if (obs->message) {
        // TODO: This doesn't show anything in situations where there's too
        // many items at one tile, which will get displayed in a new window.

        if (in_yn_function) {
            // Special case. See tty_putstr: yn_function doesn't add to
            // toplines until after that frame is over. Use last string on
            // NHW_MESSAGE instead.
            assert(windows_.size() > WIN_MESSAGE);
            rl_window *win = windows_[WIN_MESSAGE].get();
            assert(win->type == NHW_MESSAGE);
            std::strncpy((char *) &obs->message[0],
                         win->strings.back().c_str(), NLE_MESSAGE_SIZE);
            /* The source std::string was written by uninstrumented
               libstdc++, so the shadow strncpy propagated here is noise.
               The real content was vetted by MSAN_CHECK_CSTR at putstr;
               mark the copy clean so the obs funnel only reports truth. */
#if defined(__has_feature)
#if __has_feature(memory_sanitizer)
            __msan_unpoison(obs->message, NLE_MESSAGE_SIZE);
#endif
#endif
        } else if (ttyDisplay->toplin) {
            // Copy toplines[], see topl.c.
            std::strncpy((char *) &obs->message[0], toplines,
                         NLE_MESSAGE_SIZE);
        } else {
            std::memset(obs->message, 0, NLE_MESSAGE_SIZE);
        }
    }
    if (obs->blstats && !nle_partial) {
        /* Both modes read the blstats_ cache here; it is pumped at bot()/
           timebot() time — by the status pipeline when status_updates is
           on, by nle_rl_bot_direct (botl.c) when it is off — so staleness
           semantics (e.g. energy regen between the last bot() and the
           observation point) are identical in both modes. */
        if (!u.dz) {
            /* Tricky hack: On "You descend the stairs.--More--" we are
               technically on the next floor, but we don't see it yet.
               But x, y needs to be updated at every step (not just when
               blstats changes for other reasons). But if we update it
               on the descend message, it will be the new position.
               u.dz stays nonzero for the env step after, too, but there
               blstats will be updated. */
            blstats_[NLE_BL_X] = u.ux - 1; /* x coordinate, 1 <= ux <= cols */
            blstats_[NLE_BL_Y] = u.uy;     /* y coordinate, 0 <= uy < rows */
            blstats_[NLE_BL_TIME] = moves;
        }
        std::memcpy(obs->blstats, &blstats_[0], sizeof(blstats_));
    }
    if (obs->inv_glyphs && !nle_partial) {
        /* The update_inventory callback only fires on inventory CHANGES;
           the starting inventory predates the moveloop, so sync once here.
           Gated on the inv obs being bound: unbound consumers (goldens)
           keep the exact display-RNG stream. */
        if (!inv_synced_) {
            update_inventory_method();
            inv_synced_ = true;
        }
        /* This iterates over the inventory_ vector list once per inv
           observation instead of only once. I guess that's fine. */
        int i = 0;
        for (const rl_inventory_item &item : inventory_) {
            obs->inv_glyphs[i++] = item.glyph;
        }
        for (; i < NLE_INVENTORY_SIZE; ++i) {
            obs->inv_glyphs[i] = NO_GLYPH;
        }
    }
    if (obs->inv_strs && !nle_partial) {
        int i = 0;
        for (const rl_inventory_item &item : inventory_) {
            int j = 0;
            for (int size = min(item.str.size(), NLE_INVENTORY_STR_LENGTH);
                 j < size; ++j) {
                obs->inv_strs[i++] = item.str[j];
            }
            for (; j < NLE_INVENTORY_STR_LENGTH; ++j) {
                obs->inv_strs[i++] = 0;
            }
        }
        for (; i < NLE_INVENTORY_SIZE * NLE_INVENTORY_STR_LENGTH; ++i) {
            obs->inv_strs[i] = 0;
        }
    }
    if (obs->inv_letters && !nle_partial) {
        int i = 0;
        for (const rl_inventory_item &item : inventory_) {
            obs->inv_letters[i++] = item.letter;
        }
        for (; i < NLE_INVENTORY_SIZE; ++i) {
            obs->inv_letters[i] = 0;
        }
    }
    if (obs->inv_oclasses && !nle_partial) {
        int i = 0;
        for (const rl_inventory_item &item : inventory_) {
            obs->inv_oclasses[i++] = item.object_class;
        }
        for (; i < NLE_INVENTORY_SIZE; ++i) {
            obs->inv_oclasses[i] = MAXOCLASSES;
        }
    }
    if (obs->inv_state && !nle_partial) {
        /* Identification-gated per-slot state: exactly what doname would
           print (objnam.c) — BUC only if bknown (never for gold), spe or
           charges only if known on classes that display them, erosion,
           poison, grease and worn markers always visible, fooproof only if
           rknown, typeknown when the appearance's identity is discovered.
           Read live off the invent chain (same walk order as inventory_);
           flag reads consume no RNG, so goldens (which leave this obs
           unbound) see an identical stream. */
        int i = 0;
        struct obj *otmp;
        for (otmp = invent; otmp && i < NLE_INVENTORY_SIZE;
             otmp = otmp->nobj, ++i) {
            signed char *st = obs->inv_state + i * NLE_INV_STATE_FIELDS;
            st[0] = (otmp->bknown && otmp->oclass != COIN_CLASS)
                        ? (otmp->cursed ? 1 : (otmp->blessed ? 3 : 2))
                        : 0;
            boolean shows_spe =
                otmp->oclass == WEAPON_CLASS || otmp->oclass == ARMOR_CLASS
                || otmp->oclass == RING_CLASS || otmp->oclass == WAND_CLASS
                || is_weptool(otmp) || objects[otmp->otyp].oc_charged;
            st[1] =
                (otmp->known && shows_spe) ? otmp->spe : (signed char) -128;
            st[2] = otmp->quan > 127 ? 127 : (signed char) otmp->quan;
            /* erosion bits are overloaded storage on other classes
               (orotten food, odiluted potions, norevive corpses) and doname
               only calls add_erosion_words from its weapon/armor/weptool
               and ball/chain branches — exporting the bits outside those
               classes would leak hidden state (e.g. rotten food). */
            boolean erodible =
                otmp->oclass == WEAPON_CLASS || otmp->oclass == ARMOR_CLASS
                || is_weptool(otmp) || otmp->oclass == BALL_CLASS
                || otmp->oclass == CHAIN_CLASS;
            st[3] = erodible ? (signed char) otmp->oeroded : 0;
            st[4] = erodible ? (signed char) otmp->oeroded2 : 0;
            st[5] = (signed char) (((otmp->owornmask
                                     & (W_ARMOR | W_ACCESSORY | W_SADDLE))
                                        ? 1
                                        : 0)
                                   | ((otmp->owornmask & W_WEP) ? 2 : 0)
                                   | ((otmp->owornmask & W_SWAPWEP) ? 4 : 0)
                                   | ((otmp->owornmask & W_QUIVER) ? 8 : 0)
                                   | (otmp->opoisoned ? 16 : 0)
                                   | (otmp->greased ? 32 : 0)
                                   | ((erodible && otmp->rknown
                                       && otmp->oerodeproof)
                                          ? 64
                                          : 0));
            st[6] =
                (otmp->dknown && objects[otmp->otyp].oc_name_known) ? 1 : 0;
            st[7] = 0;
        }
        std::memset(obs->inv_state + i * NLE_INV_STATE_FIELDS, 0,
                    (NLE_INVENTORY_SIZE - i) * NLE_INV_STATE_FIELDS);
    }
    if (obs->screen_descriptions && !nle_partial) {
        memcpy(obs->screen_descriptions, &screen_descriptions_,
               screen_descriptions_.size());
    }
}

int
NetHackRL::getch_method()
{
    fill_obs(nle_get_obs());
    int i = ((nle_obs *) nle_yield(TRUE))->action;

    /* NOT calling tty_nhgetch() but instead getting the input from
       the context switch. No stdin required. The following code is from
       tty_nhgetch. */
    if (WIN_MESSAGE != WIN_ERR && wins[WIN_MESSAGE])
        wins[WIN_MESSAGE]->wflags &= ~WIN_STOP;
    if (!i)
        i = '\033'; /* map NUL to ESC since nethack doesn't expect NUL */
    else if (i == EOF)
        i = '\033'; /* same for EOF */
    if (ttyDisplay && ttyDisplay->toplin == 1)
        ttyDisplay->toplin = 2;
    DEBUG_API("getch_method: action=" << i << ", xwaitingforspace="
                                      << xwaitingforspace << std::endl);
    return i;
}

void
NetHackRL::update_inventory_method()
{
    /* We cannot simply call display_inventory() as window.doc suggests,
       since we want to also use the tty window proc and we don't want the
       inventory to pop up whenever it changed. Instead, we keep our inventory
       list up to date via the following code adopted from display_pickinv
       in invent.c */

    struct obj *otmp;
    inventory_.clear();

    /* When no inv_* observation is bound, keep the obj_to_glyph calls
       (hallucination draws from the display RNG — the stream must stay
       byte-identical) but skip the item list entirely. The doname/
       let_to_name string formatting (which drags the whole singplur/
       strncmpi naming chain behind it) is only paid when inv_strs itself
       is bound; glyphs/letters/oclasses come straight off the obj chain. */
    const nle_obs *o = nle_get_obs();
    const bool want_items = !o || o->inv_glyphs || o->inv_strs
                            || o->inv_letters || o->inv_oclasses;
    const bool want_strs = !o || o->inv_strs;

    for (otmp = invent; otmp; otmp = otmp->nobj) {
        auto glyph = shuffled_glyph(obj_to_glyph(otmp, rn2_on_display_rng));
        if (!want_items)
            continue;
        inventory_.emplace_back(rl_inventory_item{
            glyph, want_strs ? std::string(doname(otmp)) : std::string(),
            otmp->invlet, otmp->oclass,
            want_strs ? std::string(let_to_name(otmp->oclass, false, false))
                      : std::string() });
    }
}

void
NetHackRL::store_glyph(XCHAR_P x, XCHAR_P y, int glyph)
{
    // 1 <= x < cols, 0 <= y < rows (!)
    size_t i = (x - 1) % (COLNO - 1);
    size_t j = y % ROWNO;
    size_t offset = j * (COLNO - 1) + i;

    // TODO: Glyphs might be taken from gbuf[y][x].glyph.
    glyphs_[offset] = shuffled_glyph(glyph);
    dirty_rows_ |= 1u << j;
}

void
NetHackRL::store_mapped_glyph(int ch, int color, int special, XCHAR_P x,
                              XCHAR_P y)
{
    // 1 <= x < cols, 0 <= y < rows (!)
    size_t i = (x - 1) % (COLNO - 1);
    size_t j = y % ROWNO;
    size_t offset = j * (COLNO - 1) + i;

    chars_[offset] = ch;
    colors_[offset] = color;
    specials_[offset] = special;
    dirty_rows_ |= 1u << j;
}

void
NetHackRL::store_screen_description(XCHAR_P x, XCHAR_P y, int glyph)
{
    // 1 <= x < cols, 0 <= y < rows (!)
    size_t i = (x - 1) % (COLNO - 1);
    size_t j = y % ROWNO;
    size_t offset = j * (COLNO - 1) + i;
    size_t start = offset * NLE_SCREEN_DESCRIPTION_LENGTH;

    // see code in src/do_name.c:538 auto_describe
    coord cc;
    int sym = 0;
    char tmpbuf[BUFSZ];
    const char *firstmatch = "unknown";

    cc.x = x;
    cc.y = y;

    if (do_screen_description(cc, TRUE, sym, tmpbuf, &firstmatch,
                              (struct permonst **) 0)) {
        strncpy((char *) &screen_descriptions_ + start, firstmatch,
                NLE_SCREEN_DESCRIPTION_LENGTH);
    } else {
        strncpy((char *) &screen_descriptions_ + start, "",
                NLE_SCREEN_DESCRIPTION_LENGTH);
    }
}

void
NetHackRL::update_blstats()
{
    int hitpoints;

    /* See botl.c. */
    int i = Upolyd ? u.mh : u.uhp;
    if (i < 0)
        i = 0;

    hitpoints = min(i, 9999);

    int max_hitpoints;
    i = Upolyd ? u.mhmax : u.uhpmax;
    max_hitpoints = min(i, 9999);

    /* Cf. botl.c. */
    blstats_[NLE_BL_X] = u.ux - 1;     /* x coordinate, 1 <= ux <= cols */
    blstats_[NLE_BL_Y] = u.uy;         /* y coordinate, 0 <= uy < rows */
    blstats_[NLE_BL_STR25] = ACURRSTR; /* strength 3..25 */
    blstats_[NLE_BL_STR125] = ACURR(A_STR);        /* strength 3..125   */
    blstats_[NLE_BL_DEX] = ACURR(A_DEX);           /* dexterity         */
    blstats_[NLE_BL_CON] = ACURR(A_CON);           /* constitution      */
    blstats_[NLE_BL_INT] = ACURR(A_INT);           /* intelligence      */
    blstats_[NLE_BL_WIS] = ACURR(A_WIS);           /* wisdom            */
    blstats_[NLE_BL_CHA] = ACURR(A_CHA);           /* charisma          */
    blstats_[NLE_BL_SCORE] = botl_score();         /* score             */
    blstats_[NLE_BL_HP] = hitpoints;               /* hitpoints         */
    blstats_[NLE_BL_HPMAX] = max_hitpoints;        /* max_hitpoints     */
    blstats_[NLE_BL_DEPTH] = depth(&u.uz);         /* depth             */
    blstats_[NLE_BL_GOLD] = money_cnt(invent);     /* gold              */
    blstats_[NLE_BL_ENE] = min(u.uen, 9999);       /* energy            */
    blstats_[NLE_BL_ENEMAX] = min(u.uenmax, 9999); /* max_energy        */
    blstats_[NLE_BL_AC] = u.uac;                   /* armor_class       */
    blstats_[NLE_BL_HD] = Upolyd ? (int) mons[u.umonnum].mlevel
                                 : 0;       /* monster level, hit-dice */
    blstats_[NLE_BL_XP] = u.ulevel;         /* experience level  */
    blstats_[NLE_BL_EXP] = u.uexp;          /* experience points */
    blstats_[NLE_BL_TIME] = moves;          /* time              */
    blstats_[NLE_BL_HUNGER] = u.uhs;        /* hunger state      */
    blstats_[NLE_BL_CAP] = near_capacity(); /* carrying capacity */
    blstats_[NLE_BL_DNUM] = u.uz.dnum;      /* dungeon number */
    blstats_[NLE_BL_DLEVEL] = u.uz.dlevel;  /* level number */
    blstats_[NLE_BL_CONDITION] = condition_bits_; /* condition bit mask */
    blstats_[NLE_BL_ALIGN] = u.ualign.type;       /* character alignment */
}

void
NetHackRL::status_update_method(int fldidx, genericptr_t ptr, int,
                                int percent, int color,
                                unsigned long *colormasks)
{
    if ((fldidx < BL_RESET) || (fldidx >= MAXBLSTATS))
        return;

    // Needs to be kept in sync with the switch statement in rl_status_update.
    if (fldidx == BL_FLUSH || fldidx == BL_RESET) {
        update_blstats();
        return;
    } else if (fldidx == BL_CONDITION) {
        long *condptr = (long *) ptr;
        condition_bits_ = *condptr;
        blstats_[NLE_BL_CONDITION] = condition_bits_;
        return;
    }

    char *text = (char *) ptr;
    MSAN_CHECK_CSTR(text);
    std::string status(text);
    if (fldidx == BL_GOLD) {
        // Handle gold glyph.
        char buf[BUFSZ];
        status = decode_mixed(buf, text);
    }
    status_[fldidx] = status;
}

void
NetHackRL::putstr_method(winid wid, int attr, const char *str)
{
    DEBUG_API("About to set strings on " << wid << std::endl);
    MSAN_CHECK_CSTR(str);
    windows_[wid]->strings.push_back(str);
}

winid
NetHackRL::create_nhwindow_method(int type)
{
    std::string window_type;
    switch (type) {
    case NHW_MAP:
        window_type = "map";
        break;
    case NHW_MESSAGE:
        window_type = "message";
        break;
    case NHW_STATUS:
        window_type = "status";
        break;
    case NHW_MENU:
        window_type = "menu";
        break;
    case NHW_TEXT:
        window_type = "text";
        break;
    }

    DEBUG_API("rl_create_nhwindow(type=" << window_type << ")");

    winid wid = tty_create_nhwindow(type);
    DEBUG_API(": wid == " << wid << std::endl);

    windows_.resize(wid + 1);
    assert(!windows_[wid]);

    DEBUG_API("ABOUT TO RESET " << wid << std::endl;);

    windows_[wid].reset(new rl_window{ type });
    return wid;
}

void
NetHackRL::clear_nhwindow_method(winid wid)
{
    auto &rl_win = windows_[wid];
    rl_win->menu_items.clear();
    rl_win->strings.clear();

    if (wid == WIN_MAP) {
        glyphs_.fill(nul_glyph);
        chars_.fill(' ');
        colors_.fill(0);
        specials_.fill(0);
        dirty_rows_ = ~0u;
        if (nle_get_obs()->screen_descriptions) {
            screen_descriptions_.fill(0);
        }
    }

    DEBUG_API("rl_clear_nhwindow(wid=" << wid << ")" << std::endl);
    tty_clear_nhwindow(wid);
}

void
NetHackRL::display_nhwindow_method(winid wid, BOOLEAN_P block)
{
    DEBUG_API("rl_display_nhwindow(wid=" << wid << ", block=" << block << ")"
                                         << std::endl);

    tty_display_nhwindow(wid, block);
}

void
NetHackRL::destroy_nhwindow_method(winid wid)
{
    DEBUG_API("rl_destroy_nhwindow(wid=" << wid << ")" << std::endl);
    windows_[wid].reset(nullptr);
    tty_destroy_nhwindow(wid);
}

void
NetHackRL::start_menu_method(winid wid)
{
    DEBUG_API("rl_start_menu(wid=" << wid << ")" << std::endl);
    tty_start_menu(wid);
    windows_[wid]->menu_items.clear();
}

void
NetHackRL::add_menu_method(
    winid wid,                  /* window to use, must be of type NHW_MENU */
    int glyph,                  /* glyph to display with item (not used) */
    const anything *identifier, /* what to return if selected */
    char ch,                    /* keyboard accelerator (0 = pick our own) */
    char gch,                   /* group accelerator (0 = no group) */
    int attr,                   /* attribute for string (like putstr()) */
    const char *str,            /* menu string */
    bool preselected            /* item is marked as selected */
)
{
    DEBUG_API("rl_add_menu" << std::endl);
    MSAN_CHECK_CSTR(str);
    tty_add_menu(wid, glyph, identifier, ch, gch, attr, str, preselected);

    /* We just add the menu item here. One problem with this method is that
       we won't see any updates happening during tty_select_menu. We could
       try to inspect tty's own menu items instead? */

    windows_[wid]->menu_items.emplace_back(rl_menu_item{
        glyph, *identifier, -1L, str, attr, preselected, ch, gch });
}

void
NetHackRL::rl_init_nhwindows(int *argc, char **argv)
{
    DEBUG_API("rl_init_nhwindows" << std::endl);
    tty_init_nhwindows(argc, argv);
    instance = new NetHackRL(*argc, argv);
}

void
NetHackRL::rl_player_selection()
{
    DEBUG_API("rl_player_selection" << std::endl);
    tty_player_selection();
    instance->player_selection_method();
}

void
NetHackRL::rl_askname()
{
    DEBUG_API("rl_askname" << std::endl);
    tty_askname();
}

void
NetHackRL::rl_get_nh_event()
{
    DEBUG_API("rl_get_nh_event" << std::endl);
    tty_get_nh_event();
}

void
NetHackRL::rl_exit_nhwindows(const char *c)
{
    DEBUG_API("rl_exit_nhwindows" << std::endl);
    delete instance;
    instance = nullptr;
    tty_exit_nhwindows(c);
}

void
NetHackRL::rl_suspend_nhwindows(const char *c)
{
    DEBUG_API("rl_suspend_nhwindows" << std::endl);
    tty_suspend_nhwindows(c);
}

void
NetHackRL::rl_resume_nhwindows()
{
    DEBUG_API("rl_resume_nhwindows" << std::endl);
    tty_resume_nhwindows();
}

winid
NetHackRL::rl_create_nhwindow(int type)
{
    // win_proc_calls code happens in method.
    return instance->create_nhwindow_method(type);
}

void
NetHackRL::rl_clear_nhwindow(winid wid)
{
    instance->clear_nhwindow_method(wid);
}

/* display_nhwindow(window, boolean blocking)
                -- Display the window on the screen.  If there is data
                   pending for output in that window, it should be sent.
                   If blocking is TRUE, display_nhwindow() will not
                   return until the data has been displayed on the screen,
                   and acknowledged by the user where appropriate.
                -- All calls are blocking in the tty window-port.
                -- Calling display_nhwindow(WIN_MESSAGE,???) will do a
                   --more--, if necessary, in the tty window-port. */
void
NetHackRL::rl_display_nhwindow(winid wid, BOOLEAN_P block)
{
    instance->display_nhwindow_method(wid, block);
}

void
NetHackRL::rl_destroy_nhwindow(winid wid)
{
    instance->destroy_nhwindow_method(wid);
}

void
NetHackRL::rl_curs(winid wid, int x, int y)
{
    DEBUG_API("rl_curs(wid=" << wid << ", x=" << x << ", y=" << y << ")"
                             << std::endl);
    DEBUG_API("rl_curs for window id " << wid << std::endl);
    tty_curs(wid, x, y);
}

void
NetHackRL::rl_putstr(winid wid, int attr, const char *text)
{
    DEBUG_API("rl_putstr(wid=" << wid << ", attr=" << attr
                               << ", text=" << text << ")" << std::endl);
    instance->putstr_method(wid, attr, text);
    tty_putstr(wid, attr, text);
}

void
NetHackRL::rl_display_file(const char *filename, BOOLEAN_P must_exist)
{
    DEBUG_API("rl_display_file" << std::endl);
    tty_display_file(filename, must_exist);
}

void
NetHackRL::rl_start_menu(winid wid)
{
    instance->start_menu_method(wid);
}

void
NetHackRL::rl_add_menu(winid wid, int glyph, const ANY_P *identifier,
                       CHAR_P ch, CHAR_P gch, int attr, const char *str,
                       BOOLEAN_P presel)
{
    instance->add_menu_method(wid, glyph, identifier, ch, gch, attr, str,
                              presel);
}

void
NetHackRL::rl_end_menu(winid wid, const char *prompt)
{
    DEBUG_API("rl_end_menu" << std::endl);
    tty_end_menu(wid, prompt);
}

int
NetHackRL::rl_select_menu(winid wid, int how, MENU_ITEM_P **menu_list)
{
    DEBUG_API("rl_select_menu");
    int response = tty_select_menu(wid, how, menu_list);
    DEBUG_API(" : " << response << std::endl);
    return response;
}

void
NetHackRL::rl_update_inventory()
{
    DEBUG_API("rl_update_inventory" << std::endl);
    instance->update_inventory_method();
}

void
NetHackRL::rl_mark_synch()
{
    DEBUG_API("rl_mark_synch" << std::endl);
    tty_mark_synch();
}

void
NetHackRL::rl_wait_synch()
{
    DEBUG_API("rl_wait_synch" << std::endl);
    tty_wait_synch();
}

void
NetHackRL::rl_cliparound(int x, int y)
{
#ifdef CLIPPING
    tty_cliparound(x, y);
#endif
}

/* print_glyph(window, x, y, glyph, bkglyph)
                -- Print the glyph at (x,y) on the given window.  Glyphs are
                   integers at the interface, mapped to whatever the window-
                   port wants (symbol, font, color, attributes, ...there's
                   a 1-1 map between glyphs and distinct things on the map).
                -- bkglyph is a background glyph for potential use by some
                   graphical or tiled environments to allow the depiction
                   to fall against a background consistent with the grid
                   around x,y. If bkglyph is NO_GLYPH, then the parameter
                   should be ignored (do nothing with it). */
void
NetHackRL::rl_print_glyph(winid wid, XCHAR_P x, XCHAR_P y, int glyph,
                          int bkglyph)
{
    int ch;
    int color;
    unsigned special;

    (void) mapglyph(glyph, &ch, &color, &special, x, y, 0);
#if USE_DEBUG_API
    DEBUG_API("rl_print_glyph(wid=" << wid << ", x=" << x << ", y=" << y
                                    << ", glyph=(ch='" << (char) ch
                                    << "', color=" << color
                                    << ", special=" << special);
    int bch;
    int bcolor;
    unsigned bspecial;
    (void) mapglyph(bkglyph, &bch, &bcolor, &bspecial, x, y, 0);
    DEBUG_API("), bkglyph=(ch='" << (char) bch << "', color=" << bcolor
                                 << ", special=" << bspecial << ")"
                                 << std::endl);
#endif

    // No win_proc_calls entry here.
    if (wid == WIN_MAP) {
        instance->store_glyph(x, y, glyph);
        if (glyph != nul_glyph && color == CLR_BLACK) {
            /* This will be 'bright black' (or blue) on tty so we change it to
             * make NLE's colors and tty_colors stay compatible. */
            color = iflags.wc2_darkgray ? 8 : CLR_BLUE;
        }
        instance->store_mapped_glyph(ch, color, special, x, y);
        if (nle_get_obs()->screen_descriptions) {
            instance->store_screen_description(x, y, glyph);
        }
    } else {
        DEBUG_API("Window id is " << wid << ". This shouldn't happen."
                                  << std::endl);
    }

    /* The tty map mirror (cursor walk + attr churn per cell) matters only
       when tty bytes are consumed (tty_* obs bound or ttyrec). The NLE
       obs above come from the store_* arrays either way. */
    if (!ttyDisplay || ttyDisplay->nle_emit)
        tty_print_glyph(wid, x, y, glyph, bkglyph);
}
void
NetHackRL::rl_raw_print(const char *str)
{
    DEBUG_API("rl_raw_print" << std::endl);
    MSAN_CHECK_CSTR(str);
    /* Not calling tty_raw_print(str); here or below as that
       uses puts/fputs. */
    xputs(str);
    putchar('\n');
    fflush(stdout);
}

void
NetHackRL::rl_raw_print_bold(const char *str)
{
    DEBUG_API("rl_raw_print_bold" << std::endl);
    MSAN_CHECK_CSTR(str);
    /* Not calling tty_raw_print_bold(str);, so above. */
    xputs(str);
    putchar('\n');
    fflush(stdout);
}

int
NetHackRL::rl_nhgetch()
{
    DEBUG_API("rl_nhgetch" << std::endl);
    int i = instance->getch_method();
    return i;
}

int
NetHackRL::rl_nh_poskey(int *x, int *y, int *mod)
{
    nhUse(x);
    nhUse(y);
    nhUse(mod);

    int action = rl_nhgetch();
    DEBUG_API("rl_nh_poskey: " << action << std::endl);
    return action;
    // Not calling nh_poskey, but no extra logic necessary here.
}

void
NetHackRL::rl_nhbell()
{
    DEBUG_API("rl_nhbell" << std::endl);
    return tty_nhbell();
}

int
NetHackRL::rl_doprev_message()
{
    DEBUG_API("rl_doprev_message" << std::endl);
    int result = tty_doprev_message();
    return result;
}

char
NetHackRL::rl_yn_function(const char *question_, const char *choices,
                          CHAR_P def)
{
    DEBUG_API("rl_yn_function" << std::endl);
    in_yn_function = true;
    char result = tty_yn_function(question_, choices, def);
    in_yn_function = false;
    return result;
}

void
NetHackRL::rl_getlin(const char *prompt, char *line)
{
    DEBUG_API("rl_getlin" << std::endl);
    in_getlin = true;
    tty_getlin(prompt, line);
    in_getlin = false;
}

int
NetHackRL::rl_get_ext_cmd()
{
    DEBUG_API("rl_get_ext_cmd" << std::endl);
    return tty_get_ext_cmd();
}

void
NetHackRL::rl_number_pad(int i)
{
    DEBUG_API("rl_number_pad" << std::endl);
    tty_number_pad(i);
}

void
NetHackRL::rl_delay_output()
{
    DEBUG_API("rl_delay_output" << std::endl);
    // No call to tty_delay_output() as we don't actually want delays.
}

void
NetHackRL::rl_start_screen()
{
    DEBUG_API("rl_start_screen" << std::endl);
    tty_start_screen();
}

void
NetHackRL::rl_end_screen()
{
    DEBUG_API("rl_end_screen" << std::endl);
    tty_end_screen();

    if (instance)
        // The only way instance can still be around is in an error situation.
        // Unfortunately, ZQM doesn't close properly when destructed via
        // global objects. So we do it here.
        delete instance;
    instance = nullptr;
}

void
NetHackRL::rl_outrip(winid wid, int how, time_t when)
{
    DEBUG_API("rl_outrip" << std::endl);
    genl_outrip(wid, how, when);
}

char *
NetHackRL::rl_getmsghistory(BOOLEAN_P init)
{
    DEBUG_API("rl_getmsghistory" << std::endl);
    return tty_getmsghistory(init);
}

void
NetHackRL::rl_putmsghistory(const char *msg, BOOLEAN_P is_restoring)
{
    DEBUG_API("rl_putmsghistory" << std::endl);
    MSAN_CHECK_CSTR(msg);
    tty_putmsghistory(msg, is_restoring);
}

void
NetHackRL::rl_status_init()
{
    DEBUG_API("rl_status_init" << std::endl);
    tty_status_init();
}

void
NetHackRL::rl_status_update(int fldidx, genericptr_t ptr, int chg,
                            int percent, int color, unsigned long *colormasks)
{
    DEBUG_API("rl_status_update" << std::endl);

    instance->status_update_method(fldidx, ptr, chg, percent, color,
                                   colormasks);
#ifdef STATUS_HILITES
    tty_status_update(fldidx, ptr, chg, percent, color, colormasks);
#endif
}

static void
rl_update_positionbar(char *chrs)
{
    DEBUG_API("rl_update_positionbar" << std::endl);
#ifdef POSITIONBAR
    tty_update_positionbar(chrs);
#endif
}

/* Mirrors bot(): bot_via_windowport delivers changed fields (incl.
   BL_CONDITION) then BL_FLUSH -> update_blstats(). */
void
NetHackRL::rl_bot_direct()
{
    if (current_nle_ctx && current_nle_ctx->rl_instance)
        instance->update_blstats_direct();
}

/* Mirrors timebot(): stat_update_time delivers BL_TIME (status_ string
   only) then BL_FLUSH -> update_blstats() with the CACHED condition mask
   (no BL_CONDITION delivery), so no condition recompute here. */
void
NetHackRL::rl_timebot_direct()
{
    if (current_nle_ctx && current_nle_ctx->rl_instance)
        instance->update_blstats();
}

/* Out-of-band observation export for nle_obs_refresh (nle.c): the same
   fill the next getch would run, without stepping the game. */
void
NetHackRL::rl_fill_obs_direct(nle_obs *obs)
{
    if (current_nle_ctx && current_nle_ctx->rl_instance)
        instance->fill_obs(obs);
}

} // namespace nethack_rl

/* botl.c hooks for the !status_updates (RL perf) mode: pump the blstats_
   cache at exactly the status pipeline's trigger points (bot / timebot)
   so observation-time staleness matches the pipeline bit-for-bit. */
extern "C" void
nle_rl_bot_direct(void)
{
    nethack_rl::NetHackRL::rl_bot_direct();
}

extern "C" void
nle_rl_timebot_direct(void)
{
    nethack_rl::NetHackRL::rl_timebot_direct();
}

extern "C" void
nle_rl_fill_obs(nle_obs *obs)
{
    nethack_rl::NetHackRL::rl_fill_obs_direct(obs);
}

extern const struct window_procs
    rl_procs; /* C++ const needs explicit extern linkage */
const struct window_procs rl_procs = {
    "rl",
    (WC_COLOR | WC_HILITE_PET | WC_INVERSE | WC_EIGHT_BIT_IN
     | WC_PERM_INVENT),
    (0
#if defined(SELECTSAVED)
     | WC2_SELECTSAVED
#endif
#if defined(STATUS_HILITES)
     | WC2_HILITE_STATUS | WC2_HITPOINTBAR | WC2_FLUSH_STATUS
     | WC2_RESET_STATUS
#endif
     | WC2_DARKGRAY | WC2_SUPPRESS_HIST | WC2_STATUSLINES),
    { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
      1 }, /* color availability */
    nethack_rl::NetHackRL::rl_init_nhwindows,
    nethack_rl::NetHackRL::rl_player_selection,
    nethack_rl::NetHackRL::rl_askname,
    nethack_rl::NetHackRL::rl_get_nh_event,
    nethack_rl::NetHackRL::rl_exit_nhwindows,
    nethack_rl::NetHackRL::rl_suspend_nhwindows,
    nethack_rl::NetHackRL::rl_resume_nhwindows,
    nethack_rl::NetHackRL::rl_create_nhwindow,
    nethack_rl::NetHackRL::rl_clear_nhwindow,
    nethack_rl::NetHackRL::rl_display_nhwindow,
    nethack_rl::NetHackRL::rl_destroy_nhwindow,
    nethack_rl::NetHackRL::rl_curs,
    nethack_rl::NetHackRL::rl_putstr,
    genl_putmixed,
    nethack_rl::NetHackRL::rl_display_file,
    nethack_rl::NetHackRL::rl_start_menu,
    nethack_rl::NetHackRL::rl_add_menu,
    nethack_rl::NetHackRL::rl_end_menu,
    nethack_rl::NetHackRL::rl_select_menu,
    genl_message_menu, /* no need for X-specific handling */
    nethack_rl::NetHackRL::rl_update_inventory,
    nethack_rl::NetHackRL::rl_mark_synch,
    nethack_rl::NetHackRL::rl_wait_synch,
#ifdef CLIPPING
    nethack_rl::NetHackRL::rl_cliparound,
#endif
#ifdef POSITIONBAR
    nethack_rl::rl_update_positionbar,
#endif
    nethack_rl::NetHackRL::rl_print_glyph,
    // NetHackRL::rl_print_glyph_compose,
    nethack_rl::NetHackRL::rl_raw_print,
    nethack_rl::NetHackRL::rl_raw_print_bold,
    nethack_rl::NetHackRL::rl_nhgetch,
    nethack_rl::NetHackRL::rl_nh_poskey,
    nethack_rl::NetHackRL::rl_nhbell,
    nethack_rl::NetHackRL::rl_doprev_message,
    nethack_rl::NetHackRL::rl_yn_function,
    nethack_rl::NetHackRL::rl_getlin,
    nethack_rl::NetHackRL::rl_get_ext_cmd,
    nethack_rl::NetHackRL::rl_number_pad,
    nethack_rl::NetHackRL::rl_delay_output,
#ifdef CHANGE_COLOR /* only a Mac option currently */
    donull,
    donull,
    donull,
    donull,
#endif
    /* other defs that really should go away (they're tty specific) */
    nethack_rl::NetHackRL::rl_start_screen,
    nethack_rl::NetHackRL::rl_end_screen,
#ifdef GRAPHIC_TOMBSTONE
    nethack_rl::NetHackRL::rl_outrip,
#else
    genl_outrip,
#endif
    tty_preference_update,
    nethack_rl::NetHackRL::rl_getmsghistory,
    nethack_rl::NetHackRL::rl_putmsghistory,
    nethack_rl::NetHackRL::rl_status_init,
    genl_status_finish,
    tty_status_enablefield,
    nethack_rl::NetHackRL::rl_status_update,
    genl_can_suspend_yes,
};
