/* NetHack 3.6	decl.c	$NHDT-Date: 1573869062 2019/11/16 01:51:02 $  $NHDT-Branch: NetHack-3.6 $:$NHDT-Revision: 1.149 $ */
/* Copyright (c) Stichting Mathematisch Centrum, Amsterdam, 1985. */
/*-Copyright (c) Michael Allison, 2009. */
/* NetHack may be freely redistributed.  See license for details. */

#include "hack.h"

/* fast-nle: every mutable global that used to be defined here now lives in
 * struct nh_ctx (see tools/globals.def; accessors generated into
 * nh_ctx_gen.h). What remains below is:
 *   - genuinely constant data (unchanged from stock),
 *   - nh_tmpl_* templates: the original non-zero initializers, kept at
 *     their original site so config-conditional values (e.g. sfcap's
 *     COMPRESS flags) stay correct; nh_ctx_new() memcpys them in.
 */

/* maze limits must be even; masking off lowest bit guarantees that */
const int nh_tmpl_x_maze_max = (COLNO - 1) & ~1;
const int nh_tmpl_y_maze_max = (ROWNO - 1) & ~1;

const char quitchars[] = " \r\n\033";
const char vowels[] = "aeiouAEIOU";
const char ynchars[] = "yn";
const char ynqchars[] = "ynq";
const char ynaqchars[] = "ynaq";
const char ynNaqchars[] = "yn#aq";

const char disclosure_options[] = "iavgco";

/* x/y/z deltas for the 10 movement directions (8 compass pts, 2 up/down) */
const schar xdir[10] = { -1, -1, 0, 1, 1, 1, 0, -1, 0, 0 };
const schar ydir[10] = { 0, -1, -1, -1, 0, 1, 1, 1, 0, 0 };
const schar zdir[10] = { 0, 0, 0, 0, 0, 0, 0, 0, 1, -1 };

#ifdef TEXTCOLOR
/*
 *  This must be the same order as used for buzz() in zap.c.
 *  (They're only used in mapglyph.c so probably shouldn't be here.)
 */
const int zapcolors[NUM_ZAP] = {
    HI_ZAP,     /* 0 - missile */
    CLR_ORANGE, /* 1 - fire */
    CLR_WHITE,  /* 2 - frost */
    HI_ZAP,     /* 3 - sleep */
    CLR_BLACK,  /* 4 - death */
    CLR_WHITE,  /* 5 - lightning */
    /* 3.6.3: poison gas zap used to be yellow and acid zap was green,
       which conflicted with the corresponding dragon colors */
    CLR_GREEN,  /* 6 - poison gas */
    CLR_YELLOW, /* 7 - acid */
};
#endif /* text color */

const int shield_static[SHIELD_COUNT] = {
    S_ss1, S_ss2, S_ss3, S_ss2, S_ss1, S_ss2, S_ss4, /* 7 per row */
    S_ss1, S_ss2, S_ss3, S_ss2, S_ss1, S_ss2, S_ss4,
    S_ss1, S_ss2, S_ss3, S_ss2, S_ss1, S_ss2, S_ss4,
};

const long nh_tmpl_moves = 1L;
const long nh_tmpl_monstermoves = 1L;

/* used to zero all elements of a struct obj and a struct monst */
NEARDATA const struct obj zeroobj = DUMMY;
NEARDATA const struct monst zeromonst = DUMMY;
/* used to zero out union any; initializer deliberately omitted */
NEARDATA const anything zeroany = { 0 }; /* explicit init: keeps it in rodata, not common */

/* fast-nle: the five arrays/structs below are never written; const-ified
 * (matching decl.h) instead of migrated, so they live in rodata. */
const struct c_color_names c_color_names = {
    "black",  "amber", "golden", "light blue", "red",   "green",
    "silver", "blue",  "purple", "white",      "orange"
};

const char *const c_obj_colors[16] = {
    "black",          /* CLR_BLACK */
    "red",            /* CLR_RED */
    "green",          /* CLR_GREEN */
    "brown",          /* CLR_BROWN */
    "blue",           /* CLR_BLUE */
    "magenta",        /* CLR_MAGENTA */
    "cyan",           /* CLR_CYAN */
    "gray",           /* CLR_GRAY */
    "transparent",    /* no_color */
    "orange",         /* CLR_ORANGE */
    "bright green",   /* CLR_BRIGHT_GREEN */
    "yellow",         /* CLR_YELLOW */
    "bright blue",    /* CLR_BRIGHT_BLUE */
    "bright magenta", /* CLR_BRIGHT_MAGENTA */
    "bright cyan",    /* CLR_BRIGHT_CYAN */
    "white",          /* CLR_WHITE */
};

const struct c_common_strings c_common_strings = {
    "Nothing happens.",
    "That's enough tries!",
    "That is a silly thing to %s.",
    "shudder for a moment.",
    "something",
    "Something",
    "You can move again.",
    "Never mind.",
    "vision quickly clears.",
    { "the", "your" },
    { "mon", "you" }
};

/* NOTE: the order of these words exactly corresponds to the
   order of oc_material values #define'd in objclass.h. */
const char *const materialnm[22] = {
    "mysterious", "liquid",  "wax",        "organic",
    "flesh",      "paper",   "cloth",      "leather",
    "wooden",     "bone",    "dragonhide", "iron",
    "metal",      "copper",  "silver",     "gold",
    "platinum",   "mithril", "plastic",    "glass",
    "gemstone",   "stone"
};

/* Global windowing data, defined here for multi-window-system support */
const winid nh_tmpl_WIN_MESSAGE = WIN_ERR;
const winid nh_tmpl_WIN_STATUS = WIN_ERR;
const winid nh_tmpl_WIN_MAP = WIN_ERR;
const winid nh_tmpl_WIN_INVEN = WIN_ERR;

#ifdef PREFIXES_IN_USE
const char *const fqn_prefix_names[PREFIX_COUNT] = {
    "hackdir",  "leveldir", "savedir",    "bonesdir",  "datadir",
    "scoredir", "lockdir",  "sysconfdir", "configdir", "troubledir"
};
#endif

const struct savefile_info nh_tmpl_sfcap = {
#ifdef NHSTDC
    0x00000000UL
#else
    0x00000000L
#endif
#if defined(COMPRESS) || defined(ZLIB_COMP)
        | SFI1_EXTERNALCOMP
#endif
#if defined(ZEROCOMP)
        | SFI1_ZEROCOMP
#endif
#if defined(RLECOMP)
        | SFI1_RLECOMP
#endif
    ,
#ifdef NHSTDC
    0x00000000UL, 0x00000000UL
#else
    0x00000000L, 0x00000000L
#endif
};

const struct savefile_info nh_tmpl_sfsaveinfo = {
#ifdef NHSTDC
    0x00000000UL
#else
    0x00000000L
#endif
#if defined(COMPRESS) || defined(ZLIB_COMP)
        | SFI1_EXTERNALCOMP
#endif
#if defined(ZEROCOMP)
        | SFI1_ZEROCOMP
#endif
#if defined(RLECOMP)
        | SFI1_RLECOMP
#endif
    ,
#ifdef NHSTDC
    0x00000000UL, 0x00000000UL
#else
    0x00000000L, 0x00000000L
#endif
};

#ifdef PANICTRACE
const char *ARGV0;
#endif

/* dummy routine used to force linkage */
void
decl_init()
{
    return;
}

/*decl.c*/
